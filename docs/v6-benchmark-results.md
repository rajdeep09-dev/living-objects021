# BEAST v6 benchmark results

> These are bounded local genetic-programming measurements. The system interprets typed ASTs; it does not execute the source exports, call network services per generation, trade in markets, or claim general intelligence.

Command: `python scripts/run_v6_benchmarks.py --tasks absolute-difference --generations 1000 --population-size 96 --seed 20260814`

| Task | Generations | Train baseline | Train champion | Held-out correctness | Program nodes | Runtime |
|---|---:|---:|---:|---:|---:|---:|
| absolute-difference | 1000 | 0.050 | 1.000 | 1.000 (20/20) | 4 | 40.835s |

## Interpretation

A score is task-specific finite-suite correctness, not a claim that a discovered program is universally correct. Held-out cases use a deterministic seed distinct from the generation fitness seed. The source column in the JSON artifact is an audit export only; all scoring occurs through the bounded AST interpreter.

## Reproduction and limits

Checkpoints are written to `/tmp/beast-v6-measured-1000` and can be resumed only through the validated GP checkpoint API. This command has no network client, no subprocess execution path, no live market connection, and no production write action. Increase generations only within the documented 1,000,000-generation controller cap and a resource-bounded persistent worker.
