"""Typed events emitted by the BEAST v3 frontier APIs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MarketTradeEvent(BaseModel):
    type: Literal["market_trade"] = "market_trade"
    strategy_name: str
    buyer_id: str
    seller_id: str
    price: float
    adoption_count: int


class DiplomaticExchangeEvent(BaseModel):
    type: Literal["diplomatic_exchange"] = "diplomatic_exchange"
    proposal_id: str
    accepted: bool
    transferred_to_ours: list[str] = Field(default_factory=list)
    transferred_to_theirs: list[str] = Field(default_factory=list)


class StrategyResurrectedEvent(BaseModel):
    type: Literal["strategy_resurrected"] = "strategy_resurrected"
    strategy_name: str
    target_id: str
    relevance: float


class BenchmarkSynthesizedEvent(BaseModel):
    type: Literal["benchmark_synthesized"] = "benchmark_synthesized"
    benchmark_id: str
    generation: int
    difficulty: float


class ConsciousnessMeasuredEvent(BaseModel):
    type: Literal["consciousness_measured"] = "consciousness_measured"
    organism_id: str
    phi: float
    self_model_accuracy: float
    workspace_breadth: float
    composite: float

