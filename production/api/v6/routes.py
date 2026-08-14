"""Bounded, authenticated v6 program-evolution endpoints.

This is a control-plane API.  It only accepts a small named task registry and
creates typed ASTs internally; it neither accepts nor executes source code.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from evolution.fitness import AbsoluteDifferenceEvaluator, FitnessEvaluator, SortingEvaluator
from evolution.gp_population import GPPopulation
from production.api.v6.websocket import LiveGPPopulationBroadcaster, ProgramRejectedEvent


TaskName = Literal["absolute_difference", "sorting"]


class ProgramRunRequest(BaseModel):
    task: TaskName = "absolute_difference"
    population_size: int = Field(default=32, ge=4, le=128)
    generations: int = Field(default=50, ge=1, le=500)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)


def _evaluator_for(task: TaskName) -> FitnessEvaluator:
    if task == "absolute_difference":
        return AbsoluteDifferenceEvaluator()
    return SortingEvaluator()


@dataclass
class V6ControlState:
    events: list[dict[str, Any]] = field(default_factory=list)
    runs: list[dict[str, Any]] = field(default_factory=list)
    live_gp: LiveGPPopulationBroadcaster = field(default_factory=LiveGPPopulationBroadcaster)

    def emit(self, event: BaseModel) -> dict[str, Any]:
        payload = event.model_dump()
        self.events.append(payload)
        self.events = self.events[-500:]
        return payload

    def record_run(self, item: dict[str, Any]) -> None:
        self.runs.append(item)
        self.runs = self.runs[-100:]


state = V6ControlState()
router = APIRouter(prefix="/v6", tags=["v6"])


@router.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return {
        "run_count": len(state.runs),
        "event_count": len(state.live_gp.history),
        "allowed_tasks": ["absolute_difference", "sorting"],
        "execution_boundary": "typed AST interpreter only; user-provided source is never accepted or executed",
    }


@router.get("/runs")
def list_runs() -> dict[str, Any]:
    return {"items": list(state.runs)}


@router.post("/runs", status_code=201)
async def evolve_program(payload: ProgramRunRequest) -> dict[str, Any]:
    evaluator = _evaluator_for(payload.task)
    try:
        generation_events = await state.live_gp.advance(
            task_domain=payload.task,
            evaluator=evaluator,
            population_size=payload.population_size,
            seed=payload.seed,
            steps=payload.generations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    population = state.live_gp.population_for(payload.task)
    champion = population.champion
    event = generation_events[-1]
    source_code = str(event["champion_code"])
    source_sha256 = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
    holdout = population.evaluator.batch_evaluate([champion.genome], seed=payload.seed + 10_000)[0]
    item = {
        "run_id": event["run_id"],
        "task": payload.task,
        "generation": population.generation,
        "training_fitness": champion.fitness,
        "holdout_correctness": holdout.correctness,
        "program_source": source_code,
        "source_sha256": source_sha256,
        "node_count": champion.genome.complexity(),
        "validation": {
            "typed_ast": True,
            "interpreter_execution_only": True,
            "user_source_accepted": False,
            "external_network_calls": 0,
        },
    }
    state.record_run(item)
    return {"run": item, "event": event}


@router.post("/validate-rejection")
def validation_boundary() -> dict[str, Any]:
    """Expose the hard boundary without accepting any potentially executable input."""
    event = state.emit(ProgramRejectedEvent(
        run_id="boundary",
        reason="v6 accepts named task configuration only; source-code submission is not an API feature",
    ))
    return {"accepted": False, "event": event}
