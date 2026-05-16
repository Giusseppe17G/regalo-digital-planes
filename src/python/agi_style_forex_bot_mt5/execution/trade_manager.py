"""Position management rules for break-even and trailing stops."""

from __future__ import annotations

from dataclasses import dataclass

from agi_style_forex_bot_mt5.contracts import Direction, PositionState


@dataclass(frozen=True)
class StopManagementDecision:
    """Decision to keep or update a position stop."""

    should_modify: bool
    new_sl_price: float | None
    reason: str
    profit_r: float


@dataclass(frozen=True)
class TradeManager:
    """Apply deterministic break-even and trailing-stop rules."""

    break_even_at_r: float = 0.6
    trail_from_r: float = 0.8
    trail_distance_r: float = 0.4

    def evaluate_stop(
        self,
        *,
        position: PositionState,
        bid: float,
        ask: float,
        point: float,
        freeze_level_points: int = 0,
    ) -> StopManagementDecision:
        """Return the safest stop update allowed by current price."""

        if point <= 0 or bid <= 0 or ask <= 0 or ask < bid:
            return StopManagementDecision(False, None, "MARKET_DATA_INVALID", 0.0)
        if position.sl_price <= 0 or position.entry_price <= 0:
            return StopManagementDecision(False, None, "MISSING_SL", 0.0)

        risk_distance = abs(position.entry_price - position.sl_price)
        if risk_distance <= 0:
            return StopManagementDecision(False, None, "INVALID_RISK_DISTANCE", 0.0)

        current_price = bid if position.direction == Direction.BUY else ask
        if position.direction == Direction.BUY:
            profit_r = (current_price - position.entry_price) / risk_distance
            breakeven_sl = position.entry_price
            trailing_sl = current_price - self.trail_distance_r * risk_distance
            freeze_limit = current_price - freeze_level_points * point
            candidate = position.sl_price
            reason = "NO_CHANGE"
            if profit_r >= self.break_even_at_r and breakeven_sl > candidate:
                candidate = breakeven_sl
                reason = "BREAK_EVEN"
            if profit_r >= self.trail_from_r and trailing_sl > candidate:
                candidate = trailing_sl
                reason = "TRAILING_STOP"
            if candidate <= position.sl_price:
                return StopManagementDecision(False, None, "NO_CHANGE", profit_r)
            if candidate >= freeze_limit:
                return StopManagementDecision(False, None, "FREEZE_LEVEL", profit_r)
            return StopManagementDecision(True, candidate, reason, profit_r)

        profit_r = (position.entry_price - current_price) / risk_distance
        breakeven_sl = position.entry_price
        trailing_sl = current_price + self.trail_distance_r * risk_distance
        freeze_limit = current_price + freeze_level_points * point
        candidate = position.sl_price
        reason = "NO_CHANGE"
        if profit_r >= self.break_even_at_r and breakeven_sl < candidate:
            candidate = breakeven_sl
            reason = "BREAK_EVEN"
        if profit_r >= self.trail_from_r and trailing_sl < candidate:
            candidate = trailing_sl
            reason = "TRAILING_STOP"
        if candidate >= position.sl_price:
            return StopManagementDecision(False, None, "NO_CHANGE", profit_r)
        if candidate <= freeze_limit:
            return StopManagementDecision(False, None, "FREEZE_LEVEL", profit_r)
        return StopManagementDecision(True, candidate, reason, profit_r)
