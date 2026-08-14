"""Static validation for exported BEAST v6 GP programs.

The typed interpreter remains the authoritative execution path.  This module
checks an exported Python representation for auditability only; it never
executes that source and must not be treated as an operating-system sandbox.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterable

from evolution.gp_engine import DEFAULT_PRIMITIVES, GPNode, Primitive


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    reason: str
    node_count: int = 0
    depth: int = 0
    source_bytes: int = 0


class ProgramValidator:
    """Reject malformed trees and source outside the deliberate GP dialect."""

    MAX_TREE_DEPTH = 8
    MAX_TREE_NODES = 96
    MAX_SOURCE_BYTES = 12_000
    _BLOCKED_NAMES = {
        "__builtins__", "__import__", "breakpoint", "compile", "eval", "exec",
        "globals", "input", "locals", "open", "os", "pathlib", "socket",
        "subprocess", "sys", "type", "vars",
    }
    _BLOCKED_NODES = (ast.ClassDef, ast.Delete, ast.Global, ast.Lambda, ast.Nonlocal,
                      ast.Raise, ast.With, ast.AsyncWith, ast.While, ast.For,
                      ast.AsyncFor, ast.Yield, ast.YieldFrom)

    def __init__(self, primitives: Iterable[Primitive] = DEFAULT_PRIMITIVES) -> None:
        self._primitives = {primitive.name: primitive for primitive in primitives}

    def validate_tree(self, root: GPNode) -> ValidationReport:
        count = 0

        def walk(node: GPNode, depth: int) -> tuple[bool, str, int]:
            nonlocal count
            count += 1
            if count > self.MAX_TREE_NODES:
                return False, "tree exceeds node limit", depth
            if depth > self.MAX_TREE_DEPTH:
                return False, "tree exceeds depth limit", depth
            if node.is_terminal:
                if node.children:
                    return False, "terminal has children", depth
                return True, "ok", depth
            if node.primitive is None or node.primitive.name not in self._primitives:
                return False, "unknown primitive", depth
            expected = self._primitives[node.primitive.name]
            if len(node.children) != expected.arity:
                return False, "primitive arity mismatch", depth
            if node.result_type != expected.return_type:
                return False, "primitive return type mismatch", depth
            deepest = depth
            for child, argument_type in zip(node.children, expected.arg_types):
                if child.result_type != argument_type:
                    return False, "child type mismatch", deepest
                valid, reason, child_depth = walk(child, depth + 1)
                deepest = max(deepest, child_depth)
                if not valid:
                    return valid, reason, deepest
            return True, "ok", deepest

        valid, reason, depth = walk(root, 0)
        return ValidationReport(valid=valid, reason=reason, node_count=count, depth=depth)

    def validate_source(self, source: str) -> ValidationReport:
        source_bytes = len(source.encode("utf-8"))
        if source_bytes > self.MAX_SOURCE_BYTES:
            return ValidationReport(False, "source exceeds byte limit", source_bytes=source_bytes)
        try:
            tree = ast.parse(source, mode="exec")
        except SyntaxError as exc:
            return ValidationReport(False, f"syntax error: {exc.msg}", source_bytes=source_bytes)

        function_count = 0
        for node in ast.walk(tree):
            if isinstance(node, self._BLOCKED_NODES):
                return ValidationReport(False, f"blocked syntax: {type(node).__name__}", source_bytes=source_bytes)
            if isinstance(node, ast.Import):
                if len(node.names) != 1 or node.names[0].name != "math" or node.names[0].asname:
                    return ValidationReport(False, "only import math is allowed", source_bytes=source_bytes)
            if isinstance(node, ast.ImportFrom):
                return ValidationReport(False, "from imports are forbidden", source_bytes=source_bytes)
            if isinstance(node, ast.Name) and (node.id in self._BLOCKED_NAMES or node.id.startswith("__")):
                return ValidationReport(False, f"blocked name: {node.id}", source_bytes=source_bytes)
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                return ValidationReport(False, "dunder attribute access is forbidden", source_bytes=source_bytes)
            if isinstance(node, ast.FunctionDef):
                function_count += 1
                if node.decorator_list or node.returns is not None:
                    return ValidationReport(False, "decorators and annotations are forbidden", source_bytes=source_bytes)
        if function_count != 1:
            return ValidationReport(False, "exactly one exported function is required", source_bytes=source_bytes)
        return ValidationReport(True, "ok", source_bytes=source_bytes)


__all__ = ["ProgramValidator", "ValidationReport"]
