"""Bounded, typed genetic-programming primitives for BEAST v6.

The engine deliberately interprets a small expression language instead of
executing arbitrary generated Python.  Generated source is an export artifact
and is compile-validated, but population fitness always runs through the typed
interpreter below.  This is the safety boundary that makes program evolution
testable without treating generated source as trusted code.
"""
from __future__ import annotations

import ast
import contextvars
import copy
import math
import random
import re
import textwrap
import zlib
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence


FLOAT = "float"
BOOL = "bool"
LIST = "list"
STRING = "str"


def _safe_div(left: float, right: float) -> float:
    return left / right if right not in (0, 0.0) else 0.0


def _safe_sqrt(value: float) -> float:
    return math.sqrt(value) if value >= 0 else 0.0


def _safe_log(value: float) -> float:
    return math.log(value) if value > 0 else 0.0


@dataclass(frozen=True)
class Primitive:
    """A typed, pure operation available to evolved programs."""

    name: str
    arity: int
    fn: Callable[..., Any]
    return_type: str
    arg_types: tuple[str, ...]


ARITHMETIC_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("add", 2, lambda a, b: float(a) + float(b), FLOAT, (FLOAT, FLOAT)),
    Primitive("sub", 2, lambda a, b: float(a) - float(b), FLOAT, (FLOAT, FLOAT)),
    Primitive("mul", 2, lambda a, b: float(a) * float(b), FLOAT, (FLOAT, FLOAT)),
    Primitive("div", 2, _safe_div, FLOAT, (FLOAT, FLOAT)),
    Primitive("max2", 2, lambda a, b: max(float(a), float(b)), FLOAT, (FLOAT, FLOAT)),
    Primitive("min2", 2, lambda a, b: min(float(a), float(b)), FLOAT, (FLOAT, FLOAT)),
    Primitive("neg", 1, lambda a: -float(a), FLOAT, (FLOAT,)),
    Primitive("abs1", 1, lambda a: abs(float(a)), FLOAT, (FLOAT,)),
    Primitive("sq", 1, lambda a: float(a) * float(a), FLOAT, (FLOAT,)),
    Primitive("sqrt", 1, _safe_sqrt, FLOAT, (FLOAT,)),
    Primitive("log", 1, _safe_log, FLOAT, (FLOAT,)),
    Primitive("if_pos", 3, lambda c, t, f: t if float(c) > 0 else f, FLOAT, (FLOAT, FLOAT, FLOAT)),
)

BOOLEAN_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("and2", 2, lambda a, b: bool(a) and bool(b), BOOL, (BOOL, BOOL)),
    Primitive("or2", 2, lambda a, b: bool(a) or bool(b), BOOL, (BOOL, BOOL)),
    Primitive("not1", 1, lambda a: not bool(a), BOOL, (BOOL,)),
    Primitive("gt", 2, lambda a, b: float(a) > float(b), BOOL, (FLOAT, FLOAT)),
    Primitive("lt", 2, lambda a, b: float(a) < float(b), BOOL, (FLOAT, FLOAT)),
    Primitive("eq", 2, lambda a, b: abs(float(a) - float(b)) < 1e-9, BOOL, (FLOAT, FLOAT)),
)

LIST_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("head", 1, lambda values: float(values[0]) if values else 0.0, FLOAT, (LIST,)),
    Primitive("tail", 1, lambda values: list(values[1:]) if len(values) > 1 else [], LIST, (LIST,)),
    Primitive("cons", 2, lambda value, values: [float(value), *list(values)], LIST, (FLOAT, LIST)),
    Primitive("length", 1, lambda values: float(len(values)), FLOAT, (LIST,)),
    Primitive("sort1", 1, lambda values: sorted(list(values)), LIST, (LIST,)),
    Primitive("sum1", 1, lambda values: float(sum(values)) if values else 0.0, FLOAT, (LIST,)),
    Primitive("map_sq", 1, lambda values: [float(value) * float(value) for value in values], LIST, (LIST,)),
    Primitive("filter_pos", 1, lambda values: [value for value in values if float(value) > 0], LIST, (LIST,)),
    Primitive("unique", 1, lambda values: list(dict.fromkeys(values)), LIST, (LIST,)),
)

