# BEAST v5 Autonomous Organism Workspace

BEAST v5 adds a **local-first organism lifecycle**. A user states a short goal, BEAST resolves that text to a fixed local task profile, evolves an inherited population in bounded batches, writes atomic checkpoints, and exposes status, pause, resume, cancel, and export controls. The user goal is **data**, not executable code. It cannot become a shell command, Python source file, or unrestricted tool call.

> **Important:** v5 is an experimental evolutionary search framework. A high fitness score reports progress against its declared local trait/task objective; it does not prove general intelligence, real-world correctness, consciousness, or safe autonomous action.

## Execution model

| Layer | Responsibility | Network behavior |
|---|---|---|
| User control plane | Creates a run, sets a finite budget, and requests lifecycle transitions. | One request per user action. |
| Autonomous worker | Runs `run_batch()` over a registered local task profile. | **No per-generation network request.** |
| Checkpoint manager | Atomically snapshots ecosystem, memome, history, and metadata. | Local filesystem or durable volume only. |
| Observatory | Reads durable summaries and displays lineage, culture, novelty, and control state. | Polls only at a human-facing refresh interval. |

The worker intentionally has no internal always-running timer. A local CLI, a container worker, or an always-on persistent host calls finite batches. This prevents a web request from silently becoming unbounded compute and keeps pause/cancel boundaries observable.

## Goal routing and safety boundary

`evolution.v5.resolve_task()` maps a short goal to one of the declared local task profiles: prime strategy, sorting, compression, denoising, maze pathfinding, cooperation, or general research. Each profile evaluates genome traits and cultural reuse using deterministic local scoring. The runner does not execute natural-language goals, generated code, browser scripts, shell commands, or external tools.

| Guardrail | v5 behavior |
|---|---|
| Generation budget | A worker accepts 1 to 1,000,000 generations per declared run. |
| Population budget | 2 to 256 organisms. |
| Parallel scoring | 1 to 32 bounded local workers. |
| Checkpoint integrity | Temporary manifest followed by atomic replace. |
| Cancellation | Checked between generations; a final checkpoint is written. |
| Resume | Restores an explicit checkpoint; a run found `running` after process exit becomes `paused`. |
| Goal safety | Goal text only selects a local task profile and is never executed. |

For a request such as “millions of generations,” use several finite runs or an explicit higher-level scheduler that starts new finite workers after a reviewed completion event. Do not remove the cap or hide resource consumption. A long unattended run needs durable compute and a persistent volume; autoscaling web processes may stop while inactive.

## Reproducible commands

```bash
# A deterministic, local 100,000-generation task run.
python3 scripts/run_v5_benchmarks.py \
  --task compress \
  --generations 100000 \
  --population 12 \
  --workers 4 \
  --checkpoint-interval 1000 \
  --workspace checkpoints/v5 \
  --reports-dir reports

# Resume the same durable workspace.
python3 scripts/run_v5_benchmarks.py --task compress --generations 100000 --resume

# Run the proof suite.
python3 -m pytest -q evolution/test_v5.py evolution/test_v4.py evolution/test_security_v4.py
```

`scripts/run_v5_benchmarks.py` writes both a Markdown report and a JSON snapshot. The report records only measured state from that local run. It does not extrapolate runtime, fitness, or cost to a different computer or task.

## Web workspace lifecycle

The upgraded Signal Loom observatory stores user-owned runs and append-only lifecycle events. The web form accepts a goal and an explicit generation budget; its status panel shows the resolved task, current and target generation, average fitness, cultural complexity, novelty count, and latest events. Create, start, pause, resume, cancel, and export each make a deliberate control-plane request. The generation loop itself remains local to the worker.

For production, make the worker's checkpoint directory a durable volume and run the worker on an always-on service with CPU, memory, disk, and per-user quotas. The web UI should not claim a completed task merely because a page timer advanced. It must read the persisted worker snapshot.

## Verification status

The full Signal Loom workspace was verified at desktop and mobile viewports after the lifecycle controls were added. The creation panel remains in the primary workflow: goal, finite generation budget, task routing, lifecycle state, latest checkpoint, and explicit start/pause/resume/cancel actions are visible without pretending that a browser tab performs the evolutionary work. The server-side runtime tests also assert that a generation step does not issue HTTP requests.

## References

[1] [BEAST v5 specification](../BEAST_UPDATE_v5.md) (local project specification).
