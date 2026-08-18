"""Behavioral evaluator matrix using fixed, explicit input partitions.

The large exact-oracle lattices below are not generated scores: every expected
value is computed from the published task definition and evaluated through the
typed interpreter.  Timing telemetry is intentionally not asserted.
"""

from __future__ import annotations

from itertools import product
from typing import Any

import pytest

from evolution.fitness import (
    AbsoluteDifferenceEvaluator,
    CompressionEvaluator,
    FibonacciEvaluator,
    GameStrategyEvaluator,
    ManhattanDistanceEvaluator,
    MaxSubarrayEvaluator,
    PathfindingEvaluator,
    PrimeEvaluator,
    SortingEvaluator,
    StringReverseEvaluator,
)
from evolution.gp_engine import ARITHMETIC_PRIMITIVES, FLOAT, GPGenome, GPNode


ARITHMETIC = {primitive.name: primitive for primitive in ARITHMETIC_PRIMITIVES}


def variable(name: str) -> GPNode:
    return GPNode(terminal_name=name, value_type=FLOAT)


def operation(name: str, *children: GPNode) -> GPNode:
    primitive = ARITHMETIC[name]
    return GPNode(primitive=primitive, value_type=primitive.return_type, children=list(children))


def manhattan_genome() -> GPGenome:
    return GPGenome(operation(
        "add",
        operation("abs1", operation("sub", variable("x2"), variable("x1"))),
        operation("abs1", operation("sub", variable("y2"), variable("y1"))),
    ))


def absolute_difference_genome() -> GPGenome:
    return GPGenome(operation("abs1", operation("sub", variable("left"), variable("right"))))


COORDINATES = (-50, -10, 0, 10, 50)
MANHATTAN_CASES = [
    (x1, y1, x2, y2, float(abs(x2 - x1) + abs(y2 - y1)))
    for x1, y1, x2, y2 in product(COORDINATES, repeat=4)
]


@pytest.mark.parametrize(
    "x1,y1,x2,y2,expected", MANHATTAN_CASES,
    ids=[f"{x1}-{y1}-to-{x2}-{y2}" for x1, y1, x2, y2, _ in MANHATTAN_CASES],
)
def test_manhattan_composition_is_exact_on_fixed_coordinate_lattice(
    x1: int, y1: int, x2: int, y2: int, expected: float,
) -> None:
    evaluator = ManhattanDistanceEvaluator()
    result = evaluator._eval_on_cases(manhattan_genome(), [((x1, y1, x2, y2), expected)])
    assert result.score == 1.0
    assert result.correctness == 1.0
    assert result.robustness == 1.0
    assert result.test_cases_passed == result.test_cases_total == 1


ABSOLUTE_VALUES = (-100, -25, -1, 0, 1, 25, 100)
ABSOLUTE_CASES = [(left, right, float(abs(left - right))) for left, right in product(ABSOLUTE_VALUES, repeat=2)]


@pytest.mark.parametrize(
    "left,right,expected", ABSOLUTE_CASES,
    ids=[f"{left}-minus-{right}" for left, right, _ in ABSOLUTE_CASES],
)
def test_absolute_difference_composition_is_exact_on_fixed_value_lattice(left: int, right: int, expected: float) -> None:
    evaluator = AbsoluteDifferenceEvaluator()
    result = evaluator._eval_on_cases(absolute_difference_genome(), [((left, right), expected)])
    assert result.score == 1.0
    assert result.correctness == 1.0
    assert result.test_cases_passed == result.test_cases_total == 1


EVALUATORS = (
    SortingEvaluator, PrimeEvaluator, FibonacciEvaluator, StringReverseEvaluator,
    MaxSubarrayEvaluator, AbsoluteDifferenceEvaluator, ManhattanDistanceEvaluator,
    CompressionEvaluator, PathfindingEvaluator,
)


@pytest.mark.parametrize("evaluator_type", EVALUATORS, ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("seed", (0, 1, 7, 42, 20260814))
@pytest.mark.parametrize("size", (0, 1, 5, 15))
def test_evaluator_case_generation_is_repeatable_for_fixed_seed_and_size(
    evaluator_type: type[Any], seed: int, size: int,
) -> None:
    evaluator = evaluator_type()
    first = evaluator.generate_test_cases(seed=seed, n=size)
    second = evaluator.generate_test_cases(seed=seed, n=size)
    assert first == second
    assert len(first) == size


@pytest.mark.parametrize(
    "actual,expected,accepted",
    [
        (1.0, 1.0, True), (1, 1.0, True), (1.0 + 1e-7, 1.0, True), (1.0 + 1e-4, 1.0, False),
        (float("inf"), 1.0, False), (float("nan"), 1.0, False), ("1", 1.0, False), (None, 1.0, False),
        ([1.0, 2.0], [1.0, 2.0], True), ([1, 2], [1.0, 2.0], True), ([1.0], [1.0, 2.0], False),
        ([1.0, float("inf")], [1.0, 2.0], False), ([1.0, 2.0001], [1.0, 2.0], False),
        ("ok", "ok", True), ("OK", "ok", False), (True, True, True), (False, True, False),
        ([True, [1.0]], [True, [1.0]], True), ([True, [1.1]], [True, [1.0]], False),
    ],
)
def test_base_recursive_correctness_contract(actual: Any, expected: Any, accepted: bool) -> None:
    assert SortingEvaluator()._is_correct(actual, expected) is accepted


@pytest.mark.parametrize("evaluator_type", EVALUATORS, ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("invalid_output", (None, "wrong-type", float("nan"), float("inf")))
def test_evaluator_invalid_candidate_outputs_remain_bounded(evaluator_type: type[Any], invalid_output: Any) -> None:
    evaluator = evaluator_type()
    output_type = evaluator.output_type
    genome = GPGenome(GPNode(terminal_value=invalid_output, value_type=output_type))
    result = evaluator.evaluate(genome)
    assert 0.0 <= result.score <= 1.0
    assert 0.0 <= result.correctness <= 1.0
    assert result.test_cases_passed <= result.test_cases_total
    assert result.error_message == ""


@pytest.mark.parametrize("input_value", (-50, -1, 0, 1, 50))
def test_manhattan_context_binds_all_declared_coordinate_names(input_value: int) -> None:
    context = ManhattanDistanceEvaluator().context_for((input_value, input_value + 1, input_value + 2, input_value + 3))
    assert context == {
        "x": float(input_value), "x1": float(input_value), "y1": float(input_value + 1),
        "x2": float(input_value + 2), "y2": float(input_value + 3),
    }


@pytest.mark.parametrize("input_value", (-50, -1, 0, 1, 50))
def test_absolute_difference_context_binds_left_right_and_legacy_x(input_value: int) -> None:
    context = AbsoluteDifferenceEvaluator().context_for((input_value, input_value + 1))
    assert context == {"x": float(input_value), "left": float(input_value), "right": float(input_value + 1)}


@pytest.mark.parametrize("state", ({}, {"seed": 1}, {"unexpected": []}))
def test_stateless_evaluators_accept_only_empty_checkpoint_state(state: dict[str, object]) -> None:
    evaluator = PrimeEvaluator()
    if state:
        with pytest.raises(ValueError, match="does not accept checkpoint state"):
            evaluator.restore_checkpoint_state(state)
    else:
        evaluator.restore_checkpoint_state(state)
        assert evaluator.checkpoint_state() == {}
