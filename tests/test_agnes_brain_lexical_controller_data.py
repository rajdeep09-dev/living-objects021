"""Contracts for the narrow, source-backed v17 lexical controller probe."""

from __future__ import annotations

import json

import pytest

from agnes_brain.controller import resolve_guidance
from agnes_brain.lexical_controller_data import build_lexical_controller_split, write_lexical_controller_split


def test_lexical_controller_split_is_source_disjoint_and_name_conditioned() -> None:
    split = build_lexical_controller_split()
    assert len(split.train) == 56
    assert len(split.holdout) == 10
    assert split.manifest["evaluation"]["semantic_task_selection"] is False
    train_sources = {row["source_record_id"] for row in split.train}
    holdout_sources = {row["source_record_id"] for row in split.holdout}
    assert train_sources.isdisjoint(holdout_sources)
    for row in (*split.train, *split.holdout):
        input_payload = json.loads(row["input"])
        target = json.loads(row["output"])
        assert input_payload["candidate_name_words"] == target["name"].replace("_", " ")
        assert "existing_primitives" not in input_payload
        assert row["benchmark"]["generated_text_executed"] is False
        assert resolve_guidance(row["output"], profile_name="default").accepted


def test_lexical_controller_writer_is_create_once(tmp_path) -> None:
    split = write_lexical_controller_split(tmp_path / "lexical-evidence")
    assert len(split.train) > len(split.holdout) > 0
    with pytest.raises(FileExistsError):
        write_lexical_controller_split(tmp_path / "lexical-evidence")