# Generic list controls are registered for lossless checkpoint decoding but are
# deliberately excluded from DEFAULT_PRIMITIVES. Task profiles must opt in.
GENERIC_LIST_CONTROL_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive(
        "choose_list", 3,
        lambda condition, truthy, falsy: list(truthy) if float(condition) > 0 else list(falsy),
        LIST, (FLOAT, LIST, LIST),
    ),
    Primitive(
        "concat_lists", 2, lambda left, right: [*list(left), *list(right)], LIST, (LIST, LIST),
    ),
)

STRING_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("concat", 2, lambda a, b: str(a) + str(b), STRING, (STRING, STRING)),
    Primitive("upper1", 1, lambda value: str(value).upper(), STRING, (STRING,)),
    Primitive("strip1", 1, lambda value: str(value).strip(), STRING, (STRING,)),
    Primitive("split1", 1, lambda value: str(value).split(), LIST, (STRING,)),
    Primitive("join1", 2, lambda separator, values: str(separator).join(map(str, values)), STRING, (STRING, LIST)),
    Primitive("startswith2", 2, lambda a, b: str(a).startswith(str(b)), BOOL, (STRING, STRING)),
    Primitive("replace3", 3, lambda s, a, b: str(s).replace(str(a), str(b)), STRING, (STRING, STRING, STRING)),
    Primitive("len_str", 1, lambda value: float(len(str(value))), FLOAT, (STRING,)),
    Primitive("reverse1", 1, lambda value: str(value)[::-1], STRING, (STRING,)),
)

DEFAULT_PRIMITIVES = ARITHMETIC_PRIMITIVES + BOOLEAN_PRIMITIVES + LIST_PRIMITIVES + STRING_PRIMITIVES
ALL_REGISTERED_PRIMITIVES = DEFAULT_PRIMITIVES + GENERIC_LIST_CONTROL_PRIMITIVES


@dataclass(frozen=True)
class Terminal:
    """A typed terminal (input variable or literal) for program construction."""

    name: str = ""
    value: Any = None
    value_type: str = FLOAT

    @property
    def is_variable(self) -> bool:
        return bool(self.name)


_EVALUATION_DEPTH: contextvars.ContextVar[int] = contextvars.ContextVar("gp_evaluation_depth", default=0)


@dataclass
class GPNode:
    """A node in a typed GP expression tree.

    ``evaluate`` has a strict depth cap and returns a type-correct default when
    malformed input, invalid child arity, non-finite numeric values, or primitive
    errors appear.  A corrupt tree therefore scores poorly rather than crashing
    an evolution worker.
    """

    primitive: Primitive | None = None
    terminal_value: Any = None
    terminal_name: str = ""
    value_type: str = FLOAT
    children: list["GPNode"] = field(default_factory=list)

    MAX_EVAL_DEPTH = 50

    @property
    def is_terminal(self) -> bool:
        return self.primitive is None

    @property
    def result_type(self) -> str:
        return self.primitive.return_type if self.primitive is not None else self.value_type

    def fallback(self) -> Any:
        return {FLOAT: 0.0, BOOL: False, LIST: [], STRING: ""}.get(self.result_type, None)

    def evaluate(self, context: Mapping[str, Any]) -> Any:
        depth = _EVALUATION_DEPTH.get()
        if depth >= self.MAX_EVAL_DEPTH:
            return self.fallback()
        token = _EVALUATION_DEPTH.set(depth + 1)
        try:
            if self.is_terminal:
                value = context.get(self.terminal_name, self.terminal_value) if self.terminal_name else self.terminal_value
                return self._normalise(value)
            if self.primitive is None or len(self.children) != self.primitive.arity:
                return self.fallback()
            values = [child.evaluate(context) for child in self.children]
            value = self.primitive.fn(*values)
            return self._normalise(value)
        except (ArithmeticError, OverflowError, TypeError, ValueError):
            return self.fallback()
        finally:
            _EVALUATION_DEPTH.reset(token)

    def _normalise(self, value: Any) -> Any:
        if self.result_type == FLOAT:
            try:
                number = float(value)
            except (TypeError, ValueError):
                return 0.0
            return number if math.isfinite(number) else 0.0
        if self.result_type == BOOL:
            return bool(value)
        if self.result_type == LIST:
            return list(value) if isinstance(value, (list, tuple)) else []
        if self.result_type == STRING:
            return str(value) if value is not None else ""
        return value

    def depth(self) -> int:
        return 0 if self.is_terminal else 1 + max((child.depth() for child in self.children), default=0)

    def size(self) -> int:
        return 1 + sum(child.size() for child in self.children)

    def copy(self) -> "GPNode":
        return copy.deepcopy(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive": self.primitive.name if self.primitive else None,
            "terminal_value": self.terminal_value,
            "terminal_name": self.terminal_name,
            "value_type": self.value_type,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], primitives: Iterable[Primitive] = ALL_REGISTERED_PRIMITIVES) -> "GPNode":
        by_name = {primitive.name: primitive for primitive in primitives}
        primitive_name = payload.get("primitive")
        primitive = by_name.get(str(primitive_name)) if primitive_name is not None else None
        if primitive_name is not None and primitive is None:
            raise ValueError(f"checkpoint references an unregistered primitive: {primitive_name}")
        value_type = str(payload.get("value_type", primitive.return_type if primitive else FLOAT))
        if primitive is not None and value_type != primitive.return_type:
            raise ValueError(f"checkpoint type mismatch for primitive: {primitive.name}")
        return cls(
            primitive=primitive,
            terminal_value=payload.get("terminal_value"),
            terminal_name=str(payload.get("terminal_name", "")),
            value_type=value_type,
            children=[cls.from_dict(child, primitives) for child in payload.get("children", [])],
        )

    def to_python(self) -> str:
        if self.is_terminal:
            if self.terminal_name and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.terminal_name):
                return self.terminal_name
            return repr(self.terminal_value)
        if self.primitive is None or len(self.children) != self.primitive.arity:
            return repr(self.fallback())
        args = [child.to_python() for child in self.children]
        return _python_expression(self.primitive.name, args, self.fallback())


