import json

from agi_style_forex_bot_mt5.bot import ShadowDemoBot
from agi_style_forex_bot_mt5.cli import build_sample_features, build_sample_snapshot
from agi_style_forex_bot_mt5.config import BotConfig
from agi_style_forex_bot_mt5.contracts import AccountState, SignalAction
from agi_style_forex_bot_mt5.telemetry import JsonlAuditLogger


def test_shadow_bot_audits_and_never_attempts_execution(tmp_path) -> None:
    bot = ShadowDemoBot(
        config=BotConfig(),
        audit_logger=JsonlAuditLogger(tmp_path),
        run_id="run_test",
    )
    result = bot.run_once(
        snapshot=build_sample_snapshot(),
        features=build_sample_features(),
        account=AccountState(
            login=123,
            trade_mode="DEMO",
            balance=10_000,
            equity=10_000,
            margin_free=9_000,
            is_demo=True,
            trade_allowed=True,
        ),
    )
    assert result.strategy_action == SignalAction.BUY
    assert result.execution_attempted is False
    records = [
        json.loads(line)
        for path in tmp_path.glob("events-*.jsonl")
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert any(record["event_type"] == "SIGNAL_GENERATED" for record in records)
    assert any(record["event_type"] in {"SIGNAL_ACCEPTED", "SIGNAL_REJECTED"} for record in records)
    assert any(record["event_type"] == "EXECUTION_SKIPPED" for record in records)


def test_shadow_bot_blocks_real_account_before_execution(tmp_path) -> None:
    bot = ShadowDemoBot(
        config=BotConfig(),
        audit_logger=JsonlAuditLogger(tmp_path),
        run_id="run_real_block",
    )
    result = bot.run_once(
        snapshot=build_sample_snapshot(),
        features=build_sample_features(),
        account=AccountState(
            login=123,
            trade_mode="REAL",
            balance=10_000,
            equity=10_000,
            margin_free=9_000,
            is_demo=False,
            trade_allowed=True,
        ),
    )
    assert result.execution_attempted is False
    if result.strategy_action != SignalAction.NONE:
        assert result.risk_accepted is False
        assert result.risk_reject_code == "DEMO_ONLY_REAL_ACCOUNT"
