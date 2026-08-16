# BEAST v8 Experiment Pre-registration

**Registration ID:** `BEAST-V8-PREREG-20260816-A`  
**Registration date:** 2026-08-16  
**Status:** Registered before execution; results pending.

## Research questions

The clean sorting experiment asks whether a typed-AST population can improve on a staged, contamination-audited sorting objective when direct sorting/ranking primitives are unavailable. The Manhattan experiment asks whether five independent 10,000-generation extensions maintain or diversify correct compositions under the existing generic arithmetic evaluator.

## Fixed configurations

| Experiment | Seeds | Generations | Population | Operators | Evaluation and promotion rule |
|---|---|---:|---:|---|---|
| `clean-sorting` | 20260814–20260818 | 10,000 | 50 | depth 8; mutation 0.12; crossover 0.85; elitism 5 | `clean-sorting-v1`; fresh 1,000-case correctness ≥0.95; final tree absent from the initial population. |
| `manhattan-distance` | 20260814–20260818 | 10,000 | 128 | depth 7; mutation 0.22; crossover 0.85; elitism 4 | Fresh 1,000-case correctness ≥0.95; final tree absent from the initial population. |

The declared seeds are exactly `20260814`, `20260815`, `20260816`, `20260817`, and `20260818`. No replacement seed may be substituted for a failed run. At least four of the five preregistered trials must meet the listed promotion rule before an experiment can be eligible for the discovery log.

## Sorting curriculum and contamination boundary

Sorting stages use fixed list lengths 2, 3, 5, and 10. The next stage unlocks only after a separate evaluator-owned 100-case measurement reaches at least 95% correctness. The allowed controls are `head`, `tail`, `cons`, `length`, generic arithmetic/comparison, `choose_list`, and later `concat_lists`. `sort1`, `sorted`, `reverse1`, `map_sq`, `filter_pos`, `unique`, and `sum1` are prohibited. The phase-0/500-organism baseline and one-operation audit are in `docs/v8-clean-sorting-baseline.json`.

## Reporting protocol

Each trial writes one checkpoint, complete per-generation history, a champion audit export every 1,000 generations, first perfect training generation if it occurs, curriculum gate evidence for sorting, and a final fresh 1,000-case evaluation. Generated source remains an audit artifact; all selection and evaluation use the typed AST interpreter. Runs below threshold, plateaued curricula, and all failed seeds are retained in the summary.

This registration does not predeclare success. It only predeclares how success and failure will be measured.