def _python_expression(name: str, args: Sequence[str], fallback: Any) -> str:
    """Translate a primitive to a Python expression without dynamic imports/eval."""
    if name == "add": return f"({args[0]} + {args[1]})"
    if name == "sub": return f"({args[0]} - {args[1]})"
    if name == "mul": return f"({args[0]} * {args[1]})"
    if name == "div": return f"(({args[0]}) / ({args[1]}) if ({args[1]}) != 0 else 0.0)"
    if name == "max2": return f"max({args[0]}, {args[1]})"
    if name == "min2": return f"min({args[0]}, {args[1]})"
    if name == "neg": return f"(-({args[0]}))"
    if name == "abs1": return f"abs({args[0]})"
    if name == "sq": return f"(({args[0]}) * ({args[0]}))"
    if name == "sqrt": return f"(math.sqrt({args[0]}) if ({args[0]}) >= 0 else 0.0)"
    if name == "log": return f"(math.log({args[0]}) if ({args[0]}) > 0 else 0.0)"
    if name == "if_pos": return f"({args[1]} if ({args[0]}) > 0 else {args[2]})"
    if name == "and2": return f"(bool({args[0]}) and bool({args[1]}))"
    if name == "or2": return f"(bool({args[0]}) or bool({args[1]}))"
    if name == "not1": return f"(not bool({args[0]}))"
    if name == "gt": return f"({args[0]} > {args[1]})"
    if name == "lt": return f"({args[0]} < {args[1]})"
    if name == "eq": return f"(abs(({args[0]}) - ({args[1]})) < 1e-9)"
    if name == "head": return f"(float({args[0]}[0]) if {args[0]} else 0.0)"
    if name == "tail": return f"(list({args[0]}[1:]) if len({args[0]}) > 1 else [])"
    if name == "cons": return f"[float({args[0]})] + list({args[1]})"
    if name == "length": return f"float(len({args[0]}))"
    if name == "sort1": return f"sorted(list({args[0]}))"
    if name == "sum1": return f"(float(sum({args[0]})) if {args[0]} else 0.0)"
    if name == "map_sq": return f"[(float(v) * float(v)) for v in {args[0]}]"
    if name == "filter_pos": return f"[v for v in {args[0]} if float(v) > 0]"
    if name == "unique": return f"list(dict.fromkeys({args[0]}))"
    if name == "concat": return f"(str({args[0]}) + str({args[1]}))"
    if name == "upper1": return f"str({args[0]}).upper()"
    if name == "strip1": return f"str({args[0]}).strip()"
    if name == "split1": return f"str({args[0]}).split()"
    if name == "join1": return f"str({args[0]}).join(map(str, {args[1]}))"
    if name == "startswith2": return f"str({args[0]}).startswith(str({args[1]}))"
    if name == "replace3": return f"str({args[0]}).replace(str({args[1]}), str({args[2]}))"
    if name == "len_str": return f"float(len(str({args[0]})))"
    if name == "reverse1": return f"str({args[0]})[::-1]"
    return repr(fallback)


