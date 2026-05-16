"""Correlation guard primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from agi_style_forex_bot_mt5.contracts import PositionState


@dataclass(frozen=True)
class CorrelationResult:
    """Correlation validation result."""

    accepted: bool
    reject_reason: str = ""


class CorrelationGuard:
    """Block explicitly configured highly-correlated symbol combinations."""

    def evaluate(
        self,
        *,
        candidate_symbol: str,
        open_positions: Sequence[PositionState],
        blocked_pairs: Mapping[str, tuple[str, ...]] | None = None,
    ) -> CorrelationResult:
        """Apply an explicit blocklist; no statistical inference is done here."""

        if not blocked_pairs:
            return CorrelationResult(True)
        blocked = set(blocked_pairs.get(candidate_symbol, ()))
        open_symbols = {position.symbol for position in open_positions}
        conflicts = sorted(blocked & open_symbols)
        if conflicts:
            return CorrelationResult(
                False,
                f"correlation block for {candidate_symbol}: {', '.join(conflicts)}",
            )
        return CorrelationResult(True)
