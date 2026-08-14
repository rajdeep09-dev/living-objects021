"""Typed events emitted by the bounded v6 program-evolution API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProgramEvolvedEvent(BaseModel):
    event_type: str = "program_evolved"
    run_id: str = Field(min_length=8, max_length=96)
    task: str = Field(min_length=1, max_length=64)
    generation: int = Field(ge=0, le=500)
    training_fitness: float = Field(ge=0.0, le=1.0)
    holdout_correctness: float = Field(ge=0.0, le=1.0)
    source_sha256: str = Field(min_length=64, max_length=64)


class ProgramRejectedEvent(BaseModel):
    event_type: str = "program_rejected"
    run_id: str = Field(min_length=8, max_length=96)
    reason: str = Field(min_length=1, max_length=160)
