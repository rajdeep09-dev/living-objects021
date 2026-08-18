#!/usr/bin/env python3
"""Run and record the v11 bounded Manhattan end-to-end verification.

This command is intentionally local, deterministic, and offline.  It does not
claim a fresh-machine benchmark: it records the exact environment-independent
run parameters and elapsed wall time from the machine that executed it.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from living_objects import evolve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20_260_814)
    parser.add_argument("--population-size", type=int, default=128)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "v11" / "manhattan-real-world-test.json")
    args = parser.parse_args()

    started = time.perf_counter()
    result = evolve(
        "manhattan",
        generations=args.generations,
        seed=args.seed,
        population_size=args.population_size,
        artifact_dir=args.output.parent / "artifacts",
    )
    elapsed = time.perf_counter() - started
    record = {
        "schema": "beast-v11-real-world-manhattan-v1",
        "status": "measured",
        "configuration": {
            "task": result.task,
            "seed": result.seed,
            "generations": result.generations,
            "population_size": result.population_size,
        },
        "elapsed_seconds": elapsed,
        "champion": {
            "tree_sha256": result.champion["tree_sha256"],
            "generation": result.champion["generation"],
            "training_fitness": result.fitness,
            "fresh": result.champion["fresh"],
        },
        "initial_tree_contains_final": result.initial_tree_contains_final,
        "execution_boundary": result.execution_boundary,
        "artifact_path": result.artifact_path,
        "claim_boundary": (
            "This is one local deterministic run. It is not a fresh-machine, cloud-VM, "
            "multi-seed, production-readiness, or general-program-synthesis measurement."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
