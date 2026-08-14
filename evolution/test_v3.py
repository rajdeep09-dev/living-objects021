from __future__ import annotations

import random
from dataclasses import dataclass, field

from evolution.archaeology import KnowledgeArchaeologist
from evolution.beast_v2 import EvolutionConstitution
from evolution.beast_v2_culture import FederatedMemome, Strategy
from evolution.benchmark_synth import BenchmarkSynthesizer
from evolution.consciousness import ConsciousnessMetrics
from evolution.diplomacy import DiplomacyProtocol, Ecosystem
from evolution.lamarckian import LamarckianGenome
from evolution.market import StrategyMarket, TokenWallet
from evolution.quantum_genome import QuantumGenome
from evolution.recursive_improvement import (
    CulturalMonotonicityInvariant,
    FormalSafetyProof,
    PopulationViabilityInvariant,
    RecursiveImprover,
)
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse


@dataclass
class DummyEcosystem:
    organisms: list[object] = field(default_factory=lambda: [object(), object()])
    generation: int = 0
    memome: object = field(default_factory=lambda: type("Memome", (), {"strategies": lambda self: []})())

    def step(self, rng: random.Random) -> None:
        self.generation += 1


@dataclass
class FakeOrganism:
    object_id: str
    behavior_descriptors: dict[str, str] = field(default_factory=dict)
    learned_strategies: dict[str, Strategy] = field(default_factory=dict)
    fitness: float = 0.8
    predicted_fitness: float = 0.8
    token_wallet: TokenWallet | None = None
    generation: int = 4
    resurrected_strategies: list[str] = field(default_factory=list)

    def install_strategy(self, strategy: Strategy) -> bool:
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        return True

    def behavior_quality(self) -> float:
        return sum(strategy.effectiveness for strategy in self.learned_strategies.values()) / max(1, len(self.learned_strategies))


def make_strategy(name: str, author: str, generation: int = 0, effectiveness: float = 0.8) -> Strategy:
    return Strategy(
        strategy_id=f"strategy-{name}",
        name=name,
        source_code=f"def action_{name}(self):\n    return {effectiveness}",
        descriptor=name,
        effectiveness=effectiveness,
        author_id=author,
        generation=generation,
    )


def test_recursive_improvement_requires_and_proves_1000_witnesses() -> None:
    proof = FormalSafetyProof(PopulationViabilityInvariant(), lambda ecosystem: None, witness_runs=1000).verify(DummyEcosystem())
    assert proof.accepted
    assert proof.passed_runs == 1000
    assert RecursiveImprover((PopulationViabilityInvariant(),)).improve(DummyEcosystem(), lambda ecosystem: None, witness_runs=1000)


def test_recursive_improvement_rejects_unsafe_candidate_source() -> None:
    proof = FormalSafetyProof(PopulationViabilityInvariant(), "import os\nos.system('id')", witness_runs=1000).verify(DummyEcosystem())
    assert not proof.accepted
    assert proof.passed_runs == 0


def test_market_price_falls_with_adoption_and_transfers_tokens() -> None:
    market = StrategyMarket(base_price=20)
    seller = FakeOrganism("seller")
    buyer = FakeOrganism("buyer")
    strategy = make_strategy("coordination", seller.object_id)
    market.register(strategy, seller.object_id)
    first_price = market.price(strategy.name)
    assert market.buy(buyer, strategy.name)
    assert market.price(strategy.name) < first_price
    assert buyer.token_wallet is not None and buyer.token_wallet.balance < 100
    assert market.wallets[seller.object_id].balance > 100


def test_market_sealed_auction_selects_highest_bidder() -> None:
    market = StrategyMarket(base_price=5)
    seller = FakeOrganism("seller")
    low = FakeOrganism("low")
    high = FakeOrganism("high")
    market.register(make_strategy("auctionable", seller.object_id), seller.object_id)
    assert market.bid(low, "auctionable", 3)
    assert market.bid(high, "auctionable", 8)
    assert market.auction("auctionable", duration_generations=3) == high.object_id


