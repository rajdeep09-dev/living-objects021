#!/usr/bin/env python3
"""Run bounded, local v6 GP benchmarks and write measured artifacts.

The runner uses only the in-process typed interpreter.  It does not make HTTP
requests, execute exported source, place trades, or modify production systems.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evolution.fitness import AbsoluteDifferenceEvaluator
from evolution.gp_control import GPRunController
from evolution.gp_population import GPPopulation


TASKS = {
    "absolute-difference": ("Compose abs(left - right)", AbsoluteDifferenceEvaluator),
}


def run_task(name: str, generations: int, population_size: int, seed: int, checkpoint_dir: Path, batch_size: int) -> dict[str, Any]:
    description, evaluator_type = TASKS[name]
    evaluator = evaluator_type()
    population = GPPopulation(evaluator=evaluator, population_size=population_size, seed=seed)
    population.initialize()
    baseline = population.champion.fitness
    controller = GPRunController(population, generations, checkpoint_dir / f"{name}.json")
    controller.start()
    started = time.perf_counter()
    while controller.state == "running":
        controller.advance(batch_size)
    elapsed = time.perf_counter() - started
    champion = population.champion
    holdout = evaluator.batch_evaluate([champion.genome], seed=9_001)[0]
    return {
        "task": name,
        "description": description,
        "generations": population.generation,
        "population_size": population.population_size,
        "seed": seed,
        "baseline_training_fitness": baseline,
        "best_training_fitness": champion.fitness,
        "held_out_correctness": holdout.correctness,
        "held_out_cases_passed": holdout.test_cases_passed,
        "held_out_cases_total": holdout.test_cases_total,
        "program_size": champion.genome.complexity(),
        "program_depth": champion.genome.depth(),
        "runtime_seconds": elapsed,
        "checkpoint": str(controller.checkpoint_path),
        "state": controller.state,
        "source_export": champion.genome.to_python(f"champion_{name.replace('-', '_')}_gen{population.generation}"),
        "last_generation": asdict(population.history[-1]),
    }


def render_report(results: list[dict[str, Any]], args: argparse.Namespace) -> str:
    lines = [
        "# BEAST v6 benchmark results",
        "",
        "> These are bounded local genetic-programming measurements. The system interprets typed ASTs; it does not execute the source exports, call network services per generation, trade in markets, or claim general intelligence.",
        "",
        f"Command: `python scripts/run_v6_benchmarks.py --tasks {args.tasks} --generations {args.generations} --population-size {args.population_size} --seed {args.seed}`",
        "",
        "| Task | Generations | Train baseline | Train champion | Held-out correctness | Program nodes | Runtime |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result['task']} | {result['generations']} | {result['baseline_training_fitness']:.3f} | "
            f"{result['best_training_fitness']:.3f} | {result['held_out_correctness']:.3f} "
            f"({result['held_out_cases_passed']}/{result['held_out_cases_total']}) | {result['program_size']} | {result['runtime_seconds']:.3f}s |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A score is task-specific finite-suite correctness, not a claim that a discovered program is universally correct. Held-out cases use a deterministic seed distinct from the generation fitness seed. The source column in the JSON artifact is an audit export only; all scoring occurs through the bounded AST interpreter.",
        "",
        "## Reproduction and limits",
        "",
        f"Checkpoints are written to `{args.checkpoint_dir}` and can be resumed only through the validated GP checkpoint API. This command has no network client, no subprocess execution path, no live market connection, and no production write action. Increase generations only within the documented 1,000,000-generation controller cap and a resource-bounded persistent worker.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", default="absolute-difference", help="comma-separated subset: absolute-difference")
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--population-size", type=int, default=48)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--checkpoint-dir", default="/tmp/beast-v6-checkpoints")
    parser.add_argument("--output", default="docs/v6-benchmark-results.md")
    parser.add_argument("--json-output", default="docs/v6-benchmark-results.json")
    args = parser.parse_args()
    if not 1 <= args.generations <= 1_000_000:
        parser.error("--generations must be in 1..1000000")
    if not 2 <= args.population_size <= 512:
        parser.error("--population-size must be in 2..512")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    requested = [item.strip() for item in args.tasks.split(",") if item.strip()]
    invalid = sorted(set(requested) - set(TASKS))
    if invalid or not requested:
        parser.error(f"unknown tasks: {', '.join(invalid) or '(none)'}")
    checkpoint_dir = Path(args.checkpoint_dir)
    results = [run_task(task, args.generations, args.population_size, args.seed + index, checkpoint_dir, args.batch_size) for index, task in enumerate(requested)]
    Path(args.output).write_text(render_report(results, args), encoding="utf-8")
    Path(args.json_output).write_text(json.dumps({"results": results}, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output} and {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
