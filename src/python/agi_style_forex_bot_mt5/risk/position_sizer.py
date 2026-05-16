"""Fail-closed position sizing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, InvalidOperation
from math import isfinite

from agi_style_forex_bot_mt5.contracts import Direction, MarketSnapshot


@dataclass(frozen=True)
class SizingResult:
    """Result of a lot-size calculation."""

    lot: float
    risk_amount: float
    risk_pct: float
    price_distance: float
    reason: str = ""

    @property
    def valid(self) -> bool:
        return self.lot > 0 and self.risk_amount > 0 and not self.reason


def price_risk_per_lot(entry_price: float, sl_price: float, snapshot: MarketSnapshot) -> float:
    """Return account-currency risk per 1.0 lot from entry to SL."""

    if not all(isfinite(value) for value in (entry_price, sl_price)):
        raise ValueError("entry and SL must be finite")
    if snapshot.tick_value <= 0 or snapshot.tick_size <= 0:
        raise ValueError("tick value and size must be positive")
    try:
        distance = abs(Decimal(str(entry_price)) - Decimal(str(sl_price)))
        tick_size = Decimal(str(snapshot.tick_size))
        tick_value = Decimal(str(snapshot.tick_value))
    except InvalidOperation as exc:
        raise ValueError("price or tick metadata is invalid") from exc
    if distance <= 0:
        raise ValueError("SL distance must be positive")
    return float((distance / tick_size) * tick_value)


def risk_amount_for_lot(
    *,
    lot: float,
    entry_price: float,
    sl_price: float,
    snapshot: MarketSnapshot,
) -> float:
    """Return risk amount for a concrete lot size."""

    if lot <= 0 or not isfinite(lot):
        raise ValueError("lot must be positive and finite")
    return price_risk_per_lot(entry_price, sl_price, snapshot) * lot


def normalize_lot_down(lot: float, snapshot: MarketSnapshot) -> float:
    """Normalize lot down to broker min/max/step constraints."""

    if lot <= 0 or not isfinite(lot):
        return 0.0
    if snapshot.volume_min <= 0 or snapshot.volume_max <= 0 or snapshot.volume_step <= 0:
        return 0.0
    try:
        raw = Decimal(str(lot))
        step = Decimal(str(snapshot.volume_step))
        minimum = Decimal(str(snapshot.volume_min))
        maximum = Decimal(str(snapshot.volume_max))
    except InvalidOperation:
        return 0.0
    if raw < minimum:
        return 0.0
    bounded = min(raw, maximum)
    steps = ((bounded - minimum) / step).to_integral_value(rounding=ROUND_FLOOR)
    normalized = minimum + (steps * step)
    if normalized < minimum or normalized > maximum:
        return 0.0
    return float(normalized)


def entry_reference_price(direction: Direction, snapshot: MarketSnapshot, entry_price: float | None) -> float:
    """Return the price used for risk calculations."""

    if entry_price is not None:
        return entry_price
    return snapshot.ask if direction == Direction.BUY else snapshot.bid


class PositionSizer:
    """Calculate conservative lot sizes without ever rounding risk upward."""

    def size_for_risk(
        self,
        *,
        equity: float,
        risk_pct: float,
        direction: Direction,
        sl_price: float,
        snapshot: MarketSnapshot,
        entry_price: float | None = None,
        requested_lot: float | None = None,
    ) -> SizingResult:
        """Return an approved lot and its risk, or an invalid result with reason."""

        try:
            snapshot.validate()
            if equity <= 0 or risk_pct <= 0:
                return SizingResult(0.0, 0.0, 0.0, 0.0, "equity and risk_pct must be positive")
            reference = entry_reference_price(direction, snapshot, entry_price)
            risk_per_lot = price_risk_per_lot(reference, sl_price, snapshot)
            max_risk_amount = equity * (risk_pct / 100.0)
            risk_lot = max_risk_amount / risk_per_lot
            normalized_risk_lot = normalize_lot_down(risk_lot, snapshot)
            if requested_lot is not None:
                requested_normalized = normalize_lot_down(requested_lot, snapshot)
                if requested_normalized <= 0:
                    return SizingResult(0.0, 0.0, 0.0, 0.0, "requested lot is invalid")
                lot = min(requested_normalized, normalized_risk_lot)
            else:
                lot = normalized_risk_lot
            if lot <= 0:
                return SizingResult(0.0, 0.0, 0.0, 0.0, "no valid lot fits risk and broker limits")
            risk_amount = risk_amount_for_lot(
                lot=lot,
                entry_price=reference,
                sl_price=sl_price,
                snapshot=snapshot,
            )
            if risk_amount > max_risk_amount + 1e-9:
                return SizingResult(0.0, 0.0, 0.0, 0.0, "normalized lot exceeds risk limit")
            return SizingResult(
                lot=lot,
                risk_amount=risk_amount,
                risk_pct=(risk_amount / equity) * 100.0,
                price_distance=abs(reference - sl_price),
            )
        except (TypeError, ValueError, ZeroDivisionError, InvalidOperation) as exc:
            return SizingResult(0.0, 0.0, 0.0, 0.0, str(exc))
