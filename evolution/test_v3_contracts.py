from __future__ import annotations

import random

import pytest

from evolution.beast_v2_culture import Strategy
from evolution.benchmark_synth import BenchmarkSynthesizer
from evolution.consciousness import ConsciousnessMetrics
from evolution.market import StrategyMarket, TokenWallet
from evolution.quantum_genome import QuantumGenome
from evolution.recursive_improvement import FormalSafetyProof, PopulationViabilityInvariant
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse


class Organism:
    def __init__(self, object_id: str = "organism") -> None:
        self.object_id = object_id
        self.learned_strategies: dict[str, Strategy] = {}
        self.behavior_descriptors: dict[str, str] = {}
        self.token_wallet: TokenWallet | None = None
        self.fitness = 0.8
        self.predicted_fitness = 0.8

    def install_strategy(self, strategy: Strategy) -> bool:
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        return True

    def behavior_quality(self) -> float:
        values = [item.effectiveness for item in self.learned_strategies.values()]
        return sum(values) / max(1, len(values))


def make_strategy(name: str = "strategy", effectiveness: float = 0.8) -> Strategy:
    return Strategy(
        strategy_id=f"id-{name}", name=name, source_code="return 1", descriptor=name,
        effectiveness=effectiveness, author_id="author", generation=0,
    )


@pytest.mark.parametrize("amount", [0.0, 1.0, 2.5, 10.0, 99.0])
def test_wallet_earn_accepts_non_negative_amounts(amount: float) -> None:
    wallet = TokenWallet()
    wallet.earn(amount, "test")
    assert wallet.balance == pytest.approx(100.0 + amount)
    assert wallet.income_history[-1].amount == amount


@pytest.mark.parametrize("amount", [0.0, 0.5, 1.0, 10.0, 100.0])
def test_wallet_spend_accepts_affordable_amounts(amount: float) -> None:
    wallet = TokenWallet()
    assert wallet.spend(amount, "test")
    assert wallet.balance == pytest.approx(100.0 - amount)
    assert wallet.expense_history[-1].reason == "test"


@pytest.mark.parametrize("amount", [100.01, 1000.0])
def test_wallet_rejects_overspending(amount: float) -> None:
    wallet = TokenWallet()
    assert not wallet.spend(amount, "too-much")
    assert wallet.balance == 100.0
    assert wallet.expense_history == []


@pytest.mark.parametrize("amount", [-0.01, -1.0])
def test_wallet_rejects_negative_earning(amount: float) -> None:
    with pytest.raises(ValueError):
        TokenWallet().earn(amount, "invalid")


@pytest.mark.parametrize("effectiveness", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_market_price_is_positive_and_bounded(effectiveness: float) -> None:
    market = StrategyMarket(base_price=20)
    market.register(make_strategy(f"price-{effectiveness}", effectiveness), "seller")
    price = market.price(f"price-{effectiveness}")
    assert price >= 0.01
    assert price <= 40.0


def test_market_unknown_price_raises_key_error() -> None:
    with pytest.raises(KeyError):
        StrategyMarket().price("missing")


@pytest.mark.parametrize("strategy_name", ["missing", "not-listed", "unknown"])
def test_market_unknown_purchase_is_rejected(strategy_name: str) -> None:
    assert not StrategyMarket().buy(Organism(), strategy_name)


@pytest.mark.parametrize("amount", [-1.0, 0.0])
def test_market_non_positive_bid_is_rejected(amount: float) -> None:
    market = StrategyMarket()
    market.register(make_strategy("bid"), "seller")
    assert not market.bid(Organism(), "bid", amount)


def test_market_unknown_auction_is_empty() -> None:
    assert StrategyMarket().auction("missing") == ""


def test_market_auction_rejects_non_positive_duration() -> None:
    market = StrategyMarket()
    market.register(make_strategy("duration"), "seller")
    bidder = Organism("bidder")
    assert market.bid(bidder, "duration", 5)
    assert market.auction("duration", 0) == ""


def test_market_replacing_a_bid_refunds_the_previous_escrow() -> None:
    market = StrategyMarket()
    market.register(make_strategy("replace"), "seller")
    bidder = Organism("bidder")
    assert market.bid(bidder, "replace", 10)
    assert market.bid(bidder, "replace", 20)
    assert bidder.token_wallet is not None
    assert bidder.token_wallet.balance == pytest.approx(80.0)


def test_market_auction_refunds_losing_bidders() -> None:
    market = StrategyMarket()
    market.register(make_strategy("auction"), "seller")
    low, high = Organism("low"), Organism("high")
    assert market.bid(low, "auction", 10)
    assert market.bid(high, "auction", 20)
    assert market.auction("auction") == "high"
    assert low.token_wallet is not None and low.token_wallet.balance == pytest.approx(100.0)


@pytest.mark.parametrize("state", ["low", "high", "mutation_rate:0.1", "curiosity:0.9", "cooperation:0.2"])
def test_quantum_measurement_returns_classical_genome(state: str) -> None:
    genome = QuantumGenome({state: 1 + 0j})
    measured = genome.measure(random.Random(2))
    assert measured is not None
    assert genome.measurement_history == [state]


@pytest.mark.parametrize("amplitudes", [{}, {"zero": 0j}])
def test_quantum_zero_probability_state_is_rejected(amplitudes: dict[str, complex]) -> None:
    with pytest.raises(ValueError):
        QuantumGenome(amplitudes).measure(random.Random(0))


@pytest.mark.parametrize("left_state,right_state", [("low", "high"), ("a", "b")])
def test_quantum_interference_preserves_union_of_states(left_state: str, right_state: str) -> None:
    result = QuantumGenome({left_state: 1 + 0j}).interfere(QuantumGenome({right_state: 1 + 0j}))
    assert set(result.amplitudes) == {left_state, right_state}


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_quantum_entanglement_reuses_the_same_collapsed_state(seed: int) -> None:
    left, right = QuantumGenome({"low": 1 + 0j}), QuantumGenome({"high": 1 + 0j})
    correlated_left, correlated_right = left.entangle(right)
    assert correlated_left.measure(random.Random(seed)).mutation_rate == correlated_right.measure(random.Random(seed + 100)).mutation_rate


@pytest.mark.parametrize("timesteps", [1, 2, 3, 5, 10])
def test_spiking_forward_accepts_positive_timesteps(timesteps: int) -> None:
    genome = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1)], [Synapse(0, 1, 0.4)])
    fired = genome.forward([2.0, 0.0], timesteps=timesteps)
    assert genome.last_spike_pattern == fired
    assert all(item in {0, 1} for item in fired)


