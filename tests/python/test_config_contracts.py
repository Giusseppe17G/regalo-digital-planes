from datetime import timezone

import pytest

from agi_style_forex_bot_mt5.config import load_config
from agi_style_forex_bot_mt5.contracts import (
    Direction,
    EntryType,
    MarketSnapshot,
    TradeSignal,
    utc_now,
)


def test_default_config_is_demo_only_and_strict() -> None:
    cfg = load_config()
    assert cfg.demo_only is True
    assert cfg.live_trading_approved is False
    assert cfg.max_risk_per_trade_pct == 0.5
    assert cfg.require_sl is True
    assert cfg.require_tp is True


def test_market_snapshot_validation_rejects_invalid_prices() -> None:
    snapshot = MarketSnapshot(
        symbol="EURUSD",
        timeframe="M5",
        timestamp_utc=utc_now(),
        bid=1.2,
        ask=1.1,
        spread_points=10,
        digits=5,
        point=0.00001,
        tick_value=1.0,
        tick_size=0.00001,
        volume_min=0.01,
        volume_max=100,
        volume_step=0.01,
        stops_level_points=10,
        freeze_level_points=5,
    )
    with pytest.raises(ValueError):
        snapshot.validate()


def test_trade_signal_requires_directional_sl_tp() -> None:
    snapshot = MarketSnapshot(
        symbol="EURUSD",
        timeframe="M5",
        timestamp_utc=utc_now(),
        bid=1.10000,
        ask=1.10010,
        spread_points=10,
        digits=5,
        point=0.00001,
        tick_value=1.0,
        tick_size=0.00001,
        volume_min=0.01,
        volume_max=100,
        volume_step=0.01,
        stops_level_points=10,
        freeze_level_points=5,
    )
    signal = TradeSignal(
        signal_id="sig_test",
        created_at_utc=utc_now().astimezone(timezone.utc),
        symbol="EURUSD",
        timeframe="M5",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
        sl_price=1.10100,
        tp_price=1.10200,
    )
    with pytest.raises(ValueError):
        signal.validate_against_snapshot(snapshot)
