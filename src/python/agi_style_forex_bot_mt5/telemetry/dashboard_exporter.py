"""Read-only dashboard snapshots for local telemetry inspection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agi_style_forex_bot_mt5.telemetry.database import TelemetryDatabase
from agi_style_forex_bot_mt5.telemetry.logger_setup import compact_json, utc_now_iso


def build_dashboard_snapshot(database: TelemetryDatabase) -> dict[str, Any]:
    """Return a compact, redacted telemetry summary suitable for dashboards."""

    counts = database.table_counts()
    outbox_rows = database.fetch_all("telegram_outbox")
    pending_telegram = sum(1 for row in outbox_rows if row["status"] == "PENDING")
    failed_telegram = sum(1 for row in outbox_rows if row["status"] == "FAILED")
    return {
        "generated_at_utc": utc_now_iso(),
        "table_counts": counts,
        "telegram": {
            "pending": pending_telegram,
            "failed": failed_telegram,
        },
    }


def export_dashboard_snapshot(
    database: TelemetryDatabase,
    output_path: str | Path = "data/dashboard/telemetry_snapshot.json",
) -> Path:
    """Write the current dashboard snapshot as deterministic JSON."""

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads(compact_json(build_dashboard_snapshot(database)))
    target.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    return target

