# BEAST v6 architecture: bounded genetic programming

BEAST v6 is a **local genetic-programming research system**. It evolves a population of typed arithmetic abstract syntax trees (ASTs) against explicit test cases. It is not a general autonomous agent, an arbitrary-code execution framework, or a market-trading system.

## Execution model

The engine represents each candidate as structured data. The interpreter evaluates only registered node kinds with supplied numeric inputs. Mutation and crossover operate over the tree representation, then validation checks structural limits before a program can be scored or exported. The exported source representation is explanatory evidence for an operator; the main process never executes that text.

| Component | Responsibility | Boundary |
|---|---|---|
| `evolution/gp_engine.py` | Typed AST representation, interpreter, mutation, crossover, and audit-source rendering | No `exec`, imports, filesystem, subprocess, or network primitive |
| `evolution/fitness.py` | Finite correctness suites, repeated-trial summaries, held-out scoring, and fitness metadata | A score applies only to the named task cases |
| `evolution/gp_population.py` | Deterministic selection, breeding, diversity accounting, and checkpointable population state | Bounded population, depth, node count, and generation budget |
| `evolution/program_validation.py` | AST and audit-source validation | Rejects unsupported syntax, excessive complexity, and unsafe constructs |
| `evolution/safe_improvement.py` | Holdout-gated promotion decisions | Requires a measurable candidate gain rather than an asserted improvement |
| `evolution/gp_control.py` | Start, pause, resume, cancel, and atomic checkpoint lifecycle | Local checkpoints only; no per-generation remote control call |

## Fitness contract

Fitness is calculated from the fraction of declared test cases for which an interpreted candidate produces the expected value. The engine records train and holdout correctness separately. The holdout set uses a different deterministic seed from the train set. A candidate that scores well on the declared suite has demonstrated finite-suite performance; it has not proved universal correctness.

> **Release measurement.** The `absolute-difference` benchmark improved from 0.050 train correctness to 1.000 train and 1.000 on 20 held-out cases using a four-node program in a bounded 1,000-generation run. This result is reproducible for the documented seed and does not establish general intelligence or performance on untested input distributions.

## Long-run execution

The controller permits finite runs up to one million generations, subject to the configured population, node, depth, time, and storage limits. A web request starts or controls a worker, but the generation loop performs no request per generation. Durable checkpoints make a paused or interrupted run resumable after validation.

| Control | Purpose |
|---|---|
| Generation cap | Prevents accidental unbounded computation |
| Population and worker caps | Limits CPU and memory pressure |
| AST depth and node caps | Limits program bloat and interpreter work |
| Checkpoint manifest | Preserves state and random progression for bounded resume |
| Holdout gate | Prevents replacing a baseline with a candidate that lacks measured improvement |

## Web observatory

The full-stack Signal Loom workspace lets an authenticated user create a run from a short goal description, select the available local task profile, choose a finite budget, and inspect state later. The goal description is stored as user metadata. It is **not** compiled or treated as arbitrary program instructions. The UI exposes only status polling and lifecycle controls; the runtime interprets AST data locally and displays source as an audit string.

## Reproduction

```bash
python3 scripts/run_v6_benchmarks.py \
  --tasks absolute-difference --generations 1000 --population-size 96 --seed 20260814

python3 -m pytest -q \
  evolution/test_gp_engine.py evolution/test_fitness.py evolution/test_gp_population.py \
  evolution/test_gp_safety.py evolution/test_v6_benchmarks.py
```

The generated report is written to `docs/v6-benchmark-results.md`. Use an always-on resource-bounded worker for long retained runs. Do not infer that an autoscaled web process will keep evolving after it becomes idle.
