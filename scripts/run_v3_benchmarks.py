"""Run deterministic BEAST v3 proof benchmarks and write a Markdown report.

This is a research benchmark, not a production load test. It measures the
contracts implemented in the v3 modules and deliberately labels proxy metrics
as proxies rather than claims about sentience or quantum hardware.
"""
from __future__ import annotations

import random
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from evolution.archaeology import KnowledgeArchaeologist
from evolution.beast_v2 import EvolutionConstitution
from evolution.beast_v2_culture import FederatedMemome, Strategy
from evolution.benchmark_synth import BenchmarkSynthesizer
from evolution.consciousness import ConsciousnessMetrics
from evolution.diplomacy import DiplomacyProtocol, Ecosystem
from evolution.market import StrategyMarket, TokenWallet
from evolution.quantum_genome import QuantumGenome
from evolution.recursive_improvement import FormalSafetyProof, PopulationViabilityInvariant
from evolution.sandbox import IsolatedSandbox, ResourceLimits
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse


@dataclass
class Organism:
    object_id: str
    behavior_descriptors: dict[str, str] = field(default_factory=dict)
    learned_strategies: dict[str, Strategy] = field(default_factory=dict)
    fitness: float = 0.8
    predicted_fitness: float = 0.8
    token_wallet: TokenWallet = field(default_factory=TokenWallet)
    generation: int = 4
    resurrected_strategies: list[str] = field(default_factory=list)

    def install_strategy(self, strategy: Strategy) -> bool:
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        return True

    def behavior_quality(self) -> float:
        values = [strategy.effectiveness for strategy in self.learned_strategies.values()]
        return sum(values) / max(1, len(values))


@dataclass
class EcosystemFixture:
    organisms: list[object] = field(default_factory=lambda: [object(), object()])
    generation: int = 0

    def step(self, _: random.Random) -> None:
        self.generation += 1


def strategy(name: str, author: str, generation: int = 0, effectiveness: float = 0.8) -> Strategy:
    return Strategy(
        strategy_id=f"strategy-{name}", name=name, source_code=f"return {effectiveness}",
        descriptor=name, effectiveness=effectiveness, author_id=author, generation=generation,
    )


def run() -> str:
    rows: list[tuple[str, str, str]] = []
    proof = FormalSafetyProof(PopulationViabilityInvariant(), lambda _: None, witness_runs=1000).verify(EcosystemFixture())
    rows.append(("Recursive safety witnesses", str(proof.passed_runs), "1000 required; accepted" if proof.accepted else "rejected"))

    market = StrategyMarket(base_price=20)
    seller = Organism("seller")
    market.register(strategy("coordination", seller.object_id, effectiveness=0.82), seller.object_id)
    starting = market.price("coordination")
    for index in range(60):
        market.buy(Organism(f"buyer-{index}"), "coordination")
    rows.append(("Market trades", str(len(market.trade_history)), f"price {starting:.2f} → {market.price('coordination'):.2f}"))

    quantum = QuantumGenome({"mutation_rate:0.05": 0.35 + 0j, "mutation_rate:0.35": 0.94 + 0j})
    outcomes = {round(quantum.measure(random.Random(seed)).mutation_rate, 2) for seed in range(200)}
    rows.append(("Quantum measurement diversity", str(len(outcomes)), "same amplitudes, multiple classical collapses"))

    spiking = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1), LIFNeuron(2)], [Synapse(0, 1, 0.4)])
    spikes = spiking.forward([2.0, 0.0, 0.0], timesteps=5)
    energy = spiking.energy_cost
    spiking.hebbian_learn(1.0)
    rows.append(("Spiking strategy", str(len(spikes)), f"sparse energy cost {energy:.2f}"))

    with tempfile.TemporaryDirectory(prefix="beast-v3-bench-") as directory:
        memome = FederatedMemome(str(Path(directory) / "memome.sqlite"))
        memome.contribute(strategy("forgotten", "dead-parent", generation=0))
        target = Organism("archaeology-target")
        report = KnowledgeArchaeologist().run_archaeology_pass(memome, [target])
        rows.append(("Archaeology resurrection", str(report.resurrected), f"of {report.excavated} excavated"))

        right_memome = FederatedMemome(str(Path(directory) / "right.sqlite"))
        for index in range(5):
            memome.contribute(strategy(f"left-{index}", "left", generation=index))
            right_memome.contribute(strategy(f"right-{index}", "right", generation=index))
        left = Ecosystem("left", memome, EvolutionConstitution(), {"coop"}, {"left"})
        right = Ecosystem("right", right_memome, EvolutionConstitution(), {"coop"}, {"right"})
        protocol = DiplomacyProtocol()
        proposal = protocol.propose_exchange(left, right, [f"left-{i}" for i in range(5)], [f"right-{i}" for i in range(5)])
        exchange = protocol.accept(proposal)
        rows.append(("Cross-ecosystem exchange", str(len(exchange.transferred_to_ours) + len(exchange.transferred_to_theirs)), "strategies transferred"))
        memome.close()
        right_memome.close()

    synthesizer = BenchmarkSynthesizer(seed=9)
    solver = Organism("solver")
    solver.install_strategy(strategy("coordination", "solver", effectiveness=0.9))
    history = synthesizer.co_evolve([synthesizer], [solver], 30)
    rows.append(("Benchmark arms race", f"{history.difficulty_series[0]:.3f} → {history.difficulty_series[-1]:.3f}", "monotonic difficulty"))

    aware = Organism("aware")
    aware.install_strategy(strategy("one", "aware", effectiveness=0.7))
    aware.install_strategy(strategy("two", "aware", effectiveness=0.9))
    metrics = ConsciousnessMetrics()
    rows.append(("Awareness composite", f"{metrics.composite_awareness_score(aware):.3f}", "architectural proxy; not sentience"))

    sandbox = IsolatedSandbox(ResourceLimits(max_cpu_ms=500, max_memory_mb=32, max_output_bytes=4096))
    arithmetic = sandbox.run("2 + 2")
    escape = sandbox.run("().__class__.__bases__[0].__subclasses__()")
    rows.append(("Sandbox arithmetic", arithmetic.stdout.strip(), "normal expression"))
    rows.append(("Sandbox escape attempt", str(escape.exit_code), "blocked or rejected"))

    lines = ["# BEAST v3 Benchmark Results", "", "> Deterministic research-mode measurements generated by `scripts/run_v3_benchmarks.py`. Proxy metrics are not claims of sentience, quantum computation, or production load capacity.", "", "| Benchmark | Result | Interpretation |", "|---|---:|---|"]
    lines.extend(f"| {name} | {result} | {interpretation} |" for name, result, interpretation in rows)
    lines.extend(["", "## Reproduction", "", "```bash", "python3 scripts/run_v3_benchmarks.py > docs/v3-benchmark-results.md", "```", "", "The sandbox benchmark intentionally exercises the same subprocess path used by the API worker. Deployment still requires a stronger OS/container boundary for hostile multi-tenant workloads."])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(run(), end="")
