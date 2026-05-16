"""Currency exposure checks for open positions."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from agi_style_forex_bot_mt5.contracts import PositionState


@dataclass(frozen=True)
class CurrencyExposureResult:
    """Currency exposure validation result."""

    accepted: bool
    reject_reason: str = ""


class CurrencyExposureGuard:
    """Conservative exposure helper for six-letter Forex symbols."""

    def evaluate(
        self,
        *,
        candidate_symbol: str,
        open_positions: Sequence[PositionState],
        max_positions_per_currency: int | None = None,
    ) -> CurrencyExposureResult:
        """Block only when an explicit currency cap is supplied and exceeded."""

        if max_positions_per_currency is None:
            return CurrencyExposureResult(True)
        if len(candidate_symbol) < 6:
            return CurrencyExposureResult(False, "candidate symbol is not a Forex pair")
        counts: Counter[str] = Counter()
        for symbol in [position.symbol for position in open_positions] + [candidate_symbol]:
            if len(symbol) < 6:
                return CurrencyExposureResult(False, f"cannot parse Forex currencies from {symbol}")
            counts.update((symbol[:3], symbol[3:6]))
        overloaded = [currency for currency, count in counts.items() if count > max_positions_per_currency]
        if overloaded:
            return CurrencyExposureResult(
                False,
                f"currency exposure limit exceeded: {', '.join(sorted(overloaded))}",
            )
        return CurrencyExposureResult(True)
