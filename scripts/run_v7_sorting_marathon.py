#!/usr/bin/env python3
"""Run a bounded, resumable BEAST v7 sorting-marathon evidence experiment.

The default configuration is the guide's 100,000-generation public-marathon
configuration.  This script deliberately names a completed shorter execution a
``BOUNDED_RUN_FINAL_REPORT`` rather than the guide's public ``FINAL_REPORT``.
All fitness uses the typed GP interpreter; exported Python is audit text only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evolution.fitness import SortingEvaluator
from evolution.gp_population import GPPopulation


PUBLIC_MARATHON_GENERATIONS = 100_000
FRESH_SEED_OFFSET = 900_000


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _write_json(path: Path, payload: Any) -> None:
    _atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _git_hash() -> str:
    repository = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True,
        capture_output=True, check=False, timeout=5,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _configuration(seed: int, population_size: int) -> dict[str, Any]:
    """The v7 guide's declared sorting configuration, with explicit values."""
    return {
        "task": "sorting",
        "population_size": population_size,
        "max_depth": 8,
        "tournament_size": 7,
        "crossover_rate": 0.85,
        "mutation_rate": 0.12,
        "elitism_count": 5,
        "seed": seed,
        "train_seed_rule": "generation + 17",
        "runtime": "typed AST interpreter only",
        "llm_calls_in_generation_loop": 0,
        "network_calls_in_generation_loop": 0,
    }


def _new_population(config: dict[str, Any]) -> GPPopulation:
    population = GPPopulation(
        evaluator=SortingEvaluator(), population_size=config["population_size"],
        seed=config["seed"], max_depth=config["max_depth"],
        tournament_size=config["tournament_size"], crossover_rate=config["crossover_rate"],
        mutation_rate=config["mutation_rate"], elitism_count=config["elitism_count"],
    )
    population.initialize()
    return population


def _champion_measurement(population: GPPopulation, *, cases: int, seed: int) -> dict[str, Any]:
    champion = population.champion
    result = population.evaluator.batch_evaluate([champion.genome], seed=seed, n=cases)[0]
    source = champion.genome.to_python(f"sorting_champion_generation_{population.generation}")
    return {
        "generation": population.generation,
        "training_fitness": champion.fitness,
        "program_nodes": champion.genome.complexity(),
        "program_depth": champion.genome.depth(),
        "fresh_suite": {
            "seed": seed,
            "cases": cases,
            "cases_passed": result.test_cases_passed,
            "correctness": result.correctness,
        },
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "source_code": source,
    }


