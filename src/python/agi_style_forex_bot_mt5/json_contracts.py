"""Runtime validators for documented JSON boundary contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    """Required JSON field and accepted Python runtime types."""

    name: str
    types: tuple[type, ...]


CONTRACTS: dict[str, tuple[FieldSpec, ...]] = {
    "SignalEvent": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("signal_id", (str,)),
        FieldSpec("symbol", (str,)),
        FieldSpec("action", (str,)),
        FieldSpec("score", (int, float)),
        FieldSpec("reasons", (list, tuple)),
        FieldSpec("timestamp_utc", (str,)),
    ),
    "RiskDecision": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("signal_id", (str,)),
        FieldSpec("accepted", (bool,)),
        FieldSpec("reject_code", (str,)),
        FieldSpec("approved_lot", (int, float)),
        FieldSpec("checks", (dict,)),
    ),
    "OrderIntent": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("signal_id", (str,)),
        FieldSpec("symbol", (str,)),
        FieldSpec("side", (str,)),
        FieldSpec("entry_price", (int, float)),
        FieldSpec("sl", (int, float)),
        FieldSpec("tp", (int, float)),
        FieldSpec("lot", (int, float)),
    ),
    "ShadowOrder": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("signal_id", (str,)),
        FieldSpec("symbol", (str,)),
        FieldSpec("side", (str,)),
        FieldSpec("score", (int, float)),
        FieldSpec("reasons", (list, tuple)),
        FieldSpec("entry_price", (int, float)),
        FieldSpec("sl", (int, float)),
        FieldSpec("tp", (int, float)),
        FieldSpec("lot", (int, float)),
        FieldSpec("risk_pct", (int, float)),
        FieldSpec("timestamp", (str,)),
        FieldSpec("mode", (str,)),
        FieldSpec("status", (str,)),
    ),
    "ExecutionResult": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("signal_id", (str,)),
        FieldSpec("sent", (bool,)),
        FieldSpec("filled", (bool,)),
        FieldSpec("retcode", (int,)),
        FieldSpec("retcode_description", (str,)),
        FieldSpec("timestamp_utc", (str,)),
    ),
    "TelegramEvent": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("event_id", (str,)),
        FieldSpec("event_type", (str,)),
        FieldSpec("severity", (str,)),
        FieldSpec("message", (str,)),
        FieldSpec("timestamp_utc", (str,)),
    ),
    "AccountSnapshot": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("trade_mode", (str,)),
        FieldSpec("balance", (int, float)),
        FieldSpec("equity", (int, float)),
        FieldSpec("is_demo", (bool,)),
        FieldSpec("timestamp_utc", (str,)),
    ),
    "BrokerQualityEvent": (
        FieldSpec("idempotency_key", (str,)),
        FieldSpec("symbol", (str,)),
        FieldSpec("spread_points", (int, float)),
        FieldSpec("slippage_points", (int, float)),
        FieldSpec("timestamp_utc", (str,)),
    ),
}


CRITICAL_POSITIVE_FIELDS = {"entry_price", "sl", "tp", "lot", "risk_pct"}


def validate_contract(contract_name: str, payload: Mapping[str, Any]) -> None:
    """Validate a payload against a documented JSON contract.

    Raises `ValueError` fail-closed when a contract is unknown, a critical field
    is missing, a type is wrong, or a required positive numeric field is unsafe.
    """

    if contract_name not in CONTRACTS:
        raise ValueError(f"unknown JSON contract: {contract_name}")
    for field in CONTRACTS[contract_name]:
        if field.name not in payload:
            raise ValueError(f"{contract_name} missing required field: {field.name}")
        value = payload[field.name]
        if not isinstance(value, field.types):
            expected = ", ".join(t.__name__ for t in field.types)
            raise ValueError(f"{contract_name}.{field.name} must be {expected}")
        if field.name in CRITICAL_POSITIVE_FIELDS and float(value) <= 0:
            raise ValueError(f"{contract_name}.{field.name} must be positive")
    if contract_name == "ShadowOrder":
        if payload["mode"] != "shadow":
            raise ValueError("ShadowOrder.mode must be shadow")
        if payload["status"] != "created":
            raise ValueError("ShadowOrder.status must be created")
