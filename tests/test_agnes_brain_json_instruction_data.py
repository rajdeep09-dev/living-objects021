"""Regression coverage for provenance-labelled BEAST-BRAIN JSON supervision."""

from __future__ import annotations

import json

import pytest

from agnes_brain.controller import resolve_guidance
from agnes_brain.json_instruction_data import CONTROLLER_KEYS, build_json_instruction_split, write_json_instruction_split


def test_json_instruction_split_is_source_disjoint_and_controller_valid() -> None:
    split = build_json_instruction_split()
    assert len(split.train) + len(split.holdout) >= 30
    train_sources = {record["source_record_id"] for record in split.train}
    holdout_sources = {record["source_record_id"] for record in split.holdout}
    assert train_sources.isdisjoint(holdout_sources)
    for record in (*split.train, *split.holdout):
        output = json.loads(record["output"])
        assert set(output) == set(CONTROLLER_KEYS)
        decision = resolve_guidance(record["output"], profile_name="default")
        assert decision.accepted
        assert record["source"]["model_generated"] is False


def test_json_instruction_outputs_are_deterministic() -> None:
    first = build_json_instruction_split()
    second = build_json_instruction_split()
    assert first.train == second.train
    assert first.holdout == second.holdout
    assert first.manifest == second.manifest
    assert first.manifest["split"]["source_disjoint_primitive_names"] is True


def test_json_instruction_writer_is_create_once(tmp_path) -> None:
    split = write_json_instruction_split(tmp_path / "evidence")
    assert len(split.train) > len(split.holdout) > 0
    manifest = json.loads((tmp_path / "evidence" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["execution_boundary"]["model_calls"] == 0
    with pytest.raises(FileExistsError):
        write_json_instruction_split(tmp_path / "evidence")
