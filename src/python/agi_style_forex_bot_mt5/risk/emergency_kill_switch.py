"""Emergency halt primitives for the risk gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KillSwitchState:
    """Manual or automatic halt state."""

    active: bool = False
    reason: str = ""
    halted_until_utc: datetime | None = None


class EmergencyKillSwitch:
    """Fail-closed emergency kill switch."""

    def evaluate(self, state: KillSwitchState | None, now_utc: datetime) -> tuple[bool, str]:
        """Return (allowed, reason)."""

        if state is None or not state.active:
            return True, ""
        if state.halted_until_utc is not None and now_utc >= state.halted_until_utc:
            return True, ""
        return False, state.reason or "emergency kill switch active"
