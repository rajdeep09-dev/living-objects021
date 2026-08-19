"""Contracts for the exact local 28.9M BEAST-BRAIN architecture specification."""

from __future__ import annotations

import json

import pytest

torch = pytest.importorskip("torch")

from agnes_brain.transformer_28m import (  # noqa: E402
    DEFAULT_CONFIG,
    ByteTransformer28M,
    build_local_data_manifest,
    parameter_count,
    write_training_contract,
)


def test_default_configuration_is_exactly_declared_approximately_28_point_9m() -> None:
    assert DEFAULT_CONFIG.expected_parameter_count == 28_864_544
    model = ByteTransformer28M(DEFAULT_CONFIG)
    assert parameter_count(model) == 28_864_544


def test_transformer_forward_contract_preserves_local_byte_vocabulary() -> None:
    model = ByteTransformer28M(DEFAULT_CONFIG)
    tokens = torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8]], dtype=torch.long)
    targets = torch.tensor([[2, 3, 4, 5, 6, 7, 8, 9]], dtype=torch.long)
    logits, loss = model(tokens, targets)
    assert tuple(logits.shape) == (1, 8, 256)
    assert loss is not None
    assert float(loss.detach()) > 0.0


def test_manifest_is_stable_and_excludes_synthetic_augmentation() -> None:
    first, train_bytes, holdout_bytes = build_local_data_manifest()
    second, _, _ = build_local_data_manifest()
    assert first == second
    assert first.total_records == 78
    assert first.train_records == 66
    assert first.holdout_records == 12
    assert first.source_policy.endswith("synthetic augmentation excluded")
    assert train_bytes and holdout_bytes


def test_training_contract_is_create_once_and_records_no_network_boundary(tmp_path) -> None:
    manifest, _, _ = build_local_data_manifest()
    destination = write_training_contract(tmp_path / "contract.json", DEFAULT_CONFIG, manifest)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["model"]["parameter_count"] == 28_864_544
    assert payload["execution_boundary"]["network_calls"] == 0
    with pytest.raises(FileExistsError):
        write_training_contract(destination, DEFAULT_CONFIG, manifest)
