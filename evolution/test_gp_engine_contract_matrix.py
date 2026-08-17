"""High-value typed-interpreter regression matrix.

Each parametrized case covers a distinct primitive/input-domain cell or a
separate tree-safety boundary.  These tests exercise the interpreter directly;
they do not execute exported source as a fitness path.
"""

from __future__ import annotations

import random

import pytest

from evolution.gp_engine import (
    ALL_REGISTERED_PRIMITIVES,
    ARITHMETIC_PRIMITIVES,
    BOOL,
    FLOAT,
    LIST,
    STRING,
    GPGenome,
    GPNode,
    GPTreeBuilder,
    Primitive,
    Terminal,
)


PRIMITIVES = {primitive.name: primitive for primitive in ALL_REGISTERED_PRIMITIVES}


def literal(value: object, value_type: str) -> GPNode:
    return GPNode(terminal_value=value, value_type=value_type)


def interpreted_primitive(name: str, values: tuple[object, ...]) -> object:
    primitive = PRIMITIVES[name]
    children = [literal(value, value_type) for value, value_type in zip(values, primitive.arg_types)]
    return GPNode(primitive=primitive, value_type=primitive.return_type, children=children).evaluate({})


# Each row is a separately observable interpreter input partition.  The direct
# sorting and reversing primitives remain present here because the matrix tests
# registry semantics only; they are still excluded from the clean v8/v9 profile.
PRIMITIVE_CASES: list[tuple[str, tuple[object, ...], object]] = [
    ("add", (0.0, 0.0), 0.0), ("add", (2.5, -1.0), 1.5), ("add", (-3.0, -7.0), -10.0),
    ("add", (1e12, 2.0), 1e12 + 2.0), ("add", (0.1, 0.2), 0.3), ("add", (-0.0, 4.0), 4.0),
    ("sub", (0.0, 0.0), 0.0), ("sub", (2.5, -1.0), 3.5), ("sub", (-3.0, -7.0), 4.0),
    ("sub", (1e12, 2.0), 1e12 - 2.0), ("sub", (0.1, 0.2), -0.1), ("sub", (-0.0, 4.0), -4.0),
    ("mul", (0.0, 3.0), 0.0), ("mul", (2.5, -1.0), -2.5), ("mul", (-3.0, -7.0), 21.0),
    ("mul", (1e6, 2.0), 2e6), ("mul", (0.1, 0.2), 0.02), ("mul", (-0.0, 4.0), -0.0),
    ("div", (5.0, 0.0), 0.0), ("div", (5.0, -0.0), 0.0), ("div", (6.0, 2.0), 3.0),
    ("div", (-6.0, 2.0), -3.0), ("div", (-6.0, -2.0), 3.0), ("div", (1.0, 3.0), 1 / 3),
    ("div", (0.0, 7.0), 0.0), ("div", (1e8, 0.5), 2e8),
    ("max2", (-2.0, -3.0), -2.0), ("max2", (2.0, -3.0), 2.0), ("max2", (2.0, 2.0), 2.0),
    ("max2", (0.0, -0.0), 0.0), ("max2", (1e8, 1e9), 1e9),
    ("min2", (-2.0, -3.0), -3.0), ("min2", (2.0, -3.0), -3.0), ("min2", (2.0, 2.0), 2.0),
    ("min2", (0.0, -0.0), 0.0), ("min2", (1e8, 1e9), 1e8),
    ("neg", (0.0,), -0.0), ("neg", (2.5,), -2.5), ("neg", (-3.0,), 3.0), ("neg", (1e9,), -1e9), ("neg", (-0.25,), 0.25),
    ("abs1", (0.0,), 0.0), ("abs1", (2.5,), 2.5), ("abs1", (-3.0,), 3.0), ("abs1", (-1e9,), 1e9), ("abs1", (-0.25,), 0.25),
    ("sq", (0.0,), 0.0), ("sq", (2.5,), 6.25), ("sq", (-3.0,), 9.0), ("sq", (1e3,), 1e6), ("sq", (-0.25,), 0.0625),
    ("sqrt", (-1.0,), 0.0), ("sqrt", (0.0,), 0.0), ("sqrt", (1.0,), 1.0), ("sqrt", (2.25,), 1.5), ("sqrt", (9.0,), 3.0), ("sqrt", (1e6,), 1e3),
    ("log", (-1.0,), 0.0), ("log", (0.0,), 0.0), ("log", (1.0,), 0.0), ("log", (2.718281828459045,), 1.0), ("log", (10.0,), 2.302585092994046), ("log", (1e-9,), -20.72326583694641), ("log", (1e6,), 13.815510557964274),
    ("if_pos", (-1.0, 7.0, 9.0), 9.0), ("if_pos", (0.0, 7.0, 9.0), 9.0), ("if_pos", (1.0, 7.0, 9.0), 7.0),
    ("if_pos", (1e-12, -2.0, 3.0), -2.0), ("if_pos", (-1e-12, -2.0, 3.0), 3.0), ("if_pos", (2.0, -2.0, 3.0), -2.0),
    ("and2", (False, False), False), ("and2", (False, True), False), ("and2", (True, False), False), ("and2", (True, True), True),
    ("or2", (False, False), False), ("or2", (False, True), True), ("or2", (True, False), True), ("or2", (True, True), True),
    ("not1", (False,), True), ("not1", (True,), False),
    ("gt", (-1.0, 0.0), False), ("gt", (0.0, -1.0), True), ("gt", (1.0, 1.0), False), ("gt", (1e9, 1e8), True), ("gt", (-1e9, -1e8), False),
    ("lt", (-1.0, 0.0), True), ("lt", (0.0, -1.0), False), ("lt", (1.0, 1.0), False), ("lt", (1e8, 1e9), True), ("lt", (-1e8, -1e9), False),
    ("eq", (0.0, 0.0), True), ("eq", (1.0, 1.0 + 1e-10), True), ("eq", (1.0, 1.0 + 1e-8), False), ("eq", (-2.0, -2.0), True), ("eq", (1e9, 1e9 + 1.0), False),
    ("head", ([],), 0.0), ("head", ([4],), 4.0), ("head", ([-3, 8],), -3.0), ("head", ((2, 3),), 2.0),
    ("tail", ([],), []), ("tail", ([4],), []), ("tail", ([-3, 8],), [8]), ("tail", ((2, 3, 4),), [3, 4]),
    ("cons", (1.0, []), [1.0]), ("cons", (-2.5, [4]), [-2.5, 4]), ("cons", (0.0, [1, 2]), [0.0, 1, 2]), ("cons", (3.0, (4, 5)), [3.0, 4, 5]),
    ("length", ([],), 0.0), ("length", ([1],), 1.0), ("length", ([1, 2, 3],), 3.0), ("length", ((1, 2),), 2.0),
    ("sort1", ([],), []), ("sort1", ([3, 1, 2],), [1, 2, 3]), ("sort1", ([-1, -3, 2],), [-3, -1, 2]), ("sort1", ((2, 2, 1),), [1, 2, 2]),
    ("sum1", ([],), 0.0), ("sum1", ([3],), 3.0), ("sum1", ([3, -1, 2],), 4.0), ("sum1", ((0.5, 1.5),), 2.0),
    ("map_sq", ([],), []), ("map_sq", ([3],), [9.0]), ("map_sq", ([3, -1, 2],), [9.0, 1.0, 4.0]), ("map_sq", ((0.5, -0.5),), [0.25, 0.25]),
    ("filter_pos", ([],), []), ("filter_pos", ([3],), [3]), ("filter_pos", ([3, -1, 0, 2],), [3, 2]), ("filter_pos", ((-0.1, 0.1),), [0.1]),
    ("unique", ([],), []), ("unique", ([3],), [3]), ("unique", ([3, 1, 3, 2, 1],), [3, 1, 2]), ("unique", ((2, 2, 1),), [2, 1]),
    ("choose_list", (-1.0, [1], [2]), [2]), ("choose_list", (0.0, [1], [2]), [2]), ("choose_list", (1.0, [1], [2]), [1]),
    ("concat_lists", ([], []), []), ("concat_lists", ([1], [2]), [1, 2]), ("concat_lists", ((1, 2), (3,)), [1, 2, 3]),
    ("concat", ("", ""), ""), ("concat", ("a", "b"), "ab"), ("concat", ("a", ""), "a"), ("concat", ("hi", " there"), "hi there"),
    ("upper1", ("",), ""), ("upper1", ("ab",), "AB"), ("upper1", ("MiXeD",), "MIXED"), ("upper1", ("123a",), "123A"),
    ("strip1", ("",), ""), ("strip1", (" abc ",), "abc"), ("strip1", ("\tword\n",), "word"), ("strip1", ("inside space",), "inside space"),
    ("split1", ("",), []), ("split1", ("one",), ["one"]), ("split1", ("one two",), ["one", "two"]), ("split1", (" a  b ",), ["a", "b"]),
    ("join1", (",", []), ""), ("join1", (",", ["a"]), "a"), ("join1", (",", ["a", "b"]), "a,b"), ("join1", ("-", [1, 2]), "1-2"),
    ("startswith2", ("", ""), True), ("startswith2", ("alpha", "a"), True), ("startswith2", ("alpha", "al"), True), ("startswith2", ("alpha", "b"), False),
    ("replace3", ("", "a", "b"), ""), ("replace3", ("banana", "a", "o"), "bonono"), ("replace3", ("abc", "x", "y"), "abc"), ("replace3", ("aaaa", "aa", "b"), "bb"),
    ("len_str", ("",), 0.0), ("len_str", ("a",), 1.0), ("len_str", ("hello",), 5.0), ("len_str", (" a ",), 3.0),
    ("reverse1", ("",), ""), ("reverse1", ("a",), "a"), ("reverse1", ("abc",), "cba"), ("reverse1", ("racecar",), "racecar"),
]


