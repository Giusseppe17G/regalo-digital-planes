"""Walk-forward train/validation/test orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

import pandas as pd

from .backtester import BacktestOutcome, BacktestMetrics, calculate_metrics


BacktestCallback = Callable[[pd.DataFrame, Mapping[str, Any]], BacktestOutcome]


@dataclass(frozen=True)
class WalkForwardFold:
    fold_index: int
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str
    best_parameters: Mapping[str, Any]
    train_metrics: BacktestMetrics
    validation_metrics: BacktestMetrics
    test_metrics: BacktestMetrics


@dataclass(frozen=True)
class WalkForwardResult:
    folds: tuple[WalkForwardFold, ...]
    aggregate_test_metrics: BacktestMetrics
    selection_metric: str


class WalkForwardOptimizer:
    """Evaluate parameter grids without using test data for selection."""

    def __init__(
        self,
        *,
        train_size: int,
        validation_size: int,
        test_size: int,
        step_size: int | None = None,
        selection_metric: str = "profit_factor",
        maximize: bool = True,
    ) -> None:
        if train_size <= 0 or validation_size <= 0 or test_size <= 0:
            raise ValueError("train, validation and test sizes must be positive")
        self.train_size = train_size
        self.validation_size = validation_size
        self.test_size = test_size
        self.step_size = step_size or test_size
        self.selection_metric = selection_metric
        self.maximize = maximize

    def run(
        self,
        candles: pd.DataFrame,
        parameter_grid: Iterable[Mapping[str, Any]],
        backtest_callback: BacktestCallback,
    ) -> WalkForwardResult:
        params = [dict(item) for item in parameter_grid]
        if not params:
            raise ValueError("parameter_grid cannot be empty")
        bars = _normalize_for_split(candles)
        folds: list[WalkForwardFold] = []
        all_test_trades: list[Any] = []
        start = 0
        fold_index = 0
        window = self.train_size + self.validation_size + self.test_size
        while start + window <= len(bars):
            train = bars.iloc[start : start + self.train_size]
            validation = bars.iloc[
                start + self.train_size : start + self.train_size + self.validation_size
            ]
            test = bars.iloc[
                start
                + self.train_size
                + self.validation_size : start
                + self.train_size
                + self.validation_size
                + self.test_size
            ]
            scored: list[tuple[float, Mapping[str, Any], BacktestOutcome, BacktestOutcome]] = []
            for candidate_params in params:
                train_outcome = backtest_callback(train.copy(), candidate_params)
                validation_outcome = backtest_callback(validation.copy(), candidate_params)
                score = _metric_value(validation_outcome.metrics, self.selection_metric)
                scored.append((score, candidate_params, train_outcome, validation_outcome))
            best = sorted(scored, key=lambda item: item[0], reverse=self.maximize)[0]
            _, best_params, train_outcome, validation_outcome = best
            test_outcome = backtest_callback(test.copy(), best_params)
            all_test_trades.extend(test_outcome.trades)
            folds.append(
                WalkForwardFold(
                    fold_index=fold_index,
                    train_start=_first_ts(train),
                    train_end=_last_ts(train),
                    validation_start=_first_ts(validation),
                    validation_end=_last_ts(validation),
                    test_start=_first_ts(test),
                    test_end=_last_ts(test),
                    best_parameters=dict(best_params),
                    train_metrics=train_outcome.metrics,
                    validation_metrics=validation_outcome.metrics,
                    test_metrics=test_outcome.metrics,
                )
            )
            fold_index += 1
            start += self.step_size
        if not folds:
            raise ValueError("not enough rows to create a walk-forward fold")
        aggregate = calculate_metrics(all_test_trades)
        return WalkForwardResult(
            folds=tuple(folds),
            aggregate_test_metrics=aggregate,
            selection_metric=self.selection_metric,
        )


def _normalize_for_split(candles: pd.DataFrame) -> pd.DataFrame:
    bars = candles.copy()
    if "timestamp" not in bars.columns:
        if isinstance(bars.index, pd.DatetimeIndex):
            bars = bars.reset_index().rename(columns={bars.index.name or "index": "timestamp"})
        else:
            raise ValueError("candles require timestamp column or DatetimeIndex")
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    return bars.sort_values("timestamp").reset_index(drop=True)


def _metric_value(metrics: BacktestMetrics, metric_name: str) -> float:
    value = getattr(metrics, metric_name)
    if value is None:
        return float("-inf")
    return float(value)


def _first_ts(frame: pd.DataFrame) -> str:
    return pd.Timestamp(frame.iloc[0]["timestamp"]).isoformat()


def _last_ts(frame: pd.DataFrame) -> str:
    return pd.Timestamp(frame.iloc[-1]["timestamp"]).isoformat()
