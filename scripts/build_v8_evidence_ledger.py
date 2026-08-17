#!/usr/bin/env python3
"""Compile v8 benchmark and discovery records from measured JSON artifacts only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence_ledger(repository_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return derived ledger and discovery log without running or mutating experiments."""
    audit = _read_json(repository_root / "docs" / "v8-contamination-audit.json")
    clean = _read_json(repository_root / "reports" / "v8" / "clean-sorting" / "summary.json")
    manhattan = _read_json(repository_root / "reports" / "v8" / "manhattan-distance" / "summary.json")
    audit_rows = {
        task["task_id"]: {
            "audit_status": task["status"],
            "baseline": task["baseline"],
            "direct_solution_matches": task["direct_solution_matches"],
            "one_operation_candidates_tested": task["one_operation_candidates_tested"],
        }
        for task in audit["tasks"]
    }
    ledger = {
        "schema": "beast-v8-contamination-adjusted-ledger-v1",
        "audit_schema": audit["schema"],
        "task_count": audit["task_count"],
        "task_audit": audit_rows,
        "experiment_rows": [
            {
                "task": "sorting",
                "profile": "historical-default",
                "benchmark_status": "RETRACTED_DIRECT_PRIMITIVE",
                "official_ranking_eligible": False,
                "reason": "sort1 was available in the generation-zero primitive profile",
            },
            {
                "task": "clean-sorting",
                "profile": "clean-sorting-v1",
                "benchmark_status": "NEGATIVE_RESULT",
                "official_ranking_eligible": False,
                "completed_trials": clean["trial_count"],
                "eligible_successes": clean["eligible_successes"],
                "summary_artifact": "reports/v8/clean-sorting/summary.json",
            },
            {
                "task": "manhattan-distance",
                "profile": "default-float-compositional",
                "benchmark_status": "VALID_COMPOSITIONAL_RESULT",
                "official_ranking_eligible": True,
                "completed_trials": manhattan["trial_count"],
                "eligible_successes": manhattan["eligible_successes"],
                "summary_artifact": "reports/v8/manhattan-distance/summary.json",
                "claim_boundary": "A bounded compositional expression result; not a general algorithm-discovery result.",
            },
        ],
        "claim_boundary": "No row marked retracted or negative may be presented as a successful algorithm-discovery benchmark.",
    }
    discoveries: list[dict[str, Any]] = []
    for summary_trial in manhattan["trials"]:
        seed = summary_trial["seed"]
        trial = _read_json(repository_root / "reports" / "v8" / "manhattan-distance" / f"seed_{seed}" / "trial.json")
        final = trial["final"]
        discoveries.append({
            "record_id": f"BEAST-V8-MANHATTAN-{seed}",
            "pre_registration_id": manhattan["pre_registration_id"],
            "task": "manhattan-distance",
            "seed": seed,
            "generation": final["generation"],
            "tree_sha256": final["tree_sha256"],
            "primitives_used": final["tree"]["primitives_used"],
            "node_count": final["nodes"],
            "first_perfect_training_generation": trial["first_perfect_training_generation"],
            "fresh_suite": final["fresh"],
            "promotion_eligible": summary_trial["promotion_eligible"],
            "initial_tree_contains_final": summary_trial["initial_tree_contains_final"],
            "trial_artifact": f"reports/v8/manhattan-distance/seed_{seed}/trial.json",
        })
    discovery_log = {
        "schema": "beast-v8-discovery-log-v1",
        "status": "eligible-measured-records",
        "claim_boundary": "These records describe evaluator-specific compositional solutions only.",
        "records": discoveries,
    }
    return ledger, discovery_log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--ledger-output", default="docs/v8-benchmark-ledger.json")
    parser.add_argument("--discovery-output", default="docs/v8-discovery-log.json")
    args = parser.parse_args()
    root = args.repository_root.resolve()
    ledger, discovery_log = build_evidence_ledger(root)
    _write_json(root / args.ledger_output, ledger)
    _write_json(root / args.discovery_output, discovery_log)
    print(json.dumps({"ledger_rows": len(ledger["experiment_rows"]), "discovery_records": len(discovery_log["records"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
