"""Typed BEAST v4 frontier events."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UniverseBranchedEvent(BaseModel):
    type: Literal["v4.universe.branched"] = "v4.universe.branched"
    parent_id: str
    child_id: str
    divergence_score: float = Field(ge=0.0, le=1.0)
    branch_generation: int = Field(ge=0)


class TemporalRevisionEvent(BaseModel):
    type: Literal["v4.temporal.revision"] = "v4.temporal.revision"
    proposal_id: str
    applied: bool
    affected_organisms: int = Field(ge=0)
    net_fitness_change: float
    paradox: bool


class AntibodyDonatedEvent(BaseModel):
    type: Literal["v4.immunity.antibody"] = "v4.immunity.antibody"
    antibody_id: str
    discovered_by: str
    pattern: str
    effectiveness: float = Field(ge=0.0, le=1.0)


class TournamentCompletedEvent(BaseModel):
    type: Literal["v4.tournament.completed"] = "v4.tournament.completed"
    generation: int = Field(ge=0)
    matches: int = Field(ge=0)
    attacker_wins: int = Field(ge=0)
    defender_wins: int = Field(ge=0)
    draws: int = Field(ge=0)


class MemoryRecordedEvent(BaseModel):
    type: Literal["v4.memory.recorded"] = "v4.memory.recorded"
    strategy_id: str
    cluster_count: int = Field(ge=0)


class WritingEvolvedEvent(BaseModel):
    type: Literal["v4.writing.evolved"] = "v4.writing.evolved"
    generation: int = Field(ge=0)
    vocabulary_size: int = Field(ge=0)


class SubstrateExportedEvent(BaseModel):
    type: Literal["v4.substrate.exported"] = "v4.substrate.exported"
    organism_id: str
    substrate: Literal["wasm", "container", "circuit"]
    size: int = Field(ge=0)


class ComputationRunEvent(BaseModel):
    type: Literal["v4.computation.run"] = "v4.computation.run"
    halted: bool
    accepted: bool
    steps_used: int = Field(ge=0)
    universality_score: float = Field(ge=0.0, le=1.0)


__all__ = [
    "AntibodyDonatedEvent",
    "ComputationRunEvent",
    "MemoryRecordedEvent",
    "SubstrateExportedEvent",
    "TemporalRevisionEvent",
    "TournamentCompletedEvent",
    "UniverseBranchedEvent",
    "WritingEvolvedEvent",
]

