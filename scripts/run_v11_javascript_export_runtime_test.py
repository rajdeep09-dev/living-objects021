#!/usr/bin/env python3
"""Verify an exported Manhattan JavaScript champion against the typed interpreter."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evolution.gp_engine import GPGenome
from living_objects import evolve, export


CASES = (
    (0.0, 0.0, 3.0, 4.0),
    (-2.0, 5.0, 7.0, -1.0),
    (1.25, -3.5, 1.25, -3.5),
    (10.0, 20.0, -10.0, -20.0),
    (-0.5, 0.25, 0.75, -1.5),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20_260_814)
    parser.add_argument("--population-size", type=int, default=128)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "v11" / "javascript-export-runtime.json")
    args = parser.parse_args()

    result = evolve(
        "manhattan",
        generations=args.generations,
        seed=args.seed,
        population_size=args.population_size,
        artifact_dir=args.output.parent / "artifacts",
    )
    javascript = export(result, "javascript")
    genome = GPGenome.from_dict(result.champion["tree"])
    expected = [genome.execute({"x1": x1, "y1": y1, "x2": x2, "y2": y2}) for x1, y1, x2, y2 in CASES]

    driver = (
        '"use strict";\n'
        + javascript.source
        + "\nconst cases = "
        + json.dumps(CASES)
        + ";\nconsole.log(JSON.stringify(cases.map((values) => beast_export(...values))));\n"
    )
    with tempfile.TemporaryDirectory(prefix="beast-v11-js-") as temporary:
        source_path = Path(temporary) / "champion.mjs"
        source_path.write_text(driver, encoding="utf-8")
        completed = subprocess.run(
            ["node", str(source_path)], check=True, capture_output=True, text=True, timeout=5
        )
    actual = json.loads(completed.stdout)
    comparisons = [
        {"inputs": list(case), "typed_interpreter": want, "node_javascript": got, "match": want == got}
        for case, want, got in zip(CASES, expected, actual)
    ]
    record = {
        "schema": "beast-v11-javascript-export-runtime-v1",
        "status": "verified" if all(item["match"] for item in comparisons) else "mismatch",
        "configuration": {"task": result.task, "generations": args.generations, "seed": args.seed, "population_size": args.population_size},
        "champion_tree_sha256": result.champion["tree_sha256"],
        "comparisons": comparisons,
        "javascript_source": javascript.source,
        "execution_boundary": (
            "The typed AST interpreter remained the evolution runtime. This one-off verification executed "
            "only the generated JavaScript export in Node.js; it did not execute generated Python source."
        ),
        "claim_boundary": "Five fixed inputs verify this export only; they do not certify every primitive or target runtime.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
