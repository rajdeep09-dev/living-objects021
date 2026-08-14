"""BEAST v3 API package."""

from production.api.v3.websocket import (
    BenchmarkSynthesizedEvent,
    ConsciousnessMeasuredEvent,
    DiplomaticExchangeEvent,
    MarketTradeEvent,
    StrategyResurrectedEvent,
)

__all__ = [
    "BenchmarkSynthesizedEvent",
    "ConsciousnessMeasuredEvent",
    "DiplomaticExchangeEvent",
    "MarketTradeEvent",
    "StrategyResurrectedEvent",
]
