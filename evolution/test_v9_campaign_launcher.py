"""Bounded regression for the v9 campaign launcher; it never runs the 100k campaign."""
from __future__ import annotations

from pathlib import Path

from scripts.run_v9_clean_sorting_campaign import DECLARED_SEEDS, run_seed


def test_bounded_campaign_records_non_promotion_label_and_resumes(tmp_path: Path) -> None:
    first = run_seed(DECLARED_SEEDS[0], generations=2, output_dir=tmp_path)
    assert first["status"] == "bounded_execution_completed"
    assert first["eligible_for_declared_campaign_analysis"] is False
    resumed = run_seed(DECLARED_SEEDS[0], generations=3, output_dir=tmp_path, resume=True)
    assert resumed["configuration"]["executed_generations"] == 3
    assert (tmp_path / f"seed_{DECLARED_SEEDS[0]}" / "checkpoint.json").exists()


def test_campaign_rejects_non_preregistered_seed(tmp_path: Path) -> None:
    try:
        run_seed(42, generations=1, output_dir=tmp_path)
    except ValueError as error:
        assert "preregistered" in str(error)
    else:
        raise AssertionError("non-preregistered seed was accepted")
