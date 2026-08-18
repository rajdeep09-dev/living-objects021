from __future__ import annotations

from evolution.contamination_audit import IMPLEMENTED_TASKS, audit_all_tasks, audit_task


def test_sorting_audit_records_clean_default_profile_and_random_baseline() -> None:
    sorting = next(task for task in IMPLEMENTED_TASKS if task.task_id == "sorting")
    record = audit_task(sorting, baseline_population_size=12, baseline_seed=77)
    assert record["status"] == "NO_ONE_OPERATION_MATCH_OBSERVED"
    assert record["direct_solution_matches"] == []
    assert record["baseline"]["population_size"] == 12
    assert 0.0 <= record["baseline"]["best_fitness"] <= 1.0
    assert 0 <= record["baseline"]["perfect_programs"] <= 12


def test_reverse_remains_retracted_while_game_uses_its_real_tournament_contract() -> None:
    task_by_id = {task.task_id: task for task in IMPLEMENTED_TASKS}
    reverse = audit_task(task_by_id["string-reverse"], baseline_population_size=8)
    game = audit_task(task_by_id["game-strategy"], baseline_population_size=8)
    assert reverse["status"] == "RETRACTED_DIRECT_PRIMITIVE"
    assert "primitive:reverse1" in {match["candidate"] for match in reverse["direct_solution_matches"]}
    assert game["status"] == "NO_ONE_OPERATION_MATCH_OBSERVED"


def test_full_audit_lists_only_real_evaluators_and_marks_unimplemented_domains() -> None:
    report = audit_all_tasks(baseline_population_size=4)
    assert report["task_count"] == 10
    assert report["unimplemented_planned_domains"] == 14
    assert report["summary"]["retracted_direct_primitive"] >= 1
    assert report["summary"]["no_one_operation_match_observed"] >= 2
