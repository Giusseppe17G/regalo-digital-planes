from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from agi_style_forex_bot_mt5.bot import AuditUnavailableError, ShadowDemoBot
from agi_style_forex_bot_mt5.cli import build_sample_features, build_sample_snapshot
from agi_style_forex_bot_mt5.config import BotConfig
from agi_style_forex_bot_mt5.contracts import AccountState, RiskDecision, SignalAction
from agi_style_forex_bot_mt5.execution import ShadowExecutionEngine
from agi_style_forex_bot_mt5.json_contracts import validate_contract
from agi_style_forex_bot_mt5.telemetry import JsonlAuditLogger, TelegramNotifier, TelemetryDatabase


class FailingTelegramSender:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _url: str, _payload: object, _timeout: float) -> requests.Response:
        self.calls += 1
        raise requests.ConnectionError("telegram failed for token 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ")


class RejectingRiskEngine:
    def evaluate(self, *, signal, snapshot, account, state) -> RiskDecision:
        return RiskDecision(
            signal_id=signal.signal_id,
            accepted=False,
            reject_code="HIGH_SPREAD",
            reject_reason="spread too high",
            checks={"spread": {"status": "failed"}},
        )


class SpyShadowExecutionEngine(ShadowExecutionEngine):
    def __init__(self) -> None:
        self.calls = 0

    def create_order(self, **kwargs):
        self.calls += 1
        return super().create_order(**kwargs)


def _demo_account() -> AccountState:
    return AccountState(
        login=123,
        trade_mode="DEMO",
        balance=10_000,
        equity=10_000,
        margin_free=9_000,
        is_demo=True,
        trade_allowed=True,
    )


