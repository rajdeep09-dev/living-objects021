#!/usr/bin/env python3
"""Independently reproduce the v11 recorded Manhattan SDK artifact."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from living_objects import reproduce


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "reports" / "v11" / "artifacts")
    parser.add_argument("--run-id", default="BEAST-SDK-V1-7A730FD3A21F5743")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "v11" / "manhattan-reproduction.json")
    args = parser.parse_args()

    started = time.perf_counter()
    outcome = reproduce(args.run_id, artifact_dir=args.artifact_dir)
    record = {
        "schema": "beast-v11-manhattan-reproduction-v1",
        "status": "verified" if outcome.verified else "mismatch",
        "run_id": outcome.run_id,
        "elapsed_seconds": time.perf_counter() - started,
        "expected_tree_sha256": outcome.expected_tree_sha256,
        "reproduced_tree_sha256": outcome.reproduced_tree_sha256,
        "mismatches": outcome.mismatches,
        "execution_boundary": outcome.execution_boundary,
        "claim_boundary": "This verifies only the saved bounded configuration on this environment.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if outcome.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
