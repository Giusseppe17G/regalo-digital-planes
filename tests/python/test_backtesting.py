from pathlib import Path

import pandas as pd

from agi_style_forex_bot_mt5.backtesting import (
    Backtester,
    BacktestSettings,
    CostModel,
    MonteCarloSimulator,
    PerformanceReportWriter,
    StressTester,
    TradeCandidate,
)


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=6, freq="h", tz="UTC"),
            "open": [1.1000, 1.1000, 1.1010, 1.1020, 1.1010, 1.1005],
            "high": [1.1010, 1.1035, 1.1020, 1.1025, 1.1015, 1.1010],
            "low": [1.0996, 1.0995, 1.0980, 1.1000, 1.0990, 1.0995],
            "close": [1.1000, 1.1020, 1.0990, 1.1010, 1.1005, 1.1000],
            "spread_points": [10, 10, 10, 10, 10, 10],
        }
    )


def test_backtester_applies_costs_and_core_metrics() -> None:
    settings = BacktestSettings(
        initial_balance=10_000,
        cost_model=CostModel(
            spread_points=10,
            slippage_points=0,
            point=0.0001,
            tick_size=0.0001,
            tick_value=10,
            max_spread_points=25,
        ),
    )
    candidates = [
        TradeCandidate(
            timestamp="2026-01-01T00:00:00Z",
            symbol="EURUSD",
            direction="BUY",
            sl_price=1.0990,
            tp_price=1.1020,
            lot=1.0,
            signal_id="win",
        ),
        TradeCandidate(
            timestamp="2026-01-01T02:00:00Z",
            symbol="EURUSD",
            direction="BUY",
            sl_price=1.0990,
            tp_price=1.1030,
            lot=1.0,
            signal_id="loss",
        ),
    ]

    outcome = Backtester(settings).run(_candles(), candidates)

    assert outcome.metrics.trades_total == 2
    assert outcome.metrics.win_rate_pct == 50.0
    assert outcome.metrics.profit_factor > 0
    assert outcome.metrics.max_consecutive_losses == 1
    assert outcome.metrics.average_duration_seconds >= 0
    assert outcome.rejected_candidates == ()


def test_backtester_rejects_high_spread_candidate() -> None:
    settings = BacktestSettings(
        cost_model=CostModel(spread_points=30, max_spread_points=25),
    )
    candidate = TradeCandidate(
        timestamp="2026-01-01T00:00:00Z",
        symbol="EURUSD",
        direction="BUY",
        sl_price=1.0990,
        tp_price=1.1020,
    )

    outcome = Backtester(settings).run(_candles().drop(columns=["spread_points"]), [candidate])

    assert outcome.metrics.trades_total == 0
    assert outcome.rejected_candidates[0]["reason"] == "spread exceeds configured maximum"


def test_monte_carlo_is_reproducible_with_seed() -> None:
    profits = [100, -50, 80, -20, -10]

    first = MonteCarloSimulator(seed=42).run(profits, iterations=100)
    second = MonteCarloSimulator(seed=42).run(profits, iterations=100)

    assert first.final_equity_percentiles == second.final_equity_percentiles
    assert first.max_drawdown_percentiles == second.max_drawdown_percentiles


def test_stress_and_reports(tmp_path: Path) -> None:
    settings = BacktestSettings(
        cost_model=CostModel(
            spread_points=10,
            point=0.0001,
            tick_size=0.0001,
            tick_value=10,
            max_spread_points=25,
        ),
    )
    outcome = Backtester(settings).run(
        _candles(),
        [
            TradeCandidate(
                timestamp="2026-01-01T00:00:00Z",
                symbol="EURUSD",
                direction="BUY",
                sl_price=1.0990,
                tp_price=1.1020,
                signal_id="report",
            )
        ],
    )

    stressed = StressTester().spread_slippage_sensitivity(outcome.trades)
    artifacts = PerformanceReportWriter().write(outcome, tmp_path)

    assert stressed
    assert Path(artifacts.summary_json_path).exists()
    assert Path(artifacts.trades_csv_path).exists()
    assert Path(artifacts.equity_curve_csv_path).exists()
