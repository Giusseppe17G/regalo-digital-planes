"""Portfolio-level risk checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from agi_style_forex_bot_mt5.contracts import MarketSnapshot, PositionState

from .position_sizer import risk_amount_for_lot


@dataclass(frozen=True)
class PortfolioLimits:
    """Hard portfolio limits from the project safety policy."""

    max_open_trades: int = 10
    max_open_trades_per_symbol: int = 2
    max_open_risk_pct: float = 5.0


@dataclass(frozen=True)
class PortfolioResult:
    """Result of checking open exposure after the candidate trade."""

    accepted: bool
    reject_code: str = ""
    reject_reason: str = ""
    open_risk_amount_before: float = 0.0
    open_risk_pct_after: float = 0.0
    checks: Mapping[str, object] = field(default_factory=dict)


class PortfolioGuard:
    """Validate trade count and open risk exposure."""

    def __init__(self, limits: PortfolioLimits | None = None) -> None:
        self.limits = limits or PortfolioLimits()

    def evaluate(
        self,
        *,
        equity: float,
        candidate_symbol: str,
        candidate_risk_amount: float,
        open_positions: Sequence[PositionState],
        snapshots_by_symbol: Mapping[str, MarketSnapshot],
        open_position_risk_amounts: Mapping[int, float] | None = None,
    ) -> PortfolioResult:
        """Check global count, symbol count and total open risk."""

        checks: dict[str, object] = {}
        if equity <= 0:
            return PortfolioResult(
                False,
                "RISK_CALCULATION_UNCERTAIN",
                "equity must be positive to calculate open risk",
                checks={"equity": {"status": "failed"}},
            )
        open_after = len(open_positions) + 1
        checks["max_open_trades"] = {
            "status": "passed" if open_after <= self.limits.max_open_trades else "failed",
            "open_after": open_after,
            "limit": self.limits.max_open_trades,
        }
        if open_after > self.limits.max_open_trades:
            return PortfolioResult(
                False,
                "MAX_OPEN_TRADES",
                "candidate would exceed max open trades",
                checks=checks,
            )
        symbol_after = sum(1 for pos in open_positions if pos.symbol == candidate_symbol) + 1
        checks["max_open_trades_per_symbol"] = {
            "status": "passed"
            if symbol_after <= self.limits.max_open_trades_per_symbol
            else "failed",
            "open_after": symbol_after,
            "limit": self.limits.max_open_trades_per_symbol,
        }
        if symbol_after > self.limits.max_open_trades_per_symbol:
            return PortfolioResult(
                False,
                "MAX_OPEN_TRADES_PER_SYMBOL",
                "candidate would exceed max open trades for symbol",
                checks=checks,
            )
        amounts = open_position_risk_amounts or {}
        open_risk_before = 0.0
        for position in open_positions:
            if position.ticket in amounts:
                amount = amounts[position.ticket]
            else:
                snapshot = snapshots_by_symbol.get(position.symbol)
                if snapshot is None:
                    return PortfolioResult(
                        False,
                        "RISK_CALCULATION_UNCERTAIN",
                        f"missing snapshot to price open risk for {position.symbol}",
                        checks={**checks, "open_risk": {"status": "failed"}},
                    )
                try:
                    amount = risk_amount_for_lot(
                        lot=position.volume,
                        entry_price=position.entry_price,
                        sl_price=position.sl_price,
                        snapshot=snapshot,
                    )
                except (TypeError, ValueError, ZeroDivisionError) as exc:
                    return PortfolioResult(
                        False,
                        "RISK_CALCULATION_UNCERTAIN",
                        str(exc),
                        checks={**checks, "open_risk": {"status": "failed"}},
                    )
            if amount < 0:
                return PortfolioResult(
                    False,
                    "RISK_CALCULATION_UNCERTAIN",
                    "open risk amount cannot be negative",
                    checks={**checks, "open_risk": {"status": "failed"}},
                )
            open_risk_before += amount
        open_risk_after = open_risk_before + candidate_risk_amount
        open_risk_pct_after = (open_risk_after / equity) * 100.0
        checks["max_open_risk"] = {
            "status": "passed"
            if open_risk_pct_after <= self.limits.max_open_risk_pct
            else "failed",
            "open_risk_pct_after": open_risk_pct_after,
            "limit": self.limits.max_open_risk_pct,
        }
        if open_risk_pct_after > self.limits.max_open_risk_pct:
            return PortfolioResult(
                False,
                "MAX_OPEN_RISK",
                "candidate would exceed max open risk",
                open_risk_before,
                open_risk_pct_after,
                checks,
            )
        return PortfolioResult(True, "", "", open_risk_before, open_risk_pct_after, checks)
