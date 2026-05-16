# Interface Contracts

Los contratos canonicos estan definidos en `PROJECT_SPEC.md`, seccion 7.

Este directorio queda reservado para ampliar contratos por modulo sin duplicar semantica. Si un agente agrega detalles aqui, debe mantener `PROJECT_SPEC.md` como fuente principal o enlazar explicitamente la decision de cambio.

Contratos iniciales:

- `MarketSnapshot`
- `TradeSignal`
- `RiskDecision`
- `ExecutionRequest`
- `ExecutionResult`
- `Event`
- `BacktestRunConfig`
- `BacktestResult`

Regla: ningun modulo puede construir `ExecutionRequest` sin `RiskDecision.accepted=True` y auditoria local confirmada.
