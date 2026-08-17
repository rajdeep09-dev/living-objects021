from __future__ import annotations

import json
from pathlib import Path

from evolution.proof_benchmark import ProofBenchmarkConfig, run_proof_benchmark, verify_proof_artifact


def _small_config(**overrides: object) -> ProofBenchmarkConfig:
    values: dict[str, object] = {
        "seed": 731,
        "generations": 8,
        "population_size": 16,
        "audit_case_count": 20,
        "minimum_holdout_delta": 0.10,
    }
    values.update(overrides)
    return ProofBenchmarkConfig(**values)  # type: ignore[arg-type]


def test_proof_manifest_records_random_baseline_and_execution_boundary(tmp_path: Path) -> None:
    artifact = run_proof_benchmark(_small_config(), tmp_path / "trial.json")

    assert len(artifact["initial_population"]) == 16
    assert artifact["initial_champion"]["genome_sha256"]
    assert artifact["audit_suites"]["train"]["seed"] != artifact["audit_suites"]["holdout"]["seed"]
    assert artifact["audit_suites"]["selection_uses_audit_suites"] is False
    assert artifact["task"]["execution"] == "typed_ast_interpreter_only"
    assert artifact["task"]["llm_calls"] == 0
    assert artifact["task"]["network_calls"] == 0
    assert artifact["task"]["generated_source_executed"] is False
    assert artifact["task"]["direct_target_primitive_present"] is False
    assert (tmp_path / "trial.json").exists()
    assert (tmp_path / "trial.json.sha256").exists()


def test_proof_artifact_independently_reruns_exactly(tmp_path: Path) -> None:
    path = tmp_path / "trial.json"
    run_proof_benchmark(_small_config(seed=732), path)
    verification = verify_proof_artifact(path)

    assert verification["verified"] is True
    assert verification["mismatches"] == []
    assert verification["execution_boundary"]["llm_calls"] == 0
    assert verification["excluded_host_timing_telemetry"] == [
        "fitness_result.efficiency",
        "fitness_result.wall_time_ms",
    ]


def test_proof_verification_excludes_host_timing_telemetry(tmp_path: Path) -> None:
    path = tmp_path / "trial.json"
    run_proof_benchmark(_small_config(seed=734), path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["initial_population"][0]["fitness_result"]["efficiency"] = -1.0
    payload["initial_population"][0]["fitness_result"]["wall_time_ms"] = 9_999.0
    path.write_text(json.dumps(payload), encoding="utf-8")

    verification = verify_proof_artifact(path)

    assert verification["verified"] is True
    assert verification["mismatches"] == []


def test_tampered_proof_artifact_is_reported_as_a_verification_failure(tmp_path: Path) -> None:
    path = tmp_path / "trial.json"
    run_proof_benchmark(_small_config(seed=733), path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["final_audits"]["holdout"]["objective_score"] = -1.0
    path.write_text(json.dumps(payload), encoding="utf-8")

    verification = verify_proof_artifact(path)
    assert verification["verified"] is False
    assert "final_audits" in verification["mismatches"]


def test_promotion_requires_the_declared_independent_holdout_threshold() -> None:
    artifact = run_proof_benchmark(_small_config(minimum_holdout_delta=0.99))

    assert artifact["decision"]["promoted"] is False
    assert artifact["decision"]["minimum_holdout_delta"] == 0.99
    assert "No promotion" in artifact["decision"]["reason"]
