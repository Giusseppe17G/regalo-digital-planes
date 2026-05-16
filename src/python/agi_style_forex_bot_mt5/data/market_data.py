"""Market bar normalization and validation utilities.

The data layer is intentionally deterministic and fail-closed: empty,
incomplete or inconsistent market data raises ``ValueError`` instead of
silently producing features that could later drive unsafe decisions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_OHLCV_COLUMNS: tuple[str, ...] = (
    "timestamp_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


class MarketDataError(ValueError):
    """Raised when market data cannot be safely normalized or validated."""


def _as_frame(data: pd.DataFrame | Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()
    return pd.DataFrame(data)


def _canonical_column_name(name: object) -> str:
    return str(name).strip().strip("<>").lower().replace(" ", "_")


def _canonicalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {_name: _canonical_column_name(_name) for _name in frame.columns}
    frame = frame.rename(columns=renamed)
    if "timestamp_utc" not in frame.columns and {"date", "time"}.issubset(frame.columns):
        frame["timestamp_utc"] = frame["date"].astype(str) + " " + frame["time"].astype(str)
    aliases = {
        "time": "timestamp_utc",
        "datetime": "timestamp_utc",
        "timestamp": "timestamp_utc",
        "date_time": "timestamp_utc",
        "tick_volume": "volume",
        "real_volume": "volume",
        "vol": "volume",
        "spread": "spread_points",
    }
    alias_map = {
        col: aliases[col]
        for col in frame.columns
        if col in aliases and not (col == "time" and "timestamp_utc" in frame.columns)
    }
    frame = frame.rename(columns=alias_map)
    return frame


def _coerce_numeric(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def normalize_ohlcv_bars(
    data: pd.DataFrame | Iterable[Mapping[str, Any]],
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> pd.DataFrame:
    """Return a normalized OHLCV DataFrame sorted by UTC timestamp.

    Required output columns are ``timestamp_utc``, ``open``, ``high``, ``low``,
    ``close`` and ``volume``. Optional ``spread_points`` is preserved and
    validated when present. ``symbol`` and ``timeframe`` may be injected as
    constant metadata columns for downstream joins and reports.
    """

    frame = _canonicalize_columns(_as_frame(data))
    if frame.empty:
        raise MarketDataError("market data is empty")
    if symbol is not None:
        frame["symbol"] = symbol
    if timeframe is not None:
        frame["timeframe"] = timeframe

    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise MarketDataError(f"market data missing required columns: {', '.join(missing)}")

    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    numeric_columns = ["open", "high", "low", "close", "volume", "spread_points"]
    frame = _coerce_numeric(frame, numeric_columns)
    frame = frame.sort_values("timestamp_utc").drop_duplicates("timestamp_utc", keep="last")
    frame = frame.reset_index(drop=True)
    validate_ohlcv_frame(frame)
    return frame


def validate_ohlcv_frame(frame: pd.DataFrame, *, require_spread: bool = False) -> None:
    """Validate normalized OHLCV data or raise ``MarketDataError``.

    The validator checks for empty data, missing required columns, invalid
    timestamps, non-finite prices, inconsistent candles and negative volume.
    """

    if frame.empty:
        raise MarketDataError("market data is empty")
    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise MarketDataError(f"market data missing required columns: {', '.join(missing)}")
    if require_spread and "spread_points" not in frame.columns:
        raise MarketDataError("spread_points is required")
    if frame["timestamp_utc"].isna().any():
        raise MarketDataError("market data contains invalid timestamps")
    if not pd.api.types.is_datetime64_any_dtype(frame["timestamp_utc"]):
        raise MarketDataError("timestamp_utc must be datetime-like")

    price_columns = ["open", "high", "low", "close"]
    numeric_columns = price_columns + ["volume"]
    if "spread_points" in frame.columns:
        numeric_columns.append("spread_points")
    numeric = frame[numeric_columns]
    if numeric.isna().any().any():
        raise MarketDataError("market data contains missing numeric values")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise MarketDataError("market data contains non-finite numeric values")
    if (frame[price_columns] <= 0).any().any():
        raise MarketDataError("OHLC prices must be positive")
    if (frame["high"] < frame["low"]).any():
        raise MarketDataError("high cannot be below low")
    if (frame["high"] < frame[["open", "close"]].max(axis=1)).any():
        raise MarketDataError("high must be at least open and close")
    if (frame["low"] > frame[["open", "close"]].min(axis=1)).any():
        raise MarketDataError("low must be at most open and close")
    if (frame["volume"] < 0).any():
        raise MarketDataError("volume cannot be negative")
    if "spread_points" in frame.columns and (frame["spread_points"] < 0).any():
        raise MarketDataError("spread_points cannot be negative")
    if "symbol" in frame.columns and frame["symbol"].astype(str).str.strip().eq("").any():
        raise MarketDataError("symbol cannot be empty")
    if "timeframe" in frame.columns and frame["timeframe"].astype(str).str.strip().eq("").any():
        raise MarketDataError("timeframe cannot be empty")


def require_non_empty(frame: pd.DataFrame, *, name: str = "data") -> None:
    """Raise ``MarketDataError`` when a DataFrame is empty."""

    if frame.empty:
        raise MarketDataError(f"{name} is empty")
