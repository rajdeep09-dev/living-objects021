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
import time
import zlib
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Sequence


FLOAT = "float"
BOOL = "bool"
LIST = "list"
STRING = "str"
TEXT_INPUT_LIMIT = 16_384
TEXT_OUTPUT_LIMIT = 16_384


def _bounded_text(value: Any, limit: int = TEXT_OUTPUT_LIMIT) -> str:
    """Return a bounded string for pure Tier 2 text operations."""
    return str(value)[: max(0, min(int(limit), TEXT_OUTPUT_LIMIT))]


def _bounded_index(value: Any, upper: int = TEXT_OUTPUT_LIMIT) -> int:
    try:
        return max(0, min(int(float(value)), upper))
    except (TypeError, ValueError, OverflowError):
        return 0


def _extract_between(text: Any, start: Any, end: Any) -> str:
    source, first, last = _bounded_text(text), _bounded_text(start), _bounded_text(end)
    if not first or not last:
        return ""
    start_at = source.find(first)
    if start_at < 0:
        return ""
    content_at = start_at + len(first)
    end_at = source.find(last, content_at)
    return _bounded_text(source[content_at:end_at] if end_at >= 0 else "")


def _extract_after(text: Any, marker: Any) -> str:
    source, token = _bounded_text(text), _bounded_text(marker)
    if not token:
        return ""
    at = source.find(token)
    return _bounded_text(source[at + len(token):] if at >= 0 else "")


def _extract_before(text: Any, marker: Any) -> str:
    source, token = _bounded_text(text), _bounded_text(marker)
    if not token:
        return ""
    at = source.find(token)
    return _bounded_text(source[:at] if at >= 0 else "")


def _nth_word(text: Any, index: Any) -> str:
    words = _bounded_text(text).split()
    position = _bounded_index(index, len(words))
    return _bounded_text(words[position] if position < len(words) else "")


def _nth_line(text: Any, index: Any) -> str:
    lines = _bounded_text(text).splitlines()
    position = _bounded_index(index, len(lines))
    return _bounded_text(lines[position] if position < len(lines) else "")


_EMAIL_FORMAT = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})+$")
_HTML_TAG = re.compile(r"<[^>]{0,1024}>")
_FIRST_NUMBER = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def _is_email(text: Any) -> bool:
    return bool(_EMAIL_FORMAT.fullmatch(_bounded_text(text)))


def _is_url(text: Any) -> bool:
    value = _bounded_text(text)
    return value.startswith(("http://", "https://")) and bool(_extract_domain(value) and "." in _extract_domain(value))


def _is_phone(text: Any) -> bool:
    digits = "".join(character for character in _bounded_text(text) if character.isdigit())
    return 10 <= len(digits) <= 15


def _is_numeric(text: Any) -> bool:
    value = _bounded_text(text).strip()
    try:
        float(value)
        return bool(value)
    except ValueError:
        return False


def _remove_punctuation(text: Any) -> str:
    return _bounded_text("".join(character for character in _bounded_text(text) if character.isalnum() or character.isspace() or character == "@"))


def _collapse_whitespace(text: Any) -> str:
    return _bounded_text(" ".join(_bounded_text(text).split()))


def _remove_html_tags(text: Any) -> str:
    # Static bounded pattern only; no evolved or user-supplied regex is accepted.
    return _bounded_text(_HTML_TAG.sub("", _bounded_text(text)))


def _decode_html_entities(text: Any) -> str:
    value = _bounded_text(text)
    for encoded, decoded in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        value = value.replace(encoded, decoded)
    return _bounded_text(value)


def _split_on(text: Any, delimiter: Any) -> list[str]:
    value, token = _bounded_text(text), _bounded_text(delimiter)
    return [_bounded_text(item) for item in (value.split(token) if token else [value])]


