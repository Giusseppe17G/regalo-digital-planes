"""Deterministic price-feature engineering for normalized market bars."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .market_data import validate_ohlcv_frame


def add_price_features(
    bars: pd.DataFrame,
    *,
    volatility_window: int = 20,
    momentum_window: int = 10,
) -> pd.DataFrame:
    """Add normalized price-action features without mutating ``bars``.

    Features are calculated from current and prior candles only. Initial rows
    may contain ``NaN`` where rolling history is not yet available.
    """

    validate_ohlcv_frame(bars)
    if volatility_window <= 1:
        raise ValueError("volatility_window must be greater than 1")
    if momentum_window <= 0:
        raise ValueError("momentum_window must be positive")

    frame = bars.copy()
    close = frame["close"].astype(float)
    frame["returns"] = close.pct_change()
    frame["log_returns"] = np.log(close / close.shift(1))
    frame["volatility"] = frame["log_returns"].rolling(volatility_window, min_periods=volatility_window).std()
    frame["candle_body"] = frame["close"] - frame["open"]
    frame["upper_wick"] = frame["high"] - frame[["open", "close"]].max(axis=1)
    frame["lower_wick"] = frame[["open", "close"]].min(axis=1) - frame["low"]
    frame["momentum"] = close - close.shift(momentum_window)
    return frame
