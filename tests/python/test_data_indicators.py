from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from agi_style_forex_bot_mt5.contracts import Regime
from agi_style_forex_bot_mt5.data import (
    MarketDataError,
    add_indicators,
    add_regime_labels,
    detect_latest_regime,
    latest_market_snapshot,
    normalize_ohlcv_bars,
    normalize_ticks,
)


def _sample_bars(rows: int = 240) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=rows, freq="5min", tz="UTC")
    close = 1.10 + np.arange(rows) * 0.0001
    open_ = close - 0.00004
    high = close + 0.00008
    low = open_ - 0.00008
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps[::-1],
            "open": open_[::-1],
            "high": high[::-1],
            "low": low[::-1],
            "close": close[::-1],
            "volume": np.full(rows, 100.0),
            "spread_points": np.full(rows, 12.0),
        }
    )


def test_normalize_ohlcv_bars_sorts_and_validates() -> None:
    bars = normalize_ohlcv_bars(_sample_bars(30), symbol="EURUSD", timeframe="M5")

    assert bars["timestamp_utc"].is_monotonic_increasing
    assert str(bars["timestamp_utc"].dt.tz) == "UTC"
    assert bars.loc[0, "symbol"] == "EURUSD"
    assert bars.loc[0, "timeframe"] == "M5"


def test_empty_market_data_fails_closed() -> None:
    with pytest.raises(MarketDataError):
        normalize_ohlcv_bars(pd.DataFrame())


def test_add_indicators_outputs_expected_columns_and_values() -> None:
    features = add_indicators(normalize_ohlcv_bars(_sample_bars()))
    expected_columns = {
        "ema20",
        "ema50",
        "ema200",
        "rsi14",
        "atr14",
        "bb_middle",
        "bb_upper",
        "bb_lower",
        "vwap",
        "returns",
        "log_returns",
        "volatility",
        "candle_body",
        "upper_wick",
        "lower_wick",
        "momentum",
        "atr_percent",
        "ema_slope",
        "trend_strength",
    }

    assert expected_columns.issubset(features.columns)
    latest = features.iloc[-1]
    assert latest["ema20"] > latest["ema50"] > latest["ema200"]
    assert 0 <= latest["rsi14"] <= 100
    assert latest["atr14"] > 0
    assert latest["vwap"] > 0


def test_regime_labels_use_contract_enum_values() -> None:
    bars = normalize_ohlcv_bars(_sample_bars())
    labeled = add_regime_labels(
        bars,
        high_volatility_atr_pct=5.0,
        low_volatility_atr_pct=0.00001,
        trend_strength_threshold=0.1,
        thin_liquidity_quantile=0.01,
    )

    assert labeled.iloc[-1]["regime"] == Regime.TREND_UP.value
    assert detect_latest_regime(labeled) is Regime.TREND_UP


def test_spread_danger_has_precedence() -> None:
    bars = normalize_ohlcv_bars(_sample_bars())
    bars.loc[bars.index[-1], "spread_points"] = 99.0

    labeled = add_regime_labels(
        bars,
        max_spread_points=25.0,
        high_volatility_atr_pct=5.0,
        low_volatility_atr_pct=0.00001,
        trend_strength_threshold=0.1,
        thin_liquidity_quantile=0.01,
    )

    assert labeled.iloc[-1]["regime"] == Regime.SPREAD_DANGER.value


def test_normalize_ticks_and_snapshot_contract() -> None:
    ticks = normalize_ticks(
        [
            {
                "timestamp_utc": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "bid": 1.10000,
                "ask": 1.10012,
            }
        ],
        point=0.00001,
    )
    snapshot = latest_market_snapshot(
        ticks,
        symbol="EURUSD",
        timeframe="M5",
        digits=5,
        point=0.00001,
        tick_value=1.0,
        tick_size=0.00001,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        stops_level_points=10,
        freeze_level_points=5,
    )

    assert snapshot.symbol == "EURUSD"
    assert snapshot.spread_points == pytest.approx(12.0)
