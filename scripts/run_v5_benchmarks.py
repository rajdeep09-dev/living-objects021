#!/usr/bin/env python3
"""Run bounded, resumable BEAST v5 local evolution benchmarks.

The runner intentionally evolves local trait profiles only.  It does not execute
user text or make a request for each generation.  Use the generated report as
measured process evidence, not a claim that an arbitrary code solution was proven.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from dataclasses import asdict
from pathlib import Path

from evolution.v5 import AutonomousEvolutionWorker
from scripts.tasks import TASKS


def write_report(output: Path, *, task_id: str, snapshot: dict, elapsed: float, workspace: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# BEAST v5 Local Evolution Report",
        "",
        f"## Task: `{task_id}`",
        "",
        "| Metric | Measured value |",
        "|---|---:|",
        f"| Status | {snapshot['status']} |",
        f"| Generations | {snapshot['generation']:,} / {snapshot['target_generations']:,} |",
        f"| Peak fitness | {snapshot['peak_fitness']:.6f} |",
        f"| Average fitness | {snapshot['average_fitness']:.6f} |",
        f"| Cultural complexity | {snapshot['cultural_complexity']:.6f} |",
        f"| Novel descriptors | {snapshot['novelty_count']:,} |",
        f"| Memome strategies | {snapshot['archive_size']:,} |",
        f"| Elapsed seconds | {elapsed:.3f} |",
        "",
        "## Reproducibility",
        "",
        f"- Workspace: `{workspace}`",
        f"- Python platform: `{platform.platform()}`",
        "- The worker uses an explicit local task registry and writes atomic checkpoints.",
        "- No network request is issued in the generation loop; process persistence still requires an always-on host for unattended runs.",
        "- This report measures trait-profile evolution and cultural inheritance; it is not a correctness proof for arbitrary generated source code.",
        "",
        "## Recent lifecycle events",
        "",
    ]
    lines.extend(f"- Gen {event['generation']:,}: `{event['type']}`" for event in snapshot["events"][-10:])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_task(task_id: str, args: argparse.Namespace) -> Path:
    descriptor = TASKS[task_id]
    workspace = Path(args.workspace) / task_id
    if args.resume and (workspace / "worker.json").exists():
        worker = AutonomousEvolutionWorker.resume_from_workspace(workspace)
    else:
        worker = AutonomousEvolutionWorker(
            descriptor.goal_hint, workspace,
            target_generations=args.generations, population_size=args.population,
            workers=args.workers, checkpoint_interval=args.checkpoint_interval, seed=args.seed,
        )
    started = time.perf_counter()
    while worker.snapshot().status not in {"completed", "cancelled", "failed"}:
        worker.run_batch(args.batch_size)
    snapshot = asdict(worker.snapshot())
    elapsed = time.perf_counter() - started
    output = Path(args.reports_dir) / f"{task_id}_{snapshot['generation']}.md"
    write_report(output, task_id=task_id, snapshot=snapshot, elapsed=elapsed, workspace=workspace)
    (output.with_suffix(".json")).write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    worker.close()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded BEAST v5 local benchmarks")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--task", choices=sorted(TASKS))
    choice.add_argument("--all", action="store_true")
    parser.add_argument("--generations", type=int, default=100_000, choices=range(1, 1_000_001))
    parser.add_argument("--population", type=int, default=12, choices=range(2, 257))
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 33))
    parser.add_argument("--checkpoint-interval", type=int, default=1_000, choices=range(1, 100_001))
    parser.add_argument("--batch-size", type=int, default=1_000, choices=range(1, 100_001))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workspace", default="checkpoints/v5")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    task_ids = sorted(TASKS) if args.all else [args.task]
    for task_id in task_ids:
        print(run_task(task_id, args))


if __name__ == "__main__":
    main()
