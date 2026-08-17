from __future__ import annotations

import json
from pathlib import Path

from scripts.build_v8_evidence_ledger import build_evidence_ledger


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_evidence_ledger_derives_retractions_negative_result_and_discovery_records(tmp_path: Path) -> None:
    _write(tmp_path / "docs" / "v8-contamination-audit.json", {
        "schema": "audit", "task_count": 1,
        "tasks": [{"task_id": "sorting", "status": "RETRACTED_DIRECT_PRIMITIVE", "baseline": {}, "direct_solution_matches": ["sort1"], "one_operation_candidates_tested": 1}],
    })
    _write(tmp_path / "reports" / "v8" / "clean-sorting" / "summary.json", {
        "trial_count": 5, "eligible_successes": 0,
    })
    _write(tmp_path / "reports" / "v8" / "manhattan-distance" / "summary.json", {
        "trial_count": 5, "eligible_successes": 5, "pre_registration_id": "P",
        "trials": [{"seed": 7, "promotion_eligible": True, "initial_tree_contains_final": False}],
    })
    _write(tmp_path / "reports" / "v8" / "manhattan-distance" / "seed_7" / "trial.json", {
        "first_perfect_training_generation": 3,
        "final": {"generation": 10, "tree_sha256": "hash", "nodes": 3, "fresh": {"correctness": 1.0}, "tree": {"primitives_used": ["abs1"]}},
    })
    ledger, log = build_evidence_ledger(tmp_path)
    assert ledger["experiment_rows"][0]["official_ranking_eligible"] is False
    assert ledger["experiment_rows"][1]["benchmark_status"] == "NEGATIVE_RESULT"
    assert ledger["experiment_rows"][2]["eligible_successes"] == 5
    assert log["records"] == [{
        "record_id": "BEAST-V8-MANHATTAN-7", "pre_registration_id": "P", "task": "manhattan-distance",
        "seed": 7, "generation": 10, "tree_sha256": "hash", "primitives_used": ["abs1"], "node_count": 3,
        "first_perfect_training_generation": 3, "fresh_suite": {"correctness": 1.0}, "promotion_eligible": True,
        "initial_tree_contains_final": False, "trial_artifact": "reports/v8/manhattan-distance/seed_7/trial.json",
    }]
