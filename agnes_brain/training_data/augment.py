"""Produce a separately materialized, provenance-labelled local augmentation corpus.

Template variants are labelled synthetic and are not new BEAST measurements.
Evaluator variants are regenerated through the approved deterministic evaluator
collector with distinct fixed seeds and still execute zero candidate programs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agnes_brain.training_data.collect_test_cases import build_examples as build_evaluator_examples
from agnes_brain.training_data.build_dataset import DEFAULT_DESTINATION as DEFAULT_DATASET, _instruction_record, _read_jsonl


TRAINING_DATA_ROOT = Path(__file__).resolve().parent
DEFAULT_AUGMENTED_DATASET = TRAINING_DATA_ROOT / "dataset.augmented.jsonl"
DEFAULT_AUGMENT_MANIFEST = TRAINING_DATA_ROOT / "dataset.augmentation.manifest.json"
TASK_VARIANTS = ("lead_scraping", "sorting", "fibonacci", "string_reverse", "compression")
EVALUATOR_SEEDS = tuple(range(1, 11))


def _record_id(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "instruction-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _template_variant(record: dict[str, Any], task_variant: str) -> dict[str, Any]:
    input_payload = json.loads(record["input"])
    input_payload["task"] = task_variant
    augmented: dict[str, Any] = {
        **record,
        "input": json.dumps(input_payload, sort_keys=True, separators=(",", ":")),
        "source": {
            "kind": "synthetic_template_variation",
            "derived_from": record["source"],
            "derived_from_instruction_id": record["record_id"],
            "task_variant": task_variant,
            "is_new_measured_run": False,
        },
    }
    augmented.pop("record_id", None)
    augmented["record_id"] = _record_id(augmented)
    return augmented


def _evaluator_instruction_records() -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for seed in EVALUATOR_SEEDS:
        for row in build_evaluator_examples(seed=seed):
            records.append(
                _instruction_record(
                    category="test_case",
                    instruction="Generate 15 test cases following this pattern",
                    input_payload={"evaluator": row["evaluator"], "examples": row["input_examples"]},
                    output_payload=row["output_examples"],
                    source_record=row,
                )
            )
    return tuple(records)


def build_augmented_dataset(source_dataset: str | Path = DEFAULT_DATASET) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    """Return original plus labelled local augmentation records without writing them."""

    original = _read_jsonl(source_dataset)
    primitive_records = [record for record in original if record.get("category") == "primitive"]
    template_variants = tuple(
        _template_variant(record, task_variant)
        for record in primitive_records
        for task_variant in TASK_VARIANTS
    )
    evaluator_variants = _evaluator_instruction_records()
    all_records = tuple(original) + template_variants + evaluator_variants
    if len({record["record_id"] for record in all_records}) != len(all_records):
        raise ValueError("augmentation would introduce a duplicate instruction record")
    manifest = {
        "schema_version": "agnes-brain-augmentation-manifest-v1",
        "base_examples": len(original),
        "synthetic_template_variants": len(template_variants),
        "deterministic_evaluator_reruns": len(evaluator_variants),
        "complete_explanation_variants": 0,
        "total_examples": len(all_records),
        "template_variant_provenance": "synthetic_template_variation; not a new measured BEAST run",
        "evaluator_rerun_provenance": "approved local deterministic evaluator cases; candidate programs executed: 0",
    }
    return all_records, manifest


def write_augmented_dataset(
    destination: str | Path = DEFAULT_AUGMENTED_DATASET,
    manifest_destination: str | Path = DEFAULT_AUGMENT_MANIFEST,
    *,
    source_dataset: str | Path = DEFAULT_DATASET,
) -> dict[str, Any]:
    """Write a new augmented corpus and manifest, refusing silent replacement."""

    output = Path(destination)
    manifest_output = Path(manifest_destination)
    if output.exists() or manifest_output.exists():
        existing = output if output.exists() else manifest_output
        raise FileExistsError(f"refusing to overwrite existing augmentation output: {existing}")
    records, manifest = build_augmented_dataset(source_dataset)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with manifest_output.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, sort_keys=True, indent=2)
        handle.write("\n")
    output.chmod(0o600)
    manifest_output.chmod(0o600)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the separate local AGNES-BRAIN augmentation corpus.")
    parser.add_argument("--source", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_AUGMENTED_DATASET)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_AUGMENT_MANIFEST)
    args = parser.parse_args()
    manifest = write_augmented_dataset(args.output, args.manifest, source_dataset=args.source)
    print(
        f"Total: {manifest['total_examples']} examples "
        f"({manifest['base_examples']} base, {manifest['synthetic_template_variants']} synthetic template variants, "
        f"{manifest['deterministic_evaluator_reruns']} deterministic evaluator reruns)"
    )


if __name__ == "__main__":
    main()
