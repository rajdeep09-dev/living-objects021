"""Focused safety and persistence contracts for the local 28.9M trainer."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from agnes_brain.train_transformer_28m import (  # noqa: E402
    RUN_SCHEMA_VERSION,
    TrainingRunConfig,
    _make_batch,
    atomic_torch_save,
    load_local_checkpoint,
)


def test_training_budget_refuses_background_sized_deadline_and_cpu_oversubscription() -> None:
    with pytest.raises(ValueError, match="3600"):
        TrainingRunConfig(max_wall_seconds=3_601).validate()
    with pytest.raises(ValueError, match="six-logical"):
        TrainingRunConfig(cpu_threads=7).validate()


def test_byte_batch_is_shifted_and_never_uses_outside_vocabulary() -> None:
    inputs, targets = _make_batch(bytes(range(256)) * 2, block_size=16, batch_size=3, rng=__import__("random").Random(1))
    assert tuple(inputs.shape) == (3, 16)
    assert tuple(targets.shape) == (3, 16)
    assert int(inputs.min()) >= 0 and int(targets.max()) < 256


def test_atomic_checkpoint_loads_only_local_runner_schema(tmp_path) -> None:
    checkpoint = atomic_torch_save({"schema_version": RUN_SCHEMA_VERSION, "step": 3}, tmp_path / "latest.pt")
    assert checkpoint.stat().st_mode & 0o777 == 0o600
    assert load_local_checkpoint(checkpoint)["step"] == 3
    foreign = atomic_torch_save({"schema_version": "foreign"}, tmp_path / "foreign.pt")
    with pytest.raises(ValueError, match="run schema"):
        load_local_checkpoint(foreign)