@pytest.mark.parametrize("name,values,expected", PRIMITIVE_CASES, ids=[f"{name}-{index}" for index, (name, _, _) in enumerate(PRIMITIVE_CASES)])
def test_registered_primitive_interpreter_semantics(name: str, values: tuple[object, ...], expected: object) -> None:
    actual = interpreted_primitive(name, values)
    if isinstance(expected, float):
        assert actual == pytest.approx(expected)
    else:
        assert actual == expected


_SOURCE_CASES = {name: (values, expected) for name, values, expected in PRIMITIVE_CASES}


@pytest.mark.parametrize("name", sorted(_SOURCE_CASES))
def test_each_registered_primitive_has_parseable_audit_source(name: str) -> None:
    values, _ = _SOURCE_CASES[name]
    primitive = PRIMITIVES[name]
    tree = GPNode(
        primitive=primitive,
        value_type=primitive.return_type,
        children=[literal(value, value_type) for value, value_type in zip(values, primitive.arg_types)],
    )
    expression = tree.to_python()
    compile(expression, f"<audit-{name}>", "eval")
    assert expression


_ALL_TERMINALS = (
    Terminal(name="number", value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT),
    Terminal(name="flag", value_type=BOOL), Terminal(value=False, value_type=BOOL),
    Terminal(name="items", value_type=LIST), Terminal(value=[], value_type=LIST),
    Terminal(name="text", value_type=STRING), Terminal(value="", value_type=STRING),
)
_CONTEXT = {"number": 2.0, "flag": True, "items": [3, -1], "text": "seed"}


