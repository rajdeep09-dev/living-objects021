"""Bounded v9 API routes; this module intentionally provides no background worker."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from evolution.v9_federation import SignedDiscoveryExchange, available_discoveries
from evolution.v9_sorting_curriculum import primitive_manifest
from living_objects.sdk import SDK_VERSION, audit, evolve, export, reproduce
from production.middleware.rate_limit import rate_limit_dependency


TaskName = Literal["manhattan-distance", "clean-sorting"]
INLINE_GENERATION_LIMIT = 25


class BoundedRunRequest(BaseModel):
    task: TaskName = "manhattan-distance"
    generations: int = Field(default=10, ge=1, le=10_000)
    population_size: int = Field(default=16, ge=4, le=64)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)


class ReproduceRequest(BaseModel):
    run_id: str = Field(pattern=r"^BEAST-SDK-V1-[A-F0-9]{16}$")


class ExportRequest(BaseModel):
    run_id: str = Field(pattern=r"^BEAST-SDK-V1-[A-F0-9]{16}$")
    target: Literal["python", "javascript", "rust", "go"] = "python"


class ImportEnvelopeRequest(BaseModel):
    envelope: dict[str, Any]


@dataclass
class V9ControlState:
    artifact_dir: Path = field(default_factory=lambda: Path(tempfile.gettempdir()) / "living-objects-v9-api-runs")
    exchange: SignedDiscoveryExchange | None = None
    recent_runs: list[dict[str, Any]] = field(default_factory=list)

    def record(self, result: dict[str, Any]) -> None:
        self.recent_runs.append(result)
        self.recent_runs = self.recent_runs[-100:]


state = V9ControlState()
router = APIRouter(prefix="/v9", tags=["v9"])


@router.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return {
        "sdk_version": SDK_VERSION,
        "inline_generation_limit": INLINE_GENERATION_LIMIT,
        "recent_run_count": len(state.recent_runs),
        "worker": {
            "configured": False,
            "reason": "This API executes only short bounded runs inline; persistent campaigns require a separately authorized operator workflow.",
        },
        "execution_boundary": {
            "typed_ast_interpreter_only": True,
            "user_source_accepted": False,
            "generated_source_executed": False,
            "network_calls_during_evaluation": 0,
        },
    }


@router.get("/evidence")
def evidence() -> dict[str, Any]:
    return {
        "curriculum": primitive_manifest(),
        "discoveries": available_discoveries(),
        "audits": {task: audit(task).__dict__ for task in ("clean-sorting", "manhattan-distance")},
        "claim_boundary": "The discovery records are the five measured v8 Manhattan trials. The clean-sorting curriculum is implemented but has no positive sorting claim.",
    }


@router.get("/runs")
def list_runs() -> dict[str, Any]:
    return {"items": list(state.recent_runs)}


@router.post("/runs", status_code=201, dependencies=[Depends(rate_limit_dependency("3/minute"))])
def run_bounded(payload: BoundedRunRequest) -> dict[str, Any]:
    if payload.generations > INLINE_GENERATION_LIMIT:
        return {
            "accepted": False,
            "status": "requires_preregistered_campaign",
            "max_inline_generations": INLINE_GENERATION_LIMIT,
            "requested_generations": payload.generations,
            "reason": "Long-running compute is not hidden behind this synchronous API. Use the preregistered operator workflow after resource authorization.",
        }
    result = evolve(
        payload.task,
        generations=payload.generations,
        population_size=payload.population_size,
        seed=payload.seed,
        artifact_dir=state.artifact_dir,
    )
    item = result.to_dict() | {"artifact_path": result.artifact_path}
    state.record(item)
    return {"accepted": True, "status": "completed_inline", "run": item}


@router.post("/reproduce", dependencies=[Depends(rate_limit_dependency("10/minute"))])
def reproduce_run(payload: ReproduceRequest) -> dict[str, Any]:
    try:
        result = reproduce(payload.run_id, artifact_dir=state.artifact_dir)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"reproduction": result.__dict__}


@router.post("/export", dependencies=[Depends(rate_limit_dependency("10/minute"))])
def export_run(payload: ExportRequest) -> dict[str, Any]:
    result = next((item for item in state.recent_runs if item["run_id"] == payload.run_id), None)
    if result is None:
        raise HTTPException(status_code=404, detail="run is not available in the bounded in-memory API history")
    try:
        safe = export(result, payload.target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"export": safe.__dict__}


@router.get("/federation")
def federation_snapshot() -> dict[str, Any]:
    if state.exchange is None:
        return {
            "configured": False,
            "reason": "No trusted peer keyring is configured for this API process.",
            "available_record_ids": [record["record_id"] for record in available_discoveries()],
            "transport": "not implemented by this local exchange MVP",
        }
    return {"configured": True, "exchange": state.exchange.evidence_summary()}


@router.post("/federation/import", dependencies=[Depends(rate_limit_dependency("10/minute"))])
def import_discovery(payload: ImportEnvelopeRequest) -> dict[str, Any]:
    if state.exchange is None:
        raise HTTPException(status_code=409, detail="trusted peer keyring is not configured")
    admission = state.exchange.import_envelope(payload.envelope)
    if not admission.accepted:
        raise HTTPException(status_code=422, detail=admission.reason)
    return {"admission": admission.__dict__, "summary": state.exchange.evidence_summary()}