@pytest.mark.parametrize("timesteps", [0, -1])
def test_spiking_forward_rejects_non_positive_timesteps(timesteps: int) -> None:
    with pytest.raises(ValueError):
        SpikingStrategyGenome([LIFNeuron(0)]).forward([1.0], timesteps=timesteps)


@pytest.mark.parametrize("reward", [-1.0, -0.5, 0.0, 0.5, 1.0])
def test_spiking_hebbian_learning_keeps_weights_in_safe_range(reward: float) -> None:
    genome = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1)], [Synapse(0, 1, 1.9)])
    genome.hebbian_learn(reward)
    assert -2.0 <= genome.synapses[0].weight <= 2.0


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_spiking_topology_mutation_preserves_neuron_count(seed: int) -> None:
    genome = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1), LIFNeuron(2)], [Synapse(0, 1, 0.4)])
    mutated = genome.mutate_topology(random.Random(seed))
    assert len(mutated.neurons) == len(genome.neurons)
    assert all(-2.0 <= synapse.weight <= 2.0 for synapse in mutated.synapses)


@pytest.mark.parametrize("difficulty", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_benchmark_synthesis_clamps_difficulty_to_unit_interval(difficulty: float) -> None:
    benchmark = BenchmarkSynthesizer(seed=1).synthesize_benchmark(difficulty)
    assert 0.0 <= benchmark.difficulty <= 1.0
    assert benchmark.generation == 1
    assert benchmark.challenge.startswith("descriptor:")


@pytest.mark.parametrize("metric_name", ["integrated_information", "self_model_accuracy", "global_workspace_breadth", "composite_awareness_score"])
def test_awareness_metrics_are_bounded(metric_name: str) -> None:
    organism = Organism()
    organism.install_strategy(make_strategy("awareness", 0.8))
    score = getattr(ConsciousnessMetrics(), metric_name)(organism)
    assert 0.0 <= score <= 1.0


@pytest.mark.parametrize("witness_runs", [1, 5, 10])
def test_safety_proof_reports_every_requested_witness(witness_runs: int) -> None:
    class Ecosystem:
        organisms = [object(), object()]

        def step(self, _: random.Random) -> None:
            return None

    proof = FormalSafetyProof(PopulationViabilityInvariant(), lambda _: None, witness_runs=witness_runs).verify(Ecosystem())
    assert proof.accepted
    assert proof.passed_runs == witness_runs


def test_safety_proof_rejects_non_positive_witness_count() -> None:
    with pytest.raises(ValueError):
        FormalSafetyProof(PopulationViabilityInvariant(), lambda _: None, witness_runs=0).verify(type("Ecosystem", (), {})())


def test_safety_proof_source_candidate_requires_external_worker() -> None:
    proof = FormalSafetyProof(PopulationViabilityInvariant(), "x = 1", witness_runs=1).verify(type("Ecosystem", (), {})())
    assert not proof.accepted
    assert "external worker" in proof.failures[0]
