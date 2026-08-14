"""AST-only modularity analysis; malformed source is scored as non-modular."""
from __future__ import annotations

import ast
from typing import Any


class ModularityDetector:
    def modularity_score(self, strategy_code: str) -> float:
        try:
            tree = ast.parse(strategy_code)
        except (SyntaxError, ValueError):
            return 0.0
        functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not functions:
            return 0.0
        names = {function.name for function in functions}
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        average_lines = sum(len(function.body) for function in functions) / len(functions)
        brevity = 1.0 / max(1.0, average_lines / 5.0)
        reuse = len(calls & names) / len(names)
        return round(min(1.0, len(functions) * 0.15 + brevity * 0.45 + reuse * 0.40), 6)

    def fitness_bonus(self, organism: Any) -> float:
        scores = [self.modularity_score(str(getattr(item, "source_code", ""))) for item in getattr(organism, "learned_strategies", {}).values()]
        return round(sum(scores) / max(1, len(scores)), 6)


__all__ = ["ModularityDetector"]
