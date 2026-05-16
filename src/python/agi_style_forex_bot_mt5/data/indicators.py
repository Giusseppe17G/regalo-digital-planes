"""Technical indicators used by strategy research and market filters."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .feature_engineering import add_price_features
from .market_data import validate_ohlcv_frame


def ema(series: pd.Series, period: int) -> pd.Series:
    """Return an exponential moving average with a minimum full period."""

    if period <= 0:
        raise ValueError("period must be positive")
    return series.astype(float).ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Return Wilder-style RSI for ``close``."""

    if period <= 0:
        raise ValueError("period must be positive")
    delta = close.astype(float).diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    relative_strength = avg_gain / avg_loss.replace(0.0, np.nan)
    values = 100.0 - (100.0 / (1.0 + relative_strength))
    values = values.mask((avg_loss == 0.0) & (avg_gain > 0.0), 100.0)
    values = values.mask((avg_loss == 0.0) & (avg_gain == 0.0), 50.0)
    return values


def atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """Return Average True Range for normalized OHLCV bars."""

    validate_ohlcv_frame(bars)
    if period <= 0:
        raise ValueError("period must be positive")
    high = bars["high"].astype(float)
    low = bars["low"].astype(float)
    previous_close = bars["close"].astype(float).shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def bollinger_bands(
    close: pd.Series,
    *,
    period: int = 20,
    std_multiplier: float = 2.0,
) -> pd.DataFrame:
    """Return Bollinger Band middle, upper, lower and width columns."""

    if period <= 1:
        raise ValueError("period must be greater than 1")
    if std_multiplier <= 0:
        raise ValueError("std_multiplier must be positive")
    middle = close.astype(float).rolling(period, min_periods=period).mean()
    standard_deviation = close.astype(float).rolling(period, min_periods=period).std(ddof=0)
    upper = middle + std_multiplier * standard_deviation
    lower = middle - std_multiplier * standard_deviation
    width = (upper - lower) / middle.replace(0.0, np.nan)
    return pd.DataFrame(
        {
            "bb_middle": middle,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_width": width,
        },
        index=close.index,
    )


def approximate_vwap(bars: pd.DataFrame) -> pd.Series:
    """Return cumulative approximate VWAP using typical price and volume."""

    validate_ohlcv_frame(bars)
    typical_price = (bars["high"] + bars["low"] + bars["close"]) / 3.0
    volume = bars["volume"].astype(float)
    cumulative_volume = volume.cumsum()
    cumulative_value = (typical_price * volume).cumsum()
    vwap = cumulative_value / cumulative_volume.replace(0.0, np.nan)
    return vwap.fillna(typical_price)


def add_indicators(
    bars: pd.DataFrame,
    *,
    volatility_window: int = 20,
    momentum_window: int = 10,
) -> pd.DataFrame:
    """Add the project's standard indicator and feature columns.

    Columns added: ``ema20``, ``ema50``, ``ema200``, ``rsi14``, ``atr14``,
    ``bb_middle``, ``bb_upper``, ``bb_lower``, ``bb_width``, ``vwap``,
    ``returns``, ``log_returns``, ``volatility``, ``candle_body``,
    ``upper_wick``, ``lower_wick``, ``momentum``, ``atr_percent``,
    ``ema_slope`` and ``trend_strength``.
    """

    validate_ohlcv_frame(bars)
    frame = add_price_features(
        bars,
        volatility_window=volatility_window,
        momentum_window=momentum_window,
    )
    close = frame["close"].astype(float)
    frame["ema20"] = ema(close, 20)
    frame["ema50"] = ema(close, 50)
    frame["ema200"] = ema(close, 200)
    frame["rsi14"] = rsi(close, 14)
    frame["atr14"] = atr(frame, 14)
    bands = bollinger_bands(close, period=20, std_multiplier=2.0)
    frame = pd.concat([frame, bands], axis=1)
    frame["vwap"] = approximate_vwap(frame)
    frame["atr_percent"] = (frame["atr14"] / close) * 100.0
    frame["ema_slope"] = frame["ema20"].diff()
    frame["trend_strength"] = (frame["ema20"] - frame["ema200"]).abs() / frame["atr14"].replace(0.0, np.nan)
    return frame
