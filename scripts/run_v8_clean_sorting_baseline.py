#!/usr/bin/env python3
"""Measure and write the preregistered clean-sorting contamination baseline."""
from __future__ import annotations

import json
from pathlib import Path

from evolution.clean_sorting import CleanSortingEvaluator, PHASES, clean_primitive_manifest
from evolution.contamination_audit import TaskDefinition, audit_task


def main() -> int:
    record = audit_task(
        TaskDefinition("clean-sorting-v1", CleanSortingEvaluator), PHASES[-1].primitives,
        baseline_population_size=500, baseline_seed=2026,
    )
    payload = {
        "schema": "beast-v8-clean-sorting-baseline-v1",
        "pre_registration": {
            "direct_solution_gate": "no one-operation direct candidate may pass all three evaluator-owned audit suites",
            "random_baseline_gate": "no perfect program in the seeded 500-organism initial population and best fitness < 0.20",
            "profile_transition_generations": [phase.starts_at_generation for phase in PHASES],
        },
        "primitive_manifest": clean_primitive_manifest(),
        "audit": record,
    }
    output = Path("docs/v8-clean-sorting-baseline.json")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "status": record["status"], "baseline": record["baseline"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
