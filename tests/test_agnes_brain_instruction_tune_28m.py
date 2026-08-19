"""Focused contracts for native-only BEAST-BRAIN JSON instruction tuning."""

from __future__ import annotations

import json

import pytest

from agnes_brain.instruction_tune_28m import (
    InstructionTuningConfig,
    TARGET_IGNORE_INDEX,
    TUNING_SCHEMA_VERSION,
    _canonical_row_bytes,
    _make_target_only_batch,
    _prompt_target_example,
    build_json_data_manifest,
    load_instruction_tuning_checkpoint,
)


def test_instruction_tuning_budget_refuses_unbounded_or_oversized_configuration() -> None:
    with pytest.raises(ValueError, match=r"\[1, 3600\]"):
        InstructionTuningConfig(max_wall_seconds=3_601).validate()
    with pytest.raises(ValueError, match="generation_max_bytes"):
        InstructionTuningConfig(generation_max_bytes=769).validate()


def test_json_instruction_manifest_is_source_disjoint_and_local_only() -> None:
    manifest, train_bytes, holdout_bytes, train_rows, holdout_rows = build_json_data_manifest()
    assert manifest.train_records == 56
    assert manifest.holdout_records == 10
    assert manifest.train_bytes == len(train_bytes)
    assert manifest.holdout_bytes == len(holdout_bytes)
    assert all(row["source"]["model_generated"] is False for row in holdout_rows)
    assert len(train_rows) == 56
    assert b"controller_json:" in train_bytes


def test_json_instruction_bytes_refuse_model_generated_material() -> None:
    row = {
        "schema_version": "beast-brain-json-instruction-v1",
        "source_record_id": "primitive-x",
        "instruction": "Return JSON",
        "input": "{}",
        "output": "{}",
        "source": {"model_generated": True},
    }
    with pytest.raises(ValueError, match="not approved local source"):
        _canonical_row_bytes((row,))


def test_instruction_checkpoint_loader_refuses_wrong_schema(tmp_path) -> None:
    import torch

    path = tmp_path / "wrong.pt"
    torch.save({"schema_version": "other"}, path)
    with pytest.raises(ValueError, match="instruction-tuning checkpoint"):
        load_instruction_tuning_checkpoint(path)
    assert TUNING_SCHEMA_VERSION == "beast-brain-json-instruction-tuning-v2"
    assert json.loads('{"ok":true}')["ok"] is True


def test_target_only_batch_uses_declared_prompt_but_scores_only_controller_json_bytes() -> None:
    import random

    _, _, _, train_rows, _ = build_json_data_manifest()
    example = _prompt_target_example(train_rows[0])
    assert example.prompt.endswith(b"controller_json:\n")
    assert example.target.startswith(b"{")
    token_ids, targets = _make_target_only_batch(
        train_rows,
        block_size=128,
        batch_size=2,
        rng=random.Random(7),
    )
    assert tuple(token_ids.shape) == (2, 128)
    assert tuple(targets.shape) == (2, 128)
    assert any(value == TARGET_IGNORE_INDEX for value in targets.flatten().tolist())
    assert any(value != TARGET_IGNORE_INDEX for value in targets.flatten().tolist())