@pytest.mark.parametrize("return_type", (FLOAT, BOOL, LIST, STRING))
@pytest.mark.parametrize("method", ("full", "grow", "ramped"))
@pytest.mark.parametrize("seed", (1, 7, 19))
def test_random_trees_are_typed_bounded_and_interpretable(return_type: str, method: str, seed: int) -> None:
    builder = GPTreeBuilder(ALL_REGISTERED_PRIMITIVES, _ALL_TERMINALS, random.Random(seed))
    tree = builder.random_tree(max_depth=4, method=method, return_type=return_type)
    assert tree.result_type == return_type
    assert tree.depth() <= 4
    assert tree.size() <= GPTreeBuilder.MAX_SIZE
    expected_type = {FLOAT: float, BOOL: bool, LIST: list, STRING: str}[return_type]
    assert isinstance(tree.evaluate(_CONTEXT), expected_type)


@pytest.mark.parametrize(
    "value,value_type,expected",
    [
        (None, FLOAT, 0.0), ("4.25", FLOAT, 4.25), (float("inf"), FLOAT, 0.0), (float("nan"), FLOAT, 0.0),
        (None, BOOL, False), (0, BOOL, False), (1, BOOL, True), ("", BOOL, False),
        (None, LIST, []), ((1, 2), LIST, [1, 2]), ("not-a-list", LIST, []), (3, LIST, []),
        (None, STRING, ""), (2, STRING, "2"), (True, STRING, "True"), (["x"], STRING, "['x']"),
    ],
)
def test_typed_terminal_normalization_is_fail_closed(value: object, value_type: str, expected: object) -> None:
    assert literal(value, value_type).evaluate({}) == expected


