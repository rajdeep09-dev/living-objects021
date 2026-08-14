"""Typed, bounded BEAST v5 evolution-stream events."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EpochChangedEvent(BaseModel):
    type: Literal["epoch_change"] = "epoch_change"
    generation: int = Field(ge=0)
    epoch_name: str = Field(min_length=1, max_length=96)
    divergence_score: float = Field(ge=0.0, le=1.0)


class ImmortalizationEvent(BaseModel):
    type: Literal["immortalization"] = "immortalization"
    immortalization_id: str = Field(min_length=1, max_length=128)
    generation: int = Field(ge=0)
    task_name: str = Field(min_length=1, max_length=96)
    fitness: float = Field(ge=0.0, le=1.0)


class PollinationEvent(BaseModel):
    type: Literal["pollination"] = "pollination"
    generation: int = Field(ge=0)
    source: str = Field(min_length=1, max_length=96)
    target: str = Field(min_length=1, max_length=96)
    donated_strategies: int = Field(ge=0, le=32)


__all__ = ["EpochChangedEvent", "ImmortalizationEvent", "PollinationEvent"]

