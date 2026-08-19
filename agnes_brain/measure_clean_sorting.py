"""Preregistered local negative-control measurement for the BEAST-BRAIN adapter.

The clean-sorting grammar is frozen before the guidance response is considered.
Therefore the CPU byte-bigram preview cannot alter the benchmark configuration.
If controller validation rejects it (the expected result), the two arms have
identical seeds/configuration and are required to produce identical metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agnes_brain.controller import GuidanceDecision, resolve_guidance
from agnes_brain.cpu_smoke import DEFAULT_OUTPUT_DIRECTORY as CPU_SMOKE_OUTPUT, sha256_file
from evolution.clean_sorting import CleanSortingEvaluator, PHASES
from evolution.gp_population import GPPopulation


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CPU_SMOKE_ARTIFACT = CPU_SMOKE_OUTPUT / "experiment.json"
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v13" / "beast-brain-clean-sorting-negative-control-20260819"
PREREGISTRATION = {
    "schema_version": "beast-brain-negative-control-preregistration-v1",
    "task_profile": "clean-sorting-v1",
    "stage_index": 0,
    "population_size": 24,
    "generations": 12,
    "seed": 20260819,
    "holdout_seed": 920260819,
    "holdout_cases": 50,
    "primitive_profile_name": "task-specific",
    "frozen_grammar_rule": "Controller guidance cannot add or remove clean-sorting primitives in this preregistered benchmark.",
    "decision_rule": "If guidance fails the controller contract, the guidance arm must use identical configuration and seed to baseline; any result is a neutral negative control, not model assistance.",
}


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPOSITORY_ROOT))
    except ValueError:
        return str(resolved)


def _run_arm() -> dict[str, Any]:
    evaluator = CleanSortingEvaluator(stage_index=int(PREREGISTRATION["stage_index"]))
    population = GPPopulation(
        evaluator,
        primitives=PHASES[0].primitives,
        primitive_profile_name=str(PREREGISTRATION["primitive_profile_name"]),
        population_size=int(PREREGISTRATION["population_size"]),
        seed=int(PREREGISTRATION["seed"]),
        mutation_rate=0.15,
        crossover_rate=0.8,
        elitism_count=3,
        max_depth=7,
        bloat_penalty=0.001,
    )
    summary = population.run(int(PREREGISTRATION["generations"]))
    champion = population.champion
    heldout = evaluator.batch_evaluate(
        [champion.genome],
        seed=int(PREREGISTRATION["holdout_seed"]),
        n=int(PREREGISTRATION["holdout_cases"]),
    )[0]
    return {
        "generations": summary.generations,
        "best_train_fitness": summary.best_fitness,
        "champion_complexity": champion.genome.complexity(),
        "heldout_score": heldout.score,
        "heldout_correctness": heldout.correctness,
        "heldout_cases": int(PREREGISTRATION["holdout_cases"]),
    }


def _load_preview(artifact_path: Path) -> tuple[str, dict[str, Any]]:
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    if artifact.get("status") != "completed_local_cpu_smoke":
        raise ValueError("CPU smoke artifact must be a completed local CPU smoke result")
    if artifact.get("execution_boundary", {}).get("network_calls") != 0:
        raise ValueError("CPU smoke artifact violates zero-network prerequisite")
    preview = artifact.get("generated_preview", {}).get("text")
    if not isinstance(preview, str):
        raise ValueError("CPU smoke artifact contains no textual preview")
    return preview, artifact


def run_negative_control(
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    *,
    cpu_smoke_artifact: str | Path = DEFAULT_CPU_SMOKE_ARTIFACT,
    raw_guidance: str | None = None,
) -> dict[str, Any]:
    """Run a frozen-grammar comparison and emit a create-once local artifact."""

    output = Path(output_directory)
    artifact_path = output / "experiment.json"
    if artifact_path.exists():
        raise FileExistsError(f"refusing to overwrite negative-control artifact: {artifact_path}")
    smoke_path = Path(cpu_smoke_artifact)
    preview, smoke_artifact = _load_preview(smoke_path)
    decision: GuidanceDecision = resolve_guidance(preview if raw_guidance is None else raw_guidance)
    baseline = _run_arm()
    guidance_arm = _run_arm()
    if baseline != guidance_arm:
        raise RuntimeError("neutral negative-control arms diverged despite identical frozen configuration")
    guidance_effect = (
        "no_op_rejected_guidance" if not decision.accepted else "no_op_frozen_clean_sorting_grammar"
    )
    artifact = {
        "schema_version": "beast-brain-clean-sorting-negative-control-v1",
        "status": "completed_local_negative_control",
        "preregistration": PREREGISTRATION,
        "cpu_smoke_input": {
            "path": _display_path(smoke_path),
            "sha256": sha256_file(smoke_path),
            "model_type": smoke_artifact["model"]["type"],
        },
        "guidance_decision": decision.audit_record(),
        "guidance_effect": guidance_effect,
        "baseline": baseline,
        "guidance_arm": guidance_arm,
        "result_interpretation": {
            "outcome": "neutral_negative_control",
            "claim": "No BEAST-BRAIN-assisted benchmark improvement was measured. The controller rejected or ignored the local CPU preview while the clean grammar remained frozen.",
            "not_established": [
                "model-guided primitive selection",
                "benchmark improvement",
                "general program synthesis",
                "autonomous self-improvement",
            ],
        },
        "execution_boundary": {
            "network_calls": 0,
            "llm_calls": 0,
            "local_model_rerun": False,
            "generated_source_executed": False,
            "persistent_worker_started": False,
            "candidate_program_execution": "bounded interpreter only through the existing clean-sorting evaluator",
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    with artifact_path.open("x", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    artifact_path.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the BEAST-BRAIN clean-sorting negative-control comparison.")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--cpu-smoke-artifact", type=Path, default=DEFAULT_CPU_SMOKE_ARTIFACT)
    args = parser.parse_args()
    artifact = run_negative_control(args.output_directory, cpu_smoke_artifact=args.cpu_smoke_artifact)
    print(
        f"Negative control complete: {artifact['guidance_effect']}; "
        f"held-out correctness {artifact['baseline']['heldout_correctness']:.6f}; "
        "no BEAST-BRAIN-assisted improvement was claimed."
    )


if __name__ == "__main__":
    main()
