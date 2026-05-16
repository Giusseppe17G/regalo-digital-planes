"""Reproducible Monte Carlo validation for trade sequences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import numpy as np

from .backtester import TradeResult, calculate_metrics


@dataclass(frozen=True)
class MonteCarloResult:
    seed: int
    iterations: int
    method: str
    final_equity_percentiles: Mapping[str, float]
    max_drawdown_percentiles: Mapping[str, float]
    max_consecutive_losses_percentiles: Mapping[str, float]
    risk_of_ruin_pct: float


class MonteCarloSimulator:
    """Bootstrap or permute trade profit sequences with a fixed RNG seed."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def run(
        self,
        trades: Iterable[TradeResult | Mapping[str, Any] | float],
        *,
        initial_balance: float = 10_000.0,
        iterations: int = 1_000,
        method: str = "bootstrap",
        ruin_threshold_pct: float = 30.0,
    ) -> MonteCarloResult:
        if iterations <= 0:
            raise ValueError("iterations must be positive")
        profits = _extract_profits(trades)
        if len(profits) == 0:
            raise ValueError("at least one trade is required")
        rng = np.random.default_rng(self.seed)
        finals: list[float] = []
        drawdowns: list[float] = []
        loss_runs: list[float] = []
        ruin_count = 0
        for _ in range(iterations):
            if method == "bootstrap":
                sampled = rng.choice(profits, size=len(profits), replace=True)
            elif method == "permutation":
                sampled = rng.permutation(profits)
            else:
                raise ValueError("method must be bootstrap or permutation")
            equity = initial_balance + np.cumsum(sampled)
            curve = np.concatenate(([initial_balance], equity))
            running_max = np.maximum.accumulate(curve)
            dd = (curve - running_max) / running_max * 100.0
            finals.append(float(curve[-1]))
            drawdowns.append(float(dd.min()))
            loss_runs.append(float(_max_loss_run(sampled)))
            if dd.min() <= -abs(ruin_threshold_pct):
                ruin_count += 1
        return MonteCarloResult(
            seed=self.seed,
            iterations=iterations,
            method=method,
            final_equity_percentiles=_percentiles(finals),
            max_drawdown_percentiles=_percentiles(drawdowns),
            max_consecutive_losses_percentiles=_percentiles(loss_runs),
            risk_of_ruin_pct=ruin_count / iterations * 100.0,
        )


def monte_carlo_metrics(
    trades: Iterable[TradeResult | Mapping[str, Any] | float],
    *,
    seed: int = 0,
    initial_balance: float = 10_000.0,
    iterations: int = 1_000,
) -> MonteCarloResult:
    return MonteCarloSimulator(seed=seed).run(
        trades,
        initial_balance=initial_balance,
        iterations=iterations,
    )


def shuffled_metrics(
    trades: Iterable[TradeResult | Mapping[str, Any]],
    *,
    seed: int,
    initial_balance: float = 10_000.0,
) -> Any:
    """Return metrics for one deterministic permutation of closed trades."""

    normalized = list(trades)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(normalized))
    shuffled = [normalized[int(idx)] for idx in order]
    return calculate_metrics(shuffled, initial_balance=initial_balance)


def _extract_profits(trades: Iterable[TradeResult | Mapping[str, Any] | float]) -> np.ndarray:
    profits: list[float] = []
    for trade in trades:
        if isinstance(trade, (int, float)):
            profits.append(float(trade))
        elif isinstance(trade, TradeResult):
            profits.append(float(trade.profit))
        else:
            profits.append(float(trade["profit"]))
    return np.array(profits, dtype=float)


def _percentiles(values: Iterable[float]) -> dict[str, float]:
    arr = np.array(list(values), dtype=float)
    return {
        "p5": float(np.percentile(arr, 5)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
    }


def _max_loss_run(profits: Iterable[float]) -> int:
    best = 0
    current = 0
    for profit in profits:
        if profit < 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best
