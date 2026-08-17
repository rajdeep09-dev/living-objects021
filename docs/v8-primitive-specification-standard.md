# BEAST v8 Primitive-Specification Standard

## Objective

A task is not eligible for an algorithm-discovery claim merely because its evaluator runs. Its primitive profile must be specified, enumerated, baseline-measured, and adversarially reviewed before a population is evolved. This standard applies to every future evaluator profile.

| Required field | Requirement |
|---|---|
| Profile identity | Immutable name and version; changes create a new profile rather than modifying historical evidence. |
| Type signatures | Every terminal and primitive declares input/output types and bounded semantics. |
| Exclusions | List direct, near-direct, library-wrapper, and task-name-equivalent operations explicitly. |
| Baseline | Record a seeded random population’s size, mean, median, best score, and perfect-program count. |
| Enumeration | Test every one-operation primitive/terminal composition against at least three evaluator-owned suites; retain tested candidates and matches. |
| Near-direct review | Document selected two- and three-operation candidates capable of solving the task through a known identity or wrapper. |
| Evaluator version | Hash or version the test generator, scoring function, capability profile, and train/holdout seed rules. |
| Claim boundary | State whether a result is direct-function, compositional expression, algorithmic procedure, or negative/invalid. |

## Current profile classifications

| Profile/task | Status | Reason |
|---|---|---|
| Historical default sorting | **Retracted** | `sort1` is directly registered and initial random populations contain perfect programs. |
| Historical string reverse | **Retracted** | `reverse1` is directly registered and initial random populations contain perfect programs. |
| `clean-sorting-v1` | Baseline eligible, experiment negative | Direct/initial baseline gates passed; five measured trials produced 0/5 eligible successes. |
| Default Manhattan distance | Compositional result only | No one-operation match observed; five measured trials produced an evaluator-specific arithmetic expression. |

The generated [`v8-benchmark-ledger.json`](v8-benchmark-ledger.json) is the machine-readable status record. It never converts a “no one-operation match” observation into an unconditional clean-benchmark claim.
