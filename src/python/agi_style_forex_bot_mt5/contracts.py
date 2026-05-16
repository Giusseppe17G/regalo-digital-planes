"""Canonical Python contracts for AGI_STYLE_FOREX_BOT_MT5.

These dataclasses mirror the conceptual contracts in PROJECT_SPEC.md. Modules
should import these types instead of creating incompatible local structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class Direction(str, Enum):
    """Trade direction."""

    BUY = "BUY"
    SELL = "SELL"


class SignalAction(str, Enum):
    """High-level strategy output."""

    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"


class EntryType(str, Enum):
    """Order entry type."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class Regime(str, Enum):
    """Market regime labels used by strategies and filters."""

    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    SPREAD_DANGER = "SPREAD_DANGER"
    LIQUIDITY_THIN = "LIQUIDITY_THIN"


class Environment(str, Enum):
    """Runtime environment."""

    BACKTEST = "BACKTEST"
    DEMO = "DEMO"
    LIVE = "LIVE"


class Severity(str, Enum):
    """Structured event severity."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MarketSnapshot:
    """Normalized market snapshot used by strategy, risk and execution."""

    symbol: str
    timeframe: str
    timestamp_utc: datetime
    bid: float
    ask: float
    spread_points: float
    digits: int
    point: float
    tick_value: float
    tick_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    stops_level_points: int
    freeze_level_points: int

    def validate(self) -> None:
        """Raise ValueError when the snapshot is unsafe or inconsistent."""

        if not self.symbol:
            raise ValueError("symbol is required")
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError("bid and ask must be positive")
        if self.ask < self.bid:
            raise ValueError("ask must be greater than or equal to bid")
        if self.spread_points < 0:
            raise ValueError("spread_points must be non-negative")
        if self.point <= 0 or self.tick_value <= 0 or self.tick_size <= 0:
            raise ValueError("point, tick_value and tick_size must be positive")
        if self.volume_min <= 0 or self.volume_max <= 0 or self.volume_step <= 0:
            raise ValueError("volume constraints must be positive")
        if self.volume_min > self.volume_max:
            raise ValueError("volume_min cannot exceed volume_max")
        if self.stops_level_points < 0 or self.freeze_level_points < 0:
            raise ValueError("stops and freeze levels cannot be negative")


@dataclass(frozen=True)
class StrategySignal:
    """Strategy-level output before conversion to a trade signal."""

    action: SignalAction
    score: float
    reasons: tuple[str, ...]
    strategy_name: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError("score must be between 0 and 100")


@dataclass(frozen=True)
class TradeSignal:
    """Candidate trade signal that must still pass risk and execution gates."""

    signal_id: str
    created_at_utc: datetime
    symbol: str
    timeframe: str
    direction: Direction
    entry_type: EntryType
    sl_price: float
    tp_price: float
    entry_price: float | None = None
    requested_lot: float | None = None
    risk_pct: float | None = None
    confidence: float = 0.0
    strategy_name: str = ""
    strategy_version: str = "0.1.0"
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @staticmethod
    def new_id(prefix: str = "sig") -> str:
        """Return a unique signal id."""

        return f"{prefix}_{uuid4().hex}"

    def validate_against_snapshot(self, snapshot: MarketSnapshot) -> None:
        """Validate SL/TP direction and confidence against a snapshot."""

        snapshot.validate()
        if self.symbol != snapshot.symbol:
            raise ValueError("signal symbol does not match snapshot")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.sl_price <= 0 or self.tp_price <= 0:
            raise ValueError("SL and TP must be positive")
        reference = self.entry_price
        if self.entry_type == EntryType.MARKET:
            reference = snapshot.ask if self.direction == Direction.BUY else snapshot.bid
        if reference is None or reference <= 0:
            raise ValueError("entry reference price is required")
        if self.direction == Direction.BUY and not (self.sl_price < reference < self.tp_price):
            raise ValueError("BUY requires sl < entry reference < tp")
        if self.direction == Direction.SELL and not (self.tp_price < reference < self.sl_price):
            raise ValueError("SELL requires tp < entry reference < sl")


@dataclass(frozen=True)
class AccountState:
    """Account state needed by risk and execution gates."""

    login: int | None
    trade_mode: str | None
    balance: float
    equity: float
    margin_free: float
    currency: str = "USD"
    is_demo: bool = False
    trade_allowed: bool = False


@dataclass(frozen=True)
class PositionState:
    """Open position or pending order risk state."""

    ticket: int
    symbol: str
    direction: Direction
    volume: float
    entry_price: float
    sl_price: float
    tp_price: float
    magic_number: int
    floating_profit: float = 0.0


@dataclass(frozen=True)
class RiskDecision:
    """Risk gate output."""

    signal_id: str
    accepted: bool
    reject_code: str = ""
    reject_reason: str = ""
    approved_lot: float = 0.0
    risk_amount_account_currency: float = 0.0
    open_risk_pct_after_trade: float = 0.0
    daily_drawdown_pct: float = 0.0
    floating_drawdown_pct: float = 0.0
    checks: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.accepted:
            if self.approved_lot != 0 or self.risk_amount_account_currency != 0:
                raise ValueError("rejected decisions must not approve lot or risk amount")
            if not self.reject_code:
                raise ValueError("rejected decisions require reject_code")


@dataclass(frozen=True)
class ExecutionRequest:
    """Safe MT5 execution request built only after accepted risk."""

    signal_id: str
    symbol: str
    direction: Direction
    order_type: EntryType
    lot: float
    sl_price: float
    tp_price: float
    max_slippage_points: int
    magic_number: int
    comment: str
    entry_price: float | None = None

    def validate(self) -> None:
        """Validate mandatory execution fields."""

        if self.lot <= 0:
            raise ValueError("lot must be positive")
        if self.sl_price <= 0 or self.tp_price <= 0:
            raise ValueError("SL and TP are mandatory")
        if self.magic_number <= 0:
            raise ValueError("magic_number must be positive")


@dataclass(frozen=True)
class ExecutionResult:
    """Result returned by the MT5 execution adapter."""

    signal_id: str
    sent: bool
    filled: bool
    retcode: int
    retcode_description: str
    timestamp_utc: datetime
    ticket: int | None = None
    fill_price: float = 0.0
    requested_lot: float = 0.0
    filled_lot: float = 0.0
    error_message: str = ""
    order_ticket: int | None = None
    deal_ticket: int | None = None
    position_ticket: int | None = None
    request_id: int | None = None
    last_error: int = 0
    server_comment: str = ""
    execution_latency_ms: int = 0
    account_margin_mode: str = ""
    filling_mode_used: str = ""


@dataclass(frozen=True)
class Event:
    """Structured audit event."""

    event_id: str
    schema_version: str
    correlation_id: str
    idempotency_key: str
    run_id: str
    environment: Environment
    timestamp_utc: datetime
    severity: Severity
    module: str
    event_type: str
    message: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    signal_id: str | None = None
    symbol: str | None = None
    causation_id: str | None = None
    sequence_number: int | None = None

    @staticmethod
    def create(
        *,
        run_id: str,
        environment: Environment,
        severity: Severity,
        module: str,
        event_type: str,
        message: str,
        correlation_id: str,
        payload: Mapping[str, Any] | None = None,
        signal_id: str | None = None,
        symbol: str | None = None,
        causation_id: str | None = None,
    ) -> "Event":
        """Construct an event with stable idempotency data."""

        event_id = f"evt_{uuid4().hex}"
        key = f"{run_id}:{correlation_id}:{event_type}:{causation_id or ''}:{message}"
        return Event(
            event_id=event_id,
            schema_version="1.0",
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=key,
            run_id=run_id,
            environment=environment,
            timestamp_utc=utc_now(),
            severity=severity,
            module=module,
            event_type=event_type,
            message=message,
            payload=payload or {},
            signal_id=signal_id,
            symbol=symbol,
        )
