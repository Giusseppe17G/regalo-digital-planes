"""Deterministic Python backtesting engine.

The engine consumes OHLC bars and explicit trade candidates. It does not create
signals or execution requests; it only validates and simulates already-audited
research candidates with conservative cost and exit assumptions.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from ..contracts import Direction


ENGINE_VERSION = "0.1.0"


@dataclass(frozen=True)
class CostModel:
    """Spread, slippage and commission assumptions for one backtest run."""

    spread_points: float = 0.0
    slippage_points: float = 0.0
    commission_per_lot_round_turn: float = 0.0
    point: float = 0.00001
    tick_value: float = 1.0
    tick_size: float = 0.00001
    max_spread_points: float = 25.0

    def validate(self) -> None:
        if self.spread_points < 0 or self.slippage_points < 0:
            raise ValueError("spread and slippage must be non-negative")
        if self.commission_per_lot_round_turn < 0:
            raise ValueError("commission must be non-negative")
        if self.point <= 0 or self.tick_value <= 0 or self.tick_size <= 0:
            raise ValueError("point, tick_value and tick_size must be positive")
        if self.max_spread_points < 0:
            raise ValueError("max_spread_points must be non-negative")

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


@dataclass(frozen=True)
class TradeCandidate:
    """Research trade candidate used by the backtester."""

    timestamp: datetime | str | pd.Timestamp
    symbol: str
    direction: Direction | str
    sl_price: float
    tp_price: float
    timeframe: str = ""
    signal_id: str = ""
    lot: float = 1.0
    entry_price: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestSettings:
    """Run settings for the deterministic bar simulator."""

    run_id: str = "backtest"
    strategy_name: str = "research"
    strategy_version: str = "0.1.0"
    initial_balance: float = 10_000.0
    cost_model: CostModel = field(default_factory=CostModel)
    break_even_trigger_r: float | None = None
    break_even_lock_points: float = 0.0
    trailing_start_r: float | None = None
    trailing_distance_points: float = 0.0
    max_bars_in_trade: int | None = None
    use_next_bar_open: bool = False
    data_source: str = "unspecified"
    code_commit: str = "unknown"
    modeling_mode: str = "ohlc"
    timezone: str = "UTC"
    random_seed: int | None = None
    data_fingerprint: str = "unknown"
    broker_profile: Mapping[str, Any] = field(default_factory=dict)
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.initial_balance <= 0:
            raise ValueError("initial_balance must be positive")
        self.cost_model.validate()
        if self.break_even_trigger_r is not None and self.break_even_trigger_r < 0:
            raise ValueError("break_even_trigger_r must be non-negative")
        if self.trailing_start_r is not None and self.trailing_start_r < 0:
            raise ValueError("trailing_start_r must be non-negative")
        if self.trailing_distance_points < 0 or self.break_even_lock_points < 0:
            raise ValueError("break-even and trailing points must be non-negative")
        if self.max_bars_in_trade is not None and self.max_bars_in_trade <= 0:
            raise ValueError("max_bars_in_trade must be positive")


@dataclass(frozen=True)
class TradeResult:
    """Closed simulated trade with audit-friendly execution details."""

    signal_id: str
    symbol: str
    direction: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    initial_sl_price: float
    final_sl_price: float
    tp_price: float
    lot: float
    profit: float
    r_multiple: float
    exit_reason: str
    duration_bars: int
    duration_seconds: float
    mae: float
    mfe: float
    spread_points: float
    slippage_points: float
    commission: float
    point: float
    tick_value: float
    tick_size: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestMetrics:
    """Metrics required by the project backtesting contract."""

    total_return_pct: float
    net_profit: float
    win_rate_pct: float
    profit_factor: float
    max_drawdown_pct: float
    daily_max_drawdown_pct: float
    sharpe: float | None
    sortino: float | None
    expectancy: float
    expected_payoff: float
    average_r: float
    trades_total: int
    average_duration_seconds: float
    average_mae: float
    average_mfe: float
    max_consecutive_losses: int
    average_consecutive_losses: float
    exposure_time_pct: float
    avg_win: float
    avg_loss: float
    payoff_ratio: float
    recovery_factor: float | None
    monthly_returns: Mapping[str, float]
    trades_per_month: Mapping[str, int]
    positive_months: int
    negative_months: int
    worst_day_return_pct: float
    worst_week_return_pct: float
    worst_month_return_pct: float
    drawdown_percentiles: Mapping[str, float]
    mae_mfe_summary: Mapping[str, float]

    def to_project_result(self, *, run_id: str, artifact_dir: str = "") -> dict[str, Any]:
        """Return a dict shaped like the PROJECT_SPEC BacktestResult contract."""

        status = "INCONCLUSIVE"
        rejection_reason = "promotion gate not evaluated"
        return {
            "run_id": run_id,
            "net_profit": self.net_profit,
            "profit_factor": self.profit_factor,
            "max_drawdown_pct": self.max_drawdown_pct,
            "daily_max_drawdown_pct": self.daily_max_drawdown_pct,
            "trades_total": self.trades_total,
            "win_rate_pct": self.win_rate_pct,
            "expected_payoff": self.expected_payoff,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "recovery_factor": self.recovery_factor,
            "notes": "Python OHLC research backtest; not an MT5 execution report.",
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "payoff_ratio": self.payoff_ratio,
            "max_consecutive_losses": self.max_consecutive_losses,
            "exposure_time_pct": self.exposure_time_pct,
            "monthly_returns_json": json.dumps(self.monthly_returns, sort_keys=True),
            "regime_breakdown_json": json.dumps({}, sort_keys=True),
            "mae_mfe_summary_json": json.dumps(self.mae_mfe_summary, sort_keys=True),
            "parameter_sensitivity_json": json.dumps({}, sort_keys=True),
            "artifact_dir": artifact_dir,
            "equity_curve_path": "",
            "trades_path": "",
            "events_path": "",
            "config_snapshot_path": "",
            "report_path": "",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "rejection_reason": rejection_reason,
            "result_fingerprint": "",
        }


@dataclass(frozen=True)
class BacktestOutcome:
    """Complete deterministic backtest output."""

    settings: BacktestSettings
    metrics: BacktestMetrics
    trades: tuple[TradeResult, ...]
    rejected_candidates: tuple[dict[str, Any], ...]
    equity_curve: pd.DataFrame

    def trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(trade) for trade in self.trades])

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "settings": _jsonable(asdict(self.settings)),
            "metrics": _jsonable(asdict(self.metrics)),
            "rejected_candidates": list(self.rejected_candidates),
        }


class Backtester:
    """Conservative OHLC backtester for precomputed trade candidates."""

    def __init__(self, settings: BacktestSettings | None = None) -> None:
        self.settings = settings or BacktestSettings()
        self.settings.validate()

    def run(
        self,
        candles: pd.DataFrame,
        candidates: Iterable[TradeCandidate | Mapping[str, Any]],
    ) -> BacktestOutcome:
        """Run a deterministic backtest over OHLC candles and candidates."""

        bars = _normalize_candles(candles)
        normalized_candidates = sorted(
            (_normalize_candidate(candidate) for candidate in candidates),
            key=lambda item: pd.Timestamp(item.timestamp),
        )
        trades: list[TradeResult] = []
        rejected: list[dict[str, Any]] = []
        exposure_indices: set[int] = set()
        for candidate in normalized_candidates:
            try:
                trade, used_indices = self._simulate_candidate(bars, candidate)
            except ValueError as exc:
                rejected.append(
                    {
                        "signal_id": candidate.signal_id,
                        "timestamp": str(candidate.timestamp),
                        "symbol": candidate.symbol,
                        "reason": str(exc),
                    }
                )
                continue
            if trade is not None:
                trades.append(trade)
                exposure_indices.update(used_indices)
        equity_curve = build_equity_curve(
            trades,
            initial_balance=self.settings.initial_balance,
            candles=bars,
        )
        metrics = calculate_metrics(
            trades,
            initial_balance=self.settings.initial_balance,
            equity_curve=equity_curve,
            total_bars=len(bars),
            exposed_bars=len(exposure_indices),
        )
        return BacktestOutcome(
            settings=self.settings,
            metrics=metrics,
            trades=tuple(trades),
            rejected_candidates=tuple(rejected),
            equity_curve=equity_curve,
        )

    def _simulate_candidate(
        self, bars: pd.DataFrame, candidate: TradeCandidate
    ) -> tuple[TradeResult | None, set[int]]:
        if candidate.lot <= 0:
            raise ValueError("candidate lot must be positive")
        if candidate.sl_price <= 0 or candidate.tp_price <= 0:
            raise ValueError("candidate requires positive SL and TP")

        timestamp = pd.Timestamp(candidate.timestamp)
        start_idx = _first_bar_index_at_or_after(bars, timestamp)
        if start_idx is None:
            raise ValueError("candidate timestamp is outside candle data")
        if self.settings.use_next_bar_open:
            start_idx += 1
            if start_idx >= len(bars):
                raise ValueError("no next bar available for entry")

        entry_bar = bars.iloc[start_idx]
        spread_points = _bar_spread_points(entry_bar, self.settings.cost_model.spread_points)
        if spread_points > self.settings.cost_model.max_spread_points:
            raise ValueError("spread exceeds configured maximum")

        direction = _direction_value(candidate.direction)
        base_entry = float(candidate.entry_price if candidate.entry_price is not None else entry_bar.open)
        entry_price = _apply_entry_cost(
            base_entry,
            direction=direction,
            spread_points=spread_points,
            slippage_points=self.settings.cost_model.slippage_points,
            point=self.settings.cost_model.point,
        )
        _validate_directional_prices(direction, entry_price, candidate.sl_price, candidate.tp_price)

        initial_sl = float(candidate.sl_price)
        current_sl = initial_sl
        tp_price = float(candidate.tp_price)
        risk_distance = abs(entry_price - initial_sl)
        if risk_distance <= 0:
            raise ValueError("SL distance must be positive")

        max_idx = len(bars) - 1
        if self.settings.max_bars_in_trade is not None:
            max_idx = min(max_idx, start_idx + self.settings.max_bars_in_trade - 1)

        mae = 0.0
        mfe = 0.0
        exit_base_price = float(bars.iloc[max_idx].close)
        exit_reason = "END_OF_DATA"
        exit_idx = max_idx
        used_indices: set[int] = set()

        for idx in range(start_idx, max_idx + 1):
            row = bars.iloc[idx]
            used_indices.add(idx)
            high = float(row.high)
            low = float(row.low)
            if direction == Direction.BUY.value:
                mae = min(mae, low - entry_price)
                mfe = max(mfe, high - entry_price)
                if low <= current_sl:
                    exit_base_price = current_sl
                    exit_reason = "SL"
                    exit_idx = idx
                    break
                if high >= tp_price:
                    exit_base_price = tp_price
                    exit_reason = "TP"
                    exit_idx = idx
                    break
                current_sl = self._maybe_move_stop(
                    direction=direction,
                    current_sl=current_sl,
                    entry_price=entry_price,
                    favorable_excursion=mfe,
                    risk_distance=risk_distance,
                    bar_extreme=high,
                )
            else:
                mae = min(mae, entry_price - high)
                mfe = max(mfe, entry_price - low)
                if high >= current_sl:
                    exit_base_price = current_sl
                    exit_reason = "SL"
                    exit_idx = idx
                    break
                if low <= tp_price:
                    exit_base_price = tp_price
                    exit_reason = "TP"
                    exit_idx = idx
                    break
                current_sl = self._maybe_move_stop(
                    direction=direction,
                    current_sl=current_sl,
                    entry_price=entry_price,
                    favorable_excursion=mfe,
                    risk_distance=risk_distance,
                    bar_extreme=low,
                )

        exit_price = _apply_exit_cost(
            exit_base_price,
            direction=direction,
            spread_points=spread_points,
            slippage_points=self.settings.cost_model.slippage_points,
            point=self.settings.cost_model.point,
        )
        commission = self.settings.cost_model.commission_per_lot_round_turn * candidate.lot
        profit = _profit_for_price_move(
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            lot=candidate.lot,
            tick_size=self.settings.cost_model.tick_size,
            tick_value=self.settings.cost_model.tick_value,
            commission=commission,
        )
        planned_risk = (
            risk_distance / self.settings.cost_model.tick_size
        ) * self.settings.cost_model.tick_value * candidate.lot
        r_multiple = profit / planned_risk if planned_risk > 0 else 0.0
        entry_time = pd.Timestamp(bars.iloc[start_idx].timestamp)
        exit_time = pd.Timestamp(bars.iloc[exit_idx].timestamp)
        duration_seconds = max((exit_time - entry_time).total_seconds(), 0.0)
        signal_id = candidate.signal_id or f"candidate_{start_idx}_{len(used_indices)}"
        trade = TradeResult(
            signal_id=signal_id,
            symbol=candidate.symbol,
            direction=direction,
            entry_time=entry_time.isoformat(),
            exit_time=exit_time.isoformat(),
            entry_price=entry_price,
            exit_price=exit_price,
            initial_sl_price=initial_sl,
            final_sl_price=current_sl,
            tp_price=tp_price,
            lot=candidate.lot,
            profit=profit,
            r_multiple=r_multiple,
            exit_reason=exit_reason,
            duration_bars=len(used_indices),
            duration_seconds=duration_seconds,
            mae=mae,
            mfe=mfe,
            spread_points=spread_points,
            slippage_points=self.settings.cost_model.slippage_points,
            commission=commission,
            point=self.settings.cost_model.point,
            tick_value=self.settings.cost_model.tick_value,
            tick_size=self.settings.cost_model.tick_size,
            metadata=dict(candidate.metadata),
        )
        return trade, used_indices

    def _maybe_move_stop(
        self,
        *,
        direction: str,
        current_sl: float,
        entry_price: float,
        favorable_excursion: float,
        risk_distance: float,
        bar_extreme: float,
    ) -> float:
        new_sl = current_sl
        point = self.settings.cost_model.point
        if (
            self.settings.break_even_trigger_r is not None
            and favorable_excursion >= self.settings.break_even_trigger_r * risk_distance
        ):
            lock = self.settings.break_even_lock_points * point
            if direction == Direction.BUY.value:
                new_sl = max(new_sl, entry_price + lock)
            else:
                new_sl = min(new_sl, entry_price - lock)
        if (
            self.settings.trailing_start_r is not None
            and self.settings.trailing_distance_points > 0
            and favorable_excursion >= self.settings.trailing_start_r * risk_distance
        ):
            distance = self.settings.trailing_distance_points * point
            if direction == Direction.BUY.value:
                new_sl = max(new_sl, bar_extreme - distance)
            else:
                new_sl = min(new_sl, bar_extreme + distance)
        return new_sl


def calculate_metrics(
    trades: Iterable[TradeResult | Mapping[str, Any]],
    *,
    initial_balance: float = 10_000.0,
    equity_curve: pd.DataFrame | None = None,
    total_bars: int | None = None,
    exposed_bars: int | None = None,
) -> BacktestMetrics:
    """Calculate project-required metrics from closed trades."""

    normalized = [_trade_to_mapping(trade) for trade in trades]
    profits = np.array([float(trade["profit"]) for trade in normalized], dtype=float)
    r_values = np.array([float(trade.get("r_multiple", 0.0)) for trade in normalized], dtype=float)
    wins = profits[profits > 0]
    losses = profits[profits < 0]
    net_profit = float(profits.sum()) if len(profits) else 0.0
    gross_profit = float(wins.sum()) if len(wins) else 0.0
    gross_loss = abs(float(losses.sum())) if len(losses) else 0.0
    profit_factor = math.inf if gross_profit > 0 and gross_loss == 0 else (
        gross_profit / gross_loss if gross_loss > 0 else 0.0
    )
    trades_total = len(profits)
    win_rate_pct = (len(wins) / trades_total * 100.0) if trades_total else 0.0
    expectancy = float(profits.mean()) if trades_total else 0.0
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    payoff_ratio = abs(avg_win / avg_loss) if avg_loss < 0 else 0.0
    average_r = float(r_values.mean()) if len(r_values) else 0.0
    durations = np.array([float(trade.get("duration_seconds", 0.0)) for trade in normalized])
    maes = np.array([float(trade.get("mae", 0.0)) for trade in normalized])
    mfes = np.array([float(trade.get("mfe", 0.0)) for trade in normalized])

    if equity_curve is None:
        equity_curve = build_equity_curve(normalized, initial_balance=initial_balance)
    equity = equity_curve["equity"].astype(float)
    max_dd_pct, drawdown_pct = _max_drawdown_pct(equity)
    daily_max_dd_pct = _daily_max_drawdown_pct(equity_curve)
    trade_returns = _trade_returns(profits, initial_balance)
    sharpe = _sharpe(trade_returns)
    sortino = _sortino(trade_returns)
    recovery_factor = net_profit / abs(max_dd_pct / 100.0 * initial_balance) if max_dd_pct < 0 else None
    monthly_returns, trades_per_month = _monthly_stats(normalized, initial_balance)
    worst_day, worst_week, worst_month = _worst_period_returns(equity_curve)
    exposure_time_pct = _exposure_time_pct(
        normalized,
        total_bars=total_bars,
        exposed_bars=exposed_bars,
    )
    loss_runs = _loss_runs(profits)
    average_consecutive_losses = float(np.mean(loss_runs)) if loss_runs else 0.0
    drawdown_percentiles = {
        "p50": float(np.percentile(drawdown_pct, 50)) if len(drawdown_pct) else 0.0,
        "p75": float(np.percentile(drawdown_pct, 75)) if len(drawdown_pct) else 0.0,
        "p95": float(np.percentile(drawdown_pct, 95)) if len(drawdown_pct) else 0.0,
    }
    mae_mfe_summary = {
        "average_mae": float(maes.mean()) if len(maes) else 0.0,
        "worst_mae": float(maes.min()) if len(maes) else 0.0,
        "average_mfe": float(mfes.mean()) if len(mfes) else 0.0,
        "best_mfe": float(mfes.max()) if len(mfes) else 0.0,
    }
    return BacktestMetrics(
        total_return_pct=(net_profit / initial_balance * 100.0) if initial_balance else 0.0,
        net_profit=net_profit,
        win_rate_pct=win_rate_pct,
        profit_factor=profit_factor,
        max_drawdown_pct=max_dd_pct,
        daily_max_drawdown_pct=daily_max_dd_pct,
        sharpe=sharpe,
        sortino=sortino,
        expectancy=expectancy,
        expected_payoff=expectancy,
        average_r=average_r,
        trades_total=trades_total,
        average_duration_seconds=float(durations.mean()) if len(durations) else 0.0,
        average_mae=float(maes.mean()) if len(maes) else 0.0,
        average_mfe=float(mfes.mean()) if len(mfes) else 0.0,
        max_consecutive_losses=max(loss_runs) if loss_runs else 0,
        average_consecutive_losses=average_consecutive_losses,
        exposure_time_pct=exposure_time_pct,
        avg_win=avg_win,
        avg_loss=avg_loss,
        payoff_ratio=payoff_ratio,
        recovery_factor=recovery_factor,
        monthly_returns=monthly_returns,
        trades_per_month=trades_per_month,
        positive_months=sum(1 for value in monthly_returns.values() if value > 0),
        negative_months=sum(1 for value in monthly_returns.values() if value < 0),
        worst_day_return_pct=worst_day,
        worst_week_return_pct=worst_week,
        worst_month_return_pct=worst_month,
        drawdown_percentiles=drawdown_percentiles,
        mae_mfe_summary=mae_mfe_summary,
    )


def build_equity_curve(
    trades: Iterable[TradeResult | Mapping[str, Any]],
    *,
    initial_balance: float,
    candles: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build an equity curve from trade close times and optional candle dates."""

    normalized = [_trade_to_mapping(trade) for trade in trades]
    if candles is not None and len(candles):
        bars = _normalize_candles(candles)
        curve = pd.DataFrame({"timestamp": bars["timestamp"], "equity": initial_balance})
    else:
        timestamps = [pd.Timestamp(trade["exit_time"]) for trade in normalized]
        if not timestamps:
            timestamps = [pd.Timestamp("1970-01-01T00:00:00Z")]
        curve = pd.DataFrame({"timestamp": sorted(timestamps), "equity": initial_balance})
    curve = curve.sort_values("timestamp").reset_index(drop=True)
    equity = float(initial_balance)
    grouped: dict[pd.Timestamp, float] = {}
    for trade in normalized:
        ts = pd.Timestamp(trade["exit_time"])
        grouped[ts] = grouped.get(ts, 0.0) + float(trade["profit"])
    ordered = sorted(grouped.items(), key=lambda item: item[0])
    pointer = 0
    values: list[float] = []
    for timestamp in curve["timestamp"]:
        while pointer < len(ordered) and ordered[pointer][0] <= timestamp:
            equity += ordered[pointer][1]
            pointer += 1
        values.append(equity)
    if pointer < len(ordered):
        for timestamp, profit in ordered[pointer:]:
            equity += profit
            curve.loc[len(curve)] = [timestamp, equity]
            values.append(equity)
    curve["equity"] = values[: len(curve)]
    return curve.sort_values("timestamp").reset_index(drop=True)


