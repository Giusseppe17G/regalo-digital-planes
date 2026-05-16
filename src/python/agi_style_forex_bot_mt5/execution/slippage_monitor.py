"""Slippage measurement utilities."""

from __future__ import annotations

from dataclasses import dataclass

from agi_style_forex_bot_mt5.contracts import Direction


@dataclass(frozen=True)
class SlippageMeasurement:
    """Measured slippage in price and points."""

    requested_price: float
    fill_price: float
    slippage_price: float
    slippage_points: float
    favorable: bool


@dataclass(frozen=True)
class SlippageMonitor:
    """Measure execution slippage without side effects."""

    point: float

    def measure(
        self,
        *,
        direction: Direction,
        requested_price: float,
        fill_price: float,
    ) -> SlippageMeasurement:
        """Return signed slippage from the trader perspective."""

        if self.point <= 0:
            raise ValueError("point must be positive")
        if requested_price <= 0 or fill_price <= 0:
            raise ValueError("prices must be positive")

        raw = fill_price - requested_price
        trader_slippage = raw if direction == Direction.BUY else -raw
        points = trader_slippage / self.point
        return SlippageMeasurement(
            requested_price=requested_price,
            fill_price=fill_price,
            slippage_price=trader_slippage,
            slippage_points=points,
            favorable=points <= 0,
        )