@pytest.mark.parametrize("max_depth", (-1, GPTreeBuilder.MAX_DEPTH + 1))
def test_random_tree_rejects_out_of_range_depth(max_depth: int) -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(value=1.0, value_type=FLOAT)], random.Random(1))
    with pytest.raises(ValueError, match="max_depth"):
        builder.random_tree(max_depth=max_depth)


@pytest.mark.parametrize("method", ("", "random", "FULL"))
def test_random_tree_rejects_unknown_construction_method(method: str) -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(value=1.0, value_type=FLOAT)], random.Random(1))
    with pytest.raises(ValueError, match="method"):
        builder.random_tree(max_depth=1, method=method)


@pytest.mark.parametrize("mutation", ("point_mutate", "hoist_mutate", "expand_mutate"))
@pytest.mark.parametrize("seed", range(8))
def test_mutation_paths_preserve_parent_ownership_and_bounds(mutation: str, seed: int) -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(name="x", value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT)], random.Random(seed))
    parent = builder.random_tree(max_depth=4, method="ramped")
    before = parent.to_dict()
    child = getattr(builder, mutation)(parent)
    assert parent.to_dict() == before
    assert child is not parent
    assert child.depth() <= GPTreeBuilder.MAX_DEPTH
    assert child.size() <= GPTreeBuilder.MAX_SIZE
    assert isinstance(child.evaluate({"x": 3.0}), float)


@pytest.mark.parametrize("seed", range(12))
def test_crossover_paths_preserve_parent_ownership_and_bounds(seed: int) -> None:
    builder = GPTreeBuilder(ARITHMETIC_PRIMITIVES, [Terminal(name="x", value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT)], random.Random(seed))
    left = builder.random_tree(max_depth=4, method="full")
    right = builder.random_tree(max_depth=4, method="grow")
    left_before, right_before = left.to_dict(), right.to_dict()
    child_left, child_right = builder.subtree_crossover(left, right)
    assert left.to_dict() == left_before
    assert right.to_dict() == right_before
    for child in (child_left, child_right):
        assert child.depth() <= GPTreeBuilder.MAX_DEPTH
        assert child.size() <= GPTreeBuilder.MAX_SIZE
        assert isinstance(child.evaluate({"x": 3.0}), float)


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"primitive": "unknown", "value_type": FLOAT, "children": []}, "unregistered primitive"),
        ({"primitive": "add", "value_type": BOOL, "children": []}, "type mismatch"),
        ({"primitive": "choose_list", "value_type": FLOAT, "children": []}, "type mismatch"),
    ],
)
def test_tree_deserialization_rejects_unknown_or_type_mismatched_primitives(payload: dict[str, object], error: str) -> None:
    with pytest.raises(ValueError, match=error):
        GPNode.from_dict(payload)


@pytest.mark.parametrize(
    "tree,expected",
    [
        (literal(2.0, FLOAT), 2.0),
        (literal(True, BOOL), True),
        (literal([1, 2], LIST), [1, 2]),
        (literal("text", STRING), "text"),
    ],
)
def test_genome_round_trips_all_terminal_value_types(tree: GPNode, expected: object) -> None:
    restored = GPGenome.from_dict(GPGenome(tree).to_dict())
    assert restored.execute({}) == expected
