#!/usr/bin/env python3
"""Run the declared non-LLM proof trial set and preserve every result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evolution.proof_benchmark import ProofBenchmarkConfig, run_proof_benchmark


DEFAULT_SEEDS = (20260814, 20260815, 20260816)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default=",".join(map(str, DEFAULT_SEEDS)), help="fixed comma-separated integer seed list")
    parser.add_argument("--generations", type=int, default=300)
    parser.add_argument("--population-size", type=int, default=128)
    parser.add_argument("--audit-cases", type=int, default=128)
    parser.add_argument("--minimum-holdout-delta", type=float, default=0.10)
    parser.add_argument("--output-dir", default="docs/artifacts/non-llm-proof-release")
    args = parser.parse_args()
    seeds = tuple(int(value.strip()) for value in args.seeds.split(",") if value.strip())
    if not seeds or len(set(seeds)) != len(seeds):
        parser.error("--seeds must contain at least one unique integer")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trials: list[dict[str, object]] = []
    for seed in seeds:
        artifact_path = output_dir / f"trial-{seed}.json"
        artifact = run_proof_benchmark(
            ProofBenchmarkConfig(
                seed=seed,
                generations=args.generations,
                population_size=args.population_size,
                audit_case_count=args.audit_cases,
                minimum_holdout_delta=args.minimum_holdout_delta,
            ),
            artifact_path,
        )
        trials.append({
            "seed": seed,
            "artifact": str(artifact_path),
            "promoted": artifact["decision"]["promoted"],
            "baseline_holdout_objective": artifact["initial_audits"]["holdout"]["objective_score"],
            "final_holdout_objective": artifact["final_audits"]["holdout"]["objective_score"],
            "holdout_delta": artifact["decision"]["holdout_delta"],
            "baseline_exact_correctness": artifact["initial_audits"]["holdout"]["exact_correctness"],
            "final_exact_correctness": artifact["final_audits"]["holdout"]["exact_correctness"],
        })
    summary = {
        "trial_set": {"seeds": list(seeds), "selection_after_results": False},
        "configuration": {
            "generations": args.generations, "population_size": args.population_size,
            "audit_cases": args.audit_cases, "minimum_holdout_delta": args.minimum_holdout_delta,
        },
        "trials": trials,
        "all_trials_promoted": all(bool(item["promoted"]) for item in trials),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["all_trials_promoted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
