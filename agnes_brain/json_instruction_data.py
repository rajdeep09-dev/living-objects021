"""Local-only structured-JSON supervision for the bounded BEAST controller.

This module derives instruction rows exclusively from the checked-in primitive
registry collector.  It never asks a model to create examples: every target is
the source collector's registered primitive metadata, including its concise
rule-based rationale.  The held-out split is by source primitive record, so a
primitive target cannot appear in both tuning and validity measurements.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from agnes_brain.training_data.build_dataset import DEFAULT_PRIMITIVES, _read_jsonl


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v15" / "json-instruction-data"
SCHEMA_VERSION = "beast-brain-json-instruction-v1"
CONTROLLER_KEYS = ("name", "description", "input_types", "output_type", "rationale")


@dataclass(frozen=True)
class JsonInstructionSplit:
    """A disjoint source-labelled tuning and held-out evaluation partition."""

    train: tuple[dict[str, Any], ...]
    holdout: tuple[dict[str, Any], ...]
    manifest: dict[str, Any]


def _stable_holdout(source_record_id: str) -> bool:
    """Return a deterministic approximately-20% source-record split decision."""

    return int(hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()[:8], 16) % 5 == 0


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _example_id(source_record_id: str, output: dict[str, Any]) -> str:
    digest = hashlib.sha256(f"{source_record_id}\n{_canonical_json(output)}".encode("utf-8")).hexdigest()
    return f"json-instruction-{digest[:24]}"


def _instruction(row: dict[str, Any]) -> dict[str, Any]:
    source = row.get("source")
    suggested = row.get("suggested")
    source_record_id = row.get("record_id")
    if not isinstance(source, dict) or not isinstance(suggested, dict) or not isinstance(source_record_id, str):
        raise ValueError("primitive source row does not meet the checked-in collector contract")
    if not source.get("requires_network") is False or not source.get("requires_filesystem") is False:
        raise ValueError("JSON instruction source is not local-only")
    if source.get("has_side_effects") is not False:
        raise ValueError("JSON instruction source has side effects")
    if "default" not in source.get("approved_profiles", []):
        raise ValueError("JSON instruction source is not approved for the default controller profile")
    if set(suggested) != set(CONTROLLER_KEYS):
        raise ValueError("source suggestion does not have the exact controller schema")
    if not isinstance(suggested["name"], str) or not isinstance(suggested["description"], str):
        raise ValueError("source suggestion has invalid text fields")
    if not isinstance(suggested["rationale"], str) or not isinstance(suggested["input_types"], list):
        raise ValueError("source suggestion has invalid rationale or signature")
    prompt = {
        "task": row.get("task", "general"),
        "existing_primitives": row.get("existing_primitives"),
        "response_contract": {
            "json_only": True,
            "required_keys": list(CONTROLLER_KEYS),
            "restriction": "Select one existing default-profile primitive; do not define or execute code.",
        },
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "example_id": _example_id(source_record_id, suggested),
        "instruction": "Return exactly one controller-compatible primitive suggestion as JSON.",
        "input": _canonical_json(prompt),
        "output": _canonical_json(suggested),
        "source_record_id": source_record_id,
        "source": {
            "kind": source.get("kind"),
            "approval_tier": source.get("approval_tier"),
            "approved_profiles": sorted(source.get("approved_profiles", [])),
            "provenance": "checked-in local primitive registry metadata",
            "model_generated": False,
        },
    }
    return result


def build_json_instruction_split(
    source_rows: Iterable[dict[str, Any]] | None = None,
) -> JsonInstructionSplit:
    """Build a source-disjoint JSON tuning/evaluation partition without model calls."""

    rows = tuple(_read_jsonl(DEFAULT_PRIMITIVES) if source_rows is None else source_rows)
    eligible_rows = tuple(
        row
        for row in rows
        if isinstance(row.get("source"), dict) and "default" in row["source"].get("approved_profiles", [])
    )
    examples = tuple(_instruction(row) for row in eligible_rows)
    if len({example["example_id"] for example in examples}) != len(examples):
        raise ValueError("duplicate JSON instruction examples are not allowed")
    train = tuple(example for example in examples if not _stable_holdout(example["source_record_id"]))
    holdout = tuple(example for example in examples if _stable_holdout(example["source_record_id"]))
    if not train or not holdout:
        raise ValueError("deterministic split must contain both train and held-out examples")
    train_names = {json.loads(example["output"])["name"] for example in train}
    holdout_names = {json.loads(example["output"])["name"] for example in holdout}
    if train_names & holdout_names:
        raise ValueError("primitive names must be source-disjoint across JSON split")
    manifest = {
        "schema_version": "beast-brain-json-instruction-manifest-v1",
        "source": {
            "path": str(DEFAULT_PRIMITIVES.relative_to(REPOSITORY_ROOT)),
            "policy": "approved checked-in local primitive records only; no model-generated explanations or synthetic targets",
        },
        "response_schema": {"required_keys": list(CONTROLLER_KEYS), "json_only": True},
        "split": {
            "method": "sha256(source_record_id) modulo 5",
            "train_examples": len(train),
            "holdout_examples": len(holdout),
            "source_disjoint_primitive_names": True,
        },
        "execution_boundary": {"network_calls": 0, "model_calls": 0, "generated_text_executed": False},
        "claim_boundary": "This corpus teaches exact controller syntax for existing primitive metadata; it is not evidence of reasoning, coding, or general language ability.",
    }
    return JsonInstructionSplit(train=train, holdout=holdout, manifest=manifest)


def write_json_instruction_split(
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    source_rows: Iterable[dict[str, Any]] | None = None,
) -> JsonInstructionSplit:
    """Write create-once local JSONL partitions and their auditable manifest."""

    destination = Path(output_directory)
    train_path = destination / "train.jsonl"
    holdout_path = destination / "holdout.jsonl"
    manifest_path = destination / "manifest.json"
    if any(path.exists() for path in (train_path, holdout_path, manifest_path)):
        raise FileExistsError("refusing to overwrite JSON instruction evidence")
    split = build_json_instruction_split(source_rows)
    destination.mkdir(parents=True, exist_ok=True)
    for path, rows in ((train_path, split.train), (holdout_path, split.holdout)):
        with path.open("x", encoding="utf-8") as handle:
            for row in rows:
                handle.write(_canonical_json(row) + "\n")
        path.chmod(0o600)
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(split.manifest, handle, sort_keys=True, indent=2)
        handle.write("\n")
    manifest_path.chmod(0o600)
    return split


__all__ = [
    "CONTROLLER_KEYS",
    "DEFAULT_OUTPUT_DIRECTORY",
    "JsonInstructionSplit",
    "build_json_instruction_split",
    "write_json_instruction_split",
]


def main() -> None:
    """Materialize the checked-in-source JSON instruction evidence once."""

    split = write_json_instruction_split()
    print(
        json.dumps(
            {
                "output_directory": str(DEFAULT_OUTPUT_DIRECTORY.relative_to(REPOSITORY_ROOT)),
                "train_examples": len(split.train),
                "holdout_examples": len(split.holdout),
                "network_calls": 0,
                "model_calls": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
