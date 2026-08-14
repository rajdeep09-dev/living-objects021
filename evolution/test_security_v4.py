from __future__ import annotations

import concurrent.futures
import math
import os
from dataclasses import replace

import pytest

from evolution.archaeology import ExtinctStrategy, KnowledgeArchaeologist
from evolution.beast_v2_culture import Strategy
from evolution.consciousness import ConsciousnessMetrics
from evolution.diplomacy import DiplomacyProtocol, Ecosystem
from evolution.epistemic import EpistemicState
from evolution.lamarckian import LamarckianGenome
from evolution.market import StrategyMarket, TokenWallet
from evolution.quantum_genome import QuantumRNG
from evolution.sandbox import IsolatedSandbox, ResourceLimits
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse


class Dummy:
    def __init__(self, object_id: str = "dummy") -> None:
        self.object_id = object_id
        self.generation = 1
        self.learned_strategies: dict[str, object] = {}

    def install_strategy(self, strategy: object) -> bool:
        self.learned_strategies[str(getattr(strategy, "name", strategy))] = strategy
        return True

    def learn(self, _name: str, _source: str) -> bool:
        return True


def make_strategy(name: str, source: str = "return 1", effectiveness: float = 0.8) -> Strategy:
    return Strategy(f"id-{name}", name, source, name, effectiveness, "author", 0)


def test_sandbox_allows_safe_expression() -> None:
    result = IsolatedSandbox().run("1 + 2")
    assert result.ok and result.stdout.strip() == "3"


@pytest.mark.parametrize("code", ["import os", "open('x')", "eval('1')", "exec('pass')"])
def test_sandbox_blocks_dangerous_capabilities(code: str) -> None:
    result = IsolatedSandbox().run(code)
    assert not result.ok


def test_sandbox_times_out_and_returns_bounded_result() -> None:
    result = IsolatedSandbox(ResourceLimits(max_cpu_ms=50)).run("while True: pass", timeout_ms=50)
    assert result.timed_out or result.exit_code != 0


def test_sandbox_caps_output() -> None:
    result = IsolatedSandbox(ResourceLimits(max_output_bytes=32)).run("print('x' * 1000)")
    assert len(result.stdout) <= 32


def test_sandbox_does_not_leave_working_directory_artifacts() -> None:
    result = IsolatedSandbox().run("print('clean')")
    assert result.ok and "living-objects-sandbox" not in os.getcwd()


def test_wallet_rejects_negative_income() -> None:
    with pytest.raises(ValueError):
        TokenWallet().earn(-1, "invalid")


def test_wallet_rejects_negative_spend() -> None:
    with pytest.raises(ValueError):
        TokenWallet().spend(-1, "invalid")


def test_wallet_prevents_overspend() -> None:
    wallet = TokenWallet(1)
    assert not wallet.spend(2, "overspend") and wallet.net_worth() == 1


def test_wallet_concurrent_spending_is_atomic() -> None:
    wallet = TokenWallet(10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda _: wallet.spend(1, "race"), range(20)))
    assert sum(results) == 10 and wallet.net_worth() == 0


def test_market_failed_installation_refunds_buyer() -> None:
    market = StrategyMarket(base_price=5)
    seller = Dummy("seller")
    buyer = Dummy("buyer")
    buyer.install_strategy = lambda _strategy: False
    market.register(make_strategy("safe"), seller.object_id)
    before = market.wallet_for(buyer).net_worth()
    assert not market.buy(buyer, "safe")
    assert market.wallet_for(buyer).net_worth() == before


def test_market_rejects_missing_listing_and_invalid_bid() -> None:
    market = StrategyMarket()
    bidder = Dummy("bidder")
    assert not market.buy(bidder, "missing") and not market.bid(bidder, "missing", 0)


def test_diplomacy_rejects_self_exchange() -> None:
    memome = __import__("evolution.beast_v2_culture", fromlist=["FederatedMemome"]).FederatedMemome("same")
    eco = Ecosystem("same", memome)
    with pytest.raises(ValueError):
        DiplomacyProtocol("secret").propose_exchange(eco, eco, [], [])
    memome.close()


