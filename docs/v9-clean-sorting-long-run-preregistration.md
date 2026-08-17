# BEAST v9 Clean-Sorting Curriculum Campaign: Preregistration

**Identifier:** `BEAST-V9-PREREG-20260817-A`
**Status:** **Not launched.** This document freezes the intended protocol; it does not report a result.

## Question and baseline

Can the v9 five-stage, contamination-free curriculum produce general clean-sorting programs under a bounded typed-AST interpreter? The retained v8 baseline is **0/5 eligible successes** after 10,000 generations, with fresh correctness from **0.495 to 0.513**. That negative result remains the baseline and will not be overwritten.

## Frozen campaign configuration

| Field | Declared value |
|---|---:|
| Seeds | `20260901`, `20260902`, `20260903`, `20260904`, `20260905` |
| Target per seed | 100,000 generations |
| Population | 50 |
| Maximum depth | 8 |
| Mutation / crossover / elitism | 0.12 / 0.85 / 5 |
| Curriculum probe cadence | Every 100 generations on 100 evaluator-owned cases |
| Durable checkpoint / milestone cadence | Every 10,000 generations |
| Final fresh suite | 1,000 general-stage cases per seed |
| Runtime | Typed AST interpreter only; no LLM calls, network calls, or generated-source execution |

The five stages, primitive exclusions, culture archive, exact evaluator-state restore, and population-level advancement rule are defined by `evolution/v9_sorting_curriculum.py`. A transition requires at least **95%** of the population at **95%** individual correctness and a **0.90** population mean on the fresh stage suite. A stage champion is archived only after this test and is re-scored in the receiving stage before selection.

## Success rule and retained outcomes

A completed seed is an eligible campaign result only at 100,000 generations. The prespecified exploratory summary is the count of completed seeds with general-stage fresh correctness at or above **0.85**. No result is filtered: incomplete runs, failed resumes, no-stage-advance outcomes, and low-correctness results remain in the final report. This threshold is an analysis rule, **not** a prediction or a success claim.

## Launch and recovery command

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
python scripts/run_v9_clean_sorting_campaign.py \
  --output-dir reports/v9/clean-sorting-curriculum
```

An interrupted seed resumes only when its checkpoint, metadata, and complete fitness history exist and the frozen configuration matches:

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
python scripts/run_v9_clean_sorting_campaign.py \
  --output-dir reports/v9/clean-sorting-curriculum --seed 20260901 --resume
```

Any shorter invocation is written as `bounded_execution_completed` and is **not** eligible for the declared campaign analysis.

## Required artifacts and reporting

Each seed produces immutable-style JSON artifacts for metadata, exact checkpoint, history, curriculum events, cultural archive, 10,000-generation milestones, and `trial.json`. A post-run aggregator must state the exact completed generation count, general fresh correctness, all stage events, SHA/version information, elapsed time, and any recovery event. The report must retain v8’s retractions and its clean-sorting negative result.