def _pad(text: Any, width: Any, pad_character: Any, *, left: bool) -> str:
    value = _bounded_text(text)
    target_width = _bounded_index(width, 4_096)
    pad = _bounded_text(pad_character)[:1] or " "
    return _bounded_text(value.rjust(target_width, pad) if left else value.ljust(target_width, pad))


def _extract_domain(url: Any) -> str:
    value = _bounded_text(url)
    after_protocol = value.split("://", 1)[1] if "://" in value else value
    return _bounded_text(after_protocol.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0])


def _extract_email_domain(email: Any) -> str:
    value = _bounded_text(email)
    return _bounded_text(value.rsplit("@", 1)[1] if "@" in value else "")


def _extract_tld(domain: Any) -> str:
    value = _bounded_text(domain).rstrip(".")
    return _bounded_text(value.rsplit(".", 1)[1] if "." in value else "")


def _strip_protocol(url: Any) -> str:
    value = _bounded_text(url)
    return _bounded_text(value[8:] if value.startswith("https://") else value[7:] if value.startswith("http://") else value)


def _normalise_company_name(text: Any) -> str:
    value = _remove_punctuation(text).strip()
    words = value.split()
    if words and words[-1].lower() in {"inc", "llc", "ltd", "corp", "co", "gmbh"}:
        words.pop()
    return _bounded_text(" ".join(words))


def _extract_first_number(text: Any) -> float:
    match = _FIRST_NUMBER.search(_bounded_text(text))
    return float(match.group(0)) if match else 0.0


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
    Primitive("sum1", 1, lambda values: float(sum(values)) if values else 0.0, FLOAT, (LIST,)),
    Primitive("map_sq", 1, lambda values: [float(value) * float(value) for value in values], LIST, (LIST,)),
    Primitive("filter_pos", 1, lambda values: [value for value in values if float(value) > 0], LIST, (LIST,)),
    Primitive("unique", 1, lambda values: list(dict.fromkeys(values)), LIST, (LIST,)),
)

# Direct task-solution shortcuts are retained solely to decode historic artifacts
# or support an explicitly declared convenience profile. They must not enter the
# default grammar used for a new generic run: otherwise a sorting benchmark can
# be solved by selecting its target operation rather than composing a program.
CONVENIENCE_PRIMITIVES: tuple[Primitive, ...] = (
    Primitive("sort1", 1, lambda values: sorted(list(values)), LIST, (LIST,)),
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
    Primitive("extract_between", 3, _extract_between, STRING, (STRING, STRING, STRING)),
    Primitive("extract_after", 2, _extract_after, STRING, (STRING, STRING)),
    Primitive("extract_before", 2, _extract_before, STRING, (STRING, STRING)),
    Primitive("nth_word", 2, _nth_word, STRING, (STRING, FLOAT)),
    Primitive("nth_line", 2, _nth_line, STRING, (STRING, FLOAT)),
    Primitive("is_email", 1, _is_email, BOOL, (STRING,)),
    Primitive("is_url", 1, _is_url, BOOL, (STRING,)),
    Primitive("is_phone", 1, _is_phone, BOOL, (STRING,)),
    Primitive("is_numeric", 1, _is_numeric, BOOL, (STRING,)),
    Primitive("contains_digit", 1, lambda value: any(character.isdigit() for character in _bounded_text(value)), BOOL, (STRING,)),
    Primitive("contains_alpha", 1, lambda value: any(character.isalpha() for character in _bounded_text(value)), BOOL, (STRING,)),
    Primitive("remove_punctuation", 1, _remove_punctuation, STRING, (STRING,)),
    Primitive("collapse_whitespace", 1, _collapse_whitespace, STRING, (STRING,)),
    Primitive("to_lowercase", 1, lambda value: _bounded_text(value).lower(), STRING, (STRING,)),
    Primitive("to_titlecase", 1, lambda value: _bounded_text(value).title(), STRING, (STRING,)),
    Primitive("remove_html_tags", 1, _remove_html_tags, STRING, (STRING,)),
    Primitive("decode_html_entities", 1, _decode_html_entities, STRING, (STRING,)),
    Primitive("count_occurrences", 2, lambda text, substring: float(_bounded_text(text).count(_bounded_text(substring))) if _bounded_text(substring) else 0.0, FLOAT, (STRING, STRING)),
    Primitive("find_first", 2, lambda text, substring: float(_bounded_text(text).find(_bounded_text(substring))), FLOAT, (STRING, STRING)),
    Primitive("find_last", 2, lambda text, substring: float(_bounded_text(text).rfind(_bounded_text(substring))), FLOAT, (STRING, STRING)),
    Primitive("split_on", 2, _split_on, LIST, (STRING, STRING)),
    Primitive("join_with", 2, lambda values, delimiter: _bounded_text(_bounded_text(delimiter).join(_bounded_text(value) for value in list(values)[:TEXT_INPUT_LIMIT])), STRING, (LIST, STRING)),
    Primitive("pad_left", 3, lambda text, width, pad: _pad(text, width, pad, left=True), STRING, (STRING, FLOAT, STRING)),
    Primitive("pad_right", 3, lambda text, width, pad: _pad(text, width, pad, left=False), STRING, (STRING, FLOAT, STRING)),
    Primitive("truncate", 2, lambda text, length: _bounded_text(text, _bounded_index(length)), STRING, (STRING, FLOAT)),
    Primitive("extract_domain", 1, _extract_domain, STRING, (STRING,)),
    Primitive("extract_email_domain", 1, _extract_email_domain, STRING, (STRING,)),
    Primitive("extract_tld", 1, _extract_tld, STRING, (STRING,)),
    Primitive("strip_protocol", 1, _strip_protocol, STRING, (STRING,)),
    Primitive("normalise_company_name", 1, _normalise_company_name, STRING, (STRING,)),
    Primitive("extract_first_number", 1, _extract_first_number, FLOAT, (STRING,)),
)

