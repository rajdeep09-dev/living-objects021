"""Regression coverage for the reproducible cellular experiment entry point."""
from __future__ import annotations

from scripts.run_cellular_experiment import run_experiment


def test_cellular_experiment_has_disjoint_truth_measurement_and_finite_history():
    """The public runner exposes a finite, independently measured experiment."""

    result = run_experiment(
        generations=4,
        population_size=12,
        train_seeds=(31, 47, 59, 71),
        holdout_seeds=(901, 907, 911),
        seed=20260814,
        ticks=20,
    )

    history = result["history"]
    configuration = result["configuration"]
    assert isinstance(history, list)
    assert len(history) == 4
    assert isinstance(configuration, dict)
    assert set(configuration["train_seeds"]).isdisjoint(configuration["holdout_seeds"])
    assert result["promoted_holdout_score"] >= 0.0
    assert result["baseline_holdout_score"] >= 0.0
