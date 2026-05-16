# Minimum Test Matrix

Este archivo enumera casos minimos que futuros agentes deben cubrir antes de considerar modulos operables. No implementa pruebas.

## Risk Gate

- Bloquea cuenta real con `DEMO_ONLY=True`.
- Bloquea cuenta real sin `LIVE_TRADING_APPROVED=True`.
- Bloquea SL ausente.
- Bloquea TP ausente.
- Bloquea spread alto.
- Bloquea lotaje fuera de min/max/step.
- Bloquea riesgo por trade mayor a `MAX_RISK_PER_TRADE_PCT`.
- Bloquea riesgo abierto mayor a `MAX_OPEN_RISK_PCT`.
- Bloquea drawdown diario sin referencia persistida.
- Bloquea mas de 10 trades despues de sumar candidata.
- Bloquea si no puede auditar senal y decision.

## MT5 Execution

- Mercado cerrado.
- Simbolo no seleccionado.
- Trading terminal/cuenta/simbolo deshabilitado.
- Stops invalidos.
- Freeze level impide modificacion.
- Volumen invalido por step.
- Filling mode incompatible.
- Cuenta netting con senal opuesta.
- Requote o price changed exige nuevo snapshot.
- Terminal desconectado o tick obsoleto.

## Backtesting

- Configuracion reproduce commit, datos, motor, costos y broker profile.
- Dataset con huecos queda marcado no apto.
- Costos se serializan como JSON estructurado.
- Train/validation/test no tienen leakage.
- Walk-forward reporta folds individuales.
- Monte Carlo reporta percentiles 5/50/95.
- Estrategia se compara contra baselines.

## Observability

- JSONL valido por linea.
- `idempotency_key` deduplica reintentos.
- SQLite falla y se conserva JSONL/outbox local.
- Telegram 429 programa retry.
- Token y chat ID aparecen redactados.
- La operacion se bloquea si no puede auditarse la decision.