def _records(log_dir: Path) -> list[dict]:
    return [
        json.loads(line)
        for path in log_dir.glob("events-*.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def test_signal_accepted_creates_shadow_order_and_persists_sqlite_jsonl(tmp_path: Path) -> None:
    db = TelemetryDatabase(tmp_path / "telemetry.sqlite3")
    try:
        bot = ShadowDemoBot(
            config=BotConfig(),
            audit_logger=JsonlAuditLogger(tmp_path / "logs"),
            database=db,
            run_id="run_phase2_accept",
        )
        result = bot.run_once(
            snapshot=build_sample_snapshot(),
            features=build_sample_features(),
            account=_demo_account(),
        )

        assert result.strategy_action == SignalAction.BUY
        assert result.risk_accepted is True
        assert result.shadow_order_created is True
        assert result.execution_attempted is False
        assert db.count_rows("orders") == 1
        order = db.fetch_all("orders")[0]
        payload = json.loads(order["payload_json"])
        assert payload["mode"] == "shadow"
        assert payload["status"] == "created"
        assert payload["sl"] > 0
        assert payload["tp"] > 0
        assert payload["lot"] > 0
        validate_contract("ShadowOrder", payload)
        assert "SHADOW_ORDER_CREATED" in [record["event_type"] for record in _records(tmp_path / "logs")]
    finally:
        db.close()


def test_telegram_fail_safe_records_error_and_continues(tmp_path: Path) -> None:
    db = TelemetryDatabase(tmp_path / "telemetry.sqlite3")
    failing_sender = FailingTelegramSender()
    try:
        bot = ShadowDemoBot(
            config=BotConfig(),
            audit_logger=JsonlAuditLogger(tmp_path / "logs"),
            database=db,
            telegram_notifier=TelegramNotifier(
                database=db,
                enabled=True,
                bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                chat_id="123456789",
                sender=failing_sender,
            ),
            run_id="run_phase2_telegram",
        )

        result = bot.run_once(
            snapshot=build_sample_snapshot(),
            features=build_sample_features(),
            account=_demo_account(),
        )

        assert result.shadow_order_created is True
        assert failing_sender.calls > 0
        assert db.count_rows("telegram_outbox") > 0
        assert any(row["status"] == "FAILED" for row in db.fetch_all("telegram_outbox"))
        assert any(record["event_type"] == "TELEGRAM_ERROR" for record in _records(tmp_path / "logs"))
    finally:
        db.close()


def test_no_order_send_in_shadow_mode_even_with_shadow_order(tmp_path: Path) -> None:
    spy = SpyShadowExecutionEngine()
    bot = ShadowDemoBot(
        config=BotConfig(),
        audit_logger=JsonlAuditLogger(tmp_path / "logs"),
        shadow_execution_engine=spy,
        run_id="run_phase2_no_send",
    )
    result = bot.run_once(
        snapshot=build_sample_snapshot(),
        features=build_sample_features(),
        account=_demo_account(),
    )
    assert result.shadow_order_created is True
    assert result.execution_attempted is False
    assert spy.calls == 1


def test_signal_rejected_creates_no_shadow_order(tmp_path: Path) -> None:
    features = {**build_sample_features(), "regime": "SPREAD_DANGER", "spread_points": 40}
    spy = SpyShadowExecutionEngine()
    bot = ShadowDemoBot(
        config=BotConfig(),
        audit_logger=JsonlAuditLogger(tmp_path / "logs"),
        shadow_execution_engine=spy,
        run_id="run_phase2_signal_reject",
    )
    result = bot.run_once(snapshot=build_sample_snapshot(), features=features, account=_demo_account())
    assert result.strategy_action == SignalAction.NONE
    assert result.shadow_order_created is False
    assert spy.calls == 0


def test_risk_rejected_creates_no_shadow_order(tmp_path: Path) -> None:
    spy = SpyShadowExecutionEngine()
    bot = ShadowDemoBot(
        config=BotConfig(),
        audit_logger=JsonlAuditLogger(tmp_path / "logs"),
        risk_engine=RejectingRiskEngine(),
        shadow_execution_engine=spy,
        run_id="run_phase2_risk_reject",
    )
    result = bot.run_once(
        snapshot=build_sample_snapshot(),
        features=build_sample_features(),
        account=_demo_account(),
    )
    assert result.risk_accepted is False
    assert result.risk_reject_code == "HIGH_SPREAD"
    assert result.shadow_order_created is False
    assert spy.calls == 0


def test_missing_sl_tp_fails_closed_before_shadow_order(tmp_path: Path) -> None:
    snapshot = build_sample_snapshot()
    bad_snapshot = replace(snapshot, stops_level_points=500000)
    spy = SpyShadowExecutionEngine()
    bot = ShadowDemoBot(
        config=BotConfig(),
        audit_logger=JsonlAuditLogger(tmp_path / "logs"),
        shadow_execution_engine=spy,
        run_id="run_phase2_bad_stops",
    )
    result = bot.run_once(snapshot=bad_snapshot, features=build_sample_features(), account=_demo_account())
    assert result.shadow_order_created is False
    assert result.risk_reject_code == "CRITICAL_ERROR"
    assert spy.calls == 0


def test_missing_audit_sink_fails_closed() -> None:
    with pytest.raises(AuditUnavailableError):
        ShadowDemoBot(config=BotConfig(), audit_logger=None, database=None)


def test_idempotency_key_prevents_duplicate_shadow_order(tmp_path: Path) -> None:
    db = TelemetryDatabase(tmp_path / "telemetry.sqlite3")
    try:
        bot = ShadowDemoBot(
            config=BotConfig(),
            audit_logger=JsonlAuditLogger(tmp_path / "logs"),
            database=db,
            run_id="run_phase2_idempotency",
        )
        result = bot.run_once(
            snapshot=build_sample_snapshot(),
            features=build_sample_features(),
            account=_demo_account(),
        )
        order = db.fetch_all("orders")[0]
        inserted = db.insert_record(
            "orders",
            json.loads(order["payload_json"]),
            idempotency_key=order["idempotency_key"],
        )
        assert result.shadow_order_created is True
        assert inserted is False
        assert db.count_rows("orders") == 1
    finally:
        db.close()


def test_json_contracts_validate_required_fields() -> None:
    payload = {
        "idempotency_key": "shadow_order:sig:EURUSD:BUY",
        "signal_id": "sig",
        "symbol": "EURUSD",
        "side": "BUY",
        "score": 80.0,
        "reasons": ["accepted"],
        "entry_price": 1.1,
        "sl": 1.09,
        "tp": 1.12,
        "lot": 0.01,
        "risk_pct": 0.5,
        "timestamp": "2026-05-16T00:00:00+00:00",
        "mode": "shadow",
        "status": "created",
    }
    validate_contract("ShadowOrder", payload)
    broken = dict(payload)
    broken.pop("tp")
    with pytest.raises(ValueError):
        validate_contract("ShadowOrder", broken)
