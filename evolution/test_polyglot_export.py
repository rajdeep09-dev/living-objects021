from __future__ import annotations

import json
import subprocess

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


def test_javascript_export_matches_typed_python_interpreter_within_tolerance() -> None:
    tree = _tree()
    inputs = [(-13.5, 2.25), (0.0, 0.0), (4.125, -7.75), (100.0, 99.999999)]
    source = PolyglotCompiler().to_javascript(tree, "difference", ("left", "right"))
    process = subprocess.run(
        [
            "node", "-e",
            f"{source}\nconst inputs = {json.dumps(inputs)};\n"
            "console.log(JSON.stringify(inputs.map(([left, right]) => difference(left, right))));",
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    assert process.returncode == 0, process.stderr
    javascript_values = json.loads(process.stdout)
    python_values = [tree.evaluate({"left": left, "right": right}) for left, right in inputs]
    assert len(javascript_values) == len(python_values)
    assert all(abs(float(javascript) - float(python)) <= 1e-6 for javascript, python in zip(javascript_values, python_values))
