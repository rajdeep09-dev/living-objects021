"""Authenticated BEAST v4 control-plane routes.

The route state is intentionally process-local for research and development. The
public API keeps the state boundary explicit so it can be replaced by durable,
transactional storage without changing the frontier contracts.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from evolution.archaeology import KnowledgeArchaeologist
from evolution.epistemic import EpistemicState, UncertaintyAwareEvolution
from evolution.immunity import CivilizationImmunity
from evolution.lamarckian import Strategy
from evolution.memory_palace import MemoryPalace
from evolution.morphogenetic_ai import MorphogeneticProgram
from evolution.physics import (
    CausalityLaw,
    ConservationLaw,
    EntropyLaw,
    FormalSafetyProof,
    InformationLaw,
    ParallelUniverse,
)
from evolution.spiking import LIFNeuron
from evolution.substrate import SubstrateExporter
from evolution.temporal import TemporalRevisionEngine
from evolution.tournament import EvolutionaryTournament
from evolution.turing import OrganismTuringMachine
from evolution.writing_system import Context, StrategyIntent, WritingSystem
from production.api.v3.routes import state as v3_state
from production.api.v4.websocket import (
    AntibodyDonatedEvent,
    ComputationRunEvent,
    MemoryRecordedEvent,
    SubstrateExportedEvent,
    TemporalRevisionEvent,
    TournamentCompletedEvent,
    UniverseBranchedEvent,
    WritingEvolvedEvent,
)


class BranchRequest(BaseModel):
    law: str = Field(pattern=r"^(conservation_of_tokens|causality|entropy_gradient|information_limit)$")


class LawMutationRequest(BaseModel):
    universe_id: str = Field(min_length=1, max_length=96)
    name: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    invariant: str = Field(min_length=1, max_length=256)


class RevisionRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96)
    ancestor_id: str = Field(min_length=1, max_length=96)
    revised_strategy: str = Field(min_length=1, max_length=20_000)
    strategy_name: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")


class ApplyRevisionRequest(BaseModel):
    proposal_id: str = Field(min_length=1, max_length=96)


class ComputationRequest(BaseModel):
    input_tape: str = Field(default="_", max_length=256)
    step_limit: int = Field(default=10_000, ge=1, le=100_000)
    transition_table: dict[str, list[str]] = Field(default_factory=dict, max_length=2_000)


class ImmunityRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96)
    attack_pattern: str = Field(min_length=1, max_length=256)
    defense_strategy: str = Field(min_length=1, max_length=256)
    effectiveness: float = Field(ge=0.0, le=1.0)
    generation: int = Field(default=0, ge=0)


class EpistemicRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96)
    observation: float = Field(ge=0.0, le=1.0)
    learning_rate: float = Field(default=0.2, gt=0.0, le=1.0)


class MemoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    source_code: str = Field(min_length=1, max_length=20_000)
    descriptor: str = Field(min_length=1, max_length=256)
    effectiveness: float = Field(ge=0.0, le=1.0)
    author_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    generation: int = Field(default=0, ge=0)


class WritingRequest(BaseModel):
    action: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    parameters: dict[str, float] = Field(default_factory=dict, max_length=32)
    context: dict[str, str] = Field(default_factory=dict, max_length=32)


class TournamentRequest(BaseModel):
    generation: int = Field(default=0, ge=0)


class MorphogenesisRequest(BaseModel):
    steps: int = Field(default=10, ge=1, le=100)
    instructions: list[dict[str, Any]] = Field(default_factory=list, max_length=128)


class SubstrateRequest(BaseModel):
    organism_id: str = Field(min_length=1, max_length=96)
    substrate: str = Field(pattern=r"^(wasm|container|circuit)$")


@dataclass
class V4ControlState:
    universes: dict[str, ParallelUniverse] = field(default_factory=dict)
    temporal: TemporalRevisionEngine = field(default_factory=TemporalRevisionEngine)
    immunity: CivilizationImmunity = field(default_factory=CivilizationImmunity)
    epistemic: UncertaintyAwareEvolution = field(default_factory=UncertaintyAwareEvolution)
    memory: MemoryPalace = field(default_factory=MemoryPalace)
    archaeologist: KnowledgeArchaeologist = field(default_factory=KnowledgeArchaeologist)
    tournament: EvolutionaryTournament = field(default_factory=EvolutionaryTournament)
    writing: WritingSystem = field(default_factory=WritingSystem)
    substrate: SubstrateExporter = field(default_factory=SubstrateExporter)
    events: list[dict[str, Any]] = field(default_factory=list)
    epistemic_states: dict[str, EpistemicState] = field(default_factory=dict)
    revisions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.universes:
            origin = ParallelUniverse()
            self.universes["origin"] = origin

    def emit(self, event: Any) -> dict[str, Any]:
        payload = event.model_dump() if hasattr(event, "model_dump") else dict(event)
        self.events.append(payload)
        self.events = self.events[-500:]
        return payload


state = V4ControlState()
router = APIRouter(prefix="/v4", tags=["v4"])


def _adapter(organism_id: str) -> Any:
    return v3_state.organism(organism_id)


@router.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return {
        "universes": [universe.observe() for universe in state.universes.values()],
        "event_count": len(state.events),
        "memory": state.memory.snapshot(),
        "antibody_count": len(state.immunity.antibodies()),
        "writing_generation": state.writing.generation,
    }


@router.get("/universes")
def list_universes() -> dict[str, Any]:
    return {"items": [universe.observe() for universe in state.universes.values()]}


@router.post("/universes/{universe_id}/branch", status_code=status.HTTP_201_CREATED)
def branch_universe(universe_id: str, payload: BranchRequest) -> dict[str, Any]:
    parent = state.universes.get(universe_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="universe not found")
    laws = {
        "conservation_of_tokens": ConservationLaw,
        "causality": CausalityLaw,
        "entropy_gradient": EntropyLaw,
        "information_limit": InformationLaw,
    }
    child = parent.branch(laws[payload.law]())
    state.universes[child.universe_id] = child
    event = state.emit(UniverseBranchedEvent(parent_id=universe_id, child_id=child.universe_id, divergence_score=child.divergence_score, branch_generation=child.branch_generation))
    return {"universe": child.observe(), "event": event}


@router.post("/physics/mutations")
def mutate_physics(payload: LawMutationRequest) -> dict[str, Any]:
    universe = state.universes.get(payload.universe_id)
    if universe is None:
        raise HTTPException(status_code=404, detail="universe not found")
    law = type("EvolvingLaw", (), {"name": payload.name, "apply": lambda self, ecosystem, organisms: None})()
    proof = FormalSafetyProof(payload.invariant, True, {"source": "v4-api"})
    organism = _adapter("physics-architect")
    accepted = universe.physics.propose_law_mutation(organism, law, proof)
    return {"accepted": accepted, "fingerprint": universe.physics.fingerprint(), "history": universe.physics.mutation_history[-1:]}


@router.post("/temporal/proposals", status_code=status.HTTP_201_CREATED)
def propose_temporal_revision(payload: RevisionRequest) -> dict[str, Any]:
    proposal = state.temporal.propose_revision(_adapter(payload.organism_id), payload.ancestor_id, payload.revised_strategy, payload.strategy_name)
    state.revisions[proposal.proposal_id] = proposal
    return asdict(proposal)


@router.post("/temporal/apply")
def apply_temporal_revision(payload: ApplyRevisionRequest) -> dict[str, Any]:
    proposal = state.revisions.get(payload.proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="revision proposal not found")
    result = state.temporal.apply_revision(proposal)
    event = state.emit(TemporalRevisionEvent(proposal_id=result.proposal_id, applied=result.applied, affected_organisms=result.affected_organisms, net_fitness_change=result.net_fitness_change, paradox=result.paradox))
    return {**asdict(result), "event": event}


@router.post("/computation/run")
def run_computation(payload: ComputationRequest) -> dict[str, Any]:
    transitions: dict[tuple[str, str], tuple[str, str, str]] = {}
    for key, value in payload.transition_table.items():
        try:
            state_name, symbol = key.split("|", 1)
            new_state, write_symbol, direction = value
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="transition keys must be state|symbol and values must be [state, symbol, direction]")
        transitions[(state_name, symbol)] = (new_state, write_symbol, direction)
    machine = OrganismTuringMachine(transition_table=transitions)
    result = machine.run(payload.input_tape, payload.step_limit)
    event = state.emit(ComputationRunEvent(halted=result.halted, accepted=result.accepted, steps_used=result.steps_used, universality_score=machine.universality_score()))
    return {**asdict(result), "universality_score": machine.universality_score(), "kolmogorov_complexity": machine.kolmogorov_complexity(), "event": event}


@router.post("/immunity/antibodies", status_code=status.HTTP_201_CREATED)
def donate_antibody(payload: ImmunityRequest) -> dict[str, Any]:
    antibody_id = state.immunity.donate_defense(_adapter(payload.organism_id), payload.attack_pattern, payload.defense_strategy, payload.effectiveness, payload.generation)
    antibody = next(item for item in state.immunity.antibodies() if item["pattern"] == payload.attack_pattern)
    event = state.emit(AntibodyDonatedEvent(antibody_id=antibody_id, discovered_by=payload.organism_id, pattern=payload.attack_pattern, effectiveness=payload.effectiveness))
    return {"antibody_id": antibody_id, "antibody": antibody, "event": event}


@router.get("/immunity/antibodies")
def list_antibodies() -> dict[str, Any]:
    return {"items": state.immunity.antibodies()}


@router.post("/epistemic/update")
def update_epistemic(payload: EpistemicRequest) -> dict[str, Any]:
    epistemic = state.epistemic_states.setdefault(payload.organism_id, EpistemicState())
    epistemic.update_belief(payload.observation, payload.learning_rate)
    organism = _adapter(payload.organism_id)
    setattr(organism, "epistemic_state", epistemic)
    return {"organism_id": payload.organism_id, "belief": asdict(epistemic.fitness_belief), "confidence_interval": epistemic.confidence_interval(), "exploration_bonus": epistemic.exploration_bonus(), "protected": state.epistemic.should_protect(organism)}


@router.post("/memory/record", status_code=status.HTTP_201_CREATED)
def record_memory(payload: MemoryRequest) -> dict[str, Any]:
    strategy = v3_state.memome.publish(name=payload.name, source_code=payload.source_code, descriptor=payload.descriptor, effectiveness=payload.effectiveness, author_id=payload.author_id, generation=payload.generation)
    state.memory.add(strategy)
    event = state.emit(MemoryRecordedEvent(strategy_id=strategy.strategy_id, cluster_count=state.memory.cluster_count()))
    return {"strategy_id": strategy.strategy_id, "cluster_count": state.memory.cluster_count(), "event": event}


@router.get("/memory/snapshot")
def memory_snapshot() -> dict[str, Any]:
    return state.memory.snapshot()


@router.post("/writing/encode")
def encode_writing(payload: WritingRequest) -> dict[str, Any]:
    text = state.writing.write(StrategyIntent(payload.action, payload.parameters), Context(payload.context))
    return {"text": text, "decoded": asdict(state.writing.read(text)), "vocabulary_size": state.writing.vocabulary_size}


@router.post("/writing/evolve")
def evolve_writing() -> dict[str, Any]:
    state.writing = state.writing.evolve(random.SystemRandom())
    event = state.emit(WritingEvolvedEvent(generation=state.writing.generation, vocabulary_size=state.writing.vocabulary_size))
    return {"generation": state.writing.generation, "vocabulary_size": state.writing.vocabulary_size, "event": event}


@router.post("/tournaments/round-robin")
def run_tournament(payload: TournamentRequest) -> dict[str, Any]:
    result = state.tournament.round_robin(payload.generation)
    event = state.emit(TournamentCompletedEvent(generation=result.generation, matches=len(result.matches), attacker_wins=result.attacker_wins, defender_wins=result.defender_wins, draws=result.draws))
    return {**asdict(result), "event": event}


@router.post("/morphogenesis/develop")
def develop_morphogenesis(payload: MorphogenesisRequest) -> dict[str, Any]:
    program = MorphogeneticProgram(payload.instructions)
    genome = program.develop(LIFNeuron(0), payload.steps)
    return {"complexity": program.complexity(), "neuron_count": len(genome.neurons), "synapse_count": len(genome.synapses), "energy_cost": genome.energy_cost}


@router.post("/substrate/export")
def export_substrate(payload: SubstrateRequest) -> dict[str, Any]:
    organism = _adapter(payload.organism_id)
    if payload.substrate == "wasm":
        value = state.substrate.export_wasm(organism)
        size = len(value)
        payload_value: Any = {"bytes": size}
    elif payload.substrate == "container":
        value = state.substrate.export_container(organism)
        size = len(value.dockerfile)
        payload_value = asdict(value)
    else:
        value = state.substrate.export_circuit(organism)
        size = len(value.source)
        payload_value = asdict(value)
    event = state.emit(SubstrateExportedEvent(organism_id=payload.organism_id, substrate=payload.substrate, size=size))
    return {"substrate": payload.substrate, "artifact": payload_value, "fitness_breadth": state.substrate.fitness_substrate_breadth(organism), "event": event}


__all__ = ["V4ControlState", "router", "state"]
