from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from agnes_brain.cpu_smoke import ByteBigramModel, run_cpu_smoke_experiment


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASE_DATASET = REPOSITORY_ROOT / "agnes_brain" / "training_data" / "dataset.jsonl"


def test_byte_bigram_checkpoint_reload_and_generation_are_deterministic(tmp_path: Path) -> None:
    model = ByteBigramModel.train(("abba", "ababa"))
    checkpoint = tmp_path / "model.npz"
    heldout_nll, _ = model.negative_log_likelihood(("abba",))

    model.save(checkpoint)
    reloaded = ByteBigramModel.load(checkpoint)
    reloaded_nll, _ = reloaded.negative_log_likelihood(("abba",))
    assert np.array_equal(model.counts, reloaded.counts)
    assert heldout_nll == reloaded_nll
    assert model.generate("a", max_new_bytes=16, seed=7) == reloaded.generate("a", max_new_bytes=16, seed=7)
    assert checkpoint.stat().st_mode & 0o077 == 0


def test_cpu_smoke_experiment_records_heldout_measurement_and_strict_boundaries(tmp_path: Path) -> None:
    artifact = run_cpu_smoke_experiment(BASE_DATASET, tmp_path / "experiment")

    assert artifact["status"] == "completed_local_cpu_smoke"
    assert artifact["dataset"]["records"] == 78
    assert artifact["dataset"]["train_records"] > 0
    assert artifact["dataset"]["holdout_records"] > 0
    assert artifact["metrics"]["heldout_nll"] < artifact["metrics"]["uniform_byte_baseline_nll"]
    assert math.isclose(artifact["metrics"]["heldout_nll"], artifact["metrics"]["reload_heldout_nll"], abs_tol=1e-12)
    assert artifact["execution_boundary"] == {
        "network_calls": 0,
        "llm_calls": 0,
        "generated_source_executed": False,
        "persistent_worker_started": False,
        "runtime": "local NumPy CPU byte-bigram only",
    }
    assert artifact["claim_boundary"]["is_llm"] is False
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        run_cpu_smoke_experiment(BASE_DATASET, tmp_path / "experiment")
