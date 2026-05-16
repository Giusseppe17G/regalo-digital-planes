import json
from pathlib import Path

import pytest
import requests

from agi_style_forex_bot_mt5.contracts import Environment, Event, Severity
from agi_style_forex_bot_mt5.telemetry import (
    JsonlAuditLogger,
    TelemetryDatabase,
    TelegramNotifier,
)


def make_event(**overrides: object) -> Event:
    values = {
        "run_id": "run_test",
        "environment": Environment.DEMO,
        "severity": Severity.WARNING,
        "module": "risk",
        "event_type": "SIGNAL_REJECTED",
        "message": "blocked account 12345678 with token 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "correlation_id": "sig_1",
        "signal_id": "sig_1",
        "symbol": "EURUSD",
        "payload": {
            "account_login": 12345678,
            "server": "Broker-Demo-1",
            "safe_value": "kept",
        },
    }
    values.update(overrides)
    return Event.create(**values)


def test_sqlite_domain_tables_and_idempotent_signal_insert(tmp_path: Path) -> None:
    db = TelemetryDatabase(tmp_path / "telemetry.sqlite3")
    try:
        for table in (
            "signals",
            "orders",
            "trades",
            "errors",
            "account_snapshots",
            "risk_events",
            "broker_quality",
            "model_predictions",
            "backtest_results",
        ):
            assert db.count_rows(table) == 0

        record = {
            "signal_id": "sig_1",
            "symbol": "EURUSD",
            "status": "REJECTED",
            "account_login": 12345678,
        }
        assert db.insert_record("signals", record, idempotency_key="signal:sig_1") is True
        assert db.insert_record("signals", record, idempotency_key="signal:sig_1") is False
        assert db.count_rows("signals") == 1

        payload = json.loads(db.fetch_all("signals")[0]["payload_json"])
        assert payload["account_login"] != 12345678
        assert "12345678" not in db.fetch_all("signals")[0]["payload_json"]
    finally:
        db.close()


def test_jsonl_logger_appends_valid_redacted_event(tmp_path: Path) -> None:
    logger = JsonlAuditLogger(tmp_path / "logs")
    path = logger.append_event(make_event())

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["signal_id"] == "sig_1"
    assert record["payload_json"]
    assert "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ" not in lines[0]
    assert "12345678" not in lines[0]
    assert "Broker-Demo-1" not in lines[0]


def test_telegram_failure_is_queued_and_does_not_raise(tmp_path: Path) -> None:
    db = TelemetryDatabase(tmp_path / "telemetry.sqlite3")

    def failing_sender(_url: str, _payload: object, _timeout: float) -> requests.Response:
        raise requests.Timeout("request timed out for token 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    try:
        notifier = TelegramNotifier(
            database=db,
            enabled=True,
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            chat_id="987654321",
            sender=failing_sender,
        )
        result = notifier.notify_event(make_event(event_type="ORDER_SENT"))

        assert result.sent is False
        assert result.status == "FAILED"
        assert db.count_rows("telegram_outbox") == 1
        assert db.count_rows("delivery_attempts") == 1
        outbox = db.fetch_all("telegram_outbox")[0]
        assert outbox["status"] == "FAILED"
        assert "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ" not in outbox["last_error"]
        assert "987654321" not in outbox["chat_id_redacted"]
    finally:
        db.close()


def test_telegram_disabled_still_queues_without_attempt(tmp_path: Path) -> None:
    db = TelemetryDatabase(tmp_path / "telemetry.sqlite3")
    try:
        notifier = TelegramNotifier(database=db, enabled=False)
        result = notifier.notify_event(make_event(event_type="BOT_STARTED", severity=Severity.INFO))

        assert result.status == "DISABLED"
        assert result.sent is False
        assert db.count_rows("telegram_outbox") == 1
        assert db.count_rows("delivery_attempts") == 0
    finally:
        db.close()
