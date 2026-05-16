"""Session momentum strategy for liquid trading windows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..contracts import MarketSnapshot
from .scoring_engine import (
    choose_direction,
    feature_float,
    feature_text,
    none_signal,
    score_conditions,
    spread_is_unsafe,
)


STRATEGY_NAME = "session_momentum"
STRATEGY_VERSION = "0.1.0"
LIQUID_SESSIONS = {"LONDON", "NEW_YORK", "NY", "LONDON_NY_OVERLAP", "OVERLAP"}


def evaluate(snapshot: MarketSnapshot, features: Mapping[str, Any]) -> Any:
    """Return a StrategySignal when liquid-session momentum is directional."""

    try:
        snapshot.validate()
    except ValueError as exc:
        return none_signal(STRATEGY_NAME, f"invalid snapshot: {exc}")
    if spread_is_unsafe(snapshot, features):
        return none_signal(STRATEGY_NAME, "spread unsafe for strategy")

    session = feature_text(features, "session", "")
    momentum_points = feature_float(features, "momentum_points", 0)
    range_points = feature_float(features, "range_points", 0)
    min_range_points = feature_float(features, "min_session_range_points", 8)
    trend_slope = feature_float(features, "trend_slope", 0)
    body_ratio = feature_float(features, "body_ratio", 0)

    buy_score, buy_reasons = score_conditions(
        base=8,
        conditions=(
            (session in LIQUID_SESSIONS, 20, "liquid session"),
            (momentum_points > 0, 22, "positive session momentum"),
            (range_points >= min_range_points, 14, "session range active"),
            (trend_slope >= 0, 12, "trend not opposing buy"),
            (body_ratio >= 0.45, 12, "directional candle body"),
        ),
    )
    sell_score, sell_reasons = score_conditions(
        base=8,
        conditions=(
            (session in LIQUID_SESSIONS, 20, "liquid session"),
            (momentum_points < 0, 22, "negative session momentum"),
            (range_points >= min_range_points, 14, "session range active"),
            (trend_slope <= 0, 12, "trend not opposing sell"),
            (body_ratio >= 0.45, 12, "directional candle body"),
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
        metadata={"version": STRATEGY_VERSION, "session": session},
    )