def _normalize_candles(candles: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close"}
    missing = required - set(candles.columns)
    if missing:
        raise ValueError(f"candles missing columns: {sorted(missing)}")
    bars = candles.copy()
    if "timestamp" not in bars.columns:
        if isinstance(bars.index, pd.DatetimeIndex):
            bars = bars.reset_index().rename(columns={bars.index.name or "index": "timestamp"})
        else:
            raise ValueError("candles require a timestamp column or DatetimeIndex")
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    for column in ("open", "high", "low", "close"):
        bars[column] = bars[column].astype(float)
    if "spread_points" in bars.columns:
        bars["spread_points"] = bars["spread_points"].astype(float)
    if (bars["high"] < bars["low"]).any():
        raise ValueError("candle high cannot be below low")
    return bars.sort_values("timestamp").reset_index(drop=True)


def _normalize_candidate(candidate: TradeCandidate | Mapping[str, Any]) -> TradeCandidate:
    if isinstance(candidate, TradeCandidate):
        return candidate
    return TradeCandidate(**dict(candidate))


def _direction_value(direction: Direction | str) -> str:
    value = direction.value if isinstance(direction, Direction) else str(direction).upper()
    if value not in {Direction.BUY.value, Direction.SELL.value}:
        raise ValueError("direction must be BUY or SELL")
    return value


def _first_bar_index_at_or_after(bars: pd.DataFrame, timestamp: pd.Timestamp) -> int | None:
    timestamps = bars["timestamp"]
    positions = np.flatnonzero(timestamps >= timestamp)
    return int(positions[0]) if len(positions) else None


def _bar_spread_points(row: pd.Series, default: float) -> float:
    if "spread_points" in row and not pd.isna(row["spread_points"]):
        return float(row["spread_points"])
    return float(default)


def _apply_entry_cost(
    base_price: float,
    *,
    direction: str,
    spread_points: float,
    slippage_points: float,
    point: float,
) -> float:
    cost = ((spread_points / 2.0) + slippage_points) * point
    return base_price + cost if direction == Direction.BUY.value else base_price - cost


def _apply_exit_cost(
    base_price: float,
    *,
    direction: str,
    spread_points: float,
    slippage_points: float,
    point: float,
) -> float:
    cost = ((spread_points / 2.0) + slippage_points) * point
    return base_price - cost if direction == Direction.BUY.value else base_price + cost


def _validate_directional_prices(direction: str, entry: float, sl: float, tp: float) -> None:
    if direction == Direction.BUY.value and not (sl < entry < tp):
        raise ValueError("BUY candidate requires sl < entry < tp")
    if direction == Direction.SELL.value and not (tp < entry < sl):
        raise ValueError("SELL candidate requires tp < entry < sl")


def _profit_for_price_move(
    *,
    direction: str,
    entry_price: float,
    exit_price: float,
    lot: float,
    tick_size: float,
    tick_value: float,
    commission: float,
) -> float:
    move = exit_price - entry_price
    if direction == Direction.SELL.value:
        move *= -1.0
    return (move / tick_size) * tick_value * lot - commission


def _trade_to_mapping(trade: TradeResult | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(trade, TradeResult):
        return asdict(trade)
    return trade


def _max_drawdown_pct(equity: pd.Series) -> tuple[float, np.ndarray]:
    if len(equity) == 0:
        return 0.0, np.array([], dtype=float)
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max.replace(0, np.nan) * 100.0
    drawdown = drawdown.fillna(0.0)
    return float(drawdown.min()), np.abs(drawdown.to_numpy(dtype=float))


def _daily_max_drawdown_pct(equity_curve: pd.DataFrame) -> float:
    if len(equity_curve) == 0:
        return 0.0
    curve = equity_curve.copy()
    curve["timestamp"] = pd.to_datetime(curve["timestamp"], utc=True)
    worst = 0.0
    for _, group in curve.groupby(curve["timestamp"].dt.date):
        dd, _ = _max_drawdown_pct(group["equity"].astype(float))
        worst = min(worst, dd)
    return float(worst)


def _trade_returns(profits: np.ndarray, initial_balance: float) -> np.ndarray:
    returns: list[float] = []
    equity = float(initial_balance)
    for profit in profits:
        returns.append(float(profit) / equity if equity else 0.0)
        equity += float(profit)
    return np.array(returns, dtype=float)


def _sharpe(returns: np.ndarray) -> float | None:
    if len(returns) < 2:
        return None
    std = float(returns.std(ddof=1))
    if std == 0:
        return None
    return float(returns.mean() / std * math.sqrt(len(returns)))


def _sortino(returns: np.ndarray) -> float | None:
    if len(returns) < 2:
        return None
    downside = returns[returns < 0]
    if len(downside) == 0:
        return None
    downside_std = float(downside.std(ddof=1)) if len(downside) > 1 else abs(float(downside[0]))
    if downside_std == 0:
        return None
    return float(returns.mean() / downside_std * math.sqrt(len(returns)))


def _monthly_stats(
    trades: list[Mapping[str, Any]], initial_balance: float
) -> tuple[dict[str, float], dict[str, int]]:
    equity = float(initial_balance)
    profits_by_month: dict[str, float] = {}
    counts_by_month: dict[str, int] = {}
    for trade in trades:
        month = pd.Timestamp(trade["exit_time"]).strftime("%Y-%m")
        profits_by_month[month] = profits_by_month.get(month, 0.0) + float(trade["profit"])
        counts_by_month[month] = counts_by_month.get(month, 0) + 1
    returns: dict[str, float] = {}
    for month in sorted(profits_by_month):
        profit = profits_by_month[month]
        returns[month] = profit / equity * 100.0 if equity else 0.0
        equity += profit
    return returns, counts_by_month


def _worst_period_returns(equity_curve: pd.DataFrame) -> tuple[float, float, float]:
    if len(equity_curve) < 2:
        return 0.0, 0.0, 0.0
    curve = equity_curve.copy()
    curve["timestamp"] = pd.to_datetime(curve["timestamp"], utc=True)
    curve = curve.set_index("timestamp").sort_index()

    def worst(freq: str) -> float:
        period = curve["equity"].resample(freq).last().dropna()
        returns = period.pct_change().dropna() * 100.0
        return float(returns.min()) if len(returns) else 0.0

    return worst("D"), worst("W"), worst("ME")


def _exposure_time_pct(
    trades: list[Mapping[str, Any]],
    *,
    total_bars: int | None,
    exposed_bars: int | None,
) -> float:
    if total_bars and exposed_bars is not None:
        return min(100.0, exposed_bars / total_bars * 100.0)
    if not trades:
        return 0.0
    starts = [pd.Timestamp(trade["entry_time"]) for trade in trades]
    exits = [pd.Timestamp(trade["exit_time"]) for trade in trades]
    total = (max(exits) - min(starts)).total_seconds()
    exposed = sum(max((exit_ - start).total_seconds(), 0.0) for start, exit_ in zip(starts, exits))
    return min(100.0, exposed / total * 100.0) if total > 0 else 0.0


def _loss_runs(profits: np.ndarray) -> list[int]:
    runs: list[int] = []
    current = 0
    for profit in profits:
        if profit < 0:
            current += 1
        elif current:
            runs.append(current)
            current = 0
    if current:
        runs.append(current)
    return runs


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, float) and math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value
