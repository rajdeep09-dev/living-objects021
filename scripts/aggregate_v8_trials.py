#!/usr/bin/env python3
"""Aggregate already completed v8 trial artifacts without rerunning evolution."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_v8_multiseed import PREREGISTRATION_ID, SEEDS, SPECS


def aggregate(task: str, reports_root: Path) -> dict[str, object]:
    if task not in SPECS:
        raise ValueError(f"unsupported task: {task}")
    trials: list[dict[str, object]] = []
    missing: list[int] = []
    for seed in SEEDS:
        path = reports_root / task / f"seed_{seed}" / "trial.json"
        if not path.exists():
            missing.append(seed)
            continue
        trial = json.loads(path.read_text(encoding="utf-8"))
        if trial.get("pre_registration_id") != PREREGISTRATION_ID or trial.get("task") != task or trial.get("seed") != seed:
            raise ValueError(f"trial artifact fails preregistration identity check: {path}")
        trials.append(trial)
    completed = len(trials)
    eligible = sum(bool(trial["promotion_eligible"]) for trial in trials)
    result = {
        "schema": "beast-v8-multiseed-summary-v1",
        "pre_registration_id": PREREGISTRATION_ID,
        "task": task,
        "declared_seeds": list(SEEDS),
        "completed_seeds": [trial["seed"] for trial in trials],
        "missing_seeds": missing,
        "trial_count": completed,
        "complete": completed == len(SEEDS),
        "trials": [{
            "seed": trial["seed"],
            "fresh_correctness": trial["final"]["fresh"]["correctness"],
            "first_perfect_training_generation": trial["first_perfect_training_generation"],
            "promotion_eligible": trial["promotion_eligible"],
            "initial_tree_contains_final": trial["initial_tree_contains_final"],
        } for trial in trials],
        "eligible_successes": eligible,
        "multi_seed_discovery_threshold": "at least 4 of 5 eligible successes",
        "discovery_log_eligible": completed == len(SEEDS) and eligible >= 4,
    }
    output = reports_root / task / "summary.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=sorted(SPECS))
    parser.add_argument("--reports-root", default="reports/v8")
    args = parser.parse_args()
    print(json.dumps(aggregate(args.task, Path(args.reports_root)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