DEFAULT_PRIMITIVES = ARITHMETIC_PRIMITIVES + BOOLEAN_PRIMITIVES + LIST_PRIMITIVES + STRING_PRIMITIVES
ALL_REGISTERED_PRIMITIVES = DEFAULT_PRIMITIVES + GENERIC_LIST_CONTROL_PRIMITIVES + CONVENIENCE_PRIMITIVES


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
_EVALUATION_DEADLINE: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "gp_evaluation_deadline", default=None
)
DEFAULT_EVALUATION_TIMEOUT_SECONDS = 0.5


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
        deadline = _EVALUATION_DEADLINE.get()
        if deadline is not None and time.monotonic() >= deadline:
            return self.fallback()
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
            if deadline is not None and time.monotonic() >= deadline:
                return self.fallback()
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

    def execute(
        self,
        context: Mapping[str, Any],
        *,
        max_elapsed_seconds: float | None = DEFAULT_EVALUATION_TIMEOUT_SECONDS,
    ) -> Any:
        """Interpret one candidate with a cooperative wall-clock deadline.

        The admitted grammar contains only local typed primitives.  The deadline
        is checked before and after every interpreter node, so oversized or
        future recursive trees degrade to a type-correct fallback.  It is not a
        pre-emptive kill mechanism for arbitrary user callables; such callables
        are outside the admitted primitive boundary and require process-level
        isolation before they could be accepted.
        """
        if max_elapsed_seconds is None:
            return self.tree.evaluate(context)
        if max_elapsed_seconds <= 0:
            return self.tree.fallback()
        parent_deadline = _EVALUATION_DEADLINE.get()
        deadline = time.monotonic() + max_elapsed_seconds
        if parent_deadline is not None:
            deadline = min(deadline, parent_deadline)
        token = _EVALUATION_DEADLINE.set(deadline)
        try:
            return self.tree.evaluate(context)
        finally:
            _EVALUATION_DEADLINE.reset(token)

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
