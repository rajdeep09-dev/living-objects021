"""Compile the read-only v9 observatory evidence artifact from engine contracts."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evolution.v9_federation import EXCHANGE_SCHEMA, available_discoveries
from evolution.v9_sorting_curriculum import primitive_manifest
from living_objects.sdk import RUN_SCHEMA, SDK_VERSION, audit
from production.api.v9.routes import INLINE_GENERATION_LIMIT


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "v9-observatory-evidence.json"
SCHEMA = "beast-v9-observatory-evidence-v1"
INVENTORY = ROOT / "docs" / "v9-test-inventory.json"


def coverage_evidence() -> dict[str, Any]:
    try:
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("v9 observatory evidence requires a readable pytest inventory") from error
    collected = inventory.get("collected_cases")
    command = inventory.get("command")
    if not isinstance(collected, int) or collected < 1_000:
        raise ValueError("v9 observatory evidence requires a collected pytest inventory of at least 1,000 cases")
    if not isinstance(command, str) or not command:
        raise ValueError("v9 observatory evidence requires the inventory collection command")
    return {
        "collected_cases": collected,
        "numerical_gate": "MET",
        "threshold": 1_000,
        "collection_command": command,
        "claim_boundary": "This confirms a collected coverage threshold only; the separately recorded full-suite pass and experimental claims remain bounded by their own evidence artifacts.",
    }


def build_payload() -> dict[str, Any]:
    discoveries = available_discoveries()
    clean_sorting = audit("clean-sorting")
    manhattan = audit("manhattan-distance")
    coverage = coverage_evidence()
    if len(discoveries) != 5:
        raise ValueError("v9 observatory evidence requires exactly five eligible persisted discovery records")
    if clean_sorting.status != "NEGATIVE_RESULT":
        raise ValueError("v9 observatory evidence requires the retained clean-sorting negative result")
    if manhattan.status != "VALID_COMPOSITIONAL_RESULT":
        raise ValueError("v9 observatory evidence requires the measured Manhattan classification")
    return {
        "schema": SCHEMA,
        "sdk": {
            "version": SDK_VERSION,
            "run_schema": RUN_SCHEMA,
            "supported_tasks": ["manhattan-distance", "clean-sorting"],
            "generation_limit": 10_000,
            "runtime": "typed AST interpreter only",
            "generated_source_executed": False,
        },
        "curriculum": primitive_manifest(),
        "federation": {
            "schema": EXCHANGE_SCHEMA,
            "verified_record_count": len(discoveries),
            "verified_record_ids": [record["record_id"] for record in discoveries],
            "admission_rule": "A signature, fresh-record identity, and exact local persisted-artifact comparison are all required before memome admission.",
            "network_transport": "not implemented by this local exchange MVP",
            "generated_source_executed": False,
        },
        "service": {
            "inline_generation_limit": INLINE_GENERATION_LIMIT,
            "persistent_worker_configured": False,
            "long_run_boundary": "Requests above the inline generation limit are returned as preregistered-campaign requirements, not queued as hidden work.",
        },
        "verification": coverage,
        "measured_results": {
            "clean_sorting": {
                "status": clean_sorting.status,
                "claim_boundary": clean_sorting.claim_boundary,
            },
            "manhattan": {
                "status": manhattan.status,
                "eligible_records": [
                    {
                        "record_id": record["record_id"],
                        "seed": record["seed"],
                        "fresh_correctness": record["fresh_suite"]["correctness"],
                        "first_perfect_training_generation": record["first_perfect_training_generation"],
                    }
                    for record in discoveries
                ],
            },
        },
        "claim_boundary": "v9 implements bounded SDK, curriculum, exchange, API, and observatory contracts. It does not establish a clean-sorting success, a deployed federation, a persistent worker, a 100,000-generation result, or general intelligence.",
        "sources": [
            "living_objects/sdk.py",
            "evolution/v9_sorting_curriculum.py",
            "evolution/v9_federation.py",
            "production/api/v9/routes.py",
            "docs/v8-benchmark-ledger.json",
            "docs/v8-discovery-log.json",
            "docs/v9-test-inventory.json",
        ],
    }


def write(path: Path = OUTPUT) -> Path:
    path.write_text(json.dumps(build_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    print(write())