def test_diplomacy_proposals_are_signed() -> None:
    from evolution.beast_v2_culture import FederatedMemome

    left, right = FederatedMemome("left"), FederatedMemome("right")
    left.contribute(make_strategy("offer"))
    protocol = DiplomacyProtocol("secret")
    proposal = protocol.propose_exchange(Ecosystem("left", left), Ecosystem("right", right), ["offer"], [])
    assert proposal.signature and proposal.nonce and proposal.expires_at > proposal.created_at
    left.close(); right.close()


def test_diplomacy_tampering_is_rejected() -> None:
    from evolution.beast_v2_culture import FederatedMemome

    left, right = FederatedMemome("left-t"), FederatedMemome("right-t")
    left.contribute(make_strategy("offer"))
    protocol = DiplomacyProtocol("secret")
    proposal = protocol.propose_exchange(Ecosystem("left-t", left), Ecosystem("right-t", right), ["offer"], [])
    tampered = replace(proposal, our_offer=("changed",))
    assert not protocol.accept(tampered).accepted
    left.close(); right.close()


def test_diplomacy_replay_is_rejected_after_first_acceptance() -> None:
    from evolution.beast_v2_culture import FederatedMemome

    left, right = FederatedMemome("left-r"), FederatedMemome("right-r")
    left.contribute(make_strategy("offer"))
    protocol = DiplomacyProtocol("secret")
    proposal = protocol.propose_exchange(Ecosystem("left-r", left), Ecosystem("right-r", right), ["offer"], [])
    assert protocol.accept(proposal).accepted
    assert not protocol.accept(proposal).accepted
    left.close(); right.close()


def test_quantum_rng_uniform_is_bounded() -> None:
    rng = QuantumRNG()
    assert all(0 <= rng.uniform() < 1 for _ in range(20))


def test_quantum_rng_choice_returns_member() -> None:
    values = ["a", "b", "c"]
    assert QuantumRNG().choice(values) in values


def test_quantum_rng_gauss_is_finite() -> None:
    assert math.isfinite(QuantumRNG().gauss())


def test_spiking_nan_inputs_remain_finite() -> None:
    genome = SpikingStrategyGenome([LIFNeuron(0, float("nan"))], [])
    genome.forward([float("nan")], timesteps=2)
    assert math.isfinite(genome.neurons[0].potential)


def test_spiking_overflow_inputs_are_clamped() -> None:
    genome = SpikingStrategyGenome([LIFNeuron(0)], [Synapse(0, 0, 10**100)])
    genome.forward([10**100], timesteps=1)
    assert abs(genome.neurons[0].potential) <= 1_000_000


def test_archaeology_rejects_unsafe_source_before_install() -> None:
    archaeologist = KnowledgeArchaeologist()
    target = Dummy("target")
    extinct = ExtinctStrategy(make_strategy("unsafe", "import os\nos.system('id')"), 0)
    assert not archaeologist.resurrect(extinct, target)
    assert not target.learned_strategies


def test_archaeology_accepts_valid_expression_source() -> None:
    archaeologist = KnowledgeArchaeologist()
    target = Dummy("target")
    extinct = ExtinctStrategy(make_strategy("safe", "return 1"), 0)
    assert archaeologist.resurrect(extinct, target)


def test_consciousness_phi_is_normalized_for_large_input() -> None:
    organism = Dummy("aware")
    organism.learned_strategies = {str(i): make_strategy(str(i), effectiveness=1.0) for i in range(100)}
    phi = ConsciousnessMetrics().integrated_information(organism)
    assert 0 <= phi <= 1


def test_epistemic_interval_rejects_invalid_alpha() -> None:
    with pytest.raises(ValueError):
        EpistemicState().confidence_interval(1.0)


def test_lamarckian_genome_mutation_produces_bounded_child_rate() -> None:
    genome = LamarckianGenome(mutation_rate=2.0)
    child = genome.mutate(__import__("random").Random(4))
    assert 0.01 <= child.mutation_rate <= 0.45
