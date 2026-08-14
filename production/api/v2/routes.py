"""Authenticated v2 control-plane routes."""
from __future__ import annotations

import os
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from evolution.beast_v2 import EnvironmentState, EvolutionConstitution, RedTeamOrganism
from evolution.beast_v2_culture import (
    DSLGenome,
    EmbodiedOrganism,
    EnergyBudget,
    ThermodynamicFitness,
    register_builtin_tools,
)
from evolution.beast_v2_runtime import BeastOrganism
from production.api.v2.websocket import (
    ConstitutionMutationEvent,
    OrganismBornEvent,
    RedTeamAttackEvent,
    StrategyAdoptedEvent,
)
from production.store_v2 import StrategyRecord, V2Store
from production.middleware.rate_limit import rate_limit_dependency


class ConstitutionPatch(BaseModel):
    selection_pressure: float | None = Field(default=None, ge=0.0, le=1.0)
    crossover_strategy: str | None = None
    cultural_adoption_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    novelty_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    extinction_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    generation_overlap: float | None = Field(default=None, ge=0.0, le=1.0)
    mutation_distribution: str | None = None


class SpawnRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    parent_ids: list[str] = Field(default_factory=list)


class StrategyPublishRequest(BaseModel):
    name: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    source_code: str = Field(min_length=1, max_length=20_000)
    descriptor: str = Field(min_length=1, max_length=256)
    effectiveness: float = Field(ge=0.0, le=1.0)
    author_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    generation: int = Field(default=0, ge=0)
    parent_ids: list[str] = Field(default_factory=list)
    node_id: str = Field(default="local", min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")


class GossipRequest(BaseModel):
    peer_node_id: str = Field(min_length=1, max_length=96)
    strategies: list[StrategyPublishRequest] = Field(default_factory=list)


class AdoptRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")


class AttackRequest(BaseModel):
    attacker_id: str = Field(default="red-team", min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    attack_power: float = Field(default=0.5, ge=0.0, le=1.0)


class DSLExpressRequest(BaseModel):
    condition: str = "high"
    action: str = "coop"
    fallback: str = "defect"


class DSLParseRequest(BaseModel):
    source: str = Field(min_length=1, max_length=512)


class ToolCallRequest(BaseModel):
    kwargs: dict[str, Any] = Field(default_factory=dict)


class EnergyMeasureRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    quality: float = Field(ge=0.0, le=1.0)
    operations: int = Field(default=1, ge=1, le=1_000_000)
    memory_allocated: int = Field(default=0, ge=0, le=1_000_000_000)
    budget: int = Field(default=1000, ge=1, le=1_000_000)


class V2ControlState:
    def __init__(self) -> None:
        self.constitution = EvolutionConstitution()
        self.organisms: dict[str, BeastOrganism] = {}
        self.events: list[dict[str, Any]] = []
        self.dsl = DSLGenome()
        self.energy: dict[str, EnergyBudget] = {}
        self.store = V2Store(os.getenv("V2_MEMOME_PATH", "state/v2_memome.sqlite3"))
        register_builtin_tools()

    def emit(self, event: BaseModel | dict[str, Any]) -> dict[str, Any]:
        payload = event.model_dump() if isinstance(event, BaseModel) else dict(event)
        self.events.append(payload)
        self.events = self.events[-500:]
        return payload

    def get_organism(self, organism_id: str) -> BeastOrganism:
        organism = self.organisms.get(organism_id)
        if organism is None:
            raise HTTPException(status_code=404, detail="v2 organism not found")
        return organism


control_state = V2ControlState()
router = APIRouter(prefix="/v2", tags=["v2"])
write_dependencies = [Depends(rate_limit_dependency("60/minute"))]


@router.get("/constitution")
def get_constitution() -> dict[str, Any]:
    return control_state.constitution.to_dict()


@router.patch("/constitution", dependencies=write_dependencies)
def patch_constitution(payload: ConstitutionPatch) -> dict[str, Any]:
    before = control_state.constitution.to_dict()
    values = {**before, **payload.model_dump(exclude_none=True)}
    try:
        control_state.constitution = EvolutionConstitution(**values)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    after = control_state.constitution.to_dict()
    control_state.emit(ConstitutionMutationEvent(organism_id="ecosystem", before=before, after=after))
    return after


@router.post("/constitution/mutate", dependencies=write_dependencies)
def mutate_constitution(seed: int | None = None) -> dict[str, Any]:
    before = control_state.constitution.to_dict()
    control_state.constitution = control_state.constitution.mutate(random.Random(seed))
    after = control_state.constitution.to_dict()
    control_state.emit(ConstitutionMutationEvent(organism_id="ecosystem", before=before, after=after))
    return {"before": before, "after": after, "code": control_state.constitution.to_code()}


@router.post("/organisms", status_code=status.HTTP_201_CREATED, dependencies=write_dependencies)
def spawn_organism(payload: SpawnRequest) -> dict[str, Any]:
    if payload.organism_id in control_state.organisms:
        raise HTTPException(status_code=409, detail="v2 organism already exists")
    organism = BeastOrganism(payload.organism_id, parent_ids=tuple(payload.parent_ids))
    control_state.organisms[organism.organism_id] = organism
    event = control_state.emit(
        OrganismBornEvent(
            organism_id=organism.organism_id,
            genome_snapshot=organism.to_state(),
            parent_ids=list(organism.parent_ids),
            inherited_strategies=list(organism.learned_modules),
        )
    )
    return {**organism.to_state(), "event": event}


@router.get("/organisms")
def list_v2_organisms() -> dict[str, Any]:
    items = [organism.to_state() for organism in control_state.organisms.values()]
    return {"items": items, "count": len(items)}


@router.get("/organisms/{organism_id}")
def inspect_v2_organism(organism_id: str) -> dict[str, Any]:
    return control_state.get_organism(organism_id).to_state()


@router.post("/organisms/{organism_id}/reproduce", status_code=status.HTTP_201_CREATED, dependencies=write_dependencies)
def reproduce_v2_organism(organism_id: str, seed: int | None = None) -> dict[str, Any]:
    parent = control_state.get_organism(organism_id)
    child = parent.reproduce(random.Random(seed))
    control_state.organisms[child.organism_id] = child
    control_state.emit(
        OrganismBornEvent(
            organism_id=child.organism_id,
            genome_snapshot=child.to_state(),
            parent_ids=list(child.parent_ids),
            inherited_strategies=list(child.learned_modules),
        )
    )
    return child.to_state()


@router.get("/strategies")
def list_strategies(q: str = Query(default="", max_length=200), limit: int = Query(default=100, ge=1, le=10_000)) -> dict[str, Any]:
    records = control_state.store.query(q, limit)
    return {"items": [record.to_dict() for record in records], "count": len(records)}


@router.post("/strategies", status_code=status.HTTP_201_CREATED, dependencies=write_dependencies)
def publish_strategy(payload: StrategyPublishRequest) -> dict[str, Any]:
    record = control_state.store.publish_fields(**payload.model_dump())
    return record.to_dict()


@router.post("/strategies/{strategy_id}/adopt", dependencies=write_dependencies)
def adopt_strategy(strategy_id: str, payload: AdoptRequest) -> dict[str, Any]:
    record = control_state.store.get(strategy_id)
    if record is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    organism = control_state.get_organism(payload.organism_id)
    validation = organism.learn(record.name, record.source_code)
    if not validation.accepted:
        raise HTTPException(status_code=422, detail=validation.reason)
    event = control_state.emit(
        StrategyAdoptedEvent(
            adopter_id=organism.organism_id,
            strategy_name=record.name,
            creator_id=record.author_id,
            creator_generation=record.generation,
            adopter_generation=organism.generation,
        )
    )
    return {"adopted": True, "strategy": record.to_dict(), "event": event}


@router.post("/memome/gossip", dependencies=write_dependencies)
def gossip(payload: GossipRequest) -> dict[str, Any]:
    exchanged = 0
    for incoming in payload.strategies:
        before = control_state.store.get(control_state.store.strategy_id(incoming.name, incoming.source_code, incoming.descriptor))
        record = control_state.store.publish_fields(**incoming.model_dump())
        exchanged += int(before is None)
        _ = record
    return {
        "peer_node_id": payload.peer_node_id,
        "exchanged": exchanged,
        "influence": {record.name: control_state.store.influence_score(record.name) for record in control_state.store.query(limit=10_000)},
    }


@router.get("/memome/lineage")
def memome_lineage() -> dict[str, Any]:
    return {"edges": control_state.store.lineage()}


@router.post("/red-team/attack", dependencies=write_dependencies)
def red_team_attack(target_id: str, payload: AttackRequest) -> dict[str, Any]:
    target = control_state.get_organism(target_id)
    attacker = RedTeamOrganism(payload.attacker_id, payload.attack_power)
    result = attacker.attack(target)
    target.record_attack(result)
    outcome = "repelled" if result.detected else "success"
    event = control_state.emit(
        RedTeamAttackEvent(
            attacker_id=result.attacker_id,
            target_id=result.target_id,
            result=outcome,
            damage=result.damage,
        )
    )
    return {"result": asdict(result), "event": event, "target": target.to_state()}


@router.get("/tools")
def list_tools() -> dict[str, Any]:
    return {"items": [{"name": name, "description": description} for name, (_, description) in EmbodiedOrganism.TOOL_REGISTRY.items()]}


@router.post("/organisms/{organism_id}/tools/{tool_name}", dependencies=write_dependencies)
def use_tool(organism_id: str, tool_name: str, payload: ToolCallRequest) -> dict[str, Any]:
    organism = control_state.get_organism(organism_id)
    embodied = EmbodiedOrganism(organism_id, allowed_root=Path.cwd())
    try:
        result = embodied.use_tool(tool_name, **payload.kwargs)
    except (KeyError, PermissionError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    organism.fitness = max(organism.fitness, embodied.fitness)
    return {"tool": tool_name, "result": str(result)[:2000], "fitness": organism.fitness, "history": embodied.tool_history}


@router.post("/dsl/express", dependencies=write_dependencies)
def express_dsl(payload: DSLExpressRequest) -> dict[str, Any]:
    return {"source": control_state.dsl.express(payload.model_dump()), "vocabulary": list(control_state.dsl.vocabulary)}


@router.post("/dsl/parse", dependencies=write_dependencies)
def parse_dsl(payload: DSLParseRequest) -> dict[str, Any]:
    try:
        return {"intent": control_state.dsl.parse(payload.source)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/dsl/mutate", dependencies=write_dependencies)
def mutate_dsl() -> dict[str, Any]:
    control_state.dsl = control_state.dsl.mutate(random.Random())
    return {"vocabulary": list(control_state.dsl.vocabulary), "grammar_rules": list(control_state.dsl.grammar_rules)}


@router.get("/ancestry/{organism_id}")
def ancestry(organism_id: str) -> dict[str, Any]:
    organism = control_state.get_organism(organism_id)
    parent_ids = list(organism.parent_ids)
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    pending = list(parent_ids)
    while pending:
        ancestor_id = pending.pop(0)
        if ancestor_id in seen:
            continue
        seen.add(ancestor_id)
        ancestor = control_state.organisms.get(ancestor_id)
        if ancestor is None:
            chain.append({"organism_id": ancestor_id, "missing": True})
            continue
        chain.append({"organism_id": ancestor_id, "generation": ancestor.generation, "parent_ids": list(ancestor.parent_ids), "strategies": list(ancestor.learned_modules)})
        pending.extend(ancestor.parent_ids)
    return {"champion": organism.to_state(), "ancestors": chain, "strategy_edges": control_state.store.lineage()}


@router.post("/energy/measure", dependencies=write_dependencies)
def measure_energy(payload: EnergyMeasureRequest) -> dict[str, Any]:
    organism = control_state.get_organism(payload.organism_id)
    organism.energy = organism.energy or 100.0
    score = ThermodynamicFitness().measure(
        organism,
        lambda: (payload.quality, payload.operations, payload.memory_allocated),
        budget=payload.budget,
    )
    return {"score": asdict(score), "organism": organism.to_state()}


@router.get("/events")
def v2_events(limit: int = Query(default=100, ge=1, le=500)) -> dict[str, Any]:
    return {"items": control_state.events[-limit:], "count": min(limit, len(control_state.events))}
