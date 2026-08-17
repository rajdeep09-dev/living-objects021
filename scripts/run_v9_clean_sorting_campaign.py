"""Launch or resume the preregistered v9 clean-sorting curriculum campaign.

The default target is 100,000 generations for each of five declared seeds.
This program performs no network requests and no LLM calls.  It is a launcher
and evidence recorder, not a claim that the campaign has been run: executions
below the declared target are labelled bounded and remain ineligible for a
sorting discovery claim.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from evolution.gp_population import GPPopulation
from evolution.v9_sorting_curriculum import (
    FiveStageSortingCurriculum,
    STAGES,
    V9CleanSortingEvaluator,
    primitive_manifest,
)

PREREGISTRATION_ID = "BEAST-V9-PREREG-20260817-A"
DECLARED_SEEDS = (20_260_901, 20_260_902, 20_260_903, 20_260_904, 20_260_905)
DECLARED_GENERATIONS = 100_000


@dataclass(frozen=True)
class CampaignSpec:
    population_size: int = 50
    max_depth: int = 8
    mutation_rate: float = 0.12
    crossover_rate: float = 0.85
    elitism_count: int = 5
    curriculum_probe_interval: int = 100
    checkpoint_interval: int = 10_000
    milestone_interval: int = 10_000


SPEC = CampaignSpec()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True,
        capture_output=True, check=False, timeout=5,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _configuration(seed: int) -> dict[str, Any]:
    return asdict(SPEC) | {
        "task": "clean-sorting-v9-five-stage",
        "seed": seed,
        "declared_generations": DECLARED_GENERATIONS,
        "runtime": "typed AST interpreter only",
        "llm_calls_in_generation_loop": 0,
        "network_calls_in_generation_loop": 0,
        "generated_source_executed": False,
    }


def _new_population(seed: int) -> tuple[GPPopulation, FiveStageSortingCurriculum]:
    evaluator = V9CleanSortingEvaluator()
    population = GPPopulation(
        evaluator=evaluator, primitives=STAGES[0].primitives, population_size=SPEC.population_size,
        seed=seed, max_depth=SPEC.max_depth, mutation_rate=SPEC.mutation_rate,
        crossover_rate=SPEC.crossover_rate, elitism_count=SPEC.elitism_count,
    )
    population.initialize()
    curriculum = FiveStageSortingCurriculum()
    curriculum.bind(population)
    return population, curriculum


def _measurement(population: GPPopulation, *, seed: int) -> dict[str, Any]:
    champion = population.champion
    general_evaluator = V9CleanSortingEvaluator(stage_index=len(STAGES) - 1)
    fresh = general_evaluator.batch_evaluate([champion.genome], seed=seed, n=1_000)[0]
    return {
        "generation": population.generation,
        "active_stage": population.evaluator.stage.identifier,
        "active_stage_index": population.evaluator.stage_index,
        "training_fitness": champion.fitness,
        "tree": champion.genome.to_dict(),
        "nodes": champion.genome.complexity(),
        "depth": champion.genome.depth(),
        "general_fresh_suite": {
            "stage": "up-to-16", "seed": seed, "cases": 1_000,
            "correctness": fresh.correctness, "passed": fresh.test_cases_passed,
        },
        "source_audit_export": champion.genome.to_python(f"v9_clean_sorting_g{population.generation}"),
    }


def run_seed(
    seed: int, *, generations: int = DECLARED_GENERATIONS, output_dir: Path,
    resume: bool = False,
) -> dict[str, Any]:
    """Run one declared seed and persist only measured checkpoint artifacts."""
    if seed not in DECLARED_SEEDS:
        raise ValueError(f"seed {seed} is not in the preregistered five-seed set")
    if not 1 <= generations <= DECLARED_GENERATIONS:
        raise ValueError(f"generations must be in 1..{DECLARED_GENERATIONS}")
    seed_dir = output_dir / f"seed_{seed}"
    checkpoint_path = seed_dir / "checkpoint.json"
    history_path = seed_dir / "fitness_history.json"
    metadata_path = seed_dir / "metadata.json"
    config = _configuration(seed)
    if resume:
        if not all(path.exists() for path in (checkpoint_path, history_path, metadata_path)):
            raise FileNotFoundError("--resume requires checkpoint, metadata, and fitness history artifacts")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("configuration") != config:
            raise ValueError("resume configuration differs from preregistered configuration")
        population = GPPopulation.load_checkpoint(V9CleanSortingEvaluator(), checkpoint_path)
        curriculum = FiveStageSortingCurriculum.from_population(population)
        curriculum.bind(population)
        history = json.loads(history_path.read_text(encoding="utf-8"))
    else:
        population, curriculum = _new_population(seed)
        history = [asdict(population.history[-1])]
        metadata = {
            "schema": "beast-v9-clean-sorting-campaign-v1",
            "preregistration_id": PREREGISTRATION_ID,
            "configuration": config,
            "primitive_manifest": primitive_manifest(),
            "git_hash_at_start": _git_hash(),
        }
        _write_json(metadata_path, metadata)
        _write_json(history_path, history)

    started = perf_counter()
    while population.generation < generations:
        population.step()
        history.append(asdict(population.history[-1]))
        if population.generation % SPEC.curriculum_probe_interval == 0:
            curriculum.evaluate_and_advance(population, cases=100)
        if population.generation % SPEC.checkpoint_interval == 0 or population.generation == generations:
            _write_json(checkpoint_path, population.checkpoint_payload())
            _write_json(history_path, history)
        if population.generation % SPEC.milestone_interval == 0 or population.generation == generations:
            _write_json(seed_dir / f"milestone_{population.generation}.json", _measurement(
                population, seed=900_000 + seed + population.generation,
            ))

    final = _measurement(population, seed=990_000 + seed)
    complete = generations == DECLARED_GENERATIONS
    result = {
        "schema": "beast-v9-clean-sorting-trial-v1",
        "preregistration_id": PREREGISTRATION_ID,
        "status": "completed" if complete else "bounded_execution_completed",
        "eligible_for_declared_campaign_analysis": complete,
        "configuration": config | {"executed_generations": generations},
        "elapsed_seconds_this_invocation": perf_counter() - started,
        "curriculum_events": curriculum.events,
        "cultural_archive": curriculum.archive,
        "final": final,
        "checkpoint": str(checkpoint_path),
        "fitness_history": str(history_path),
    }
    _write_json(seed_dir / "trial.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="reports/v9/clean-sorting-curriculum")
    parser.add_argument("--generations", type=int, default=DECLARED_GENERATIONS)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    seeds = tuple(args.seeds) if args.seeds else DECLARED_SEEDS
    result = [run_seed(seed, generations=args.generations, output_dir=Path(args.output_dir), resume=args.resume) for seed in seeds]
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
