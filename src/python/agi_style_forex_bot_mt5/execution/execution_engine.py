"""Fail-closed execution gate and MT5 order orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from agi_style_forex_bot_mt5.config import BotConfig
from agi_style_forex_bot_mt5.contracts import (
    Direction,
    EntryType,
    ExecutionRequest,
    ExecutionResult,
    RiskDecision,
    TradeSignal,
    utc_now,
)
from agi_style_forex_bot_mt5.execution.broker_quality import BrokerQualityMonitor
from agi_style_forex_bot_mt5.execution.mt5_connector import MT5Connector
from agi_style_forex_bot_mt5.execution.slippage_monitor import SlippageMonitor
from agi_style_forex_bot_mt5.execution.spread_filter import SpreadFilter


@dataclass
class ExecutionEngine:
    """Build and send MT5 requests only after all execution gates pass."""

    config: BotConfig
    connector: MT5Connector
    spread_filter: SpreadFilter | None = None
    broker_quality: BrokerQualityMonitor = field(default_factory=BrokerQualityMonitor)
    max_retries: int = 1
    _seen_signal_ids: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.spread_filter is None:
            self.spread_filter = SpreadFilter(self.config)

    def execute(
        self,
        *,
        signal: TradeSignal,
        risk_decision: RiskDecision,
        audit_confirmed: bool,
        magic_number: int,
        max_slippage_points: int = 10,
        comment_prefix: str = "agi",
    ) -> ExecutionResult:
        """Validate and send one signal, using finite recoverable retries."""

        initial_reject = self._preflight(signal, risk_decision, audit_confirmed, magic_number)
        if initial_reject is not None:
            return initial_reject
        self._seen_signal_ids.add(signal.signal_id)

        last_result: ExecutionResult | None = None
        attempts = max(0, self.max_retries) + 1
        for attempt_index in range(attempts):
            gate_result = self._validate_and_send_once(
                signal=signal,
                risk_decision=risk_decision,
                magic_number=magic_number,
                max_slippage_points=max_slippage_points,
                comment_prefix=comment_prefix,
            )
            last_result = gate_result
            if gate_result.filled:
                return gate_result
            if not gate_result.sent:
                return gate_result
            recoverable = self.connector.is_recoverable_retcode(gate_result.retcode)
            self.broker_quality.record_reject(recoverable=recoverable)
            if not recoverable or attempt_index == attempts - 1:
                return gate_result
        return last_result or self._reject(signal.signal_id, "INTERNAL_ERROR", "execution failed")

    def _preflight(
        self,
        signal: TradeSignal,
        risk_decision: RiskDecision,
        audit_confirmed: bool,
        magic_number: int,
    ) -> ExecutionResult | None:
        if not audit_confirmed:
            return self._reject(
                signal.signal_id,
                "AUDIT_NOT_CONFIRMED",
                "signal and risk decision were not persisted or enqueued",
            )
        if signal.signal_id in self._seen_signal_ids:
            return self._reject(signal.signal_id, "DUPLICATE_SIGNAL", "signal already processed")
        if not risk_decision.accepted:
            return self._reject(
                signal.signal_id,
                risk_decision.reject_code or "RISK_REJECTED",
                risk_decision.reject_reason or "risk decision rejected",
            )
        if risk_decision.signal_id != signal.signal_id:
            return self._reject(signal.signal_id, "INTERNAL_ERROR", "risk decision signal mismatch")
        if risk_decision.approved_lot <= 0:
            return self._reject(signal.signal_id, "INVALID_LOT", "approved lot must be positive")
        if magic_number <= 0:
            return self._reject(signal.signal_id, "EXECUTION_CONSTRAINT", "magic number required")
        signal_age = (utc_now() - signal.created_at_utc).total_seconds()
        if signal_age > self.config.max_signal_age_seconds:
            return self._reject(signal.signal_id, "STALE_SIGNAL", "signal is stale")
        return None

    def _validate_and_send_once(
        self,
        *,
        signal: TradeSignal,
        risk_decision: RiskDecision,
        magic_number: int,
        max_slippage_points: int,
        comment_prefix: str,
    ) -> ExecutionResult:
        account_check = self.connector.validate_account_for_trading()
        if not account_check.accepted:
            return self._reject(signal.signal_id, account_check.code, account_check.reason)

        snapshot_check, snapshot = self.connector.ensure_symbol_snapshot(signal.symbol)
        if not snapshot_check.accepted or snapshot is None:
            return self._reject(signal.signal_id, snapshot_check.code, snapshot_check.reason)

        try:
            signal.validate_against_snapshot(snapshot)
        except ValueError as exc:
            return self._reject(signal.signal_id, "EXECUTION_CONSTRAINT", str(exc))

        spread_decision = self.spread_filter.check(snapshot)  # type: ignore[union-attr]
        if not spread_decision.accepted:
            return self._reject(signal.signal_id, "HIGH_SPREAD", spread_decision.reason)

        execution_request = self._build_execution_request(
            signal=signal,
            risk_decision=risk_decision,
            magic_number=magic_number,
            max_slippage_points=max_slippage_points,
            comment_prefix=comment_prefix,
        )

        volume_check = self.connector.validate_volume(execution_request, snapshot)
        if not volume_check.accepted:
            return self._reject(signal.signal_id, volume_check.code, volume_check.reason)

        stops_check = self.connector.validate_stops(execution_request, snapshot)
        if not stops_check.accepted:
            return self._reject(signal.signal_id, stops_check.code, stops_check.reason)

        netting_check = self._validate_netting_policy(execution_request)
        if not netting_check.accepted:
            return self._reject(signal.signal_id, netting_check.code, netting_check.reason)

        filling_check, filling_mode, filling_mode_name = self.connector.select_filling_mode(
            execution_request.symbol
        )
        if not filling_check.accepted or filling_mode is None:
            return self._reject(signal.signal_id, "INVALID_FILLING_MODE", filling_check.reason)

        try:
            trade_request = self.connector.build_trade_request(
                execution_request,
                snapshot,
                filling_mode,
            )
        except ValueError as exc:
            return self._reject(signal.signal_id, "EXECUTION_CONSTRAINT", str(exc))

        order_check = self.connector.order_check(trade_request)
        if not order_check.accepted:
            return self._reject(signal.signal_id, order_check.code, order_check.reason)

        result = self.connector.order_send(
            execution_request=execution_request,
            trade_request=trade_request,
            filling_mode_name=filling_mode_name,
        )
        if result.filled and result.fill_price > 0:
            requested_price = trade_request["price"]
            slippage = SlippageMonitor(snapshot.point).measure(
                direction=signal.direction,
                requested_price=requested_price,
                fill_price=result.fill_price,
            )
            self.broker_quality.record_fill(slippage.slippage_points)
        return result

    def _build_execution_request(
        self,
        *,
        signal: TradeSignal,
        risk_decision: RiskDecision,
        magic_number: int,
        max_slippage_points: int,
        comment_prefix: str,
    ) -> ExecutionRequest:
        return ExecutionRequest(
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            direction=signal.direction,
            order_type=signal.entry_type,
            lot=risk_decision.approved_lot,
            sl_price=signal.sl_price,
            tp_price=signal.tp_price,
            max_slippage_points=max_slippage_points,
            magic_number=magic_number,
            comment=comment_prefix,
            entry_price=signal.entry_price,
        )

    def _validate_netting_policy(self, request: ExecutionRequest):
        account = self.connector.mt5.account_info()
        margin_mode = "" if account is None else getattr(account, "margin_mode", "")
        margin_text = str(margin_mode).upper()
        retail_netting = self.connector.const("ACCOUNT_MARGIN_MODE_RETAIL_NETTING", 0)
        exchange = self.connector.const("ACCOUNT_MARGIN_MODE_EXCHANGE", 2)
        is_netting = margin_mode in {retail_netting, exchange} or "NETTING" in margin_text
        if not is_netting:
            return _EngineCheck(True, "OK", "hedging or unknown margin mode accepted")

        positions_get = getattr(self.connector.mt5, "positions_get", None)
        if not callable(positions_get):
            return _EngineCheck(False, "EXECUTION_CONSTRAINT", "positions unavailable for netting check")
        positions = positions_get(symbol=request.symbol) or ()
        for position in positions:
            if int(getattr(position, "magic", request.magic_number)) != request.magic_number:
                continue
            position_type = int(getattr(position, "type", -1))
            buy_type = self.connector.const("POSITION_TYPE_BUY", 0)
            sell_type = self.connector.const("POSITION_TYPE_SELL", 1)
            opposite = (
                request.direction == Direction.BUY
                and position_type == sell_type
                or request.direction == Direction.SELL
                and position_type == buy_type
            )
            if opposite:
                return _EngineCheck(
                    False,
                    "EXECUTION_CONSTRAINT",
                    "opposite signal in netting account requires explicit close/reverse policy",
                )
        return _EngineCheck(True, "OK", "netting policy accepted")

    def _reject(self, signal_id: str, code: str, reason: str) -> ExecutionResult:
        return ExecutionResult(
            signal_id=signal_id,
            sent=False,
            filled=False,
            retcode=0,
            retcode_description=code,
            timestamp_utc=utc_now(),
            error_message=reason,
        )


@dataclass(frozen=True)
class _EngineCheck:
    accepted: bool
    code: str
    reason: str
