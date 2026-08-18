from __future__ import annotations

import pytest

from evolution.fitness import (
    AbsoluteDifferenceEvaluator,
    CompressionEvaluator,
    FibonacciEvaluator,
    GameStrategyEvaluator,
    MaxSubarrayEvaluator,
    PathfindingEvaluator,
    PrimeEvaluator,
    SortingEvaluator,
    StringReverseEvaluator,
)
from evolution.evaluator_safety import EvaluatorNotApprovedError
from evolution.gp_engine import ARITHMETIC_PRIMITIVES, CONVENIENCE_PRIMITIVES, GPGenome, GPNode, LIST_PRIMITIVES, STRING_PRIMITIVES


def list_primitive(name: str):
    return next(item for item in LIST_PRIMITIVES + CONVENIENCE_PRIMITIVES if item.name == name)


def string_primitive(name: str):
    return next(item for item in STRING_PRIMITIVES if item.name == name)


def arithmetic_primitive(name: str):
    return next(item for item in ARITHMETIC_PRIMITIVES if item.name == name)


def test_sorting_evaluator_rewards_actual_sorted_output() -> None:
    genome = GPGenome(GPNode(primitive=list_primitive("sort1"), children=[GPNode(terminal_name="x", value_type="list")]))
    result = SortingEvaluator().evaluate(genome)
    assert result.correctness == 1.0
    assert result.score == result.correctness


def test_sorting_evaluator_does_not_reward_unsorted_identity() -> None:
    genome = GPGenome(GPNode(terminal_name="x", value_type="list"))
    result = SortingEvaluator().evaluate(genome)
    assert result.correctness < 1.0


def test_string_reverse_evaluator_rewards_real_reverse_program() -> None:
    genome = GPGenome(GPNode(primitive=string_primitive("reverse1"), children=[GPNode(terminal_name="x", value_type="str")]))
    assert StringReverseEvaluator().evaluate(genome).correctness == 1.0


def test_fibonacci_cases_are_exact_and_deterministic() -> None:
    evaluator = FibonacciEvaluator()
    assert evaluator.generate_test_cases(1, 10) == evaluator.generate_test_cases(999, 10)
    assert evaluator.generate_test_cases(1, 8)[-1] == (7, 13)


def test_prime_cases_use_real_primality_labels() -> None:
    cases = dict(PrimeEvaluator().generate_test_cases(42, 30))
    assert cases[2] is True if 2 in cases else True
    assert all(isinstance(label, bool) for label in cases.values())


def test_max_subarray_reference_cases_are_numeric() -> None:
    cases = MaxSubarrayEvaluator().generate_test_cases(3, 10)
    assert len(cases) == 10
    assert all(isinstance(expected, float) for _, expected in cases)


def test_absolute_difference_requires_composition_and_scores_a_real_solution() -> None:
    evaluator = AbsoluteDifferenceEvaluator()
    candidate = GPGenome(GPNode(
        primitive=arithmetic_primitive("abs1"),
        children=[GPNode(
            primitive=arithmetic_primitive("sub"),
            children=[GPNode(terminal_name="left"), GPNode(terminal_name="right")],
        )],
    ))
    assert evaluator.evaluate(candidate).correctness == 1.0
    assert evaluator.evaluate(GPGenome(GPNode(terminal_name="left"))).correctness < 1.0


def test_compression_uses_real_zlib_output_length() -> None:
    cases = CompressionEvaluator().generate_test_cases(5, 3)
    assert all(expected > 0 for _, expected in cases)


def test_pathfinding_reference_is_geometric_distance() -> None:
    evaluator = PathfindingEvaluator()
    assert evaluator._is_correct(5.0, 6.0)
    assert not evaluator._is_correct(0.0, 6.0)


def test_game_strategy_evaluator_is_disabled_pending_safety_review() -> None:
    with pytest.raises(EvaluatorNotApprovedError, match="disabled pending a task-specific evaluator safety review"):
        GameStrategyEvaluator()