def test_quantum_measurement_collapses_and_entanglement_correlates() -> None:
    genome = QuantumGenome({"mutation_rate:0.05": 0.2 + 0j, "mutation_rate:0.35": 0.98 + 0j})
    measured = [genome.measure(random.Random(seed)).mutation_rate for seed in range(100)]
    assert set(measured) <= {0.05, 0.35}
    left, right = QuantumGenome({"low": 1 + 0j}), QuantumGenome({"high": 1 + 0j})
    entangled_left, entangled_right = left.entangle(right)
    assert entangled_left.measure(random.Random(1)).mutation_rate == entangled_right.measure(random.Random(2)).mutation_rate


def test_interference_combines_amplitudes_and_returns_genome() -> None:
    result = QuantumGenome({"low": 0.5 + 0j}).interfere(QuantumGenome({"low": 0.5 + 0j, "high": 0.5 + 0j}))
    assert result.amplitudes["low"] == 1 + 0j
    assert isinstance(result.measure(random.Random(0)), LamarckianGenome)


def test_spiking_strategy_fires_mutates_and_learns() -> None:
    genome = SpikingStrategyGenome(
        neurons=[LIFNeuron(0), LIFNeuron(1), LIFNeuron(2)],
        synapses=[Synapse(0, 1, 0.4)],
    )
    fired = genome.forward([2.0, 0.0, 0.0], timesteps=3)
    assert 0 in fired
    weight_before = genome.synapses[0].weight
    genome.hebbian_learn(1.0)
    assert genome.synapses[0].weight >= weight_before
    assert len(genome.mutate_topology(random.Random(4)).neurons) == 3


def test_archaeology_excavates_and_resurrects_extinct_strategy() -> None:
    memome = FederatedMemome("archaeology-test")
    memome.contribute(make_strategy("forgotten", "dead-parent", generation=0))
    target = FakeOrganism("new-organism", generation=4)
    report = KnowledgeArchaeologist().run_archaeology_pass(memome, [target])
    assert report.excavated == 1
    assert report.resurrected == 1
    assert "forgotten" in target.resurrected_strategies
    memome.close()


def test_diplomacy_transfers_five_strategies_between_ecosystems() -> None:
    left_memome, right_memome = FederatedMemome("left-test"), FederatedMemome("right-test")
    for index in range(5):
        left_memome.contribute(make_strategy(f"left_{index}", "left", generation=index))
        right_memome.contribute(make_strategy(f"right_{index}", "right", generation=index))
    left = Ecosystem("left", left_memome, EvolutionConstitution(), {"coop"}, {"left"})
    right = Ecosystem("right", right_memome, EvolutionConstitution(), {"coop"}, {"right"})
    protocol = DiplomacyProtocol()
    proposal = protocol.propose_exchange(left, right, [f"left_{i}" for i in range(5)], [f"right_{i}" for i in range(5)])
    result = protocol.accept(proposal)
    assert result.accepted
    assert len(result.transferred_to_ours) == 5
    assert len(result.transferred_to_theirs) == 5
    assert len(right_memome.strategies()) == 10
    left_memome.close()
    right_memome.close()


def test_benchmark_synthesis_makes_difficulty_open_ended_over_30_generations() -> None:
    synthesizer = BenchmarkSynthesizer(seed=9)
    solver = FakeOrganism("solver", {"s": "coordination"})
    solver.install_strategy(make_strategy("coordination", "solver", effectiveness=0.9))
    history = synthesizer.co_evolve([synthesizer], [solver], 30)
    assert len(history.benchmarks) == 30
    assert all(left < right for left, right in zip(history.difficulty_series, history.difficulty_series[1:]))
    assert history.difficulty_series[-1] > history.difficulty_series[0]


def test_consciousness_metrics_are_bounded_and_nonzero_for_integrated_agent() -> None:
    organism = FakeOrganism("aware")
    organism.install_strategy(make_strategy("one", "aware", effectiveness=0.7))
    organism.install_strategy(make_strategy("two", "aware", effectiveness=0.9))
    metrics = ConsciousnessMetrics()
    assert 0 < metrics.integrated_information(organism) <= 1
    assert 0 < metrics.self_model_accuracy(organism) <= 1
    assert 0 < metrics.global_workspace_breadth(organism) <= 1
    assert 0 < metrics.composite_awareness_score(organism) <= 1
