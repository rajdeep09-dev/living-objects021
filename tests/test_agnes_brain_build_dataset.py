from __future__ import annotations

import json
from pathlib import Path

import pytest

from agnes_brain.training_data.build_dataset import build_dataset, write_dataset


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TRAINING_ROOT = REPOSITORY_ROOT / "agnes_brain" / "training_data"


def test_dataset_builder_uses_complete_local_records_and_excludes_fill_explanations() -> None:
    build = build_dataset()
    counts = build.manifest["source_counts"]

    assert counts == {
        "primitive": 69,
        "test_case": 9,
        "complete_explanation": 0,
        "excluded_incomplete_explanation": 16,
    }
    assert build.manifest["total_examples"] == 78
    assert len(build.records) == 78
    assert {record["category"] for record in build.records} == {"primitive", "test_case"}
    assert all("FILL" not in record["output"] for record in build.records)
    assert all(record["source_record_id"] for record in build.records)


def test_dataset_builder_writes_a_truthful_manifest_without_overwriting(tmp_path: Path) -> None:
    output = tmp_path / "dataset.jsonl"
    manifest = tmp_path / "dataset.manifest.json"

    build = write_dataset(output, manifest)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    written_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    assert rows == list(build.records)
    assert written_manifest == build.manifest
    assert output.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_dataset(output, manifest)
