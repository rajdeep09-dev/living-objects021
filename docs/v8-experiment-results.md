# BEAST v8 Pre-Registered Experiment Results

## Protocol

Both experiments use pre-registration `BEAST-V8-PREREG-20260816-A`, five declared seeds (`20260814`–`20260818`), 10,000 generations per seed, typed-AST interpreter evaluation, no LLM calls in the generation loop, no network calls in the generation loop, and persisted milestones at each 1,000 generations. A result is eligible only when its final program was absent from the generation-zero population, achieved perfect training fitness, and passed the evaluator-owned fresh suite. The pre-registered multi-seed discovery threshold is **at least four eligible successes of five**.

The complete records remain the machine-readable summaries and per-seed `trial.json`, milestone, and checkpoint files under [`../reports/v8/`](../reports/v8/).

## Clean sorting — completed failure result

The clean sorting profile excludes the historical direct sort primitive and passed its random-baseline eligibility gate before this experiment. All five 10,000-generation trials completed, but none met the promotion criteria.

| Seed | First perfect training generation | Fresh correctness | Promotion eligible |
|---:|---:|---:|---|
| 20260814 | — | 0.512 | No |
| 20260815 | — | 0.513 | No |
| 20260816 | — | 0.495 | No |
| 20260817 | — | 0.511 | No |
| 20260818 | — | 0.499 | No |

The aggregate reports **0/5 eligible successes**, `discovery_log_eligible: false`, and no missing declared seed. This is a genuine negative result for the stated clean profile, population, operators, generation budget, and mastery gate. It does not demonstrate sorting-algorithm discovery, and it does not make the historical contaminated run valid.

Source of truth: [`../reports/v8/clean-sorting/summary.json`](../reports/v8/clean-sorting/summary.json).

## Manhattan distance — completed five-seed result

The Manhattan evaluator has no registered one-operation `manhattan_distance` primitive; the result remains a compositional-expression claim, not a novel general algorithm claim. All five 10,000-generation trials completed and met the declared eligibility criteria.

| Seed | First perfect training generation | Fresh correctness | Promotion eligible |
|---:|---:|---:|---|
| 20260814 | 38 | 1.000 | Yes |
| 20260815 | 35 | 1.000 | Yes |
| 20260816 | 11 | 1.000 | Yes |
| 20260817 | 76 | 1.000 | Yes |
| 20260818 | 61 | 1.000 | Yes |

The aggregate reports **5/5 eligible successes**, `discovery_log_eligible: true`, and no missing declared seed. Each terminal record states `initial_tree_contains_final: false`; source/lineage records remain archived in the individual trial artifacts.

Source of truth: [`../reports/v8/manhattan-distance/summary.json`](../reports/v8/manhattan-distance/summary.json).

## Claim boundary

> V8 shows that this bounded interpreter-only GP implementation repeatedly synthesised a program that solves the declared Manhattan-distance evaluator and independent fresh suites under five predeclared seeds. It does not establish open-ended general intelligence, unrestricted program synthesis, a general sorting discovery capability, or any unmeasured deployment claim.

The clean-sorting negative result is retained alongside the Manhattan result rather than filtered out. The historical v7 sorting artifact remains **Retracted — direct sort primitive available**.