class GPTreeBuilder:
    """Construct, mutate, and crossover independently owned typed GP trees."""

    MAX_DEPTH = 8
    MAX_SIZE = 96

    def __init__(self, primitives: Iterable[Primitive], terminals: Iterable[Terminal], rng: random.Random) -> None:
        self.primitives = tuple(primitives)
        self.terminals = tuple(terminals)
        self.rng = rng
        if not self.terminals:
            raise ValueError("a GP builder requires at least one terminal")

    def random_tree(self, max_depth: int = 4, method: str = "ramped", return_type: str = FLOAT) -> GPNode:
        if max_depth < 0 or max_depth > self.MAX_DEPTH:
            raise ValueError(f"max_depth must be within 0..{self.MAX_DEPTH}")
        selected = self.rng.choice(("full", "grow")) if method == "ramped" else method
        if selected not in {"full", "grow"}:
            raise ValueError("method must be full, grow, or ramped")
        return self._build(max_depth, selected, return_type)

    def _build(self, max_depth: int, method: str, return_type: str) -> GPNode:
        choices = [primitive for primitive in self.primitives if primitive.return_type == return_type]
        terminals = [terminal for terminal in self.terminals if terminal.value_type == return_type]
        force_terminal = max_depth == 0 or not choices or (method == "grow" and terminals and self.rng.random() < 0.35)
        if force_terminal:
            if terminals:
                terminal = self.rng.choice(terminals)
                return GPNode(terminal_value=terminal.value, terminal_name=terminal.name, value_type=terminal.value_type)
            # Permit a type-correct literal fallback for under-specified task sets.
            return GPNode(terminal_value={FLOAT: 0.0, BOOL: False, LIST: [], STRING: ""}[return_type], value_type=return_type)
        primitive = self.rng.choice(choices)
        return GPNode(
            primitive=primitive,
            value_type=primitive.return_type,
            children=[self._build(max_depth - 1, method, child_type) for child_type in primitive.arg_types],
        )

    def point_mutate(self, tree: GPNode) -> GPNode:
        candidate = tree.copy()
        refs = self._collect_nodes(candidate)
        parent, index, target = self.rng.choice(refs)
        replacement = self.random_tree(self.rng.randint(0, min(3, self.MAX_DEPTH)), "grow", target.result_type)
        mutated = self._replace(candidate, parent, index, replacement)
        return mutated if self._within_limits(mutated) else tree.copy()

    def hoist_mutate(self, tree: GPNode) -> GPNode:
        candidate = tree.copy()
        internal = [node for _, _, node in self._collect_nodes(candidate) if not node.is_terminal and node.children]
        if not internal:
            return candidate
        return self.rng.choice(self.rng.choice(internal).children).copy()

    def expand_mutate(self, tree: GPNode) -> GPNode:
        candidate = tree.copy()
        terminal_refs = [reference for reference in self._collect_nodes(candidate) if reference[2].is_terminal]
        if not terminal_refs:
            return candidate
        parent, index, target = self.rng.choice(terminal_refs)
        replacement = self.random_tree(self.rng.randint(1, 2), "grow", target.result_type)
        expanded = self._replace(candidate, parent, index, replacement)
        return expanded if self._within_limits(expanded) else candidate

    def subtree_crossover(self, parent1: GPNode, parent2: GPNode) -> tuple[GPNode, GPNode]:
        """Cross over deep copies only; no descendant can share mutable nodes."""
        child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
        refs1, refs2 = self._collect_nodes(child1), self._collect_nodes(child2)
        compatible = [(left, right) for left in refs1 for right in refs2 if left[2].result_type == right[2].result_type]
        if not compatible:
            return child1, child2
        (p1, i1, n1), (p2, i2, n2) = self.rng.choice(compatible)
        proposed1 = self._replace(child1, p1, i1, n2.copy())
        proposed2 = self._replace(child2, p2, i2, n1.copy())
        return (
            proposed1 if self._within_limits(proposed1) else child1,
            proposed2 if self._within_limits(proposed2) else child2,
        )

    def _collect_nodes(self, root: GPNode, parent: GPNode | None = None, index: int = -1) -> list[tuple[GPNode | None, int, GPNode]]:
        result = [(parent, index, root)]
        for child_index, child in enumerate(root.children):
            result.extend(self._collect_nodes(child, root, child_index))
        return result

    @staticmethod
    def _replace(root: GPNode, parent: GPNode | None, index: int, replacement: GPNode) -> GPNode:
        if parent is None:
            return replacement
        parent.children[index] = replacement
        return root

    def _within_limits(self, tree: GPNode) -> bool:
        return tree.depth() <= self.MAX_DEPTH and tree.size() <= self.MAX_SIZE

    def to_python_function(
        self, tree: GPNode, name: str, args: Sequence[str], aliases: Mapping[str, str] | None = None,
    ) -> str:
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", safe_name):
            safe_name = "evolved_fn"
        valid_args = [arg for arg in args if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", arg)]
        alias_lines = [
            f"        {alias} = {target}"
            for alias, target in (aliases or {}).items()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias)
            and target in valid_args and alias not in valid_args
        ]
        bindings = "\n".join(alias_lines)
        source = textwrap.dedent(
            f"""
            import math

            def {safe_name}({", ".join(valid_args)}):
                try:
            {bindings if bindings else '        pass'}
                    return {tree.to_python()}
                except Exception:
                    return None
            """
        ).strip()
        try:
            compiled = compile(source, "<beast-gp-output>", "exec")
            if not isinstance(compiled, type(compile("pass", "<check>", "exec"))):
                raise SyntaxError("invalid code object")
            return source
        except (SyntaxError, ValueError, TypeError):
            return f"def {safe_name}({', '.join(valid_args)}):\n    return None"


