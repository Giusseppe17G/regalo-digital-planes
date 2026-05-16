"""Shadow execution engine that never calls MT5 order_send."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from agi_style_forex_bot_mt5.contracts import MarketSnapshot, RiskDecision, TradeSignal


@dataclass(frozen=True)
class ShadowOrder:
    """Simulated order intent persisted by the shadow execution path."""

    order_id: str
    idempotency_key: str
    signal_id: str
    symbol: str
    side: str
    score: float
    reasons: tuple[str, ...]
    entry_price: float
    sl: float
    tp: float
    lot: float
    risk_pct: float
    timestamp: str
    mode: str = "shadow"
    status: str = "created"

    def as_record(self) -> dict[str, Any]:
        """Return a JSON-serializable database/logging record."""

        return asdict(self)


class ShadowExecutionEngine:
    """Create idempotent shadow orders without touching MetaTrader order_send."""

    def create_order(
        self,
        *,
        signal: TradeSignal,
        risk_decision: RiskDecision,
        snapshot: MarketSnapshot,
        strategy_score: float,
        reasons: tuple[str, ...],
    ) -> ShadowOrder:
        """Build a validated `ShadowOrder` or raise `ValueError` fail-closed."""

        if not risk_decision.accepted:
            raise ValueError("risk decision must be accepted before shadow order")
        if risk_decision.signal_id != signal.signal_id:
            raise ValueError("risk decision signal_id mismatch")
        if risk_decision.approved_lot <= 0:
            raise ValueError("approved lot must be positive")
        signal.validate_against_snapshot(snapshot)
        entry_price = snapshot.ask if signal.direction.value == "BUY" else snapshot.bid
        risk_pct = signal.risk_pct if signal.risk_pct is not None else 0.0
        if risk_pct <= 0:
            raise ValueError("risk_pct must be positive")
        key = f"shadow_order:{signal.signal_id}:{signal.symbol}:{signal.direction.value}"
        return ShadowOrder(
            order_id=f"sho_{uuid4().hex}",
            idempotency_key=key,
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            side=signal.direction.value,
            score=float(strategy_score),
            reasons=tuple(reasons),
            entry_price=round(entry_price, snapshot.digits),
            sl=signal.sl_price,
            tp=signal.tp_price,
            lot=risk_decision.approved_lot,
            risk_pct=float(risk_pct),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
