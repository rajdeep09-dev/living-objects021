"""Collect deterministic local evaluator patterns for AGNES-BRAIN research.

Each row holds five observed input/output pairs and fifteen continuation pairs
from an approved evaluator. No generated program is run by this script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evolution.fitness import (
    AbsoluteDifferenceEvaluator,
    CompressionEvaluator,
    FibonacciEvaluator,
    FitnessEvaluator,
    ManhattanDistanceEvaluator,
    MaxSubarrayEvaluator,
    PathfindingEvaluator,
    PrimeEvaluator,
    SortingEvaluator,
    StringReverseEvaluator,
)
from living_objects.beast_brain.collectors import _record_id, collect_evaluator_case_cards, write_jsonl_new


DEFAULT_DESTINATION = Path(__file__).resolve().parent / "test_cases" / "from_evaluators.jsonl"
EXAMPLE_SEED = 42
TOTAL_CASES = 20
OBSERVED_CASES = 5


def working_evaluators() -> tuple[FitnessEvaluator, ...]:
    """Return the reviewed deterministic evaluator set for local case collection.

    ``GameStrategyEvaluator`` is intentionally absent because its v12 review is
    pending and its constructor fails closed. Adding an evaluator requires an
    explicit update here and passing the shared evaluator-approval gate.
    """

    return (
        SortingEvaluator(),
        PrimeEvaluator(),
        FibonacciEvaluator(),
        StringReverseEvaluator(),
        MaxSubarrayEvaluator(),
        AbsoluteDifferenceEvaluator(),
        ManhattanDistanceEvaluator(),
        CompressionEvaluator(),
        PathfindingEvaluator(),
    )


def _pair(card: dict[str, Any]) -> list[Any]:
    return [card["input"], card["expected_output"]]


def build_examples(*, seed: int = EXAMPLE_SEED) -> tuple[dict[str, Any], ...]:
    """Create one non-executing prediction-pattern record for each working evaluator."""

    records: list[dict[str, Any]] = []
    for evaluator in working_evaluators():
        case_cards = collect_evaluator_case_cards(evaluator, seed=seed, case_count=TOTAL_CASES)
        if len(case_cards) != TOTAL_CASES:
            raise ValueError(f"{type(evaluator).__name__} returned {len(case_cards)} rather than {TOTAL_CASES} cases")
        record: dict[str, Any] = {
            "schema_version": "agnes-brain-evaluator-pattern-v1",
            "evaluator": type(evaluator).__name__,
            "input_examples": [_pair(card) for card in case_cards[:OBSERVED_CASES]],
            "output_examples": [_pair(card) for card in case_cards[OBSERVED_CASES:]],
            "source": {
                "kind": "local_deterministic_evaluator",
                "seed": seed,
                "case_count": TOTAL_CASES,
                "approval_checked": True,
                "candidate_programs_executed": 0,
            },
        }
        record["record_id"] = _record_id(record)
        records.append(record)
    return tuple(records)


def collect(destination: str | Path = DEFAULT_DESTINATION, *, seed: int = EXAMPLE_SEED) -> Path:
    """Write the fixed-seed local evaluator corpus exactly once."""

    return write_jsonl_new(build_examples(seed=seed), destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect approved local evaluator examples.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--seed", type=int, default=EXAMPLE_SEED)
    args = parser.parse_args()
    output = collect(args.output, seed=args.seed)
    print(f"Wrote {len(build_examples(seed=args.seed))} local evaluator patterns to {output}")


if __name__ == "__main__":
    main()
