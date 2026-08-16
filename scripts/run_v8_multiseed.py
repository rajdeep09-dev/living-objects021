#!/usr/bin/env python3
"""Execute pre-registered, interpreter-only BEAST v8 multi-seed experiments.

All seeds are fixed in ``docs/v8-experiment-preregistration.md``. A low score
or an absent curriculum advance is reported as a result; it is never silently
discarded. Generated source is recorded solely as an audit artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evolution.clean_sorting import CleanSortingCurriculum, CleanSortingEvaluator, PHASES
from evolution.fitness import ManhattanDistanceEvaluator
from evolution.gp_population import GPPopulation


PREREGISTRATION_ID = "BEAST-V8-PREREG-20260816-A"
SEEDS = (20_260_814, 20_260_815, 20_260_816, 20_260_817, 20_260_818)


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    generations: int
    population_size: int
    max_depth: int
    mutation_rate: float
    crossover_rate: float
    elitism_count: int
    milestone_interval: int = 1_000


SPECS = {
    "clean-sorting": ExperimentSpec("clean-sorting", 10_000, 50, 8, 0.12, 0.85, 5),
    "manhattan-distance": ExperimentSpec("manhattan-distance", 10_000, 128, 7, 0.22, 0.85, 4),
}


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _population(task: str, seed: int, spec: ExperimentSpec) -> GPPopulation:
    if task == "clean-sorting":
        population = GPPopulation(
            CleanSortingEvaluator(), primitives=PHASES[0].primitives, population_size=spec.population_size,
            seed=seed, max_depth=spec.max_depth, mutation_rate=spec.mutation_rate,
            crossover_rate=spec.crossover_rate, elitism_count=spec.elitism_count,
        )
    elif task == "manhattan-distance":
        population = GPPopulation(
            ManhattanDistanceEvaluator(), population_size=spec.population_size, seed=seed,
            max_depth=spec.max_depth, mutation_rate=spec.mutation_rate,
            crossover_rate=spec.crossover_rate, elitism_count=spec.elitism_count,
        )
    else:
        raise ValueError(f"unsupported v8 experiment task: {task}")
    population.initialize()
    return population


def _champion_record(population: GPPopulation, *, fresh_seed: int, fresh_cases: int = 1_000) -> dict[str, Any]:
    champion = population.champion
    fresh = population.evaluator.batch_evaluate([champion.genome], seed=fresh_seed, n=fresh_cases)[0]
    source = champion.genome.to_python(f"{population.evaluator.__class__.__name__.lower()}_g{population.generation}")
    return {
        "generation": population.generation,
        "training_fitness": champion.fitness,
        "tree": champion.genome.to_dict(),
        "tree_sha256": _digest(champion.genome.to_dict()),
        "nodes": champion.genome.complexity(),
        "depth": champion.genome.depth(),
        "fresh": {
            "seed": fresh_seed, "cases": fresh_cases, "correctness": fresh.correctness,
            "passed": fresh.test_cases_passed,
        },
        "source_audit_export": source,
    }


def run_trial(task: str, seed: int, *, generations: int | None = None, output_dir: Path | None = None) -> dict[str, Any]:
    spec = SPECS[task]
    target = spec.generations if generations is None else generations
    if not 1 <= target <= spec.generations:
        raise ValueError(f"generations must be in 1..{spec.generations}")
    population = _population(task, seed, spec)
    initial_hashes = {organism.genome.to_dict().__repr__() for organism in population.population}
    history = [asdict(population.history[-1])]
    milestones: list[dict[str, Any]] = []
    curriculum: list[dict[str, Any]] = []
    first_perfect_training_generation: int | None = 0 if population.champion.fitness == 1.0 else None

    for _ in range(target):
        if task == "clean-sorting":
            CleanSortingCurriculum.apply_to_population(population)
        population.step()
        if task == "clean-sorting":
            CleanSortingCurriculum.apply_to_population(population)
            # A task stage changes only after an evaluator-owned, 100-case
            # mastery measurement and is recorded even when it does not advance.
            curriculum.append(CleanSortingCurriculum.advance_if_mastered(population, cases=100))
        history.append(asdict(population.history[-1]))
        if first_perfect_training_generation is None and population.champion.fitness == 1.0:
            first_perfect_training_generation = population.generation
        if population.generation % spec.milestone_interval == 0 or population.generation == target:
            record = _champion_record(
                population, fresh_seed=900_000 + seed + population.generation,
            )
            if task == "clean-sorting":
                record["curriculum_stage_index"] = population.evaluator.stage_index
                record["curriculum_stage_length"] = population.evaluator.stage_length
            milestones.append(record)
            if output_dir:
                _atomic_json(output_dir / task / f"seed_{seed}" / f"milestone_{population.generation}.json", record)

    final = _champion_record(population, fresh_seed=990_000 + seed)
    trial = {
        "schema": "beast-v8-multiseed-trial-v1",
        "pre_registration_id": PREREGISTRATION_ID,
        "task": task,
        "seed": seed,
        "configuration": asdict(spec) | {"executed_generations": target},
        "execution_boundary": {
            "runtime": "typed AST interpreter only", "llm_calls": 0,
            "network_calls": 0, "generated_source_executed": False,
        },
        "initial_population_tree_hashes": sorted(_digest(value) for value in initial_hashes),
        "history": history,
        "curriculum": curriculum,
        "milestones": milestones,
        "first_perfect_training_generation": first_perfect_training_generation,
        "final": final,
        "initial_tree_contains_final": final["tree"].__repr__() in initial_hashes,
        "promotion_eligible": bool(
            target == spec.generations
            and final["fresh"]["correctness"] >= 0.95
            and not final["tree"].__repr__() in initial_hashes
        ),
    }
    if output_dir:
        _atomic_json(output_dir / task / f"seed_{seed}" / "trial.json", trial)
        _atomic_json(output_dir / task / f"seed_{seed}" / "checkpoint.json", population.checkpoint_payload())
    return trial


def run_experiment(task: str, *, output_dir: Path, generations: int | None = None, seeds: tuple[int, ...] = SEEDS) -> dict[str, Any]:
    trials = [run_trial(task, seed, generations=generations, output_dir=output_dir) for seed in seeds]
    successful = sum(1 for trial in trials if trial["promotion_eligible"])
    result = {
        "schema": "beast-v8-multiseed-summary-v1",
        "pre_registration_id": PREREGISTRATION_ID,
        "task": task,
        "declared_seeds": list(seeds),
        "executed_generations": generations or SPECS[task].generations,
        "trials": [{
            "seed": trial["seed"], "fresh_correctness": trial["final"]["fresh"]["correctness"],
            "first_perfect_training_generation": trial["first_perfect_training_generation"],
            "promotion_eligible": trial["promotion_eligible"],
        } for trial in trials],
        "eligible_successes": successful,
        "multi_seed_discovery_threshold": "at least 4 of 5 eligible successes",
        "discovery_log_eligible": successful >= 4 and len(seeds) == 5,
    }
    _atomic_json(output_dir / task / "summary.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=sorted(SPECS))
    parser.add_argument("--output-dir", default="reports/v8")
    parser.add_argument("--generations", type=int)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    args = parser.parse_args()
    seeds = tuple(args.seeds) if args.seeds else SEEDS
    if not seeds:
        raise ValueError("at least one seed is required")
    result = run_experiment(args.task, output_dir=Path(args.output_dir), generations=args.generations, seeds=seeds)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
