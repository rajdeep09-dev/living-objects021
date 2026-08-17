"""Render the Manhattan learning-curve figure from persisted v8 trial artifacts.

This script performs no evolution. It reads the five declared v8 Manhattan trial
histories and plots their recorded best training fitness at every generation.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


ROOT = Path(__file__).resolve().parents[1]
TRIAL_ROOT = ROOT / "reports" / "v8" / "manhattan-distance"
OUTPUT = ROOT / "docs" / "v9-manhattan-fitness-curves.png"
EXPECTED_SEEDS = (20260814, 20260815, 20260816, 20260817, 20260818)


def load_history(seed: int) -> tuple[list[int], list[float]]:
    """Load the persisted per-generation best fitness for one declared seed."""
    path = TRIAL_ROOT / f"seed_{seed}" / "trial.json"
    with path.open(encoding="utf-8") as handle:
        trial = json.load(handle)
    history = trial["history"]
    if not history:
        raise ValueError(f"Trial history is empty for seed {seed}")
    return (
        [int(row["generation"]) for row in history],
        [float(row["best_fitness"]) for row in history],
    )


def main() -> None:
    """Create a single evidence-backed five-seed learning-curve figure."""
    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axis = plt.subplots(figsize=(8.5, 4.8), layout="constrained")
    inset = inset_axes(axis, width="42%", height="42%", loc="center right", borderpad=2.1)
    for seed in EXPECTED_SEEDS:
        generations, fitness = load_history(seed)
        axis.plot(generations, fitness, linewidth=1.1, alpha=0.86, label=str(seed))
        inset.plot(generations, fitness, linewidth=1.0, alpha=0.9)
    axis.axhline(1.0, color="#303030", linewidth=0.8, linestyle="--", label="perfect training fitness")
    axis.set_title("Persisted v8 Manhattan-distance learning curves")
    axis.set_xlabel("Generation")
    axis.set_ylabel("Best training fitness")
    axis.set_xlim(left=0)
    axis.set_ylim(0.0, 1.02)
    axis.legend(title="Seed", ncols=3, fontsize=8, title_fontsize=8, loc="lower right")
    inset.set_xlim(0, 100)
    inset.set_ylim(0.45, 1.02)
    inset.set_title("0–100 generation detail", fontsize=8)
    inset.tick_params(labelsize=7)
    figure.savefig(OUTPUT, dpi=180)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} from {len(EXPECTED_SEEDS)} persisted trials")


if __name__ == "__main__":
    main()
