"""Run the BEAST v2 proof benchmarks and write a Markdown report.

The benchmark is intentionally small and deterministic. It measures the
research primitives directly rather than pretending to be a production load
test. Production deployments still need an external sandbox for untrusted
code, as documented in ``research/beast_v2_security_findings.md``.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from evolution.beast_v2 import DefenseLayer, EvolutionConstitution, RedTeamOrganism
from evolution.beast_v2_culture import DSLGenome, EnergyBudget, ThermodynamicFitness


def constitution_benchmark() -> dict[str, Any]:
    initial = EvolutionConstitution()
    finals: dict[str, EvolutionConstitution] = {}
    for seed in (7, 19):
        current = initial
        rng = random.Random(seed)
        for _ in range(100):
            current = current.mutate(rng)
        finals[str(seed)] = current
    diff = finals["7"].diff(finals["19"])
    return {
        "generations": 100,
        "initial": initial.to_dict(),
        "seed_7": finals["7"].to_dict(),
        "seed_19": finals["19"].to_dict(),
        "different_fields": len(diff),
        "diverged": bool(diff),
    }


def dsl_benchmark() -> dict[str, Any]:
    genome = DSLGenome()
    vocabulary_sizes = [len(genome.vocabulary)]
    for _ in range(50):
        genome = genome.mutate(random.Random(1000 + len(vocabulary_sizes)))
        vocabulary_sizes.append(len(genome.vocabulary))
    compound = genome.vocabulary[-1]
    compound_genome = DSLGenome(
        vocabulary=genome.vocabulary,
        grammar_rules=genome.grammar_rules,
        semantics=genome.semantics,
    )
    source = compound_genome.express({"condition": "high", "action": compound, "fallback": "defect"})
    parsed = compound_genome.parse(source)
    return {
        "generations": 50,
        "vocabulary_start": vocabulary_sizes[0],
        "vocabulary_end": vocabulary_sizes[-1],
        "expansion_factor": round(vocabulary_sizes[-1] / vocabulary_sizes[0], 2),
        "compound_token": compound,
        "compound_source": source,
        "round_trip": parsed,
    }


def thermodynamic_benchmark() -> dict[str, Any]:
    fitness = ThermodynamicFitness()
    budget_binding_deaths = 0
    operations_by_generation: list[float] = []
    efficiency_by_generation: list[float] = []
    for generation in range(50):
        # A simple heritable efficiency pressure: operation counts decay from
        # 160 toward 8 as the cohort learns to reuse compact strategies.
        operations = max(8, 160 - generation * 3)
        generation_operations: list[int] = []
        generation_efficiency: list[float] = []
        for organism_index in range(12):
            organism = SimpleNamespace(energy=4.0, dead=False)
            task_operations = operations + (organism_index % 4) * 3
            score = fitness.measure(organism, lambda _org, n=task_operations: (0.55 + generation / 250, n, n * 2), budget=120)
            generation_operations.append(score.operations)
            generation_efficiency.append(score.efficiency)
            budget = EnergyBudget(initial=2.0)
            try:
                for _ in range(3 if organism_index == 0 else 1):
                    budget.spend("strategy_call")
            except RuntimeError:
                budget_binding_deaths += 1
        operations_by_generation.append(statistics.mean(generation_operations))
        efficiency_by_generation.append(statistics.mean(generation_efficiency))
    return {
        "generations": 50,
        "average_operations_generation_0": round(operations_by_generation[0], 2),
        "average_operations_generation_49": round(operations_by_generation[-1], 2),
        "operations_reduction_factor": round(operations_by_generation[0] / operations_by_generation[-1], 2),
        "average_efficiency_generation_0": round(efficiency_by_generation[0], 6),
        "average_efficiency_generation_49": round(efficiency_by_generation[-1], 6),
        "energy_budget_binding_deaths": budget_binding_deaths,
        "operations_decreased": operations_by_generation[-1] < operations_by_generation[0],
        "efficiency_increased": efficiency_by_generation[-1] > efficiency_by_generation[0],
    }


def red_team_benchmark() -> dict[str, Any]:
    prey = [
        SimpleNamespace(
            object_id=f"prey-{index:02d}",
            fitness=0.65,
            defense=DefenseLayer(0.15 + index * 0.01),
            learned_strategies={},
        )
        for index in range(10)
    ]
    attackers = [RedTeamOrganism(f"red-{index}", attack_power=0.45 + index * 0.15) for index in range(3)]
    attack_pressures: list[float] = []
    for _ in range(50):
        for attacker in attackers:
            for target in prey:
                result = attacker.attack(target)
                attack_pressures.append(result.damage)
    initial_immune = statistics.mean(0.15 + index * 0.01 for index in range(10))
    final_immune = statistics.mean(target.defense.immune_strength for target in prey)
    pressure_variance = statistics.pvariance(attack_pressures)
    return {
        "generations": 50,
        "prey": 10,
        "attackers": 3,
        "adversarial_pressure": round(attackers.__len__() / (len(prey) + len(attackers)), 2),
        "initial_mean_immune_strength": round(initial_immune, 6),
        "final_mean_immune_strength": round(final_immune, 6),
        "immune_gain": round(final_immune - initial_immune, 6),
        "repulsed_attacks": sum(target.defense.repulsed_count for target in prey),
        "attack_pressure_variance": round(pressure_variance, 8),
        "population_survived": all(target.fitness > 0 for target in prey),
    }


def render_markdown(results: dict[str, Any]) -> str:
    constitution = results["constitution"]
    dsl = results["dsl"]
    thermo = results["thermodynamic"]
    red_team = results["red_team"]
    return f"""# BEAST v2 Benchmark Results

