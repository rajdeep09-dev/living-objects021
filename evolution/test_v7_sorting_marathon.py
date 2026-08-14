from __future__ import annotations

import json
from pathlib import Path

from scripts.run_v7_sorting_marathon import run_marathon


def test_bounded_sorting_marathon_writes_measured_curve_checkpoint_and_no_false_100k_claim(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    checkpoint = tmp_path / "checkpoints" / "population.json"
    artifact = run_marathon(
        generations=4, seed=211, population_size=8, checkpoint_path=checkpoint,
        report_dir=reports, milestone_interval=2, checkpoint_interval=2, resume=False,
    )
    assert artifact["status"] == "completed"
    assert artifact["claimed_public_100k_marathon_completed"] is False
    assert checkpoint.exists()
    curve = json.loads((reports / "fitness_curve.json").read_text(encoding="utf-8"))
    assert [row["generation"] for row in curve] == list(range(5))
    assert (reports / "milestone_gen_2.md").exists()
    assert (reports / "milestone_gen_4.md").exists()
    report = reports / "BOUNDED_RUN_FINAL_REPORT.md"
    assert report.exists()
    assert not (reports / "FINAL_REPORT.md").exists()
    content = report.read_text(encoding="utf-8")
    assert "not the v7 guide's 100,000-generation public-marathon claim" in content
    assert "def sorting_champion_generation_4" in content
