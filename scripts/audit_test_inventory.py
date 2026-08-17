"""Collect and summarize the repository's real pytest inventory.

This script executes ``pytest --collect-only -q`` and writes a JSON summary of
the test node IDs pytest actually collects. It does not infer coverage from
file names or fabricate a test count.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _module_for_node(node_id: str) -> str | None:
    """Return the test module portion of a pytest node identifier."""
    if "::" not in node_id or not node_id.endswith("]") and "::" not in node_id:
        return None
    module, _, _ = node_id.partition("::")
    return module if module.endswith(".py") else None


def collect_inventory() -> dict[str, object]:
    """Run pytest collection and return an evidence-backed inventory."""
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "pytest collection failed:\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )

    nodes = [
        line.strip()
        for line in completed.stdout.splitlines()
        if "::" in line and line.strip().split("::", 1)[0].endswith(".py")
    ]
    counts = Counter(
        module
        for node in nodes
        if (module := _module_for_node(node)) is not None
    )
    return {
        "command": "APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest --collect-only -q",
        "collected_cases": len(nodes),
        "modules": [
            {"path": path, "cases": cases}
            for path, cases in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "v9-test-inventory.json",
        help="JSON destination for the collected inventory.",
    )
    args = parser.parse_args()
    inventory = collect_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"Collected {inventory['collected_cases']} pytest cases into {args.output}")


if __name__ == "__main__":
    main()
