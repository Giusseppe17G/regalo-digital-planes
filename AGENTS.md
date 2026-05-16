# AGENTS.md

## Proyecto

Nombre: `AGI_STYLE_FOREX_BOT_MT5`

Objetivo: construir un bot Forex avanzado para MetaTrader 5 con arquitectura modular, controles estrictos de riesgo, auditoria completa y canales de revision multiagente. El proyecto puede inspirarse en patrones publicos de EAs Forex de alto rendimiento, pero no debe copiar codigo propietario, nombres comerciales protegidos, artefactos privados ni afirmar que este bot es un EA original de terceros.

## Reglas Globales Para Agentes

1. Trabajar siempre desde la especificacion en `PROJECT_SPEC.md`.
2. No implementar funcionalidades fuera del alcance del modulo asignado.
3. No cambiar contratos publicos sin actualizar `PROJECT_SPEC.md` y documentar compatibilidad.
4. No eliminar cambios de otros agentes.
5. Mantener los cambios pequenos, revisables y con pruebas o plan de verificacion.
6. Preferir componentes deterministas, observables y auditables sobre logica opaca.
7. Registrar toda decision de arquitectura relevante en `docs/decisions/`.
8. Todo modulo debe fallar de forma cerrada: ante error, incertidumbre o datos incompletos, no abrir operaciones.
9. No agregar dependencias externas sin justificar su uso, licencia y mantenimiento.
10. No incluir secretos, tokens, credenciales, IDs reales de cuentas ni datos personales en el repositorio.

## Politica De Seguridad Obligatoria

Estas reglas son invariantes del proyecto y ningun agente puede debilitarlas:

- `DEMO_ONLY=True` por defecto.
- No operar en cuenta real si `DEMO_ONLY=True`.
- Nunca abrir operacion sin SL.
- Nunca abrir operacion sin TP.
- Nunca abrir operacion si el spread esta alto.
- Nunca abrir operacion si el lotaje es invalido.
- Nunca abrir operacion si se supera el drawdown diario.
- Nunca abrir operacion si se supera el drawdown flotante.
- Nunca abrir operacion si la apertura dejaria mas de 10 trades abiertos.
- Nunca abrir operacion si el riesgo abierto supera 5%.
- Registrar toda senal aceptada o rechazada con motivo.
- Enviar eventos importantes por Telegram.

Reglas adicionales consolidadas por revision multiagente:

- La operacion en cuenta real esta fuera del alcance inicial.
- Aunque `DEMO_ONLY=False`, no se permite cuenta real sin `LIVE_TRADING_APPROVED=True`, cuenta en whitelist y decision de arquitectura aprobada.
- Ninguna orden puede construirse ni enviarse si no se pudo persistir o encolar localmente la senal y la decision de riesgo.
- Una estrategia no puede pasar a demo ejecutable sin cumplir el Strategy Promotion Gate de `PROJECT_SPEC.md`.
- Todo executor MT5 debe pasar por un unico adapter de ejecucion y conservar auditoria completa de request/result.
- Todo reporte de backtesting debe ser reproducible desde commit, configuracion, datos y perfil de broker.

## Orden De Trabajo

1. Leer `AGENTS.md` y `PROJECT_SPEC.md`.
2. Identificar el modulo asignado y sus contratos.
3. Revisar dependencias de entrada y salida.
4. Implementar solo despues de confirmar que el contrato esta claro.
5. Agregar pruebas unitarias o casos de verificacion.
6. Ejecutar validaciones locales disponibles.
7. Documentar huecos, riesgos y deuda tecnica.

## Roles Multiagente

### Quant Strategy Reviewer

Evalua calidad estadistica, sesgos, regimenes de mercado, indicadores, filtros, condiciones de entrada/salida y robustez de senales. Debe evitar sobreajuste y exigir evidencia en backtesting antes de activar estrategias.

### Risk & Safety Reviewer

Evalua limites de riesgo, lotaje, exposicion abierta, drawdown, spread, SL/TP, modo demo, fallos seguros y escenarios extremos. Tiene autoridad para bloquear cualquier flujo que pueda abrir operaciones inseguras.

### MT5 Execution Reviewer

Evalua compatibilidad con MQL5, adapter `MqlTradeRequest`/`OrderSend`, posible encapsulamiento de `CTrade`, validacion de simbolos, volumen minimo/paso/maximo, filling mode, magic number, slippage, errores de broker y sincronizacion con posiciones abiertas.

### Backtesting Reviewer

Evalua reproducibilidad de pruebas, calidad de datos, costos, spread, comisiones, walk-forward, Monte Carlo, metricas y separacion entre entrenamiento, validacion y prueba.

### Telegram/Logging/Database Reviewer

Evalua trazabilidad, formato de eventos, persistencia, manejo de errores, colas, idempotencia, redaccion de mensajes y seguridad de secretos.

## Contratos De Entrega

Cada agente debe entregar:

- Archivos tocados.
- Supuestos tomados.
- Riesgos detectados.
- Pruebas ejecutadas o no ejecutadas.
- Recomendaciones pendientes.

## Estilo De Codigo Esperado

- MQL5: modulos pequenos en `src/mt5/Include/`, EA principal en `src/mt5/Experts/`.
- Python: utilidades de investigacion, backtesting externo, reportes y tooling en `src/python/`.
- Configuracion: valores por defecto seguros en `config/`, sin secretos.
- Tests: pruebas automatizadas en `tests/` y casos manuales documentados en `docs/testing/`.
- Logs: eventos estructurados con timestamp, modulo, severidad, simbolo, decision y motivo.

## Definicion De Listo

Una tarea solo esta lista si:

- Respeta todas las reglas de seguridad.
- Mantiene compatibilidad con los contratos del proyecto.
- Tiene pruebas o verificacion documentada.
- No introduce secretos ni dependencias injustificadas.
- Es entendible para el siguiente agente.
- Declara si toca estrategia, riesgo, ejecucion, observabilidad o backtesting.
- No habilita rutas de operacion real.
- No debilita auditoria, idempotencia, logging local ni redaccion de secretos.
