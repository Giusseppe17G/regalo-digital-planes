from datetime import timedelta

from agi_style_forex_bot_mt5.contracts import (
    AccountState,
    Direction,
    EntryType,
    MarketSnapshot,
    PositionState,
    TradeSignal,
    utc_now,
)
from agi_style_forex_bot_mt5.risk import PositionSizer, RiskEngine, RiskRuntimeState


def _snapshot(spread_points: float = 10) -> MarketSnapshot:
    now = utc_now()
    return MarketSnapshot(
        symbol="EURUSD",
        timeframe="M5",
        timestamp_utc=now,
        bid=1.10000,
        ask=1.10010,
        spread_points=spread_points,
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


def _signal() -> TradeSignal:
    return TradeSignal(
        signal_id="sig_risk_test",
        created_at_utc=utc_now(),
        symbol="EURUSD",
        timeframe="M5",
        direction=Direction.BUY,
        entry_type=EntryType.MARKET,
        sl_price=1.09910,
        tp_price=1.10200,
        risk_pct=0.5,
        confidence=0.7,
        strategy_name="test",
    )


def _account(equity: float = 10_000.0) -> AccountState:
    return AccountState(
        login=123,
        trade_mode="DEMO",
        balance=10_000.0,
        equity=equity,
        margin_free=9_000.0,
        is_demo=True,
        trade_allowed=True,
    )


def _state(**overrides: object) -> RiskRuntimeState:
    values = {
        "daily_equity_reference": 10_000.0,
        "audit_confirmed": True,
    }
    values.update(overrides)
    return RiskRuntimeState(**values)


def test_position_sizer_normalizes_lot_down_to_risk_and_step() -> None:
    snapshot = _snapshot()
    result = PositionSizer().size_for_risk(
        equity=10_000.0,
        risk_pct=0.5,
        direction=Direction.BUY,
        sl_price=1.09910,
        snapshot=snapshot,
    )
    assert result.valid is True
    assert result.lot == 0.5
    assert result.risk_amount == 50.0
    assert result.risk_pct == 0.5


def test_risk_engine_accepts_safe_demo_signal() -> None:
    snapshot = _snapshot()
    decision = RiskEngine().evaluate(
        signal=_signal(),
        snapshot=snapshot,
        account=_account(),
        state=_state(),
    )
    assert decision.accepted is True
    assert decision.approved_lot == 0.5
    assert decision.open_risk_pct_after_trade == 0.5


def test_risk_engine_blocks_daily_drawdown_limit() -> None:
    snapshot = _snapshot()
    decision = RiskEngine().evaluate(
        signal=_signal(),
        snapshot=snapshot,
        account=_account(equity=9_700.0),
        state=_state(),
    )
    assert decision.accepted is False
    assert decision.reject_code == "DAILY_DRAWDOWN_LIMIT"
    assert decision.approved_lot == 0.0


def test_risk_engine_blocks_open_risk_above_limit() -> None:
    snapshot = _snapshot()
    positions = tuple(
        PositionState(
            ticket=i,
            symbol="EURUSD",
            direction=Direction.BUY,
            volume=1.0,
            entry_price=1.10010,
            sl_price=1.09910,
            tp_price=1.10200,
            magic_number=7,
        )
        for i in range(1, 6)
    )
    decision = RiskEngine().evaluate(
        signal=_signal(),
        snapshot=snapshot,
        account=_account(),
        state=_state(open_positions=positions),
    )
    assert decision.accepted is False
    assert decision.reject_code == "MAX_OPEN_TRADES_PER_SYMBOL"


def test_risk_engine_blocks_global_open_risk_above_limit() -> None:
    snapshot = _snapshot()
    positions = (
        PositionState(1, "GBPUSD", Direction.BUY, 2.5, 1.25000, 1.24900, 1.25200, 7),
        PositionState(2, "USDJPY", Direction.SELL, 2.0, 150.000, 150.100, 149.500, 7),
    )
    decision = RiskEngine().evaluate(
        signal=_signal(),
        snapshot=snapshot,
        account=_account(),
        state=_state(
            open_positions=positions,
            open_position_risk_amounts={1: 250.0, 2: 250.0},
        ),
    )
    assert decision.accepted is False
    assert decision.reject_code == "MAX_OPEN_RISK"


def test_risk_engine_blocks_high_spread_and_stale_signal() -> None:
    stale = TradeSignal(
        **{
            **_signal().__dict__,
            "created_at_utc": utc_now() - timedelta(seconds=31),
        }
    )
    stale_decision = RiskEngine().evaluate(
        signal=stale,
        snapshot=_snapshot(),
        account=_account(),
        state=_state(),
    )
    assert stale_decision.accepted is False
    assert stale_decision.reject_code == "STALE_SIGNAL"

    spread_decision = RiskEngine().evaluate(
        signal=_signal(),
        snapshot=_snapshot(spread_points=30),
        account=_account(),
        state=_state(),
    )
    assert spread_decision.accepted is False
    assert spread_decision.reject_code == "HIGH_SPREAD"
