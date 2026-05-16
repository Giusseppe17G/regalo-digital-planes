"""Backtesting and validation tools for AGI_STYLE_FOREX_BOT_MT5."""

from .backtester import (
    Backtester,
    BacktestMetrics,
    BacktestOutcome,
    BacktestSettings,
    CostModel,
    TradeCandidate,
    TradeResult,
    calculate_metrics,
)
from .monte_carlo import MonteCarloResult, MonteCarloSimulator, monte_carlo_metrics
from .performance_report import PerformanceReportWriter, ReportArtifacts, write_reports
from .stress_tester import StressResult, StressTester
from .walk_forward_optimizer import WalkForwardFold, WalkForwardOptimizer, WalkForwardResult

__all__ = [
    "Backtester",
    "BacktestMetrics",
    "BacktestOutcome",
    "BacktestSettings",
    "CostModel",
    "MonteCarloResult",
    "MonteCarloSimulator",
    "PerformanceReportWriter",
    "ReportArtifacts",
    "StressResult",
    "StressTester",
    "TradeCandidate",
    "TradeResult",
    "WalkForwardFold",
    "WalkForwardOptimizer",
    "WalkForwardResult",
    "calculate_metrics",
    "monte_carlo_metrics",
    "write_reports",
]
