# BEAST non-LLM evolutionary proof results

## Answer to the benchmark question

> **Yes.** On the declared Manhattan-distance benchmark, a population of typed programs—initialized from seeded randomness and without an LLM—evolved programs with objectively better measured behavior than their recorded generation-zero champions. All three predeclared trials reached **1.000000** on a disjoint 128-case holdout and independently reproduced exactly from their saved artifacts.

This answer is intentionally narrow and falsifiable. It answers the question:

> Can a population of programs, without an LLM, evolve a better program than the initial population, on a task where the fitness is objectively measurable?

It does **not** establish general intelligence, arbitrary self-improvement, autonomous software engineering, or a software civilization.

## Task and execution boundary

Each program received four numeric inputs and was scored against the target function:

```text
abs(x2 - x1) + abs(y2 - y1)
```

The primitive whitelist included generic arithmetic such as subtraction, absolute value, and addition; it did **not** include a Manhattan-distance primitive. The population began as randomly constructed typed ASTs. Fitness used the bounded interpreter only. The source snippets recorded in the artifacts are audits; they were never used for scoring or executed by the benchmark.

| Boundary | Measured status |
|---|---|
| LLM calls | `0` |
| Network calls | `0` |
| Generated source executed | `false` |
| Direct target primitive present | `false` |
| Population per trial | `128` |
| Generations per trial | `300` |
| Audit cases per suite | `128` |
| Holdout used for selection | `false` |
| Promotion rule | Structural change, train improvement, and holdout objective delta ≥ `0.10` |

The primary objective was derived from actual program output: one minus mean clipped absolute numeric error divided by 300. Exact-output correctness is reported separately. This creates a graded but fully objective selection signal; it does not inject a desired program or a simulated score.

## Predeclared fixed-seed results

The seed set was fixed as `20260814`, `20260815`, and `20260816` before execution. No seed was removed after observing results.

| Seed | Baseline holdout objective | Final holdout objective | Objective delta | Baseline exact correctness | Final exact correctness | Promotion | Independent rerun |
|---:|---:|---:|---:|---:|---:|---|---|
| 20260814 | 0.778255 | 1.000000 | +0.221745 | 0.000000 | 1.000000 | accepted | exact match |
| 20260815 | 0.768420 | 1.000000 | +0.231580 | 0.000000 | 1.000000 | accepted | exact match |
| 20260816 | 0.835938 | 1.000000 | +0.164063 | 0.007812 | 1.000000 | accepted | exact match |

Every promoted champion passed all **128/128** held-out cases. The three independent verifier invocations each found an empty mismatch list across configuration, initial population, champion AST, complete generation history, train audit, holdout audit, and promotion decision.

## What the population actually found

The discovered ASTs differ across trials. Their semantics are equivalent to the target, but their structures expose genuine search outcomes rather than a single inserted template.

| Seed | Champion structure expressed as mathematics | Why it solves the task |
|---:|---|---|
| 20260814 | `max(|a − b|, |a + b|)`, where `a = y1 − y2`, `b = x2 − x1` | This identity equals `|a| + |b|` for real inputs. |
| 20260815 | `|−|a| − |b||` | The outer absolute value yields `|a| + |b|`. |
| 20260816 | `|x2 − x1| + |y1 − y2|` | Direct composition of the required operation. |

The first two solutions are useful evidence that selection did not merely return one fixed source string. They remain bounded expressions assembled from the same generic primitive set. They are **not** evidence that the system has an understanding of geometry or algebra beyond the behavior measured by this task.

## Artifacts and reproduction

The release keeps every raw trial, a detached SHA-256 digest per trial, and an aggregate summary under [`docs/artifacts/non-llm-proof-release/`](artifacts/non-llm-proof-release/). The manifest includes the full generation-zero population, every generation statistic, immutable configuration, audit-suite seeds, initial and final champions, and the promotion decision.

Run the declared trial set:

```bash
python3 scripts/run_non_llm_proof_trials.py --output-dir docs/artifacts/non-llm-proof-release
```

Independently verify each saved run:

```bash
python3 scripts/run_non_llm_proof.py --verify docs/artifacts/non-llm-proof-release/trial-20260814.json
python3 scripts/run_non_llm_proof.py --verify docs/artifacts/non-llm-proof-release/trial-20260815.json
python3 scripts/run_non_llm_proof.py --verify docs/artifacts/non-llm-proof-release/trial-20260816.json
```

The verifier returns a nonzero status if any deterministic proof field differs. A failed run remains a failed run: the runner preserves all predeclared trial artifacts and reports `all_trials_promoted: false` if any seed does not meet the promotion rule.

## What would falsify this result

The claim fails if any of the following occurs:

| Falsification condition | Required response |
|---|---|
| An artifact rerun produces a mismatch | Report the mismatch and withhold the reproducibility claim. |
| A final holdout delta is below `0.10` | Mark that trial unpromoted; do not replace it with another seed. |
| A direct target primitive, LLM call, network request, or source execution path is introduced | The execution-boundary claim no longer holds. |
| The holdout seed participates in selection | The independent-generalization claim no longer holds. |
| A different evaluator or tolerance is used | Treat it as a new benchmark, not a continuation of this result. |

## Limits

This is a real evolutionary program-search result, but a bounded one. The target is a compact symbolic regression task, the search language and evaluator are engineered by humans, and the holdout distribution is generated from known rules. The benchmark therefore demonstrates **selection-driven improvement of executable programs from a random initial population under objective measurement**. It does not prove unbounded novelty, reasoning in the human sense, or that the same method will reliably solve arbitrary software tasks.
