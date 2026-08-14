"""Typed v2 evolution events shared by HTTP and WebSocket clients."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OrganismBornEvent(BaseModel):
    type: Literal["organism_born"] = "organism_born"
    organism_id: str
    genome_snapshot: dict[str, Any] = Field(default_factory=dict)
    parent_ids: list[str] = Field(default_factory=list)
    inherited_strategies: list[str] = Field(default_factory=list)


class StrategyAdoptedEvent(BaseModel):
    type: Literal["strategy_adopted"] = "strategy_adopted"
    adopter_id: str
    strategy_name: str
    creator_id: str
    creator_generation: int
    adopter_generation: int


class ConstitutionMutationEvent(BaseModel):
    type: Literal["constitution_mutated"] = "constitution_mutated"
    organism_id: str
    before: dict[str, Any]
    after: dict[str, Any]


class RedTeamAttackEvent(BaseModel):
    type: Literal["red_team_attack"] = "red_team_attack"
    attacker_id: str
    target_id: str
    result: Literal["repelled", "success", "partial"]
    damage: float = 0.0

