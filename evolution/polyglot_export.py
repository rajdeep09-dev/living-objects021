"""Direct, bounded export of numeric GP trees to portable source snippets.

Export is serialization, not execution.  Generated snippets must be compiled,
reviewed, and sandboxed by the receiving environment before use.
"""
from __future__ import annotations

import re
from typing import Mapping, Sequence

from evolution.gp_engine import FLOAT, GPNode


class PolyglotCompiler:
    """Compile the supported numeric GP primitive subset to source strings."""

    MAX_TREE_SIZE = 96
    _NUMERIC_TEMPLATES: Mapping[str, Mapping[str, str]] = {
        "javascript": {
            "add": "({0} + {1})", "sub": "({0} - {1})", "mul": "({0} * {1})",
            "div": "({1} === 0 ? 0 : {0} / {1})", "neg": "(-{0})", "abs1": "Math.abs({0})",
            "sq": "({0} * {0})", "max2": "Math.max({0}, {1})", "min2": "Math.min({0}, {1})",
        },
        "rust": {
            "add": "({0} + {1})", "sub": "({0} - {1})", "mul": "({0} * {1})",
            "div": "(if {1} == 0.0 {{ 0.0 }} else {{ {0} / {1} }})", "neg": "(-{0})", "abs1": "{0}.abs()",
            "sq": "({0} * {0})", "max2": "{0}.max({1})", "min2": "{0}.min({1})",
        },
        "go": {
            "add": "({0} + {1})", "sub": "({0} - {1})", "mul": "({0} * {1})",
            "div": "safeDiv({0}, {1})", "neg": "(-{0})", "abs1": "math.Abs({0})",
            "sq": "({0} * {0})", "max2": "math.Max({0}, {1})", "min2": "math.Min({0}, {1})",
        },
    }

    def _validate(self, tree: GPNode) -> None:
        if tree.size() > self.MAX_TREE_SIZE or tree.depth() > 8:
            raise ValueError("tree exceeds portable export limits")
        for node in self._nodes(tree):
            if node.result_type != FLOAT:
                raise ValueError("only numeric GP trees can be exported")
            if node.primitive and node.primitive.name not in self._NUMERIC_TEMPLATES["javascript"]:
                raise ValueError(f"unsupported portable primitive: {node.primitive.name}")

    def to_javascript(self, tree: GPNode, name: str = "evolved", args: Sequence[str] = ("x",)) -> str:
        return self._wrap("javascript", tree, name, args)

    def to_rust(self, tree: GPNode, name: str = "evolved", args: Sequence[str] = ("x",)) -> str:
        return self._wrap("rust", tree, name, args)

    def to_go(self, tree: GPNode, name: str = "Evolved", args: Sequence[str] = ("x",)) -> str:
        return self._wrap("go", tree, name, args)

    def _wrap(self, language: str, tree: GPNode, name: str, args: Sequence[str]) -> str:
        self._validate(tree)
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name) or "evolved"
        safe_args = tuple(arg for arg in args if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", arg)) or ("x",)
        expression = self._expression(tree, language)
        if language == "javascript":
            return f"function {safe_name}({', '.join(safe_args)}) {{ return {expression}; }}"
        if language == "rust":
            typed = ", ".join(f"{arg}: f64" for arg in safe_args)
            return f"fn {safe_name}({typed}) -> f64 {{ {expression} }}"
        typed = ", ".join(f"{arg} float64" for arg in safe_args)
        return "import \"math\"\n\nfunc safeDiv(a, b float64) float64 { if b == 0 { return 0 }; return a / b }\n\n" + f"func {safe_name}({typed}) float64 {{ return {expression} }}"

    def _expression(self, node: GPNode, language: str) -> str:
        if node.is_terminal:
            if node.terminal_name:
                return node.terminal_name
            return repr(float(node.terminal_value or 0.0))
        assert node.primitive is not None
        template = self._NUMERIC_TEMPLATES[language][node.primitive.name]
        return template.format(*(self._expression(child, language) for child in node.children))

    @staticmethod
    def _nodes(root: GPNode) -> list[GPNode]:
        found = [root]
        for child in root.children:
            found.extend(PolyglotCompiler._nodes(child))
        return found


__all__ = ["PolyglotCompiler"]
