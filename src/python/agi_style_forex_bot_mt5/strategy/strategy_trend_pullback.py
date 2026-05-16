"""Trend continuation after a controlled pullback."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..contracts import MarketSnapshot
from .scoring_engine import (
    choose_direction,
    feature_float,
    none_signal,
    score_conditions,
    spread_is_unsafe,
)


STRATEGY_NAME = "trend_pullback"
STRATEGY_VERSION = "0.1.0"


def evaluate(snapshot: MarketSnapshot, features: Mapping[str, Any]) -> Any:
    """Return a StrategySignal for pullbacks aligned with the dominant trend."""

    try:
        snapshot.validate()
    except ValueError as exc:
        return none_signal(STRATEGY_NAME, f"invalid snapshot: {exc}")
    if spread_is_unsafe(snapshot, features):
        return none_signal(STRATEGY_NAME, "spread unsafe for strategy")

    close = feature_float(features, "close", (snapshot.bid + snapshot.ask) / 2)
    previous_close = feature_float(features, "previous_close", close)
    ema_fast = feature_float(features, "ema_fast", close)
    ema_slow = feature_float(features, "ema_slow", close)
    rsi = feature_float(features, "rsi", 50)
    trend_slope = feature_float(features, "trend_slope", ema_fast - ema_slow)
    atr_points = feature_float(features, "atr_points", 0)
    pullback_depth_points = abs(close - ema_fast) / snapshot.point if snapshot.point > 0 else 0

    buy_score, buy_reasons = score_conditions(
        base=10,
        conditions=(
            (ema_fast > ema_slow, 22, "fast EMA above slow EMA"),
            (trend_slope > 0, 18, "positive trend slope"),
            (close <= ema_fast or 38 <= rsi <= 58, 18, "controlled bullish pullback"),
            (close > previous_close, 14, "bullish resumption candle"),
            (atr_points > 0 and pullback_depth_points <= max(atr_points * 1.25, 1), 10, "pullback depth within ATR"),
        ),
    )
    sell_score, sell_reasons = score_conditions(
        base=10,
        conditions=(
            (ema_fast < ema_slow, 22, "fast EMA below slow EMA"),
            (trend_slope < 0, 18, "negative trend slope"),
            (close >= ema_fast or 42 <= rsi <= 62, 18, "controlled bearish pullback"),
            (close < previous_close, 14, "bearish resumption candle"),
            (atr_points > 0 and pullback_depth_points <= max(atr_points * 1.25, 1), 10, "pullback depth within ATR"),
        ),
    )
    return choose_direction(
        buy_score=buy_score,
        sell_score=sell_score,
        buy_reasons=buy_reasons,
        sell_reasons=sell_reasons,
        threshold=62,
        min_margin=8,
        strategy_name=STRATEGY_NAME,
        metadata={"version": STRATEGY_VERSION, "close": close, "rsi": rsi},
    )
