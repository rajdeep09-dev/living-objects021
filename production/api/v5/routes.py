"""Authenticated v5 frontier endpoints for reports, history, and cross-domain exchange.

The endpoints deliberately control or observe bounded local evolution state. They do
not execute user-provided code and are never in the per-generation worker path.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from evolution.epochs import EpochDetector
from evolution.hall_of_evolution import HallOfEvolution
from evolution.lamarckian import LamarckianGenome
from production.api.v5.websocket import EpochChangedEvent, ImmortalizationEvent, PollinationEvent


class EpochCheckRequest(BaseModel):
    generation: int = Field(ge=0, le=1_000_000)
    previous_scores: list[float] = Field(min_length=2, max_length=256)
    current_scores: list[float] = Field(min_length=2, max_length=256)
    dominant_strategy_type: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")


class ImmortalizeRequest(BaseModel):
    generation: int = Field(ge=0, le=1_000_000)
    task_name: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    fitness: float = Field(ge=0.0, le=1.0)
    epoch_name: str = Field(default="Primordial Era", min_length=1, max_length=96)
    strategy_count: int = Field(default=0, ge=0, le=64)


class PollinationRequest(BaseModel):
    generation: int = Field(ge=0, le=1_000_000)
    source: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    target: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    donated_strategies: int = Field(ge=0, le=32)


@dataclass
class V5ControlState:
    detector: EpochDetector = field(default_factory=EpochDetector)
    hall: HallOfEvolution = field(default_factory=lambda: HallOfEvolution(Path(tempfile.gettempdir()) / "living-objects-v5-hall.db"))
    epochs: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    pollination_count: int = 0

    def emit(self, event: Any) -> dict[str, Any]:
        payload = event.model_dump() if hasattr(event, "model_dump") else dict(event)
        self.events.append(payload)
        self.events = self.events[-500:]
        return payload


state = V5ControlState()
router = APIRouter(prefix="/v5", tags=["v5"])


@router.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return {
        "epoch_count": len(state.epochs),
        "latest_epoch": state.epochs[-1] if state.epochs else None,
        "pollination_count": state.pollination_count,
        "event_count": len(state.events),
        "execution_boundary": "control-plane only; local workers do not call this endpoint per generation",
    }


@router.post("/epochs/check")
def check_epoch(payload: EpochCheckRequest) -> dict[str, Any]:
    epoch = state.detector.check_epoch_boundary(
        payload.generation,
        payload.current_scores,
        payload.previous_scores,
    )
    if epoch is None:
        return {"changed": False, "epoch": None}
    item = {
        "start_generation": epoch.start_generation,
        "dominant_strategy_type": payload.dominant_strategy_type,
        "divergence_score": epoch.divergence_score,
        "name": epoch.name,
    }
    state.epochs.append(item)
    event = state.emit(EpochChangedEvent(generation=epoch.start_generation, epoch_name=epoch.name, divergence_score=epoch.divergence_score))
    return {"changed": True, "epoch": item, "event": event}


@router.get("/epochs")
def list_epochs() -> dict[str, Any]:
    return {"items": list(state.epochs)}


@router.post("/hall/immortalize", status_code=201)
def immortalize(payload: ImmortalizeRequest) -> dict[str, Any]:
    strategies = {
        f"strategy_{index}": SimpleNamespace(source_code="", effectiveness=payload.fitness, generation=payload.generation)
        for index in range(payload.strategy_count)
    }
    champion = SimpleNamespace(
        learned_strategies=strategies,
        genome=LamarckianGenome(fitness=payload.fitness, generation_born=payload.generation),
        ancestor_ids=[],
    )
    immortalization_id = state.hall.immortalize(champion, payload.generation, payload.task_name, payload.fitness, payload.epoch_name)
    event = state.emit(ImmortalizationEvent(immortalization_id=immortalization_id, generation=payload.generation, task_name=payload.task_name, fitness=payload.fitness))
    return {"immortalization_id": immortalization_id, "record": state.hall.query(payload.generation), "event": event}


@router.get("/hall")
def query_hall(generation: int = 0) -> dict[str, Any]:
    return {"record": state.hall.query(max(0, min(generation, 1_000_000)))}


@router.post("/pollination", status_code=201)
def record_pollination(payload: PollinationRequest) -> dict[str, Any]:
    state.pollination_count += payload.donated_strategies
    event = state.emit(PollinationEvent(**payload.model_dump()))
    return {"accepted": True, "total_donated_strategies": state.pollination_count, "event": event}
