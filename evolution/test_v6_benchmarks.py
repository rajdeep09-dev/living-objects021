from __future__ import annotations

from pathlib import Path

from scripts.run_v6_benchmarks import run_task


def test_v6_benchmark_runner_records_held_out_correctness_and_checkpoint(tmp_path: Path) -> None:
    result = run_task("absolute-difference", generations=4, population_size=8, seed=7, checkpoint_dir=tmp_path, batch_size=2)
    assert result["state"] == "completed"
    assert result["generations"] == 4
    assert 0.0 <= result["held_out_correctness"] <= 1.0
    assert Path(result["checkpoint"]).exists()
    assert "def champion_absolute_difference_gen4" in result["source_export"]
