# JSON Contracts

These contracts define the JSON boundary shape for Python, future MQL5 adapters, telemetry, Telegram, and reports. If a required field is missing or invalid, consumers must fail closed: do not create an order, do not send MT5 requests, and emit/audit a rejection when an audit sink is available.

## SignalEvent

Required fields:

- `idempotency_key`: string.
- `signal_id`: string.
- `symbol`: string.
- `action`: string, one of `BUY`, `SELL`, `NONE`.
- `score`: number from 0 to 100.
- `reasons`: array of strings.
- `timestamp_utc`: ISO-8601 UTC string.

Example:

```json
{
  "idempotency_key": "signal:sig_123",
  "signal_id": "sig_123",
  "symbol": "EURUSD",
  "action": "BUY",
  "score": 82.5,
  "reasons": ["trend_pullback: fast EMA above slow EMA"],
  "timestamp_utc": "2026-05-16T00:00:00+00:00"
}
```

Validation: `action=NONE` must not create an order. Missing `signal_id`, `symbol`, `action`, `score`, or `idempotency_key` fails closed.

## RiskDecision

Required fields:

- `idempotency_key`: string.
- `signal_id`: string.
- `accepted`: boolean.
- `reject_code`: string, empty only when accepted.
- `approved_lot`: number.
- `checks`: object.

Example:

```json
{
  "idempotency_key": "risk:sig_123",
  "signal_id": "sig_123",
  "accepted": true,
  "reject_code": "",
  "approved_lot": 0.05,
  "checks": {"demo_only": {"status": "passed"}}
}
```

Validation: if `accepted=false`, no order may be created. If `accepted=true`, `approved_lot` must be positive.

## OrderIntent

Required fields:

- `idempotency_key`: string.
- `signal_id`: string.
- `symbol`: string.
- `side`: string, `BUY` or `SELL`.
- `entry_price`: positive number.
- `sl`: positive number.
- `tp`: positive number.
- `lot`: positive number.

Example:

```json
{
  "idempotency_key": "intent:sig_123",
  "signal_id": "sig_123",
  "symbol": "EURUSD",
  "side": "BUY",
  "entry_price": 1.1001,
  "sl": 1.0991,
  "tp": 1.1019,
  "lot": 0.05
}
```

Validation: missing or non-positive `sl`, `tp`, or `lot` fails closed.

## ShadowOrder

Required fields:

- `idempotency_key`: string.
- `signal_id`: string.
- `symbol`: string.
- `side`: string.
- `score`: number.
- `reasons`: array of strings.
- `entry_price`: positive number.
- `sl`: positive number.
- `tp`: positive number.
- `lot`: positive number.
- `risk_pct`: positive number.
- `timestamp`: ISO-8601 UTC string.
- `mode`: string, must be `shadow`.
- `status`: string, must be `created`.

Example:

```json
{
  "idempotency_key": "shadow_order:sig_123:EURUSD:BUY",
  "signal_id": "sig_123",
  "symbol": "EURUSD",
  "side": "BUY",
  "score": 82.5,
  "reasons": ["ensemble accepted"],
  "entry_price": 1.1001,
  "sl": 1.0991,
  "tp": 1.1019,
  "lot": 0.05,
  "risk_pct": 0.5,
  "timestamp": "2026-05-16T00:00:00+00:00",
  "mode": "shadow",
  "status": "created"
}
```

Validation: shadow orders are persisted only after audit and accepted risk. They never call `order_send`.

## ExecutionResult

Required fields:

- `idempotency_key`: string.
- `signal_id`: string.
- `sent`: boolean.
- `filled`: boolean.
- `retcode`: integer.
- `retcode_description`: string.
- `timestamp_utc`: ISO-8601 UTC string.

Example:

```json
{
  "idempotency_key": "execution:sig_123",
  "signal_id": "sig_123",
  "sent": false,
  "filled": false,
  "retcode": 0,
  "retcode_description": "SHADOW_MODE",
  "timestamp_utc": "2026-05-16T00:00:00+00:00"
}
```

Validation: any result with `sent=true` must have passed SL, TP, lot, spread, risk, audit, demo/live safety, order_check, and execution gates.

## TelegramEvent

Required fields:

- `idempotency_key`: string.
- `event_id`: string.
- `event_type`: string.
- `severity`: string.
- `message`: string.
- `timestamp_utc`: ISO-8601 UTC string.

Example:

```json
{
  "idempotency_key": "telegram:evt_123",
  "event_id": "evt_123",
  "event_type": "SHADOW_ORDER_CREATED",
  "severity": "INFO",
  "message": "shadow order created",
  "timestamp_utc": "2026-05-16T00:00:00+00:00"
}
```

Validation: Telegram failure must be recorded and must not break the bot loop.

## AccountSnapshot

Required fields:

- `idempotency_key`: string.
- `trade_mode`: string.
- `balance`: number.
- `equity`: number.
- `is_demo`: boolean.
- `timestamp_utc`: ISO-8601 UTC string.

Example:

```json
{
  "idempotency_key": "account:run_123",
  "trade_mode": "DEMO",
  "balance": 10000.0,
  "equity": 10000.0,
  "is_demo": true,
  "timestamp_utc": "2026-05-16T00:00:00+00:00"
}
```

Validation: unknown account type or non-demo account under `DEMO_ONLY=True` fails closed.

## BrokerQualityEvent

Required fields:

- `idempotency_key`: string.
- `symbol`: string.
- `spread_points`: number.
- `slippage_points`: number.
- `timestamp_utc`: ISO-8601 UTC string.

Example:

```json
{
  "idempotency_key": "broker_quality:EURUSD:run_123",
  "symbol": "EURUSD",
  "spread_points": 10.0,
  "slippage_points": 0.2,
  "timestamp_utc": "2026-05-16T00:00:00+00:00"
}
```

Validation: missing symbol, spread, slippage, or timestamp fails closed for broker-quality decisions.
