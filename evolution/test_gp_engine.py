from __future__ import annotations

import random

import pytest

from evolution.gp_engine import (
    ALL_REGISTERED_PRIMITIVES,
    ARITHMETIC_PRIMITIVES,
    BOOL,
    DEFAULT_PRIMITIVES,
    FLOAT,
    GPGenome,
    GPNode,
    GPTreeBuilder,
    Primitive,
    Terminal,
)


def primitive(name: str) -> Primitive:
    return next(item for item in ARITHMETIC_PRIMITIVES if item.name == name)


def test_real_tree_executes_arithmetic_not_a_template_value() -> None:
    tree = GPNode(primitive=primitive("add"), children=[GPNode(terminal_name="x"), GPNode(terminal_value=2.0)])
    assert GPGenome(tree).execute({"x": 5.0}) == 7.0
    assert GPGenome(tree).execute({"x": -2.0}) == 0.0


def test_default_grammar_excludes_direct_sorting_shortcut_but_registry_decodes_legacy_artifacts() -> None:
    default_names = {item.name for item in DEFAULT_PRIMITIVES}
    registered_names = {item.name for item in ALL_REGISTERED_PRIMITIVES}
    assert "sort1" not in default_names
    assert "sort1" in registered_names


def test_depth_guard_returns_safe_default_on_corrupt_deep_tree() -> None:
    tree = GPNode(terminal_value=1.0)
    for _ in range(GPNode.MAX_EVAL_DEPTH + 5):
        tree = GPNode(primitive=primitive("neg"), children=[tree])
    assert tree.evaluate({}) == 0.0


def test_safe_division_and_nonfinite_values_are_normalised() -> None:
    divide = GPNode(primitive=primitive("div"), children=[GPNode(terminal_value=5.0), GPNode(terminal_value=0.0)])
    multiply = GPNode(primitive=primitive("mul"), children=[GPNode(terminal_value=1e308), GPNode(terminal_value=1e308)])
    assert divide.evaluate({}) == 0.0
    assert multiply.evaluate({}) == 0.0


def test_tree_builder_produces_typed_bounded_trees() -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(name="x", value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT)], random.Random(7))
    tree = builder.random_tree(max_depth=4, method="ramped", return_type=FLOAT)
    assert tree.depth() <= 4
    assert tree.size() <= GPTreeBuilder.MAX_SIZE
    assert isinstance(tree.evaluate({"x": 2.0}), float)


def test_crossover_never_mutates_parent_tree() -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(name="x", value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT)], random.Random(11))
    left = builder.random_tree(3, "full")
    right = builder.random_tree(3, "grow")
    left_before, right_before = left.to_dict(), right.to_dict()
    child_left, child_right = builder.subtree_crossover(left, right)
    child_left.terminal_value = 99.0
    assert left.to_dict() == left_before
    assert right.to_dict() == right_before
    assert child_left is not left and child_right is not right


def test_mutation_isolated_from_original() -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(name="x", value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT)], random.Random(23))
    original = builder.random_tree(3, "full")
    before = original.to_dict()
    mutated = builder.point_mutate(original)
    assert original.to_dict() == before
    assert mutated is not original


def test_invalid_tree_source_falls_back_to_compile_valid_function() -> None:
    invalid = GPNode(primitive=Primitive("bad-name!", 1, lambda value: value, FLOAT, (FLOAT,)), children=[GPNode(terminal_value=1.0)])
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(value=0.0, value_type=FLOAT)], random.Random(3))
    source = builder.to_python_function(invalid, "not valid!", ["x"])
    compile(source, "<test>", "exec")
    assert "return None" in source


def test_serialisation_round_trip_preserves_program_result() -> None:
    tree = GPNode(primitive=primitive("sq"), children=[GPNode(terminal_name="x")])
    genome = GPGenome(tree)
    restored = GPGenome.from_dict(genome.to_dict())
    assert restored.execute({"x": 3.0}) == 9.0
    assert restored.to_dict() == genome.to_dict()


@pytest.mark.parametrize("value,expected", [(-4.0, 16.0), (-1.5, 2.25), (0.0, 0.0), (1.5, 2.25), (9.0, 81.0)])
def test_parameterized_square_evaluation(value: float, expected: float) -> None:
    tree = GPNode(primitive=primitive("sq"), children=[GPNode(terminal_name="x")])
    assert GPGenome(tree).execute({"x": value}) == expected


def test_execute_returns_typed_fallback_when_cooperative_deadline_is_exhausted(monkeypatch) -> None:
    genome = GPGenome(GPNode(primitive=primitive("abs1"), children=[GPNode(terminal_value=-3.0)]))
    monotonic_values = iter((10.0, 10.6))
    monkeypatch.setattr("evolution.gp_engine.time.monotonic", lambda: next(monotonic_values))

    assert genome.execute({}, max_elapsed_seconds=0.5) == 0.0


def test_execute_rejects_non_positive_deadline_without_evaluating_tree() -> None:
    genome = GPGenome(GPNode(primitive=primitive("abs1"), children=[GPNode(terminal_value=-3.0)]))

    assert genome.execute({}, max_elapsed_seconds=0.0) == 0.0
