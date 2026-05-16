"""Stress tests for cost sensitivity and trade concentration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable, Mapping

from .backtester import TradeResult, calculate_metrics


@dataclass(frozen=True)
class StressResult:
    scenario: str
    parameters: Mapping[str, Any]
    metrics: Any


class StressTester:
    """Apply deterministic degradation scenarios to closed trades."""

    def __init__(self, *, initial_balance: float = 10_000.0) -> None:
        self.initial_balance = initial_balance

    def spread_slippage_sensitivity(
        self,
        trades: Iterable[TradeResult | Mapping[str, Any]],
        *,
        spread_multipliers: Iterable[float] = (1.0, 1.5, 2.0),
        extra_slippage_points: Iterable[float] = (0.0, 1.0, 2.0),
    ) -> list[StressResult]:
        source = [_ensure_trade(trade) for trade in trades]
        results: list[StressResult] = []
        for spread_multiplier in spread_multipliers:
            if spread_multiplier < 0:
                raise ValueError("spread multipliers must be non-negative")
            for slippage_points in extra_slippage_points:
                if slippage_points < 0:
                    raise ValueError("extra slippage must be non-negative")
                stressed = [
                    _apply_cost_penalty(
                        trade,
                        spread_multiplier=spread_multiplier,
                        extra_slippage_points=slippage_points,
                    )
                    for trade in source
                ]
                metrics = calculate_metrics(stressed, initial_balance=self.initial_balance)
                results.append(
                    StressResult(
                        scenario="spread_slippage",
                        parameters={
                            "spread_multiplier": spread_multiplier,
                            "extra_slippage_points": slippage_points,
                        },
                        metrics=metrics,
                    )
                )
        return results

    def remove_best_trades(
        self,
        trades: Iterable[TradeResult | Mapping[str, Any]],
        *,
        counts: Iterable[int] = (1, 3, 5),
    ) -> list[StressResult]:
        source = [_ensure_trade(trade) for trade in trades]
        ordered = sorted(source, key=lambda trade: trade.profit, reverse=True)
        results: list[StressResult] = []
        for count in counts:
            if count < 0:
                raise ValueError("remove count must be non-negative")
            removed_ids = {id(trade) for trade in ordered[:count]}
            remaining = [trade for trade in source if id(trade) not in removed_ids]
            metrics = calculate_metrics(remaining, initial_balance=self.initial_balance)
            results.append(
                StressResult(
                    scenario="remove_best_trades",
                    parameters={"removed_count": min(count, len(source))},
                    metrics=metrics,
                )
            )
        return results


def _ensure_trade(trade: TradeResult | Mapping[str, Any]) -> TradeResult:
    if isinstance(trade, TradeResult):
        return trade
    return TradeResult(**dict(trade))


def _apply_cost_penalty(
    trade: TradeResult,
    *,
    spread_multiplier: float,
    extra_slippage_points: float,
) -> TradeResult:
    extra_spread_points = max(0.0, trade.spread_points * (spread_multiplier - 1.0))
    extra_round_trip_points = extra_spread_points + (2.0 * extra_slippage_points)
    penalty = (
        extra_round_trip_points
        * trade.point
        / trade.tick_size
        * trade.tick_value
        * trade.lot
    )
    data = asdict(trade)
    data["profit"] = trade.profit - penalty
    if trade.r_multiple != 0 and trade.profit != 0:
        data["r_multiple"] = trade.r_multiple * (data["profit"] / trade.profit)
    return replace(trade, profit=data["profit"], r_multiple=data["r_multiple"])
