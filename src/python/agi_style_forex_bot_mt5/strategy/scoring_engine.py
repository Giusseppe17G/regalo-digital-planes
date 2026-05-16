"""Deterministic scoring helpers for strategy modules.

The strategy layer only emits candidate intent. It does not size positions,
build execution requests or bypass risk/execution gates.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..contracts import MarketSnapshot, Regime, SignalAction, StrategySignal


FeatureMap = Mapping[str, Any]


def clamp_score(value: float) -> float:
    """Clamp a score to the StrategySignal 0-100 contract."""

    return max(0.0, min(100.0, float(value)))


def feature_float(features: FeatureMap, key: str, default: float = 0.0) -> float:
    """Read a numeric feature, failing closed to a conservative default."""

    value = features.get(key, default)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def feature_bool(features: FeatureMap, key: str, default: bool = False) -> bool:
    """Read a boolean-like feature."""

    value = features.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def feature_text(features: FeatureMap, key: str, default: str = "") -> str:
    """Read a text feature as an uppercase normalized label."""

    value = features.get(key, default)
    return str(value).strip().upper()


def detected_regime(features: FeatureMap) -> Regime:
    """Resolve a regime label, defaulting to RANGE when unknown."""

    value = features.get("regime", Regime.RANGE)
    if isinstance(value, Regime):
        return value
    try:
        return Regime(str(value).strip().upper())
    except ValueError:
        return Regime.RANGE


def spread_is_unsafe(
    snapshot: MarketSnapshot,
    features: FeatureMap,
    default_max_spread_points: float = 25.0,
) -> bool:
    """Return True when strategy should fail closed on spread awareness."""

    max_spread = feature_float(features, "max_strategy_spread_points", default_max_spread_points)
    spread = feature_float(features, "spread_points", snapshot.spread_points)
    return spread < 0 or spread > max_spread


def score_conditions(
    *,
    base: float,
    conditions: Sequence[tuple[bool, float, str]],
) -> tuple[float, tuple[str, ...]]:
    """Score weighted conditions and return matched human-readable reasons."""

    score = base
    reasons: list[str] = []
    for passed, weight, reason in conditions:
        if passed:
            score += weight
            reasons.append(reason)
    return clamp_score(score), tuple(reasons)


def choose_direction(
    *,
    buy_score: float,
    sell_score: float,
    buy_reasons: Sequence[str],
    sell_reasons: Sequence[str],
    threshold: float,
    min_margin: float,
    strategy_name: str,
    metadata: Mapping[str, Any] | None = None,
) -> StrategySignal:
    """Choose BUY, SELL or NONE using a score threshold and conflict margin."""

    buy_score = clamp_score(buy_score)
    sell_score = clamp_score(sell_score)
    if buy_score < threshold and sell_score < threshold:
        return StrategySignal(
            action=SignalAction.NONE,
            score=0,
            reasons=("score below threshold",),
            strategy_name=strategy_name,
            metadata=metadata or {},
        )
    if abs(buy_score - sell_score) < min_margin:
        return StrategySignal(
            action=SignalAction.NONE,
            score=0,
            reasons=("directional conflict",),
            strategy_name=strategy_name,
            metadata=metadata or {},
        )
    if buy_score > sell_score:
        return StrategySignal(
            action=SignalAction.BUY,
            score=buy_score,
            reasons=tuple(buy_reasons),
            strategy_name=strategy_name,
            metadata=metadata or {},
        )
    return StrategySignal(
        action=SignalAction.SELL,
        score=sell_score,
        reasons=tuple(sell_reasons),
        strategy_name=strategy_name,
        metadata=metadata or {},
    )


def none_signal(strategy_name: str, reason: str, metadata: Mapping[str, Any] | None = None) -> StrategySignal:
    """Build a fail-closed NONE signal."""

    return StrategySignal(
        action=SignalAction.NONE,
        score=0,
        reasons=(reason,),
        strategy_name=strategy_name,
        metadata=metadata or {},
    )


@dataclass(frozen=True)
class PromotionEvidence:
    """Evidence required by the Strategy Promotion Gate."""

    historical_trades: int = 0
    statistical_justification: str = ""
    oos_profit_factor: float = 0.0
    oos_expected_payoff: float = 0.0
    oos_max_drawdown_pct: float = 100.0
    max_drawdown_limit_pct: float = 0.0
    max_profit_concentration_pct: float = 100.0
    spread_slippage_sensitivity_passed: bool = False
    walk_forward_passed: bool = False
    optimization_used: bool = False
    shadow_signals: int = 0
    shadow_days: int = 0
    shadow_audit_complete: bool = False


@dataclass(frozen=True)
class PromotionDecision:
    """Result of checking whether a strategy can run in shadow or demo mode."""

    requested_mode: str
    approved: bool
    effective_mode: str
    reasons: tuple[str, ...]
    checks: Mapping[str, bool] = field(default_factory=dict)


def evaluate_promotion_gate(
    evidence: PromotionEvidence | Mapping[str, Any] | None,
    *,
    requested_mode: str = "shadow",
) -> PromotionDecision:
    """Apply the Strategy Promotion Gate from PROJECT_SPEC.md section 12.1.

    Shadow mode is allowed for audit collection. Demo mode is blocked unless all
    required evidence is present and passes.
    """

    mode = requested_mode.strip().lower()
    if mode not in {"shadow", "demo"}:
        return PromotionDecision(
            requested_mode=requested_mode,
            approved=False,
            effective_mode="shadow",
            reasons=("unsupported strategy mode",),
            checks={"mode_supported": False},
        )
    if mode == "shadow":
        return PromotionDecision(
            requested_mode=requested_mode,
            approved=True,
            effective_mode="shadow",
            reasons=("shadow mode only; signals are for audit, not execution",),
            checks={"shadow_mode_allowed": True},
        )

    data = _coerce_evidence(evidence)
    checks = {
        "sample_size": data.historical_trades >= 200 or bool(data.statistical_justification),
        "profit_factor": data.oos_profit_factor > 1.15,
        "expected_payoff": data.oos_expected_payoff > 0,
        "drawdown": (
            data.max_drawdown_limit_pct > 0
            and data.oos_max_drawdown_pct < data.max_drawdown_limit_pct
        ),
        "profit_concentration": data.max_profit_concentration_pct <= 50.0,
        "spread_slippage_sensitivity": data.spread_slippage_sensitivity_passed,
        "walk_forward": (not data.optimization_used) or data.walk_forward_passed,
        "shadow_forward": (
            data.shadow_audit_complete
            and data.shadow_signals > 0
            and data.shadow_days > 0
        ),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    if failed:
        return PromotionDecision(
            requested_mode=requested_mode,
            approved=False,
            effective_mode="shadow",
            reasons=tuple(f"promotion gate failed: {name}" for name in failed),
            checks=checks,
        )
    return PromotionDecision(
        requested_mode=requested_mode,
        approved=True,
        effective_mode="demo",
        reasons=("strategy promotion gate passed for demo mode",),
        checks=checks,
    )


def _coerce_evidence(evidence: PromotionEvidence | Mapping[str, Any] | None) -> PromotionEvidence:
    if isinstance(evidence, PromotionEvidence):
        return evidence
    if not evidence:
        return PromotionEvidence()
    return PromotionEvidence(
        historical_trades=int(evidence.get("historical_trades", 0)),
        statistical_justification=str(evidence.get("statistical_justification", "")),
        oos_profit_factor=float(evidence.get("oos_profit_factor", 0.0)),
        oos_expected_payoff=float(evidence.get("oos_expected_payoff", 0.0)),
        oos_max_drawdown_pct=float(evidence.get("oos_max_drawdown_pct", 100.0)),
        max_drawdown_limit_pct=float(evidence.get("max_drawdown_limit_pct", 0.0)),
        max_profit_concentration_pct=float(evidence.get("max_profit_concentration_pct", 100.0)),
        spread_slippage_sensitivity_passed=bool(
            evidence.get("spread_slippage_sensitivity_passed", False)
        ),
        walk_forward_passed=bool(evidence.get("walk_forward_passed", False)),
        optimization_used=bool(evidence.get("optimization_used", False)),
        shadow_signals=int(evidence.get("shadow_signals", 0)),
        shadow_days=int(evidence.get("shadow_days", 0)),
        shadow_audit_complete=bool(evidence.get("shadow_audit_complete", False)),
    )