@dataclass
class GPGenome:
    """A program genome with empirical fitness metadata."""

    tree: GPNode
    primitives_used: list[str] = field(default_factory=list)
    generation_created: int = 0
    parent_ids: list[str] = field(default_factory=list)
    fitness: float = 0.0
    fitness_variance: float = 1.0
    evaluations: int = 0

    def __post_init__(self) -> None:
        if not self.primitives_used:
            self.primitives_used = sorted({node.primitive.name for _, _, node in _nodes(self.tree) if node.primitive})

    def to_python(self, func_name: str = "evolved_fn", args: Sequence[str] | None = None) -> str:
        terminal_names = sorted({
            node.terminal_name for _, _, node in _nodes(self.tree)
            if node.is_terminal and node.terminal_name and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", node.terminal_name)
        })
        compatibility_aliases = {"input", "data"}
        if args is None:
            exported_args = ["x"] if set(terminal_names).issubset({"x", *compatibility_aliases}) else terminal_names or ["x"]
        else:
            exported_args = [arg for arg in args if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", arg)] or ["x"]
        aliases = {
            name: "x" for name in terminal_names
            if name in compatibility_aliases and "x" in exported_args
        }
        terminals = [Terminal(name=name, value_type=FLOAT) for name in exported_args]
        return GPTreeBuilder(DEFAULT_PRIMITIVES, terminals, random.Random(0)).to_python_function(
            self.tree, func_name, exported_args, aliases=aliases,
        )

    def execute(self, context: Mapping[str, Any]) -> Any:
        return self.tree.evaluate(context)

    def description_length(self) -> int:
        return len(zlib.compress(self.to_python().encode("utf-8"), level=9))

    def complexity(self) -> int:
        return self.tree.size()

    def depth(self) -> int:
        return self.tree.depth()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tree": self.tree.to_dict(), "primitives_used": self.primitives_used,
            "generation_created": self.generation_created, "parent_ids": self.parent_ids,
            "fitness": self.fitness, "fitness_variance": self.fitness_variance,
            "evaluations": self.evaluations,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], primitives: Iterable[Primitive] = ALL_REGISTERED_PRIMITIVES) -> "GPGenome":
        return cls(
            tree=GPNode.from_dict(payload["tree"], primitives=primitives),
            primitives_used=list(payload.get("primitives_used", [])),
            generation_created=int(payload.get("generation_created", 0)),
            parent_ids=list(payload.get("parent_ids", [])),
            fitness=float(payload.get("fitness", 0.0)),
            fitness_variance=float(payload.get("fitness_variance", 1.0)),
            evaluations=int(payload.get("evaluations", 0)),
        )


def _nodes(root: GPNode) -> list[tuple[GPNode | None, int, GPNode]]:
    return GPTreeBuilder._collect_nodes(GPTreeBuilder.__new__(GPTreeBuilder), root)  # type: ignore[misc]
