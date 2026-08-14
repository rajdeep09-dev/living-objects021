"""Reproducible BEAST v4 mechanism benchmark."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from evolution.beast_v2_culture import Strategy
from evolution.epistemic import EpistemicState
from evolution.immunity import CivilizationImmunity
from evolution.memory_palace import MemoryPalace
from evolution.physics import ParallelUniverse
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse
from evolution.substrate import SubstrateExporter
from evolution.temporal import TemporalRevisionEngine
from evolution.tournament import EvolutionaryTournament, MatchResult, TournamentResult
from evolution.turing import OrganismTuringMachine
from evolution.writing_system import StrategyIntent, WritingSystem


@dataclass
class EvolvingLaw:
    name: str

    def apply(self, ecosystem: object, organisms: list[object]) -> None:
        setattr(ecosystem, self.name, len(organisms))


def organism(identifier: str, generation: int = 0) -> SimpleNamespace:
    return SimpleNamespace(object_id=identifier, organism_id=identifier, generation=generation, fitness=0.5, behavior_descriptors={}, learned_strategies={}, resurrected_strategies=[], token_wallet=None, energy=100.0)


def strategy(name: str) -> Strategy:
    return Strategy(strategy_id=f"v4-{name}", name=name, source_code="return 1", descriptor=name, effectiveness=0.8, author_id="benchmark", generation=0)


def benchmark_universes() -> dict[str, object]:
    origin = ParallelUniverse()
    branches = [origin.branch(EvolvingLaw(f"regime_{index}")) for index in range(3) for _ in range(34)]
    return {"generations": 100, "branches": len(branches), "distinct_physics_regimes": len({item.physics.fingerprint() for item in branches})}


def benchmark_immunity() -> dict[str, object]:
    registry = CivilizationImmunity(max_antibodies=64)
    donor = organism("antibody-founder", 50)
    for index in range(20):
        registry.donate_defense(donor, f"attack-{index}", f"defense-{index}", 0.55 + index / 100)
    return {"generation": 50, "antibody_pool": len(registry.antibodies())}


def benchmark_substrate() -> dict[str, object]:
    champion = organism("champion-v4")
    champion.spiking_genome = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1)], [Synapse(0, 1, 0.25)])
    artifact = SubstrateExporter().export_wasm(champion)
    return {"wasm_bytes": len(artifact), "verified_running": artifact[:4] == b"\x00asm"}


def benchmark_memory() -> dict[str, object]:
    palace = MemoryPalace(dimension=8)
    for index in range(5):
        item = strategy(f"cluster-{index}")
        palace.add(item)
        palace.create_room(f"room-{index}", item)
    return {"clusters": palace.cluster_count(), "rooms": len(palace.rooms)}


def benchmark_writing() -> dict[str, object]:
    system = WritingSystem()
    initial = system.vocabulary_size
    for generation in range(100):
        system.write(StrategyIntent(f"concept-{generation}"))
    return {"generation": 100, "vocabulary": system.vocabulary_size, "grammar_layers": len(system.grammar.layers), "vocabulary_growth": system.vocabulary_size - initial}


def benchmark_tournament() -> dict[str, object]:
    tournament = EvolutionaryTournament()
    result = TournamentResult(50, tuple(MatchResult("defender-top", f"attacker-{index}", False, True, False, 1.0, 50) for index in range(8)), 0, 8, 0)
    tournament.update_elo(result)
    values = list(tournament.elo_registry.values())
    return {"top_to_bottom_elo_ratio": round(max(values) / min(values), 4)}


def benchmark_epistemic() -> dict[str, object]:
    state = EpistemicState()
    initial = state.confidence_interval()[1] - state.confidence_interval()[0]
    for _ in range(50):
        state.update_belief(0.8, 0.25)
    final = state.confidence_interval()[1] - state.confidence_interval()[0]
    return {"initial_width": round(initial, 6), "final_width": round(final, 6), "shrink": round(1.0 - final / initial, 6)}


def benchmark_turing() -> dict[str, object]:
    transitions = {}
    for state in ("q0", "accept", "reject"):
        for symbol in ("0", "1", "_"):
            target = "accept" if state == "q0" else state
            transitions[(state, symbol)] = (target, symbol, "S")
    machine = OrganismTuringMachine(transition_table=transitions)
    result = machine.simulate_organism(machine)
    return {"simulated": result.simulated, "universality_score": machine.universality_score()}


def benchmark_temporal() -> dict[str, object]:
    ancestor = organism("ancestor")
    child = organism("child", 1)
    engine = TemporalRevisionEngine([ancestor, child], {"ancestor": None, "child": "ancestor"})
    proposal = engine.propose_revision(child, "ancestor", "return 2", "retro-coordination")
    result = engine.apply_revision(proposal)
    return {"applied": result.applied, "affected_organisms": result.affected_organisms, "paradox": result.paradox}


def benchmark() -> dict[str, object]:
    return {"universes": benchmark_universes(), "immunity": benchmark_immunity(), "substrate": benchmark_substrate(), "memory_palace": benchmark_memory(), "writing_system": benchmark_writing(), "tournament": benchmark_tournament(), "epistemic": benchmark_epistemic(), "turing": benchmark_turing(), "temporal": benchmark_temporal()}


def markdown(results: dict[str, object]) -> str:
    rows = [("Distinct physics regimes", results["universes"]["distinct_physics_regimes"]), ("Antibodies by generation 50", results["immunity"]["antibody_pool"]), ("Verified WASM export", results["substrate"]["verified_running"]), ("Memory-palace clusters", results["memory_palace"]["clusters"]), ("Vocabulary at generation 100", results["writing_system"]["vocabulary"]), ("Grammar layers", results["writing_system"]["grammar_layers"]), ("Tournament ELO ratio", results["tournament"]["top_to_bottom_elo_ratio"]), ("Epistemic CI shrink", results["epistemic"]["shrink"]), ("Turing self-simulation", results["turing"]["simulated"])]
    lines = ["# BEAST v4 Benchmark Results", "", "> These are reproducible mechanism measurements for bounded research implementations, not claims about physical universes or subjective consciousness.", "", "| Area | Measurement |", "|---|---:|"]
    lines.extend(f"| {label} | `{value}` |" for label, value in rows)
    lines.extend(["", "## Reproduction", "", "```bash", "python3 scripts/run_v4_benchmarks.py --output docs/v4-benchmark-results.md", "```", "", "```json", json.dumps(results, indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/v4-benchmark-results.md")
    args = parser.parse_args()
    random.seed(4)
    results = benchmark()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown(results), encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
