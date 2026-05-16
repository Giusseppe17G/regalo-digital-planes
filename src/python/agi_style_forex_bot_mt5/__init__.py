"""AGI_STYLE_FOREX_BOT_MT5 package.

The package is intentionally demo/shadow oriented. Real-account execution is
outside the initial scope and is blocked by configuration defaults.
"""

from .bot import BotCycleResult, ShadowDemoBot
from .config import BotConfig, load_config
from .contracts import (
    Direction,
    EntryType,
    Environment,
    Event,
    ExecutionRequest,
    ExecutionResult,
    MarketSnapshot,
    Regime,
    RiskDecision,
    SignalAction,
    StrategySignal,
    TradeSignal,
)

__all__ = [
    "BotConfig",
    "BotCycleResult",
    "Direction",
    "EntryType",
    "Environment",
    "Event",
    "ExecutionRequest",
    "ExecutionResult",
    "MarketSnapshot",
    "Regime",
    "RiskDecision",
    "SignalAction",
    "ShadowDemoBot",
    "StrategySignal",
    "TradeSignal",
    "load_config",
]
