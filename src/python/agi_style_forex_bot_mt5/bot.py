"""Demo/shadow orchestration for the first functional bot version."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from .config import BotConfig
from .contracts import (
    AccountState,
    Direction,
    EntryType,
    Environment,
    Event,
    MarketSnapshot,
    Severity,
    SignalAction,
    TradeSignal,
)
from .execution import ShadowExecutionEngine, ShadowOrder
from .risk import RiskEngine, RiskRuntimeState
from .strategy import evaluate_ensemble
from .telemetry import JsonlAuditLogger, TelegramNotifier, TelemetryDatabase


_DEFAULT_LOGGER = object()


class AuditUnavailableError(RuntimeError):
    """Raised when required local audit persistence is unavailable."""


@dataclass(frozen=True)
class BotCycleResult:
    """Summary returned by a single shadow/demo bot cycle."""

    run_id: str
    signal_id: str | None
    strategy_action: SignalAction
    strategy_score: float
    risk_accepted: bool
    risk_reject_code: str
    execution_attempted: bool
    mode: str
    reasons: tuple[str, ...]
    shadow_order_created: bool = False
    shadow_order_id: str | None = None


class ShadowDemoBot:
    """Coordinate data, strategy, risk and audit without enabling live trading."""

    def __init__(
        self,
        *,
        config: BotConfig | None = None,
        audit_logger: JsonlAuditLogger | None | object = _DEFAULT_LOGGER,
        database: TelemetryDatabase | None = None,
        telegram_notifier: TelegramNotifier | None = None,
        risk_engine: RiskEngine | None = None,
        shadow_execution_engine: ShadowExecutionEngine | None = None,
        run_id: str | None = None,
    ) -> None:
        self.config = config or BotConfig()
        self.config.validate_safety()
        if audit_logger is _DEFAULT_LOGGER:
            self.audit_logger: JsonlAuditLogger | None = JsonlAuditLogger(
                Path("data") / "logs",
                max_file_mb=self.config.max_jsonl_file_mb,
            )
        else:
            self.audit_logger = audit_logger  # type: ignore[assignment]
        self.database = database
        self.telegram_notifier = telegram_notifier
        self.risk_engine = risk_engine or RiskEngine(self.config)
        self.shadow_execution_engine = shadow_execution_engine or ShadowExecutionEngine()
        self.run_id = run_id or f"run_{uuid4().hex}"
        if self.audit_logger is None and self.database is None:
            raise AuditUnavailableError("at least one local audit sink is required")

    def run_once(
        self,
        *,
        snapshot: MarketSnapshot,
        features: Mapping[str, Any],
        account: AccountState,
        mode: str = "shadow",
    ) -> BotCycleResult:
        """Run one fail-closed decision cycle.

        The first functional release supports shadow/demo decisioning only.
        Execution is intentionally not attempted while `shadow_mode` is true,
        which is the mandatory default.
        """

        try:
            self._audit(
                severity=Severity.INFO,
                module="bot",
                event_type="BOT_STARTED",
                message="bot cycle started",
                correlation_id=self.run_id,
                payload={"mode": mode, "shadow_mode": self.config.shadow_mode},
                notify=True,
            )
            snapshot.validate()
            self._audit_account_snapshot(account, snapshot)
            strategy_signal = evaluate_ensemble(snapshot, features, mode=mode)
        except Exception as exc:
            self._critical_error("critical error before strategy evaluation", exc)
            return BotCycleResult(
                run_id=self.run_id,
                signal_id=None,
                strategy_action=SignalAction.NONE,
                strategy_score=0,
                risk_accepted=False,
                risk_reject_code="CRITICAL_ERROR",
                execution_attempted=False,
                mode=mode,
                reasons=(str(exc),),
                shadow_order_created=False,
                shadow_order_id=None,
            )
        signal_id: str | None = None
        risk_accepted = False
        risk_reject_code = ""
        reasons = tuple(strategy_signal.reasons)

        self._audit(
            severity=Severity.INFO,
            module="strategy",
            event_type="SIGNAL_DETECTED",
            message=f"strategy emitted {strategy_signal.action.value}",
            correlation_id=f"strategy_{self.run_id}",
            payload={
                "action": strategy_signal.action.value,
                "score": strategy_signal.score,
                "reasons": strategy_signal.reasons,
                "metadata": dict(strategy_signal.metadata),
            },
            symbol=snapshot.symbol,
            notify=True,
        )
        self._audit(
            severity=Severity.INFO,
            module="strategy",
            event_type="SIGNAL_GENERATED",
            message=f"strategy emitted {strategy_signal.action.value}",
            correlation_id=f"strategy_{self.run_id}",
            payload={
                "action": strategy_signal.action.value,
                "score": strategy_signal.score,
                "reasons": strategy_signal.reasons,
                "metadata": dict(strategy_signal.metadata),
            },
            symbol=snapshot.symbol,
        )

        if strategy_signal.action == SignalAction.NONE:
            self._audit(
                severity=Severity.INFO,
                module="strategy",
                event_type="SIGNAL_REJECTED",
                message="strategy returned NONE",
                correlation_id=f"strategy_{self.run_id}",
                payload={"reasons": strategy_signal.reasons},
                symbol=snapshot.symbol,
                notify=True,
            )
            self._audit_bot_stopped(mode)
            return BotCycleResult(
                run_id=self.run_id,
                signal_id=None,
                strategy_action=strategy_signal.action,
                strategy_score=strategy_signal.score,
                risk_accepted=False,
                risk_reject_code="STRATEGY_NONE",
                execution_attempted=False,
                mode=mode,
                reasons=reasons,
            )

        try:
            trade_signal = self._trade_signal_from_strategy(snapshot, strategy_signal)
        except Exception as exc:
            self._critical_error("trade signal construction failed", exc)
            self._audit_bot_stopped(mode)
            return BotCycleResult(
                run_id=self.run_id,
                signal_id=None,
                strategy_action=strategy_signal.action,
                strategy_score=strategy_signal.score,
                risk_accepted=False,
                risk_reject_code="CRITICAL_ERROR",
                execution_attempted=False,
                mode=mode,
                reasons=(str(exc),),
                shadow_order_created=False,
                shadow_order_id=None,
            )
        signal_id = trade_signal.signal_id
        self._audit(
            severity=Severity.INFO,
            module="strategy",
            event_type="TRADE_SIGNAL_CREATED",
            message="trade signal candidate created",
            correlation_id=signal_id,
            signal_id=signal_id,
            symbol=snapshot.symbol,
            payload={
                "direction": trade_signal.direction.value,
                "sl_price": trade_signal.sl_price,
                "tp_price": trade_signal.tp_price,
                "confidence": trade_signal.confidence,
                "reason": trade_signal.reason,
            },
        )

        risk_decision = self.risk_engine.evaluate(
            signal=trade_signal,
            snapshot=snapshot,
            account=account,
            state=RiskRuntimeState(
                daily_equity_reference=account.balance,
                floating_drawdown_reference=account.balance,
                audit_confirmed=True,
            ),
        )
        risk_accepted = risk_decision.accepted
        risk_reject_code = risk_decision.reject_code
        self._audit(
            severity=Severity.INFO if risk_decision.accepted else Severity.WARNING,
            module="risk",
            event_type="SIGNAL_ACCEPTED" if risk_decision.accepted else "RISK_REJECTED",
            message="risk accepted signal" if risk_decision.accepted else risk_decision.reject_reason,
            correlation_id=signal_id,
            signal_id=signal_id,
            symbol=snapshot.symbol,
            payload={
                "accepted": risk_decision.accepted,
                "reject_code": risk_decision.reject_code,
                "reject_reason": risk_decision.reject_reason,
                "approved_lot": risk_decision.approved_lot,
                "checks": dict(risk_decision.checks),
            },
            notify=not risk_decision.accepted,
        )

        if not risk_decision.accepted:
            self._audit_bot_stopped(mode)
            return BotCycleResult(
                run_id=self.run_id,
                signal_id=signal_id,
                strategy_action=strategy_signal.action,
                strategy_score=strategy_signal.score,
                risk_accepted=False,
                risk_reject_code=risk_reject_code,
                execution_attempted=False,
                mode=mode,
                reasons=reasons,
                shadow_order_created=False,
                shadow_order_id=None,
            )

        if self.config.shadow_mode:
            try:
                shadow_order = self._create_shadow_order(
                    signal=trade_signal,
                    risk_decision=risk_decision,
                    snapshot=snapshot,
                    strategy_score=strategy_signal.score,
                    reasons=reasons,
                )
            except Exception as exc:
                self._critical_error("shadow order creation failed", exc)
                self._audit_bot_stopped(mode)
                return BotCycleResult(
                    run_id=self.run_id,
                    signal_id=signal_id,
                    strategy_action=strategy_signal.action,
                    strategy_score=strategy_signal.score,
                    risk_accepted=risk_accepted,
                    risk_reject_code="SHADOW_ORDER_FAILED",
                    execution_attempted=False,
                    mode=mode,
                    reasons=(str(exc),),
                    shadow_order_created=False,
                    shadow_order_id=None,
                )
            self._audit(
                severity=Severity.INFO,
                module="execution",
                event_type="SHADOW_ORDER_CREATED",
                message="shadow order created; MT5 order_send not called",
                correlation_id=signal_id,
                signal_id=signal_id,
                symbol=snapshot.symbol,
                payload=shadow_order.as_record(),
                notify=True,
            )
            self._audit(
                severity=Severity.INFO,
                module="execution",
                event_type="EXECUTION_SKIPPED",
                message="shadow mode blocks MT5 order_send",
                correlation_id=signal_id,
                signal_id=signal_id,
                symbol=snapshot.symbol,
                payload={
                    "shadow_mode": True,
                    "shadow_order_id": shadow_order.order_id,
                    "risk_accepted": risk_decision.accepted,
                },
            )
            self._audit_bot_stopped(mode)
            return BotCycleResult(
                run_id=self.run_id,
                signal_id=signal_id,
                strategy_action=strategy_signal.action,
                strategy_score=strategy_signal.score,
                risk_accepted=risk_accepted,
                risk_reject_code=risk_reject_code,
                execution_attempted=False,
                mode=mode,
                reasons=reasons,
                shadow_order_created=True,
                shadow_order_id=shadow_order.order_id,
            )

        self._audit(
            severity=Severity.CRITICAL,
            module="execution",
            event_type="EXECUTION_BLOCKED",
            message="non-shadow execution is outside the initial release",
            correlation_id=signal_id,
            signal_id=signal_id,
            symbol=snapshot.symbol,
            payload={"demo_only": self.config.demo_only},
        )
        self._audit_bot_stopped(mode)
        return BotCycleResult(
            run_id=self.run_id,
            signal_id=signal_id,
            strategy_action=strategy_signal.action,
            strategy_score=strategy_signal.score,
            risk_accepted=risk_accepted,
            risk_reject_code="EXECUTION_OUT_OF_SCOPE",
            execution_attempted=False,
            mode=mode,
            reasons=reasons,
            shadow_order_created=False,
            shadow_order_id=None,
        )

    def _audit_account_snapshot(self, account: AccountState, snapshot: MarketSnapshot) -> None:
        self._audit(
            severity=Severity.INFO,
            module="account",
            event_type="ACCOUNT_SNAPSHOT",
            message="account snapshot captured",
            correlation_id=self.run_id,
            symbol=snapshot.symbol,
            payload={
                "login": account.login,
                "trade_mode": account.trade_mode,
                "balance": account.balance,
                "equity": account.equity,
                "margin_free": account.margin_free,
                "currency": account.currency,
                "is_demo": account.is_demo,
                "trade_allowed": account.trade_allowed,
            },
            notify=True,
        )

    def _create_shadow_order(
        self,
        *,
        signal: TradeSignal,
        risk_decision: Any,
        snapshot: MarketSnapshot,
        strategy_score: float,
        reasons: tuple[str, ...],
    ) -> ShadowOrder:
        shadow_order = self.shadow_execution_engine.create_order(
            signal=signal,
            risk_decision=risk_decision,
            snapshot=snapshot,
            strategy_score=strategy_score,
            reasons=reasons,
        )
        if self.database is not None:
            inserted = self.database.insert_record(
                "orders",
                shadow_order.as_record(),
                idempotency_key=shadow_order.idempotency_key,
            )
            if not inserted:
                existing = self.database.fetch_by_idempotency_key(
                    "orders",
                    shadow_order.idempotency_key,
                )
                if existing is not None:
                    payload = existing["payload_json"]
                    return _shadow_order_from_payload(payload)
        return shadow_order

    def _audit_bot_stopped(self, mode: str) -> None:
        self._audit(
            severity=Severity.INFO,
            module="bot",
            event_type="BOT_STOPPED",
            message="bot cycle stopped",
            correlation_id=self.run_id,
            payload={"mode": mode, "shadow_mode": self.config.shadow_mode},
            notify=True,
        )

    def _critical_error(self, message: str, exc: Exception) -> None:
        try:
            self._audit(
                severity=Severity.CRITICAL,
                module="bot",
                event_type="CRITICAL_ERROR",
                message=message,
                correlation_id=self.run_id,
                payload={"error": str(exc), "error_type": type(exc).__name__},
                notify=True,
            )
        except Exception:
            pass

    def _trade_signal_from_strategy(
        self,
        snapshot: MarketSnapshot,
        strategy_signal: Any,
    ) -> TradeSignal:
        direction = Direction.BUY if strategy_signal.action == SignalAction.BUY else Direction.SELL
        reference = snapshot.ask if direction == Direction.BUY else snapshot.bid
        atr = _positive_float(strategy_signal.metadata.get("atr")) or snapshot.point * 100
        stop_distance = max(atr, snapshot.stops_level_points * snapshot.point * 2)
        take_profit_distance = stop_distance * 1.8
        if direction == Direction.BUY:
            sl_price = reference - stop_distance
            tp_price = reference + take_profit_distance
        else:
            sl_price = reference + stop_distance
            tp_price = reference - take_profit_distance
        signal = TradeSignal(
            signal_id=TradeSignal.new_id(),
            created_at_utc=snapshot.timestamp_utc,
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            direction=direction,
            entry_type=EntryType.MARKET,
            sl_price=round(sl_price, snapshot.digits),
            tp_price=round(tp_price, snapshot.digits),
            risk_pct=self.config.max_risk_per_trade_pct,
            confidence=min(1.0, max(0.0, strategy_signal.score / 100)),
            strategy_name=strategy_signal.strategy_name,
            strategy_version=str(strategy_signal.metadata.get("version", "0.1.0")),
            reason="; ".join(strategy_signal.reasons),
            metadata=dict(strategy_signal.metadata),
        )
        signal.validate_against_snapshot(snapshot)
        return signal

    def _audit(
        self,
        *,
        severity: Severity,
        module: str,
        event_type: str,
        message: str,
        correlation_id: str,
        payload: Mapping[str, Any],
        signal_id: str | None = None,
        symbol: str | None = None,
        notify: bool = False,
    ) -> Event:
        if self.audit_logger is None and self.database is None:
            raise AuditUnavailableError("local audit sink is unavailable")
        event = Event.create(
            run_id=self.run_id,
            environment=Environment.DEMO,
            severity=severity,
            module=module,
            event_type=event_type,
            message=message,
            correlation_id=correlation_id,
            payload=payload,
            signal_id=signal_id,
            symbol=symbol,
        )
        if self.audit_logger is not None:
            self.audit_logger.append_event(event)
        if self.database is not None:
            self.database.insert_event(event)
        if notify and self.telegram_notifier is not None:
            try:
                result = self.telegram_notifier.notify_event(event)
                if result.status == "FAILED":
                    self._audit(
                        severity=Severity.ERROR,
                        module="telegram",
                        event_type="TELEGRAM_ERROR",
                        message=result.error or "telegram notification failed",
                        correlation_id=event.correlation_id,
                        payload={"telegram_message_id": result.telegram_message_id},
                        signal_id=signal_id,
                        symbol=symbol,
                        notify=False,
                    )
            except Exception as exc:
                self._audit(
                    severity=Severity.ERROR,
                    module="telegram",
                    event_type="TELEGRAM_ERROR",
                    message=str(exc),
                    correlation_id=event.correlation_id,
                    payload={"error_type": type(exc).__name__},
                    signal_id=signal_id,
                    symbol=symbol,
                    notify=False,
                )
        return event


def _positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _shadow_order_from_payload(payload_json: str) -> ShadowOrder:
    import json

    payload = json.loads(payload_json)
    return ShadowOrder(
        order_id=str(payload["order_id"]),
        idempotency_key=str(payload["idempotency_key"]),
        signal_id=str(payload["signal_id"]),
        symbol=str(payload["symbol"]),
        side=str(payload["side"]),
        score=float(payload["score"]),
        reasons=tuple(payload.get("reasons", ())),
        entry_price=float(payload["entry_price"]),
        sl=float(payload["sl"]),
        tp=float(payload["tp"]),
        lot=float(payload["lot"]),
        risk_pct=float(payload["risk_pct"]),
        timestamp=str(payload["timestamp"]),
        mode=str(payload.get("mode", "shadow")),
        status=str(payload.get("status", "created")),
    )
