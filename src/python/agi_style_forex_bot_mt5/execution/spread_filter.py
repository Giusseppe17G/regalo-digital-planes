"""Deterministic spread checks for execution-time validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from agi_style_forex_bot_mt5.config import BotConfig
from agi_style_forex_bot_mt5.contracts import MarketSnapshot


@dataclass(frozen=True)
class SpreadDecision:
    """Result of a spread validation."""

    accepted: bool
    spread_points: float
    max_spread_points: float
    reason: str


@dataclass(frozen=True)
class SpreadFilter:
    """Validate symbol spreads using per-symbol limits or safe defaults."""

    config: BotConfig
    symbol_limits: Mapping[str, float] = field(default_factory=dict)

    def max_for_symbol(self, symbol: str) -> float:
        """Return configured spread limit for a symbol."""

        limit = self.symbol_limits.get(symbol, self.config.max_spread_points_default)
        if limit <= 0:
            raise ValueError("spread limit must be positive")
        return float(limit)

    def check(self, snapshot: MarketSnapshot) -> SpreadDecision:
        """Fail closed when spread is invalid or above the configured limit."""

        try:
            snapshot.validate()
            limit = self.max_for_symbol(snapshot.symbol)
        except ValueError as exc:
            return SpreadDecision(False, snapshot.spread_points, 0.0, str(exc))

        if snapshot.spread_points > limit:
            return SpreadDecision(
                accepted=False,
                spread_points=snapshot.spread_points,
                max_spread_points=limit,
                reason="HIGH_SPREAD",
            )
        return SpreadDecision(
            accepted=True,
            spread_points=snapshot.spread_points,
            max_spread_points=limit,
            reason="OK",
        )
