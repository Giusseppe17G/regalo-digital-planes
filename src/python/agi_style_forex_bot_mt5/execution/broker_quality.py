"""Broker execution quality summaries."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrokerQualityReport:
    """Small immutable report for broker execution quality."""

    samples: int
    average_slippage_points: float
    max_adverse_slippage_points: float
    reject_rate_pct: float
    recoverable_rejects: int


@dataclass
class BrokerQualityMonitor:
    """Accumulate execution outcomes for local diagnostics."""

    _slippages: list[float] = field(default_factory=list)
    _rejects: int = 0
    _recoverable_rejects: int = 0

    def record_fill(self, slippage_points: float) -> None:
        """Record a filled order slippage."""

        self._slippages.append(float(slippage_points))

    def record_reject(self, *, recoverable: bool = False) -> None:
        """Record an MT5 rejection."""

        self._rejects += 1
        if recoverable:
            self._recoverable_rejects += 1

    def report(self) -> BrokerQualityReport:
        """Build a deterministic summary."""

        total = len(self._slippages) + self._rejects
        average = sum(self._slippages) / len(self._slippages) if self._slippages else 0.0
        adverse = max([0.0, *self._slippages])
        reject_rate = (self._rejects / total * 100.0) if total else 0.0
        return BrokerQualityReport(
            samples=total,
            average_slippage_points=average,
            max_adverse_slippage_points=adverse,
            reject_rate_pct=reject_rate,
            recoverable_rejects=self._recoverable_rejects,
        )
