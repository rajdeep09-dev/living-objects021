from __future__ import annotations

import json
from pathlib import Path

import pytest

from agnes_brain.training_data.collect_test_cases import build_examples, collect, working_evaluators
from living_objects.beast_brain import ProvenanceError


def test_evaluator_case_collector_uses_the_complete_approved_set_and_excludes_game() -> None:
    records = build_examples()

    assert [type(evaluator).__name__ for evaluator in working_evaluators()] == [
        "SortingEvaluator",
        "PrimeEvaluator",
        "FibonacciEvaluator",
        "StringReverseEvaluator",
        "MaxSubarrayEvaluator",
        "AbsoluteDifferenceEvaluator",
        "ManhattanDistanceEvaluator",
        "CompressionEvaluator",
        "PathfindingEvaluator",
    ]
    assert len(records) == 9
    assert "GameStrategyEvaluator" not in {record["evaluator"] for record in records}
    assert all(len(record["input_examples"]) == 5 for record in records)
    assert all(len(record["output_examples"]) == 15 for record in records)
    assert all(record["source"]["candidate_programs_executed"] == 0 for record in records)
    assert all("fitness" not in json.dumps(record) for record in records)


def test_evaluator_case_collector_is_deterministic_and_writes_once(tmp_path: Path) -> None:
    output = tmp_path / "from_evaluators.jsonl"
    first = build_examples(seed=42)
    second = build_examples(seed=42)

    assert first == second
    assert collect(output, seed=42) == output
    assert [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()] == list(first)
    with pytest.raises(ProvenanceError, match="already exists"):
        collect(output, seed=42)
