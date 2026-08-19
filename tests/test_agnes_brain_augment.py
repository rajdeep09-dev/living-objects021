from __future__ import annotations

import json
from pathlib import Path

import pytest

from agnes_brain.training_data.augment import build_augmented_dataset, write_augmented_dataset


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASE_DATASET = REPOSITORY_ROOT / "agnes_brain" / "training_data" / "dataset.jsonl"


def test_augmentation_reaches_target_with_explicit_synthetic_and_deterministic_provenance() -> None:
    records, manifest = build_augmented_dataset(BASE_DATASET)
    synthetic = [record for record in records if record["source"].get("kind") == "synthetic_template_variation"]
    evaluator_reruns = [
        record for record in records
        if record["category"] == "test_case" and record["source"].get("seed") in range(1, 11)
    ]

    assert manifest["base_examples"] == 78
    assert manifest["synthetic_template_variants"] == 345
    assert manifest["deterministic_evaluator_reruns"] == 90
    assert manifest["total_examples"] == 513
    assert len(records) == 513
    assert len({record["record_id"] for record in records}) == len(records)
    assert len(synthetic) == 345
    assert all(record["source"]["is_new_measured_run"] is False for record in synthetic)
    assert len(evaluator_reruns) == 90
    assert all(record["source"]["candidate_programs_executed"] == 0 for record in evaluator_reruns)


def test_augmentation_writes_a_separate_create_once_corpus_and_manifest(tmp_path: Path) -> None:
    output = tmp_path / "dataset.augmented.jsonl"
    manifest_output = tmp_path / "dataset.augmentation.manifest.json"

    manifest = write_augmented_dataset(output, manifest_output, source_dataset=BASE_DATASET)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == manifest["total_examples"] == 513
    assert json.loads(manifest_output.read_text(encoding="utf-8")) == manifest
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_augmented_dataset(output, manifest_output, source_dataset=BASE_DATASET)
