from __future__ import annotations

import json
from pathlib import Path

import pytest

from living_objects.beast_brain import (
    ArtifactMeasurement,
    ExperienceRecord,
    ExperimentPlan,
    ExperimentResult,
    ProvenanceError,
    SourceKind,
    SourceReference,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REAL_ARTIFACT = REPOSITORY_ROOT / "reports" / "v11" / "artifacts" / "BEAST-SDK-V1-5312CD4D9BDDC82C.json"
TRAINING_FIELD = ("result", "champion", "training_fitness")
FRESH_FIELD = ("result", "champion", "fresh", "correctness")


def _real_measurement(field_path: tuple[str, ...] = TRAINING_FIELD) -> ArtifactMeasurement:
    return ArtifactMeasurement.from_artifact(REAL_ARTIFACT, field_path)


def _real_source() -> SourceReference:
    measurement = _real_measurement()
    return SourceReference(
        kind=SourceKind.REAL_BEAST_RUN,
        artifact_path=measurement.artifact_path,
        artifact_sha256=measurement.artifact_sha256,
        note="Persisted v11 Manhattan artifact used only as a provenance-contract fixture.",
    )


def test_artifact_measurement_reads_and_verifies_persisted_fitness() -> None:
    measurement = _real_measurement()

    assert measurement.value == 1.0
    measurement.verify()


def test_measurement_rejects_tampered_artifact(tmp_path: Path) -> None:
    copied = tmp_path / "artifact.json"
    copied.write_bytes(REAL_ARTIFACT.read_bytes())
    measurement = ArtifactMeasurement.from_artifact(copied, TRAINING_FIELD)
    copied.write_text(json.dumps({"result": {"champion": {"training_fitness": 0.0}}}), encoding="utf-8")

    with pytest.raises(ProvenanceError, match="SHA-256"):
        measurement.verify()


def test_real_experience_requires_two_verified_measurements_from_its_source() -> None:
    before = _real_measurement(TRAINING_FIELD)
    after = _real_measurement(FRESH_FIELD)
    record = ExperienceRecord(
        task="manhattan-distance",
        state="approved arithmetic primitive profile",
        available_actions=("retain", "mutate"),
        action="retain",
        observation="persisted champion achieved a recorded local score",
        source=_real_source(),
        success=True,
        fitness_before=before,
        fitness_after=after,
    )

    payload = record.to_dict()

    assert payload["record_id"] == record.record_id()
    assert payload["source"]["kind"] == "real_beast_run"
    assert payload["fitness_after"]["value"] == 1.0


@pytest.mark.parametrize("kind", [SourceKind.SYNTHETIC, SourceKind.TEACHER_GENERATED])
def test_nonmeasured_sources_cannot_claim_fitness(kind: SourceKind) -> None:
    if kind is SourceKind.SYNTHETIC:
        source = SourceReference(kind=kind, note="schema-only synthetic fixture")
    else:
        source = SourceReference(
            kind=kind,
            teacher_model="example-teacher",
            teacher_version="test-only",
            prompt_template_id="primitive-v1",
        )

    record = ExperienceRecord(
        task="schema-test",
        state="fixture state",
        available_actions=("inspect",),
        action="inspect",
        observation="no BEAST execution occurred",
        source=source,
        success=None,
        fitness_before=_real_measurement(),
        fitness_after=_real_measurement(),
    )

    with pytest.raises(ProvenanceError, match="cannot contain measured fitness"):
        record.validate()


def test_teacher_source_requires_reproducibility_metadata() -> None:
    source = SourceReference(kind=SourceKind.TEACHER_GENERATED, teacher_model="teacher")

    with pytest.raises(ProvenanceError, match="teacher_version"):
        source.validate()


def test_experiment_plan_is_preregistered_once_with_owner_only_permissions(tmp_path: Path) -> None:
    plan = ExperimentPlan(
        experiment_id="manhattan-controller-smoke-v1",
        task="manhattan-distance",
        seeds=(7, 11),
        generations=10,
        population_size=8,
    )
    plan_path = plan.write_new(tmp_path / "plans" / "manhattan.json")

    assert json.loads(plan_path.read_text(encoding="utf-8"))["seeds"] == [7, 11]
    assert plan_path.stat().st_mode & 0o077 == 0
    with pytest.raises(ProvenanceError, match="already exists"):
        plan.write_new(plan_path)


def test_experiment_result_requires_preregistered_seed_and_verified_score() -> None:
    plan = ExperimentPlan(
        experiment_id="manhattan-controller-smoke-v1",
        task="manhattan-distance",
        seeds=(7,),
        generations=10,
        population_size=8,
    )
    result = ExperimentResult(
        plan=plan,
        condition="baseline",
        seed=7,
        score=_real_measurement(FRESH_FIELD),
    )

    assert result.to_dict()["score"]["value"] == 1.0


def test_experiment_result_rejects_unregistered_seed() -> None:
    plan = ExperimentPlan(
        experiment_id="manhattan-controller-smoke-v1",
        task="manhattan-distance",
        seeds=(7,),
        generations=10,
        population_size=8,
    )
    result = ExperimentResult(plan=plan, condition="baseline", seed=8, score=_real_measurement())

    with pytest.raises(ProvenanceError, match="preregistered plan"):
        result.validate()
