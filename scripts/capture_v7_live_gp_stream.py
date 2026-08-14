#!/usr/bin/env python3
"""Capture real bounded GP broadcaster messages as a reviewable v7 artifact.

This utility uses the same interpreter-only broadcaster tested by the API
integration suite. It does not contact a network endpoint, execute champion
source, or simulate events: every JSON event follows a completed
``GPPopulation.step()`` call.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from evolution.fitness import SortingEvaluator
from production.api.v6.websocket import LiveGPPopulationBroadcaster


async def capture(*, steps: int, seed: int, population_size: int) -> dict[str, object]:
    broadcaster = LiveGPPopulationBroadcaster()
    events = await broadcaster.advance(
        task_domain="sorting", evaluator=SortingEvaluator(), population_size=population_size,
        seed=seed, steps=steps,
    )
    return {
        "schema": "beast-v7-live-gp-stream-capture-v1",
        "status": "captured-real-generation-events",
        "configuration": {
            "task_domain": "sorting",
            "steps": steps,
            "seed": seed,
            "population_size": population_size,
            "runtime": "typed AST interpreter only",
            "llm_calls_in_generation_loop": 0,
            "network_calls_in_generation_loop": 0,
        },
        "events": events,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--seed", type=int, default=901)
    parser.add_argument("--population-size", type=int, default=8)
    parser.add_argument("--output", default="reports/v7_live_gp_stream.json")
    args = parser.parse_args()
    if not 1 <= args.steps <= 100:
        raise ValueError("steps must be in 1..100")
    payload = asyncio.run(capture(steps=args.steps, seed=args.seed, population_size=args.population_size))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "event_count": len(payload["events"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