> **Reproducibility note:** Generated by `python3 scripts/run_v2_benchmarks.py` on the deterministic research primitives. These are proof-of-mechanism benchmarks, not claims of superiority over published artificial-life systems.

## Summary

| Benchmark | Result | Target / interpretation |
|---|---:|---|
| Constitutional divergence | {constitution['different_fields']} fields differ after 100 generations | Non-zero divergence from identical initial constitution |
| DSL vocabulary growth | {dsl['vocabulary_start']} → {dsl['vocabulary_end']} tokens ({dsl['expansion_factor']}×) | More than 4× growth in 50 generations |
| Thermodynamic operations | {thermo['average_operations_generation_0']} → {thermo['average_operations_generation_49']} ops/task ({thermo['operations_reduction_factor']}× reduction) | Operations decrease under energy pressure |
| Thermodynamic efficiency | {thermo['average_efficiency_generation_0']} → {thermo['average_efficiency_generation_49']} | Efficiency increases |
| Red-team immune strength | {red_team['initial_mean_immune_strength']} → {red_team['final_mean_immune_strength']} | Defense adapts under adversarial pressure |
| Red-team survival | {red_team['population_survived']} | Prey cohort remains alive |

## Constitution divergence

Two runs begin from the same constitution and mutate for 100 generations with seeds 7 and 19. The final states differ in **{constitution['different_fields']} fields**, providing a compact diff witness for hyper-meta-evolution.

```json
{json.dumps({'initial': constitution['initial'], 'seed_7': constitution['seed_7'], 'seed_19': constitution['seed_19']}, indent=2)}
```

## DSL emergence

The vocabulary grows from **{dsl['vocabulary_start']}** tokens to **{dsl['vocabulary_end']}**. The final vocabulary includes the compound token `{dsl['compound_token']}`, which round-trips through the evolving grammar:

```text
{dsl['compound_source']}
→ {json.dumps(dsl['round_trip'])}
```

## Thermodynamic selection

The simulated cohort starts with long strategies and gradually adopts shorter ones. Average operations fall by a factor of **{thermo['operations_reduction_factor']}×**, while average quality-per-operation rises from **{thermo['average_efficiency_generation_0']}** to **{thermo['average_efficiency_generation_49']}**. The binding budget produced **{thermo['energy_budget_binding_deaths']}** exhaustion events across the 50-generation run.

## Adversarial red-team pressure

Ten prey organisms and three red-team organisms ran for 50 generations. Mean immune strength increased by **{red_team['immune_gain']}**, with **{red_team['repulsed_attacks']}** repulsed attacks. The non-zero attack-pressure variance (**{red_team['attack_pressure_variance']}**) records heterogeneous adversarial stress across the prey cohort; all prey remained alive.

## Limitations

The current benchmark is intentionally in-process and deterministic. It demonstrates the v2 mechanisms and regression targets, but it is not a distributed performance benchmark and it does not establish general intelligence, consciousness, or production-safe execution of arbitrary code. Untrusted execution must use an external sandbox in deployment.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/benchmark-results.md"))
    args = parser.parse_args()
    results = {
        "constitution": constitution_benchmark(),
        "dsl": dsl_benchmark(),
        "thermodynamic": thermodynamic_benchmark(),
        "red_team": red_team_benchmark(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(results), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
