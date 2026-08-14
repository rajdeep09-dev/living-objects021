"""Authenticated HTTP surface for BEAST v3 frontier experiments."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from evolution.archaeology import KnowledgeArchaeologist
from evolution.beast_v2 import EvolutionConstitution
from evolution.beast_v2_culture import FederatedMemome, Strategy
from evolution.benchmark_synth import BenchmarkSynthesizer
from evolution.consciousness import ConsciousnessMetrics
from evolution.diplomacy import DiplomacyProtocol, Ecosystem
from evolution.market import StrategyMarket
from evolution.quantum_genome import QuantumGenome
from evolution.recursive_improvement import (
    CulturalMonotonicityInvariant,
    FormalSafetyProof,
    PopulationViabilityInvariant,
)
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse
from production.api.v3.websocket import (
    BenchmarkSynthesizedEvent,
    ConsciousnessMeasuredEvent,
    DiplomaticExchangeEvent,
    MarketTradeEvent,
    StrategyResurrectedEvent,
)


class MarketRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    source_code: str = Field(min_length=1, max_length=20_000)
    descriptor: str = Field(min_length=1, max_length=256)
    effectiveness: float = Field(ge=0.0, le=1.0)
    author_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    generation: int = Field(default=0, ge=0)


class MarketBuyRequest(BaseModel):
    buyer_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")


class MarketBidRequest(MarketBuyRequest):
    amount: float = Field(gt=0.0, le=1_000_000)


class AuctionRequest(BaseModel):
    duration_generations: int = Field(default=3, ge=1, le=100)


class ArchaeologyRequest(BaseModel):
    target_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    cutoff_generation: int = Field(default=10_000, ge=0)


class EcosystemRequest(BaseModel):
    ecosystem_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    dsl_vocabulary: set[str] = Field(default_factory=set, max_length=128)
    novelty_archive: set[str] = Field(default_factory=set, max_length=10_000)


class ExchangeRequest(BaseModel):
    our_ecosystem_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    their_ecosystem_id: str = Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.-]+$")
    our_offer: list[str] = Field(default_factory=list, max_length=128)
    our_request: list[str] = Field(default_factory=list, max_length=128)


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=512)


class BenchmarkRequest(BaseModel):
    difficulty: float = Field(ge=0.0, le=1.0)


class CoEvolutionRequest(BaseModel):
    generations: int = Field(default=30, ge=1, le=1_000)
    solver_ids: list[str] = Field(default_factory=list, max_length=1_000)


class QuantumRequest(BaseModel):
    amplitudes: dict[str, float] = Field(min_length=1, max_length=128)
    seed: int = 0


class SpikingRequest(BaseModel):
    inputs: list[float] = Field(min_length=1, max_length=256)
    timesteps: int = Field(default=10, ge=1, le=1_000)


class ImprovementRequest(BaseModel):
    invariant: str = Field(default="population_viability", pattern=r"^(population_viability|cultural_monotonicity)$")
    witness_runs: int = Field(default=1_000, ge=1, le=1_000)


@dataclass
class _OrganismAdapter:
    object_id: str
    generation: int = 0
    alive: bool = True
    fitness: float = 0.0
    learned_strategies: dict[str, Strategy] = field(default_factory=dict)
    behavior_descriptors: dict[str, str] = field(default_factory=dict)
    predicted_fitness: float = 0.0
    token_wallet: Any = None

    def install_strategy(self, strategy: Strategy) -> bool:
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        self.predicted_fitness = self.behavior_quality()
        return True

    def behavior_quality(self) -> float:
        if not self.learned_strategies:
            return 0.0
        return sum(item.effectiveness for item in self.learned_strategies.values()) / len(self.learned_strategies)


@dataclass
class V3ControlState:
    memome: FederatedMemome = field(default_factory=lambda: FederatedMemome("api-v3"))
    market: StrategyMarket = field(default_factory=StrategyMarket)
    archaeologist: KnowledgeArchaeologist = field(default_factory=KnowledgeArchaeologist)
    diplomacy: DiplomacyProtocol = field(default_factory=DiplomacyProtocol)
    synthesizer: BenchmarkSynthesizer = field(default_factory=lambda: BenchmarkSynthesizer(seed=17))
    consciousness: ConsciousnessMetrics = field(default_factory=ConsciousnessMetrics)
    organisms: dict[str, _OrganismAdapter] = field(default_factory=dict)
    ecosystems: dict[str, Ecosystem] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.ecosystems["default"] = Ecosystem("default", self.memome, EvolutionConstitution(), set(), set())

    def organism(self, organism_id: str) -> _OrganismAdapter:
        return self.organisms.setdefault(organism_id, _OrganismAdapter(organism_id))

    def emit(self, event: Any) -> dict[str, Any]:
        payload = event.model_dump() if hasattr(event, "model_dump") else dict(event)
        self.events.append(payload)
        self.events = self.events[-500:]
        return payload


state = V3ControlState()
router = APIRouter(prefix="/v3", tags=["v3"])


@router.get("/market/listings")
def market_listings() -> dict[str, Any]:
    return {"items": [{"name": name, "seller_id": item.seller_id, "price": state.market.price(name), "adoption_count": item.adoption_count, "effectiveness": item.strategy.effectiveness} for name, item in state.market.listings.items()]}


@router.post("/market/listings", status_code=status.HTTP_201_CREATED)
def register_market_strategy(payload: MarketRegisterRequest) -> dict[str, Any]:
    strategy = state.memome.publish(name=payload.name, source_code=payload.source_code, descriptor=payload.descriptor, effectiveness=payload.effectiveness, author_id=payload.author_id, generation=payload.generation)
    listing = state.market.register(strategy, payload.author_id)
    return {"name": strategy.name, "strategy_id": strategy.strategy_id, "price": state.market.price(strategy.name), "seller_id": listing.seller_id}


@router.post("/market/listings/{strategy_name}/buy")
def buy_market_strategy(strategy_name: str, payload: MarketBuyRequest) -> dict[str, Any]:
    buyer = state.organism(payload.buyer_id)
    listing = state.market.listings.get(strategy_name)
    if listing is None:
        raise HTTPException(status_code=404, detail="market listing not found")
    price = state.market.price(strategy_name)
    if not state.market.buy(buyer, strategy_name):
        raise HTTPException(status_code=409, detail="buyer cannot afford or install strategy")
    event = state.emit(MarketTradeEvent(strategy_name=strategy_name, buyer_id=payload.buyer_id, seller_id=listing.seller_id, price=price, adoption_count=listing.adoption_count))
    return {"purchased": True, "wallet_balance": buyer.token_wallet.balance, "event": event}


@router.post("/market/listings/{strategy_name}/bid")
def bid_market_strategy(strategy_name: str, payload: MarketBidRequest) -> dict[str, Any]:
    if not state.market.bid(state.organism(payload.buyer_id), strategy_name, payload.amount):
        raise HTTPException(status_code=409, detail="bid rejected")
    return {"accepted": True, "strategy_name": strategy_name, "amount": payload.amount}


@router.post("/market/listings/{strategy_name}/auction")
def auction_market_strategy(strategy_name: str, payload: AuctionRequest) -> dict[str, Any]:
    winner = state.market.auction(strategy_name, payload.duration_generations)
    if not winner:
        raise HTTPException(status_code=409, detail="auction has no valid bids")
    return {"winner_id": winner, "strategy_name": strategy_name}


@router.post("/ecosystems", status_code=status.HTTP_201_CREATED)
def create_ecosystem(payload: EcosystemRequest) -> dict[str, Any]:
    if payload.ecosystem_id in state.ecosystems:
        raise HTTPException(status_code=409, detail="ecosystem already exists")
    state.ecosystems[payload.ecosystem_id] = Ecosystem(payload.ecosystem_id, FederatedMemome(payload.ecosystem_id), EvolutionConstitution(), set(payload.dsl_vocabulary), set(payload.novelty_archive))
    return {"ecosystem_id": payload.ecosystem_id}


@router.post("/diplomacy/proposals", status_code=status.HTTP_201_CREATED)
def propose_diplomatic_exchange(payload: ExchangeRequest) -> dict[str, Any]:
    try:
        proposal = state.diplomacy.propose_exchange(state.ecosystems[payload.our_ecosystem_id], state.ecosystems[payload.their_ecosystem_id], payload.our_offer, payload.our_request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ecosystem not found") from exc
    return asdict(proposal)


@router.post("/diplomacy/proposals/{proposal_id}/accept")
def accept_diplomatic_exchange(proposal_id: str) -> dict[str, Any]:
    proposal = state.diplomacy.proposals.get(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    result = state.diplomacy.accept(proposal)
    event = state.emit(DiplomaticExchangeEvent(proposal_id=result.proposal_id, accepted=result.accepted, transferred_to_ours=list(result.transferred_to_ours), transferred_to_theirs=list(result.transferred_to_theirs)))
    return {**asdict(result), "event": event}


@router.post("/diplomacy/proposals/{proposal_id}/reject")
def reject_diplomatic_exchange(proposal_id: str, payload: RejectRequest) -> dict[str, Any]:
    proposal = state.diplomacy.proposals.get(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="proposal not found")
    state.diplomacy.reject(proposal, payload.reason)
    return {"rejected": True, "proposal_id": proposal_id, "reason": payload.reason}


@router.get("/diplomacy/compatibility")
def ecosystem_compatibility(our_ecosystem_id: str, their_ecosystem_id: str) -> dict[str, Any]:
    try:
        report = state.diplomacy.assess_compatibility(state.ecosystems[our_ecosystem_id], state.ecosystems[their_ecosystem_id])
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ecosystem not found") from exc
    return asdict(report)


@router.post("/archaeology/pass")
def archaeology_pass(payload: ArchaeologyRequest) -> dict[str, Any]:
    target = state.organism(payload.target_id)
    extinct = state.archaeologist.excavate(state.memome, payload.cutoff_generation)
    relevance: dict[str, float] = {}
    resurrected: list[str] = []
    for item in extinct:
        score = state.archaeologist.evaluate_relevance(item, [target])
        relevance[item.name] = score
        if score >= state.archaeologist.relevance_threshold and state.archaeologist.resurrect(item, target):
            resurrected.append(item.name)
            state.emit(StrategyResurrectedEvent(strategy_name=item.name, target_id=payload.target_id, relevance=score))
    return {"excavated": len(extinct), "resurrected": len(resurrected), "relevance": relevance, "resurrected_names": resurrected}


@router.post("/benchmarks/synthesize")
def synthesize_benchmark(payload: BenchmarkRequest) -> dict[str, Any]:
    benchmark = state.synthesizer.synthesize_benchmark(payload.difficulty)
    event = state.emit(BenchmarkSynthesizedEvent(benchmark_id=benchmark.benchmark_id, generation=benchmark.generation, difficulty=benchmark.difficulty))
    return {**asdict(benchmark), "event": event}


@router.post("/benchmarks/co-evolve")
def co_evolve_benchmarks(payload: CoEvolutionRequest) -> dict[str, Any]:
    solvers = [state.organism(item) for item in payload.solver_ids] or list(state.organisms.values())
    history = state.synthesizer.co_evolve([state.synthesizer], solvers, payload.generations)
    return asdict(history)


@router.post("/quantum/measure")
def measure_quantum_genome(payload: QuantumRequest) -> dict[str, Any]:
    genome = QuantumGenome({key: complex(value, 0) for key, value in payload.amplitudes.items()})
    return {"genome": genome.measure(random.Random(payload.seed)).to_dict(), "history": genome.measurement_history}


@router.post("/quantum/interfere")
def interfere_quantum_genomes(left: QuantumRequest, right: QuantumRequest) -> dict[str, Any]:
    first = QuantumGenome({key: complex(value, 0) for key, value in left.amplitudes.items()})
    second = QuantumGenome({key: complex(value, 0) for key, value in right.amplitudes.items()})
    return {"amplitudes": {key: [value.real, value.imag] for key, value in first.interfere(second).amplitudes.items()}}


@router.post("/spiking/forward")
def spiking_forward(payload: SpikingRequest) -> dict[str, Any]:
    neurons = [LIFNeuron(index) for index in range(len(payload.inputs))]
    synapses = [Synapse(index, index + 1, 0.25) for index in range(len(neurons) - 1)]
    genome = SpikingStrategyGenome(neurons, synapses)
    spikes = genome.forward(payload.inputs, payload.timesteps)
    return {"spikes": spikes, "energy_cost": genome.energy_cost, "synapse_count": len(genome.synapses)}


@router.post("/improvement/prove")
def prove_improvement(payload: ImprovementRequest) -> dict[str, Any]:
    invariant = PopulationViabilityInvariant() if payload.invariant == "population_viability" else CulturalMonotonicityInvariant()
    class _ProofEcosystem:
        organisms = [type("Alive", (), {"alive": True})(), type("Alive", (), {"alive": True})()]
        memome = state.memome

        def step(self, _: random.Random) -> None:
            return None

    proof = FormalSafetyProof(invariant, lambda ecosystem: None, witness_runs=payload.witness_runs).verify(_ProofEcosystem())
    return asdict(proof)


@router.get("/consciousness/{organism_id}")
def measure_consciousness(organism_id: str) -> dict[str, Any]:
    organism = state.organisms.get(organism_id)
    if organism is None:
        raise HTTPException(status_code=404, detail="v3 organism not found")
    metrics = {
        "organism_id": organism_id,
        "phi": state.consciousness.integrated_information(organism),
        "self_model_accuracy": state.consciousness.self_model_accuracy(organism),
        "workspace_breadth": state.consciousness.global_workspace_breadth(organism),
    }
    metrics["composite"] = state.consciousness.composite_awareness_score(organism)
    state.emit(ConsciousnessMeasuredEvent(**metrics))
    return metrics


__all__ = ["V3ControlState", "router", "state"]
