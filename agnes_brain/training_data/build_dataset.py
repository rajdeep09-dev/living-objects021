"""Build a local instruction corpus from source-labelled AGNES-BRAIN records.

Only records with complete outputs are eligible. In particular, a champion
record whose explanation is ``FILL`` is excluded rather than being presented to
a model as a completed supervision example.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


TRAINING_DATA_ROOT = Path(__file__).resolve().parent
DEFAULT_PRIMITIVES = TRAINING_DATA_ROOT / "primitives" / "from_codebase.jsonl"
DEFAULT_TEST_CASES = TRAINING_DATA_ROOT / "test_cases" / "from_evaluators.jsonl"
DEFAULT_EXPLANATIONS = TRAINING_DATA_ROOT / "explanations" / "from_champions.jsonl"
DEFAULT_DESTINATION = TRAINING_DATA_ROOT / "dataset.jsonl"
DEFAULT_MANIFEST = TRAINING_DATA_ROOT / "dataset.manifest.json"


@dataclass(frozen=True)
class DatasetBuild:
    records: tuple[dict[str, Any], ...]
    manifest: dict[str, Any]


def _read_jsonl(path: str | Path) -> tuple[dict[str, Any], ...]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"required local source corpus does not exist: {source}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{source}:{line_number} is not an object")
        rows.append(row)
    return tuple(rows)


def _dataset_id(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "instruction-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _instruction_record(
    *,
    category: str,
    instruction: str,
    input_payload: Any,
    output_payload: Any,
    source_record: dict[str, Any],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": "agnes-brain-instruction-v1",
        "category": category,
        "instruction": instruction,
        "input": json.dumps(input_payload, sort_keys=True, separators=(",", ":")),
        "output": json.dumps(output_payload, sort_keys=True, separators=(",", ":")),
        "source_record_id": source_record["record_id"],
        "source": source_record["source"],
    }
    record["record_id"] = _dataset_id(record)
    return record


def build_dataset(
    *,
    primitives_path: str | Path = DEFAULT_PRIMITIVES,
    test_cases_path: str | Path = DEFAULT_TEST_CASES,
    explanations_path: str | Path = DEFAULT_EXPLANATIONS,
) -> DatasetBuild:
    """Create instruction rows and a manifest from checked-in local corpora."""

    primitives = _read_jsonl(primitives_path)
    test_cases = _read_jsonl(test_cases_path)
    explanations = _read_jsonl(explanations_path)
    records: list[dict[str, Any]] = []
    for row in primitives:
        records.append(
            _instruction_record(
                category="primitive",
                instruction="Suggest one primitive for this GP task",
                input_payload={"task": row["task"], "existing_primitives": row["existing_primitives"]},
                output_payload=row["suggested"],
                source_record=row,
            )
        )
    for row in test_cases:
        records.append(
            _instruction_record(
                category="test_case",
                instruction="Generate 15 test cases following this pattern",
                input_payload={"evaluator": row["evaluator"], "examples": row["input_examples"]},
                output_payload=row["output_examples"],
                source_record=row,
            )
        )
    complete_explanations = [row for row in explanations if isinstance(row.get("explanation"), str) and row["explanation"] != "FILL"]
    for row in complete_explanations:
        records.append(
            _instruction_record(
                category="explanation",
                instruction="Explain what this evolved program computes",
                input_payload={"task": row["task"], "source_code": row["source_code"]},
                output_payload=row["explanation"],
                source_record=row,
            )
        )
    if len({record["record_id"] for record in records}) != len(records):
        raise ValueError("instruction dataset contains a duplicate content-derived record ID")
    manifest = {
        "schema_version": "agnes-brain-dataset-manifest-v1",
        "source_counts": {
            "primitive": len(primitives),
            "test_case": len(test_cases),
            "complete_explanation": len(complete_explanations),
            "excluded_incomplete_explanation": len(explanations) - len(complete_explanations),
        },
        "total_examples": len(records),
        "provenance_note": "Dataset contains only declared local records. Incomplete FILL explanations are excluded, not imputed.",
    }
    return DatasetBuild(records=tuple(records), manifest=manifest)


def write_dataset(
    destination: str | Path = DEFAULT_DESTINATION,
    manifest_destination: str | Path = DEFAULT_MANIFEST,
    **source_paths: str | Path,
) -> DatasetBuild:
    """Create the dataset and manifest atomically enough to avoid silent overwrite."""

    dataset_path = Path(destination)
    manifest_path = Path(manifest_destination)
    if dataset_path.exists() or manifest_path.exists():
        existing = dataset_path if dataset_path.exists() else manifest_path
        raise FileExistsError(f"refusing to overwrite existing dataset output: {existing}")
    build = build_dataset(**source_paths)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with dataset_path.open("x", encoding="utf-8") as handle:
        for record in build.records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(build.manifest, handle, sort_keys=True, indent=2)
        handle.write("\n")
    dataset_path.chmod(0o600)
    manifest_path.chmod(0o600)
    return build


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local AGNES-BRAIN instruction dataset.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    build = write_dataset(args.output, args.manifest)
    counts = build.manifest["source_counts"]
    print(
        f"Total: {build.manifest['total_examples']} examples "
        f"({counts['primitive']} primitive, {counts['test_case']} test_case, {counts['complete_explanation']} explanation; "
        f"{counts['excluded_incomplete_explanation']} incomplete explanations excluded)"
    )


if __name__ == "__main__":
    main()
