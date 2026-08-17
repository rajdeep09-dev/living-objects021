"""Falsifiable, interpreter-only evidence runner for BEAST genetic programming.

This module deliberately exposes the machinery needed to disprove a claimed
improvement.  It records the random initial population before selection,
evaluates final and initial champions on fixed audit suites, writes JSON-only
artifacts, and can independently re-run an artifact from its configuration.
It contains no LLM client, network client, ``exec`` path, or source evaluator.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from evolution.fitness import FitnessEvaluator, ManhattanDistanceEvaluator
from evolution.gp_population import GPPopulation


SCHEMA_VERSION = 1
TASK_ID = "manhattan-distance-v1"
TRAIN_AUDIT_SEED = 42_424
HOLDOUT_SEED = 90_001
DEFAULT_CASE_COUNT = 128


@dataclass(frozen=True)
class ProofBenchmarkConfig:
    """All evolution-relevant inputs required for an independent rerun."""

    seed: int
    generations: int = 1_000
    population_size: int = 128
    train_audit_seed: int = TRAIN_AUDIT_SEED
    holdout_seed: int = HOLDOUT_SEED
    audit_case_count: int = DEFAULT_CASE_COUNT
    mutation_rate: float = 0.22
    crossover_rate: float = 0.85
    elitism_count: int = 4
    max_depth: int = 7
    minimum_holdout_delta: float = 0.10

    def validate(self) -> None:
        if not 1 <= self.generations <= 10_000:
            raise ValueError("generations must be in 1..10000")
        if not 2 <= self.population_size <= 512:
            raise ValueError("population_size must be in 2..512")
        if not 20 <= self.audit_case_count <= 1_024:
            raise ValueError("audit_case_count must be in 20..1024")
        if not 0.0 < self.minimum_holdout_delta <= 1.0:
            raise ValueError("minimum_holdout_delta must be in (0, 1]")


def _evaluator_for(task_id: str) -> FitnessEvaluator:
    if task_id != TASK_ID:
        raise ValueError(f"unsupported proof benchmark task: {task_id}")
    return ManhattanDistanceEvaluator()


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _without_timing_telemetry(value: Any) -> Any:
    """Copy an artifact field while removing host-noise from fitness telemetry.

    Fitness selection uses objective correctness rather than latency.  The
    population artifact retains ``wall_time_ms`` and the derived efficiency for
    operational inspection, but another process cannot reproduce either value
    bit-for-bit because scheduler and host load are not controlled.  Independent
    proof verification must therefore compare the deterministic evolution
    contract, not incidental timing samples.
    """
    if isinstance(value, list):
        return [_without_timing_telemetry(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _without_timing_telemetry(item)
            for key, item in value.items()
            if key not in {"efficiency", "wall_time_ms"}
        }
    return value


def _program_record(genome: Any, score: float) -> dict[str, Any]:
    tree = genome.to_dict()
    return {
        "genome": tree,
        "genome_sha256": _sha256(tree),
        "nodes": genome.complexity(),
        "depth": genome.depth(),
        "objective_score": score,
        # Audit text only. Scoring below uses genome.execute through evaluator.
        "source_audit_export": genome.to_python("evolved_program"),
    }


def _score(genome: Any, evaluator: FitnessEvaluator, seed: int, cases: int) -> dict[str, Any]:
    result = evaluator.batch_evaluate([genome], seed=seed, n=cases)[0]
    return {
        "seed": seed,
        "cases": cases,
        "objective_score": result.score,
        "exact_correctness": result.correctness,
        "exact_cases_passed": result.test_cases_passed,
        "exact_cases_total": result.test_cases_total,
    }


def _run(config: ProofBenchmarkConfig) -> dict[str, Any]:
    config.validate()
    evaluator = _evaluator_for(TASK_ID)
    population = GPPopulation(
        evaluator=evaluator,
        population_size=config.population_size,
        seed=config.seed,
        crossover_rate=config.crossover_rate,
        mutation_rate=config.mutation_rate,
        elitism_count=config.elitism_count,
        max_depth=config.max_depth,
    )
    population.initialize()
    initial_population = [organism.to_dict() for organism in population.population]
    initial_champion = population.champion
    initial_train = _score(initial_champion.genome, evaluator, config.train_audit_seed, config.audit_case_count)
    initial_holdout = _score(initial_champion.genome, evaluator, config.holdout_seed, config.audit_case_count)
    initial_record = _program_record(initial_champion.genome, initial_champion.fitness)

    # All selection feedback comes from GPPopulation's fixed, bounded interpreter
    # evaluation. It does not receive either audit seed below.
    for _ in range(config.generations):
        population.step()

    champion = population.champion
    final_train = _score(champion.genome, evaluator, config.train_audit_seed, config.audit_case_count)
    final_holdout = _score(champion.genome, evaluator, config.holdout_seed, config.audit_case_count)
    final_record = _program_record(champion.genome, champion.fitness)
    train_delta = final_train["objective_score"] - initial_train["objective_score"]
    holdout_delta = final_holdout["objective_score"] - initial_holdout["objective_score"]
    structurally_changed = initial_record["genome_sha256"] != final_record["genome_sha256"]
    promoted = bool(
        structurally_changed
        and train_delta > 0.0
        and holdout_delta >= config.minimum_holdout_delta
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "task": {
            "id": TASK_ID,
            "target": "abs(x2 - x1) + abs(y2 - y1)",
            "direct_target_primitive_present": False,
            "execution": "typed_ast_interpreter_only",
            "llm_calls": 0,
            "network_calls": 0,
            "generated_source_executed": False,
        },
        "config": asdict(config),
        "audit_suites": {
            "train": {"seed": config.train_audit_seed, "cases": config.audit_case_count},
            "holdout": {"seed": config.holdout_seed, "cases": config.audit_case_count},
            "selection_uses_audit_suites": False,
        },
        "initial_population": initial_population,
        "initial_champion": initial_record,
        "final_champion": final_record,
        "initial_audits": {"train": initial_train, "holdout": initial_holdout},
        "final_audits": {"train": final_train, "holdout": final_holdout},
        "history": [asdict(item) for item in population.history],
        "decision": {
            "train_delta": train_delta,
            "holdout_delta": holdout_delta,
            "structurally_changed": structurally_changed,
            "minimum_holdout_delta": config.minimum_holdout_delta,
            "promoted": promoted,
            "reason": (
                "Independent holdout improved beyond the configured threshold."
                if promoted
                else "No promotion: baseline separation, structural change, train gain, or holdout threshold failed."
            ),
        },
    }


def run_proof_benchmark(config: ProofBenchmarkConfig, artifact_path: str | Path | None = None) -> dict[str, Any]:
    """Run one deterministic trial and optionally write JSON plus a detached digest."""
    artifact = _run(config)
    if artifact_path is not None:
        path = Path(artifact_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
        path.write_text(encoded, encoding="utf-8")
        path.with_suffix(path.suffix + ".sha256").write_text(
            hashlib.sha256(encoded.encode("utf-8")).hexdigest() + "\n", encoding="utf-8"
        )
    return artifact


def verify_proof_artifact(artifact_path: str | Path) -> dict[str, Any]:
    """Independently recreate a trial and compare all deterministic proof fields."""
    stored = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    if int(stored.get("schema_version", 0)) != SCHEMA_VERSION:
        raise ValueError("unsupported proof artifact schema")
    if stored.get("task", {}).get("id") != TASK_ID:
        raise ValueError("proof artifact task does not match this verifier")
    rerun = _run(ProofBenchmarkConfig(**stored["config"]))
    paths = (
        "task", "config", "audit_suites", "initial_population", "initial_champion", "final_champion",
        "initial_audits", "final_audits", "history", "decision",
    )
    mismatches = [
        path
        for path in paths
        if _without_timing_telemetry(stored.get(path))
        != _without_timing_telemetry(rerun.get(path))
    ]
    return {
        "artifact": str(artifact_path),
        "verified": not mismatches,
        "mismatches": mismatches,
        "rerun_decision": rerun["decision"],
        "execution_boundary": rerun["task"],
        "excluded_host_timing_telemetry": ["fitness_result.efficiency", "fitness_result.wall_time_ms"],
    }
