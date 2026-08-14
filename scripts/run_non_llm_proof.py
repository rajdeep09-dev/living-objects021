#!/usr/bin/env python3
"""Execute or independently verify BEAST's falsifiable non-LLM proof benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evolution.proof_benchmark import ProofBenchmarkConfig, run_proof_benchmark, verify_proof_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", metavar="ARTIFACT", help="independently rerun and verify an existing JSON artifact")
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--generations", type=int, default=1_000)
    parser.add_argument("--population-size", type=int, default=128)
    parser.add_argument("--audit-cases", type=int, default=128)
    parser.add_argument("--minimum-holdout-delta", type=float, default=0.10)
    parser.add_argument("--output", default="docs/artifacts/non-llm-proof-20260814.json")
    args = parser.parse_args()
    if args.verify:
        result = verify_proof_artifact(args.verify)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["verified"] else 1
    config = ProofBenchmarkConfig(
        seed=args.seed,
        generations=args.generations,
        population_size=args.population_size,
        audit_case_count=args.audit_cases,
        minimum_holdout_delta=args.minimum_holdout_delta,
    )
    artifact = run_proof_benchmark(config, Path(args.output))
    print(json.dumps({"artifact": args.output, "decision": artifact["decision"], "final_audits": artifact["final_audits"]}, indent=2, sort_keys=True))
    return 0 if artifact["decision"]["promoted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
