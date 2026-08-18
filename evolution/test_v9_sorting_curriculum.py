from __future__ import annotations

import json

import pytest

from evolution.gp_population import GPPopulation
from evolution.v9_sorting_curriculum import (
    CHECKPOINT_NAMESPACE,
    FiveStageSortingCurriculum,
    PROHIBITED_PRIMITIVES,
    STAGES,
    V9CleanSortingEvaluator,
    primitive_manifest,
)


def _population(seed: int = 31) -> GPPopulation:
    return GPPopulation(
        V9CleanSortingEvaluator(), primitives=STAGES[0].primitives,
        population_size=12, seed=seed, max_depth=5,
        primitive_profile_name="task-specific",
    )


def test_five_stage_evaluator_domains_are_deterministic_and_match_declared_lengths() -> None:
    for stage in STAGES:
        evaluator = V9CleanSortingEvaluator(stage.index)
        first = evaluator.generate_test_cases(seed=71, n=20)
        assert first == evaluator.generate_test_cases(seed=71, n=20)
        assert all(stage.length_min <= len(values) <= stage.length_max for values, _ in first)
        assert all(expected == sorted(values) for values, expected in first)
    negatives = V9CleanSortingEvaluator(3).generate_test_cases(seed=3, n=20)
    assert all(any(value < 0 for value in values) for values, _ in negatives)


def test_v9_primitive_manifest_preserves_prohibitions_and_five_explicit_stages() -> None:
    manifest = primitive_manifest()

    assert [stage["id"] for stage in manifest["stages"]] == ["pairs", "triples", "duplicates", "negatives", "up-to-16"]
    assert all(name not in primitive["primitive_names"] for primitive in manifest["stages"] for name in PROHIBITED_PRIMITIVES)
    assert manifest["stages"][-1]["length_range"] == [2, 16]


def test_population_level_mastery_event_retains_negative_evidence_without_advancing() -> None:
    population = _population()
    population.initialize()
    curriculum = FiveStageSortingCurriculum()
    curriculum.bind(population)

    event = curriculum.evaluate_and_advance(population, cases=20, seed=123)

    assert event["advanced"] is False
    assert event["stage_index_before"] == event["stage_index_after"] == 0
    assert event["population_mastery_required"] == 0.95
    assert population.checkpoint_metadata(CHECKPOINT_NAMESPACE)["events"] == [event]


def test_population_gate_advances_exactly_at_declared_boundary_and_archives_culture(monkeypatch) -> None:
    population = _population()
    population.initialize()
    curriculum = FiveStageSortingCurriculum()
    curriculum.bind(population)
    monkeypatch.setattr(curriculum, "_mastery_measurement", lambda *_args, **_kwargs: (0.95, 0.90))

    event = curriculum.evaluate_and_advance(population, cases=20, seed=812)

    assert event["advanced"] is True
    assert event["stage_index_before"] == 0
    assert event["stage_index_after"] == 1
    assert event["culture"]["injected"] is True
    assert event["culture"]["archived_tree_sha256"] == curriculum.archive[0]["tree_sha256"]
    assert population.evaluator.stage_index == 1


def test_cultural_seed_is_typed_re_scored_and_checkpointed_without_source_execution() -> None:
    population = _population()
    population.initialize()
    curriculum = FiveStageSortingCurriculum()
    curriculum.bind(population)
    champion = population.champion.genome.to_dict()
    curriculum.archive.append({
        "schema": "beast-v9-cultural-seed-v1",
        "tree_sha256": "a" * 64,
        "genome": champion,
        "source_stage_index": 0,
        "source_stage_id": "pairs",
        "population_generation": 0,
        "mastery_measurement": {"observed": True},
    })

    injected = curriculum._inject_latest_verified_seed(population)
    curriculum.bind(population)
    payload = population.checkpoint_payload()

    assert injected["injected"] is True
    assert any(organism.cultural_strategies == 1 for organism in population.population)
    assert payload["metadata"][CHECKPOINT_NAMESPACE]["archive"][0]["tree_sha256"] == "a" * 64
    assert payload["evaluator_state"] == {"profile": "clean-sorting-v9-five-stage", "stage_index": 0}


def test_checkpoint_restore_preserves_stateful_stage_and_controller_archive() -> None:
    population = _population()
    population.initialize()
    curriculum = FiveStageSortingCurriculum(archive=[{"tree_sha256": "b" * 64, "genome": population.champion.genome.to_dict()}])
    population.evaluator.set_stage(3)
    curriculum.bind(population)
    payload = json.loads(json.dumps(population.checkpoint_payload()))

    restored = GPPopulation.from_checkpoint_payload(V9CleanSortingEvaluator(), payload)
    restored_curriculum = FiveStageSortingCurriculum.from_population(restored)

    assert restored.evaluator.stage_index == 3
    assert [primitive.name for primitive in restored.builder.primitives] == [primitive.name for primitive in STAGES[3].primitives]
    assert restored_curriculum.archive == curriculum.archive


def test_curriculum_rejects_wrong_evaluator_and_too_small_measurement() -> None:
    population = _population()
    curriculum = FiveStageSortingCurriculum()
    with pytest.raises(ValueError, match="at least 20"):
        population.initialize()
        curriculum.evaluate_and_advance(population, cases=19)
