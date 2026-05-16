"""Deterministic market-regime labeling."""

from __future__ import annotations

import pandas as pd

from agi_style_forex_bot_mt5.contracts import Regime

from .indicators import add_indicators
from .market_data import MarketDataError, validate_ohlcv_frame


def _ensure_indicator_columns(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"ema20", "ema50", "ema200", "atr_percent", "ema_slope", "trend_strength"}
    if required.issubset(frame.columns):
        return frame.copy()
    return add_indicators(frame)


def add_regime_labels(
    bars: pd.DataFrame,
    *,
    max_spread_points: float = 25.0,
    high_volatility_atr_pct: float = 0.35,
    low_volatility_atr_pct: float = 0.04,
    trend_strength_threshold: float = 1.0,
    thin_liquidity_quantile: float = 0.10,
    liquidity_window: int = 50,
) -> pd.DataFrame:
    """Add a single fail-closed ``regime`` label per row.

    Precedence is risk-oriented: dangerous spread and thin liquidity labels are
    assigned before market-shape labels. The labels are values from the
    canonical ``Regime`` enum.
    """

    validate_ohlcv_frame(bars)
    if max_spread_points < 0:
        raise ValueError("max_spread_points cannot be negative")
    if high_volatility_atr_pct <= low_volatility_atr_pct:
        raise ValueError("high_volatility_atr_pct must exceed low_volatility_atr_pct")
    if trend_strength_threshold < 0:
        raise ValueError("trend_strength_threshold cannot be negative")
    if not 0 < thin_liquidity_quantile < 1:
        raise ValueError("thin_liquidity_quantile must be between 0 and 1")
    if liquidity_window <= 1:
        raise ValueError("liquidity_window must be greater than 1")

    frame = _ensure_indicator_columns(bars)
    regimes = pd.Series(Regime.RANGE.value, index=frame.index, dtype="object")

    trend_up = (
        (frame["ema20"] > frame["ema50"])
        & (frame["ema50"] > frame["ema200"])
        & (frame["ema_slope"] > 0)
        & (frame["trend_strength"] >= trend_strength_threshold)
    )
    trend_down = (
        (frame["ema20"] < frame["ema50"])
        & (frame["ema50"] < frame["ema200"])
        & (frame["ema_slope"] < 0)
        & (frame["trend_strength"] >= trend_strength_threshold)
    )
    regimes.loc[trend_up.fillna(False)] = Regime.TREND_UP.value
    regimes.loc[trend_down.fillna(False)] = Regime.TREND_DOWN.value
    regimes.loc[(frame["atr_percent"] >= high_volatility_atr_pct).fillna(False)] = Regime.HIGH_VOLATILITY.value
    regimes.loc[(frame["atr_percent"] <= low_volatility_atr_pct).fillna(False)] = Regime.LOW_VOLATILITY.value

    liquidity_floor = frame["volume"].rolling(liquidity_window, min_periods=1).quantile(thin_liquidity_quantile)
    thin_liquidity = (frame["volume"] <= 0) | (frame["volume"] < liquidity_floor)
    regimes.loc[thin_liquidity.fillna(False)] = Regime.LIQUIDITY_THIN.value
    if "spread_points" in frame.columns:
        regimes.loc[(frame["spread_points"] > max_spread_points).fillna(False)] = Regime.SPREAD_DANGER.value

    frame["regime"] = regimes
    return frame


def detect_latest_regime(bars: pd.DataFrame, **kwargs: object) -> Regime:
    """Return the latest ``Regime`` label for normalized bars."""

    if "regime" in bars.columns and not kwargs:
        if bars.empty:
            raise MarketDataError("cannot detect regime from empty data")
        return Regime(str(bars.iloc[-1]["regime"]))
    labeled = add_regime_labels(bars, **kwargs)
    if labeled.empty:
        raise MarketDataError("cannot detect regime from empty data")
    return Regime(str(labeled.iloc[-1]["regime"]))