def _curve_table(curve: list[dict[str, Any]], maximum_rows: int = 24) -> list[str]:
    if len(curve) <= maximum_rows:
        selected = curve
    else:
        stride = max(1, len(curve) // (maximum_rows - 1))
        selected = curve[::stride]
        if selected[-1]["generation"] != curve[-1]["generation"]:
            selected.append(curve[-1])
    lines = ["| Generation | Best fitness | Average fitness | Best nodes |", "|---:|---:|---:|---:|"]
    lines.extend(
        f"| {row['generation']:,} | {row['best_fitness']:.6f} | {row['average_fitness']:.6f} | {row['best_program_size']} |"
        for row in selected
    )
    return lines


def _render_milestone(
    measurement: dict[str, Any], curve: list[dict[str, Any]], *, config: dict[str, Any], git_hash: str,
) -> str:
    fresh = measurement["fresh_suite"]
    lines = [
        f"# BEAST v7 Sorting Marathon Milestone — Generation {measurement['generation']:,}",
        "",
        "> This is a measured local checkpoint from the typed-AST interpreter. No exported source was executed for selection, no LLM call occurred in the generation loop, and the fresh suite was disjoint from the rotating training seed for this generation.",
        "",
        "| Measurement | Value |",
        "|---|---:|",
        f"| Training fitness | {measurement['training_fitness']:.6f} |",
        f"| Fresh sorting correctness | {fresh['correctness']:.6f} ({fresh['cases_passed']}/{fresh['cases']}) |",
        f"| Fresh suite seed | {fresh['seed']} |",
        f"| Program nodes | {measurement['program_nodes']} |",
        f"| Program depth | {measurement['program_depth']} |",
        f"| Git commit | `{git_hash}` |",
        "",
        "## Champion audit source",
        "",
        "```python",
        measurement["source_code"],
        "```",
        "",
        "## Fitness curve from generation 0",
        "",
        "The complete measured curve is stored in `fitness_curve.json`; this table is a sampled rendering.",
        "",
        *_curve_table(curve),
        "",
    ]
    return "\n".join(lines)


def _render_bounded_final(
    measurement: dict[str, Any], curve: list[dict[str, Any]], *, config: dict[str, Any], git_hash: str, elapsed_seconds: float,
) -> str:
    fresh = measurement["fresh_suite"]
    return "\n".join([
        f"# BEAST v7 Bounded Sorting Run — Final Report (Generation {measurement['generation']:,})",
        "",
        "> This is the final report for the completed **bounded execution stated below**. It is not the v7 guide's 100,000-generation public-marathon claim, and it must not be represented as one.",
        "",
        "## Measured result",
        "",
        "| Measurement | Value |",
        "|---|---:|",
        f"| Completed generations | {measurement['generation']:,} |",
        f"| Target generations for this execution | {measurement['generation']:,} |",
        f"| Training champion fitness | {measurement['training_fitness']:.6f} |",
        f"| Fresh-sort correctness | {fresh['correctness']:.6f} ({fresh['cases_passed']}/{fresh['cases']}) |",
        f"| Fresh inputs | {fresh['cases']} at seed {fresh['seed']} |",
        f"| Champion program nodes | {measurement['program_nodes']} |",
        f"| Elapsed seconds in this invocation | {elapsed_seconds:.3f} |",
        f"| Git commit | `{git_hash}` |",
        "",
        "## Champion audit source",
        "",
        "```python",
        measurement["source_code"],
        "```",
        "",
        "## Fitness curve",
        "",
        "The complete machine-readable curve is `fitness_curve.json`; this rendering is sampled from it.",
        "",
        *_curve_table(curve),
        "",
        "## Reproduction boundary",
        "",
        "```bash",
        "APP_ENV=dev JWT_SECRET='v7-local-test-secret' python scripts/run_v7_sorting_marathon.py "
        f"--generations {measurement['generation']} --seed {config['seed']} --population-size {config['population_size']} "
        "--report-dir reports/sorting_marathon --checkpoint-path checkpoints/sorting_marathon/population.json",
        "```",
        "",
        "All scoring is performed by the bounded typed-AST interpreter. The audit-source block is not executed by this runner. Training cases rotate by generation; the fresh suite is evaluator-owned and uses a distinct seed.",
        "",
    ])


def run_marathon(
    *, generations: int, seed: int, population_size: int, checkpoint_path: Path,
    report_dir: Path, milestone_interval: int, checkpoint_interval: int, resume: bool,
) -> dict[str, Any]:
    if not 1 <= generations <= 1_000_000:
        raise ValueError("generations must be in 1..1000000")
    if not 2 <= population_size <= 512:
        raise ValueError("population_size must be in 2..512")
    if milestone_interval < 1 or checkpoint_interval < 1:
        raise ValueError("intervals must be positive")

    config = _configuration(seed, population_size)
    metadata_path = checkpoint_path.with_name("run_metadata.json")
    curve_path = report_dir / "fitness_curve.json"
    if resume:
        if not checkpoint_path.exists() or not metadata_path.exists() or not curve_path.exists():
            raise FileNotFoundError("--resume requires checkpoint, metadata, and fitness_curve artifacts")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata["configuration"] != config:
            raise ValueError("resume configuration differs from the recorded run configuration")
        population = GPPopulation.load_checkpoint(SortingEvaluator(), checkpoint_path)
        curve = json.loads(curve_path.read_text(encoding="utf-8"))
    else:
        population = _new_population(config)
        curve = [asdict(stat) for stat in population.history]
        metadata = {
            "schema": "beast-v7-sorting-marathon-v1",
            "configuration": config,
            "git_hash": _git_hash(),
            "started_generation": population.generation,
        }
        _write_json(metadata_path, metadata)
        _write_json(curve_path, curve)

    report_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    while population.generation < generations:
        population.step()
        curve.append(asdict(population.history[-1]))
        if population.generation % checkpoint_interval == 0 or population.generation == generations:
            _atomic_write(checkpoint_path, json.dumps(population.checkpoint_payload(), sort_keys=True))
            _write_json(curve_path, curve)
        if population.generation % milestone_interval == 0:
            measurement = _champion_measurement(
                population, cases=100, seed=FRESH_SEED_OFFSET + population.generation,
            )
            milestone = report_dir / f"milestone_gen_{population.generation}.md"
            _atomic_write(milestone, _render_milestone(measurement, curve, config=config, git_hash=metadata["git_hash"]))
            _write_json(milestone.with_suffix(".json"), measurement)

    elapsed = time.perf_counter() - started
    final_cases = 1_000 if generations >= PUBLIC_MARATHON_GENERATIONS else 100
    final_measurement = _champion_measurement(
        population, cases=final_cases, seed=FRESH_SEED_OFFSET + generations,
    )
    completed_public_marathon = generations >= PUBLIC_MARATHON_GENERATIONS
    final_name = "FINAL_REPORT.md" if completed_public_marathon else "BOUNDED_RUN_FINAL_REPORT.md"
    _atomic_write(
        report_dir / final_name,
        _render_bounded_final(final_measurement, curve, config=config, git_hash=metadata["git_hash"], elapsed_seconds=elapsed),
    )
    artifact = {
        "schema": "beast-v7-sorting-marathon-result-v1",
        "status": "completed",
        "claimed_public_100k_marathon_completed": completed_public_marathon,
        "configuration": config,
        "git_hash": metadata["git_hash"],
        "elapsed_seconds_this_invocation": elapsed,
        "final": final_measurement,
        "checkpoint": str(checkpoint_path),
        "curve": str(curve_path),
        "report": str(report_dir / final_name),
    }
    _write_json(report_dir / "run_result.json", artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=PUBLIC_MARATHON_GENERATIONS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--checkpoint-path", default="checkpoints/sorting_marathon/population.json")
    parser.add_argument("--report-dir", default="reports/sorting_marathon")
    parser.add_argument("--milestone-interval", type=int, default=10_000)
    parser.add_argument("--checkpoint-interval", type=int, default=1_000)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    artifact = run_marathon(
        generations=args.generations, seed=args.seed, population_size=args.population_size,
        checkpoint_path=Path(args.checkpoint_path), report_dir=Path(args.report_dir),
        milestone_interval=args.milestone_interval, checkpoint_interval=args.checkpoint_interval,
        resume=args.resume,
    )
    print(json.dumps(artifact, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
