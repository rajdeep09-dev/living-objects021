from __future__ import annotations

from evolution.clean_sorting import CleanSortingCurriculum, CleanSortingEvaluator, PHASES, clean_primitive_manifest
from evolution.contamination_audit import TaskDefinition, audit_task
from evolution.gp_population import GPPopulation


def test_clean_sorting_profile_excludes_direct_and_near_complete_list_operators() -> None:
    manifest = clean_primitive_manifest()
    names = set(manifest["all_primitive_names"])
    assert not names.intersection(manifest["explicitly_prohibited_names"])
    assert all("sort" not in name for name in names)
    assert [phase.name for phase in PHASES] == ["structural", "ordering", "composition"]


def test_clean_sorting_audit_has_no_one_operation_solution_and_low_random_baseline() -> None:
    task = TaskDefinition("clean-sorting-v1", CleanSortingEvaluator)
    record = audit_task(
        task, PHASES[-1].primitives, baseline_population_size=100, baseline_seed=2026,
        primitive_profile_name="task-specific",
    )
    assert record["status"] == "NO_ONE_OPERATION_MATCH_OBSERVED"
    assert record["direct_solution_matches"] == []
    assert record["baseline"]["perfect_programs"] == 0
    assert record["baseline"]["mean_fitness"] < 0.20


def test_clean_curriculum_changes_only_future_variation_profile_at_declared_boundaries() -> None:
    population = GPPopulation(
        CleanSortingEvaluator(), primitives=PHASES[0].primitives,
        population_size=8, seed=141, primitive_profile_name="task-specific",
    )
    population.initialize()
    assert CleanSortingCurriculum.apply_to_population(population).name == "structural"
    assert {primitive.name for primitive in population.builder.primitives} == {primitive.name for primitive in PHASES[0].primitives}
    population.generation = 200
    assert CleanSortingCurriculum.apply_to_population(population).name == "ordering"
    assert {primitive.name for primitive in population.builder.primitives} == {primitive.name for primitive in PHASES[1].primitives}
