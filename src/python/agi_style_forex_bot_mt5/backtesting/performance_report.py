"""JSON and CSV report writer for reproducible backtests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .backtester import BacktestOutcome


@dataclass(frozen=True)
class ReportArtifacts:
    artifact_dir: str
    summary_json_path: str
    trades_csv_path: str
    equity_curve_csv_path: str
    config_snapshot_json_path: str


class PerformanceReportWriter:
    """Persist backtest outputs as JSON and CSV artifacts."""

    def write(self, outcome: BacktestOutcome, artifact_dir: str | Path) -> ReportArtifacts:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        summary_path = path / "summary.json"
        trades_path = path / "trades.csv"
        equity_path = path / "equity_curve.csv"
        config_path = path / "config_snapshot.json"

        summary = outcome.to_summary_dict()
        project_result = outcome.metrics.to_project_result(
            run_id=outcome.settings.run_id,
            artifact_dir=str(path),
        )
        project_result.update(
            {
                "equity_curve_path": str(equity_path),
                "trades_path": str(trades_path),
                "config_snapshot_path": str(config_path),
                "report_path": str(summary_path),
            }
        )
        summary["project_result"] = project_result
        summary_path.write_text(
            json.dumps(_jsonable(summary), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        trades_frame = outcome.trades_frame()
        if trades_frame.empty:
            trades_frame = pd.DataFrame(columns=["signal_id", "profit", "r_multiple"])
        trades_frame.to_csv(trades_path, index=False)
        outcome.equity_curve.to_csv(equity_path, index=False)
        config_path.write_text(
            json.dumps(_jsonable(asdict(outcome.settings)), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return ReportArtifacts(
            artifact_dir=str(path),
            summary_json_path=str(summary_path),
            trades_csv_path=str(trades_path),
            equity_curve_csv_path=str(equity_path),
            config_snapshot_json_path=str(config_path),
        )


def write_reports(outcome: BacktestOutcome, artifact_dir: str | Path) -> ReportArtifacts:
    return PerformanceReportWriter().write(outcome, artifact_dir)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if value == float("inf"):
        return "Infinity"
    if value == float("-inf"):
        return "-Infinity"
    return value
