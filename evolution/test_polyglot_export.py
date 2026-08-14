from __future__ import annotations

from evolution.gp_engine import DEFAULT_PRIMITIVES, FLOAT, GPNode
from evolution.polyglot_export import PolyglotCompiler


def _tree() -> GPNode:
    primitives = {item.name: item for item in DEFAULT_PRIMITIVES}
    return GPNode(primitive=primitives["abs1"], children=[
        GPNode(primitive=primitives["sub"], children=[
            GPNode(terminal_name="left", value_type=FLOAT),
            GPNode(terminal_name="right", value_type=FLOAT),
        ]),
    ])


def test_polyglot_export_serializes_numeric_tree_without_running_it() -> None:
    compiler = PolyglotCompiler()
    javascript = compiler.to_javascript(_tree(), "difference", ("left", "right"))
    rust = compiler.to_rust(_tree(), "difference", ("left", "right"))
    go = compiler.to_go(_tree(), "Difference", ("left", "right"))
    assert "Math.abs" in javascript and "function difference" in javascript
    assert ".abs()" in rust and "fn difference" in rust
    assert "math.Abs" in go and "func Difference" in go
