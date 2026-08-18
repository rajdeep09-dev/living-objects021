from __future__ import annotations

import json
import os

import pytest

from living_objects import audit, evolve, export, reproduce


def test_sdk_evolve_persists_real_bounded_run_and_declares_interpreter_boundary(tmp_path) -> None:
    result = evolve("manhattan", generations=3, seed=712, population_size=12, artifact_dir=tmp_path)

    assert result.task == "manhattan-distance"
    assert result.champion["generation"] == 3
    assert result.fitness == result.champion["training_fitness"]
    assert result.source_code == result.champion["source_audit_export"]
    assert "def beast_3" in result.source_code
    assert result.execution_boundary == {
        "runtime": "typed AST interpreter only",
        "llm_calls": 0,
        "network_calls": 0,
        "generated_source_executed": False,
    }
    assert result.artifact_path is not None
    persisted = json.loads((tmp_path / f"{result.run_id}.json").read_text(encoding="utf-8"))
    assert persisted["result"]["champion"]["tree_sha256"] == result.champion["tree_sha256"]
    if os.name == "posix":
        assert (tmp_path / f"{result.run_id}.json").stat().st_mode & 0o077 == 0


def test_sdk_compatibility_accessors_remain_available_after_artifact_round_trip(tmp_path) -> None:
    result = evolve("manhattan", generations=2, seed=713, population_size=12, artifact_dir=tmp_path)
    persisted = json.loads((tmp_path / f"{result.run_id}.json").read_text(encoding="utf-8"))["result"]

    restored = type(result)(**(persisted | {"artifact_path": result.artifact_path}))

    assert restored.fitness == float(persisted["champion"]["training_fitness"])
    assert restored.source_code == persisted["champion"]["source_audit_export"]
    assert "def beast_" in restored.source_code


def test_sdk_reproduce_reruns_the_saved_deterministic_configuration(tmp_path) -> None:
    original = evolve("manhattan-distance", generations=4, seed=44, population_size=10, artifact_dir=tmp_path)

    rerun = reproduce(original.run_id, artifact_dir=tmp_path)

    assert rerun.verified is True
    assert rerun.mismatches == []
    assert rerun.expected_tree_sha256 == rerun.reproduced_tree_sha256


def test_sdk_reproduction_rejects_tampered_deterministic_artifact(tmp_path) -> None:
    original = evolve("manhattan", generations=2, seed=99, population_size=10, artifact_dir=tmp_path)
    path = tmp_path / f"{original.run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["result"]["champion"]["tree_sha256"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")

    rerun = reproduce(original.run_id, artifact_dir=tmp_path)

    assert rerun.verified is False
    assert "champion" in rerun.mismatches


def test_sdk_audit_exposes_retraction_and_retained_negative_result_from_persisted_ledger() -> None:
    sorting = audit("sorting")
    clean_sorting = audit("clean-sorting")

    assert sorting.status == "RETRACTED_DIRECT_PRIMITIVE"
    assert "sort1" in sorting.details["reason"]
    assert clean_sorting.status == "NEGATIVE_RESULT"
    assert clean_sorting.details["eligible_successes"] == 0


def test_sdk_export_is_source_only_and_does_not_accept_unknown_targets(tmp_path) -> None:
    result = evolve("manhattan", generations=2, seed=121, population_size=10, artifact_dir=tmp_path)

    rendered = export(result, "python")

    assert rendered.target == "python"
    assert "def beast_export" in rendered.source
    assert "source-only" in rendered.execution_boundary
    with pytest.raises(ValueError, match="target must"):
        export(result, "wasm")


def test_sdk_rejects_unbounded_or_unknown_tasks(tmp_path) -> None:
    with pytest.raises(ValueError, match="unsupported SDK task"):
        evolve("sorting", generations=1, seed=1, artifact_dir=tmp_path)
    with pytest.raises(ValueError, match="generations"):
        evolve("manhattan", generations=10_001, seed=1, artifact_dir=tmp_path)
