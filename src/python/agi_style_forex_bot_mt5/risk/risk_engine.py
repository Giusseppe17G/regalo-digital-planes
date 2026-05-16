"""Fail-closed risk gate implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence

from agi_style_forex_bot_mt5.config import BotConfig
from agi_style_forex_bot_mt5.contracts import (
    AccountState,
    Direction,
    EntryType,
    MarketSnapshot,
    PositionState,
    RiskDecision,
    TradeSignal,
    utc_now,
)

from .emergency_kill_switch import EmergencyKillSwitch, KillSwitchState
from .portfolio_guard import PortfolioGuard, PortfolioLimits
from .position_sizer import PositionSizer, entry_reference_price


@dataclass(frozen=True)
class RiskRuntimeState:
    """Runtime-only inputs needed by the risk gate."""

    daily_equity_reference: float | None
    floating_drawdown_reference: float | None = None
    audit_confirmed: bool = False
    open_positions: Sequence[PositionState] = field(default_factory=tuple)
    snapshots_by_symbol: Mapping[str, MarketSnapshot] = field(default_factory=dict)
    open_position_risk_amounts: Mapping[int, float] = field(default_factory=dict)
    now_utc: datetime | None = None
    spread_limits_points: Mapping[str, float] = field(default_factory=dict)
    allowed_symbols: frozenset[str] | None = None
    consecutive_losses: int = 0
    max_consecutive_losses: int = 3
    cooldown_until_utc: datetime | None = None
    kill_switch: KillSwitchState | None = None


class RiskEngine:
    """Evaluate candidate trade signals against project safety limits."""

    def __init__(
        self,
        config: BotConfig | None = None,
        *,
        position_sizer: PositionSizer | None = None,
        portfolio_guard: PortfolioGuard | None = None,
        kill_switch: EmergencyKillSwitch | None = None,
    ) -> None:
        self.config = config or BotConfig()
        self.position_sizer = position_sizer or PositionSizer()
        self.portfolio_guard = portfolio_guard or PortfolioGuard(
            PortfolioLimits(
                max_open_trades=self.config.max_open_trades,
                max_open_trades_per_symbol=2,
                max_open_risk_pct=self.config.max_open_risk_pct,
            )
        )
        self.kill_switch = kill_switch or EmergencyKillSwitch()

    def evaluate(
        self,
        *,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
        account: AccountState,
        state: RiskRuntimeState,
    ) -> RiskDecision:
        """Return a fail-closed `RiskDecision`; never send or build orders."""

        checks: dict[str, object] = {}
        now = state.now_utc or utc_now()
        try:
            self.config.validate_safety()
            self._check_account(account, checks)
            self._check_kill_switch(state, now, checks)
            self._check_symbol(signal, snapshot, state, checks)
            self._check_freshness(signal, snapshot, now, checks)
            self._check_market_and_signal(signal, snapshot, checks)
            self._check_audit(state, checks)
            self._check_spread(snapshot, state, checks)
            daily_dd, floating_dd = self._check_drawdown(account, state, checks)
            self._check_frequency(state, now, checks)
            risk_pct = self._candidate_risk_pct(signal)
            sizing = self.position_sizer.size_for_risk(
                equity=account.equity,
                risk_pct=risk_pct,
                direction=signal.direction,
                entry_price=signal.entry_price
                if signal.entry_type != EntryType.MARKET
                else None,
                sl_price=signal.sl_price,
                snapshot=snapshot,
                requested_lot=signal.requested_lot,
            )
            checks["lot_sizing"] = {
                "status": "passed" if sizing.valid else "failed",
                "approved_lot": sizing.lot,
                "risk_pct": sizing.risk_pct,
                "reason": sizing.reason,
            }
            if not sizing.valid:
                return self._reject(
                    signal,
                    "INVALID_LOT",
                    sizing.reason or "could not calculate valid lot",
                    checks,
                    daily_dd,
                    floating_dd,
                )
            if sizing.risk_pct > self.config.max_risk_per_trade_pct + 1e-9:
                checks["max_risk_per_trade"] = {
                    "status": "failed",
                    "risk_pct": sizing.risk_pct,
                    "limit": self.config.max_risk_per_trade_pct,
                }
                return self._reject(
                    signal,
                    "MAX_RISK_PER_TRADE",
                    "candidate risk exceeds max risk per trade",
                    checks,
                    daily_dd,
                    floating_dd,
                )
            checks["max_risk_per_trade"] = {
                "status": "passed",
                "risk_pct": sizing.risk_pct,
                "limit": self.config.max_risk_per_trade_pct,
            }
            snapshots_by_symbol = {**state.snapshots_by_symbol, snapshot.symbol: snapshot}
            portfolio = self.portfolio_guard.evaluate(
                equity=account.equity,
                candidate_symbol=signal.symbol,
                candidate_risk_amount=sizing.risk_amount,
                open_positions=state.open_positions,
                snapshots_by_symbol=snapshots_by_symbol,
                open_position_risk_amounts=state.open_position_risk_amounts,
            )
            checks["portfolio"] = portfolio.checks
            if not portfolio.accepted:
                return self._reject(
                    signal,
                    portfolio.reject_code,
                    portfolio.reject_reason,
                    checks,
                    daily_dd,
                    floating_dd,
                    portfolio.open_risk_pct_after,
                )
            return RiskDecision(
                signal_id=signal.signal_id,
                accepted=True,
                approved_lot=sizing.lot,
                risk_amount_account_currency=sizing.risk_amount,
                open_risk_pct_after_trade=portfolio.open_risk_pct_after,
                daily_drawdown_pct=daily_dd,
                floating_drawdown_pct=floating_dd,
                checks=checks,
            )
        except RiskReject as reject:
            return self._reject(
                signal,
                reject.code,
                reject.reason,
                checks,
                reject.daily_drawdown_pct,
                reject.floating_drawdown_pct,
            )
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            checks["internal_error"] = {"status": "failed", "reason": str(exc)}
            return self._reject(signal, "INTERNAL_ERROR", str(exc), checks, 0.0, 0.0)

    def _candidate_risk_pct(self, signal: TradeSignal) -> float:
        requested = signal.risk_pct
        if requested is None:
            return self.config.max_risk_per_trade_pct
        if requested <= 0:
            raise RiskReject("RISK_CALCULATION_UNCERTAIN", "risk_pct must be positive")
        return min(requested, self.config.max_risk_per_trade_pct)

    def _check_account(self, account: AccountState, checks: dict[str, object]) -> None:
        checks["account_known"] = {"status": "passed"}
        if account.login is None or account.trade_mode is None:
            checks["account_known"] = {"status": "failed"}
            raise RiskReject("ACCOUNT_TYPE_UNKNOWN", "account type or login is unknown")
        checks["demo_only"] = {"status": "passed", "demo_only": self.config.demo_only}
        if self.config.demo_only and not account.is_demo:
            checks["demo_only"] = {"status": "failed", "demo_only": True}
            raise RiskReject("DEMO_ONLY_REAL_ACCOUNT", "demo-only mode blocks non-demo account")
        if not account.trade_allowed:
            checks["account_trade_allowed"] = {"status": "failed"}
            raise RiskReject("ACCOUNT_TRADE_DISABLED", "account trading is disabled")
        checks["account_trade_allowed"] = {"status": "passed"}
        if account.equity <= 0 or account.balance <= 0:
            checks["account_equity"] = {"status": "failed"}
            raise RiskReject("RISK_CALCULATION_UNCERTAIN", "account balance and equity must be positive")
        checks["account_equity"] = {
            "status": "passed",
            "balance": account.balance,
            "equity": account.equity,
        }

    def _check_kill_switch(
        self,
        state: RiskRuntimeState,
        now: datetime,
        checks: dict[str, object],
    ) -> None:
        allowed, reason = self.kill_switch.evaluate(state.kill_switch, now)
        checks["kill_switch"] = {"status": "passed" if allowed else "failed", "reason": reason}
        if not allowed:
            raise RiskReject("EMERGENCY_KILL_SWITCH", reason)

    def _check_symbol(
        self,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
        state: RiskRuntimeState,
        checks: dict[str, object],
    ) -> None:
        if state.allowed_symbols is not None and signal.symbol not in state.allowed_symbols:
            checks["symbol_allowed"] = {"status": "failed", "symbol": signal.symbol}
            raise RiskReject("SYMBOL_NOT_ALLOWED", "symbol is not allowed")
        checks["symbol_allowed"] = {"status": "passed", "symbol": signal.symbol}
        if signal.symbol != snapshot.symbol:
            checks["symbol_match"] = {"status": "failed"}
            raise RiskReject("MARKET_DATA_INVALID", "signal symbol does not match snapshot")
        checks["symbol_match"] = {"status": "passed"}

    def _check_freshness(
        self,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
        now: datetime,
        checks: dict[str, object],
    ) -> None:
        signal_age = (now - _as_utc(signal.created_at_utc)).total_seconds()
        snapshot_age = (now - _as_utc(snapshot.timestamp_utc)).total_seconds()
        checks["signal_age"] = {
            "status": "passed" if 0 <= signal_age <= self.config.max_signal_age_seconds else "failed",
            "age_seconds": signal_age,
            "limit": self.config.max_signal_age_seconds,
        }
        if signal_age < 0 or signal_age > self.config.max_signal_age_seconds:
            raise RiskReject("STALE_SIGNAL", "signal is stale or from the future")
        checks["market_snapshot_age"] = {
            "status": "passed"
            if 0 <= snapshot_age <= self.config.max_market_snapshot_age_seconds
            else "failed",
            "age_seconds": snapshot_age,
            "limit": self.config.max_market_snapshot_age_seconds,
        }
        if snapshot_age < 0 or snapshot_age > self.config.max_market_snapshot_age_seconds:
            raise RiskReject("MARKET_DATA_INVALID", "market snapshot is stale or from the future")

    def _check_market_and_signal(
        self,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
        checks: dict[str, object],
    ) -> None:
        try:
            snapshot.validate()
            signal.validate_against_snapshot(snapshot)
            self._check_stops_distance(signal, snapshot)
        except (TypeError, ValueError) as exc:
            code = "MISSING_SL" if not signal.sl_price else "MISSING_TP" if not signal.tp_price else "MARKET_DATA_INVALID"
            checks["market_and_signal"] = {"status": "failed", "reason": str(exc)}
            raise RiskReject(code, str(exc))
        checks["market_and_signal"] = {"status": "passed"}

    def _check_stops_distance(self, signal: TradeSignal, snapshot: MarketSnapshot) -> None:
        minimum_distance = snapshot.stops_level_points * snapshot.point
        if minimum_distance <= 0:
            return
        if signal.entry_type == EntryType.MARKET:
            if signal.direction == Direction.BUY:
                if signal.sl_price > snapshot.bid - minimum_distance:
                    raise ValueError("BUY SL violates stops level")
                if signal.tp_price < snapshot.bid + minimum_distance:
                    raise ValueError("BUY TP violates stops level")
            else:
                if signal.sl_price < snapshot.ask + minimum_distance:
                    raise ValueError("SELL SL violates stops level")
                if signal.tp_price > snapshot.ask - minimum_distance:
                    raise ValueError("SELL TP violates stops level")

    def _check_audit(self, state: RiskRuntimeState, checks: dict[str, object]) -> None:
        checks["audit_confirmed"] = {"status": "passed" if state.audit_confirmed else "failed"}
        if not state.audit_confirmed:
            raise RiskReject("INTERNAL_ERROR", "signal audit was not persisted or enqueued")

    def _check_spread(
        self,
        snapshot: MarketSnapshot,
        state: RiskRuntimeState,
        checks: dict[str, object],
    ) -> None:
        limit = state.spread_limits_points.get(snapshot.symbol, self.config.max_spread_points_default)
        if limit <= 0:
            checks["spread"] = {"status": "failed", "reason": "spread limit is invalid"}
            raise RiskReject("HIGH_SPREAD", "spread limit is invalid")
        status = "passed" if snapshot.spread_points <= limit else "failed"
        checks["spread"] = {"status": status, "spread_points": snapshot.spread_points, "limit": limit}
        if snapshot.spread_points > limit:
            raise RiskReject("HIGH_SPREAD", "spread exceeds configured limit")

    def _check_drawdown(
        self,
        account: AccountState,
        state: RiskRuntimeState,
        checks: dict[str, object],
    ) -> tuple[float, float]:
        if state.daily_equity_reference is None or state.daily_equity_reference <= 0:
            checks["daily_drawdown"] = {"status": "failed", "reason": "missing daily reference"}
            raise RiskReject("DAILY_DRAWDOWN_REFERENCE_MISSING", "daily equity reference is missing")
        daily_dd = max(0.0, ((state.daily_equity_reference - account.equity) / state.daily_equity_reference) * 100.0)
        checks["daily_drawdown"] = {
            "status": "passed" if daily_dd < self.config.max_daily_drawdown_pct else "failed",
            "drawdown_pct": daily_dd,
            "limit": self.config.max_daily_drawdown_pct,
        }
        if daily_dd >= self.config.max_daily_drawdown_pct:
            raise RiskReject(
                "DAILY_DRAWDOWN_LIMIT",
                "daily drawdown limit reached",
                daily_dd,
                0.0,
            )
        floating_reference = state.floating_drawdown_reference or account.balance
        if floating_reference <= 0:
            checks["floating_drawdown"] = {"status": "failed", "reason": "invalid floating reference"}
            raise RiskReject("RISK_CALCULATION_UNCERTAIN", "floating drawdown reference is invalid")
        floating_dd = max(0.0, ((floating_reference - account.equity) / floating_reference) * 100.0)
        checks["floating_drawdown"] = {
            "status": "passed" if floating_dd < self.config.max_floating_drawdown_pct else "failed",
            "drawdown_pct": floating_dd,
            "limit": self.config.max_floating_drawdown_pct,
        }
        if floating_dd >= self.config.max_floating_drawdown_pct:
            raise RiskReject(
                "FLOATING_DRAWDOWN_LIMIT",
                "floating drawdown limit reached",
                daily_dd,
                floating_dd,
            )
        return daily_dd, floating_dd

    def _check_frequency(
        self,
        state: RiskRuntimeState,
        now: datetime,
        checks: dict[str, object],
    ) -> None:
        checks["consecutive_losses"] = {
            "status": "passed"
            if state.consecutive_losses < state.max_consecutive_losses
            else "failed",
            "value": state.consecutive_losses,
            "limit": state.max_consecutive_losses,
        }
        if state.consecutive_losses >= state.max_consecutive_losses:
            raise RiskReject("CONSECUTIVE_LOSS_LIMIT", "consecutive loss limit reached")
        cooldown_active = state.cooldown_until_utc is not None and now < state.cooldown_until_utc
        checks["cooldown"] = {
            "status": "failed" if cooldown_active else "passed",
            "until": state.cooldown_until_utc.isoformat() if state.cooldown_until_utc else "",
        }
        if cooldown_active:
            raise RiskReject("COOLDOWN_ACTIVE", "cooldown is active")

    def _reject(
        self,
        signal: TradeSignal,
        code: str,
        reason: str,
        checks: Mapping[str, object],
        daily_drawdown_pct: float,
        floating_drawdown_pct: float,
        open_risk_pct_after: float = 0.0,
    ) -> RiskDecision:
        return RiskDecision(
            signal_id=signal.signal_id,
            accepted=False,
            reject_code=code or "INTERNAL_ERROR",
            reject_reason=reason,
            approved_lot=0.0,
            risk_amount_account_currency=0.0,
            open_risk_pct_after_trade=open_risk_pct_after,
            daily_drawdown_pct=daily_drawdown_pct,
            floating_drawdown_pct=floating_drawdown_pct,
            checks=checks,
        )


class RiskReject(Exception):
    """Internal exception used to stop evaluation at first unsafe condition."""

    def __init__(
        self,
        code: str,
        reason: str,
        daily_drawdown_pct: float = 0.0,
        floating_drawdown_pct: float = 0.0,
    ) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.daily_drawdown_pct = daily_drawdown_pct
        self.floating_drawdown_pct = floating_drawdown_pct


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
