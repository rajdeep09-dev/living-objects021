from __future__ import annotations

import json

from scripts.run_v8_multiseed import run_experiment


def test_v8_runner_records_failures_and_interpreter_only_boundary(tmp_path) -> None:
    result = run_experiment(
        "clean-sorting", output_dir=tmp_path, generations=4, seeds=(101, 102),
    )
    assert result["declared_seeds"] == [101, 102]
    assert result["discovery_log_eligible"] is False
    trial = json.loads((tmp_path / "clean-sorting" / "seed_101" / "trial.json").read_text())
    assert trial["execution_boundary"]["generated_source_executed"] is False
    assert len(trial["history"]) == 5
    assert (tmp_path / "clean-sorting" / "seed_101" / "checkpoint.json").exists()
