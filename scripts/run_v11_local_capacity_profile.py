#!/usr/bin/env python3
"""Profile bounded local Manhattan evolution across several population sizes.

The output describes the executing local process only. It does not establish a
cloud-VM throughput claim, a clean-laptop onboarding time, or a production safe
capacity threshold.
"""
from __future__ import annotations

import argparse
import json
import resource
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from living_objects import evolve


def _single(population_size: int, generations: int, seed: int) -> dict[str, object]:
    started = time.perf_counter()
    result = evolve(
        "manhattan",
        generations=generations,
        seed=seed,
        population_size=population_size,
        artifact_dir=ROOT / "reports" / "v11" / "artifacts" / f"capacity-{population_size}",
    )
    elapsed = time.perf_counter() - started
    max_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return {
        "population_size": population_size,
        "generations": generations,
        "elapsed_seconds": elapsed,
        "generations_per_second": generations / elapsed if elapsed else None,
        "peak_rss_kib": max_rss_kib,
        "training_fitness": result.fitness,
        "tree_sha256": result.champion["tree_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--single", action="store_true")
    parser.add_argument("--population-size", type=int)
    parser.add_argument("--generations", type=int, default=25)
    parser.add_argument("--seed", type=int, default=7300)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "v11" / "local-capacity-profile.json")
    args = parser.parse_args()
    if args.single:
        if not args.population_size:
            raise ValueError("--population-size is required with --single")
        print(json.dumps(_single(args.population_size, args.generations, args.seed), sort_keys=True))
        return 0

    rows = []
    for population_size in (50, 100, 200, 500):
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--single",
                "--population-size",
                str(population_size),
                "--generations",
                str(args.generations),
                "--seed",
                str(args.seed),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        rows.append(json.loads(completed.stdout))
    record = {
        "schema": "beast-v11-local-capacity-profile-v1",
        "status": "measured",
        "environment_scope": "local sandbox process only",
        "rows": rows,
        "claim_boundary": (
            "These local bounded measurements do not establish clean-laptop setup time, standard cloud VM "
            "throughput, a 1 GB safe population maximum, or production service capacity."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
