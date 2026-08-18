#!/usr/bin/env python3
"""Measure one bounded v11 Stage 0 clean-sorting curriculum run.

The command intentionally keeps the population in Stage 0 throughout the
requested evolution loop, then applies the predeclared 100-case mastery check
once at the end.  It is not the separately gated 100,000-generation campaign.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evolution.gp_population import GPPopulation
from evolution.v9_sorting_curriculum import FiveStageSortingCurriculum, STAGES, V9CleanSortingEvaluator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "v11" / "sorting-stage0-5000.json")
    args = parser.parse_args()
    if args.generations < 1:
        raise ValueError("generations must be positive")

    evaluator = V9CleanSortingEvaluator(stage_index=0)
    population = GPPopulation(
        evaluator=evaluator,
        primitives=STAGES[0].primitives,
        population_size=args.population_size,
        seed=args.seed,
        mutation_rate=0.12,
        crossover_rate=0.85,
        elitism_count=5,
        max_depth=8,
        primitive_profile_name="task-specific",
    )
    curriculum = FiveStageSortingCurriculum()
    population.initialize()
    curriculum.bind(population)

    started = time.perf_counter()
    for _ in range(args.generations):
        population.step()
    elapsed = time.perf_counter() - started
    mastery_event = curriculum.evaluate_and_advance(population, cases=100, seed=900_042)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = args.output.parent / "artifacts" / "sorting-stage0-5000-checkpoint.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    population.save_checkpoint(checkpoint)
    champion = population.champion
    champion_payload = json.dumps(champion.genome.to_dict(), sort_keys=True, separators=(",", ":"))
    record = {
        "schema": "beast-v11-clean-sorting-stage0-v1",
        "status": "measured",
        "configuration": {
            "seed": args.seed,
            "generations": args.generations,
            "population_size": args.population_size,
            "stage_held_during_evolution": "pairs",
            "mastery_seed": 900_042,
            "mastery_cases": 100,
        },
        "elapsed_seconds": elapsed,
        "mastery_event": mastery_event,
        "champion": {
            "tree_sha256": hashlib.sha256(champion_payload.encode("utf-8")).hexdigest(),
            "generation": champion.generation,
            "fitness": champion.fitness,
            "nodes": champion.genome.complexity(),
            "depth": champion.genome.depth(),
        },
        "checkpoint_path": str(checkpoint),
        "execution_boundary": {
            "runtime": "typed AST interpreter only",
            "llm_calls": 0,
            "network_calls": 0,
            "generated_source_executed": False,
        },
        "claim_boundary": (
            "One bounded Stage 0 seed does not demonstrate general sorting, later-stage mastery, "
            "the preregistered 100,000-generation campaign, or a persistent worker."
        ),
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
