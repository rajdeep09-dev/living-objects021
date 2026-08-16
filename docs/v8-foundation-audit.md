# BEAST v8 Foundation Audit — Scientific Claim Correction

## Audit method and boundary

This document audits the **current repository state** against `BEAST_UPDATE_v8.md`. It distinguishes source-verified facts from results that still require a fresh measurement. A guide statement is not treated as evidence merely because it appears in the guide.

| Audit input | Current verified source | Consequence |
|---|---|---|
| Direct sorting primitive | `LIST_PRIMITIVES` contains `sort1`, implemented as `sorted(list(values))`. | The prior sorting marathon is **contaminated** and is not evidence of sorting-algorithm discovery. |
| Prior bounded run | `reports/sorting_marathon/run_result.json` records a 1,000-generation execution and explicitly says the 100k marathon is false. | The report must additionally be labelled **retracted as an algorithm-discovery benchmark** because its generation-zero solution space contained `sort1`. Its operational/runtime evidence remains usable, but not its discovery claim. |
| Typed engine runtime | `GPNode.evaluate()` interprets typed trees; source export is audit text. | The interpreter-only boundary remains intact. |
| Checkpoint payload | `GPNode.to_dict()` recursively stores primitive, terminal fields, type, and children; `GPGenome.from_dict()` and `GPPopulation.from_checkpoint_payload()` restore that payload. | The v8 claim that active checkpoints restore by source parsing is **stale for this branch**. Stronger structural and deterministic-trajectory tests remain required before long-run use. |
| Cellular action capabilities | `CellGenome.action_capabilities` and world/tissue checks were implemented in v7. | The v8 appendix statement that evolvable cellular actions are absent is **stale for this branch**. |
| Test counts | The v7 final full-repository regression was 435 passed. | v8's “259 pass / 3 skipped” is environment- and revision-specific, not a current release fact. |

## Implemented-task scope

The repository currently implements **ten** evaluator classes: sorting, primality, Fibonacci, string reversal, maximum subarray, absolute difference, Manhattan distance, compression, pathfinding, and game strategy. It does not yet have the guide’s promised 20-domain registry, and the “14 planned” domains have no evaluator implementation to audit. They must be marked **not implemented**, not assigned a synthetic baseline.

## Mandate decision matrix

| v8 mandate | Current factual state | Repair gate |
|---|---|---|
| V8-01 clean sorting | **Open; contamination confirmed.** `sort1` is a one-node direct solution. | Replace the benchmark with a separate clean evaluator/primitive profile, prove no direct primitive, and measure the random-population baseline before evolution. |
| V8-02 task contamination audit | **Open.** No general task registry or baseline/audit artifact exists. | Implement one deterministic audit harness for the ten actual evaluators, and list absent planned domains separately. |
| V8-03 clean sorting 10k | **Blocked.** | Start only after V8-01 and exact checkpoint proof; predeclare five seeds, success criteria, and artifacts. |
| V8-04 primitive standard | **Open.** | Publish exclusions, measured baseline, direct/near-direct enumeration, evaluator version, and known representational limits per profile. |
| V8-05 Manhattan 10k | **Blocked on preregistration and exact resume proof.** | Declare five seeds and acceptance thresholds; run a bounded pilot first, then only report measured terminal results. |
| V8-06 exact tree serialization | **Implementation present; proof incomplete.** | Test a nested tree’s recursive payload bit-for-bit after load and compare an uninterrupted versus resumed population’s next ten generation statistics and trees. |
| V8-07 contamination observatory | **Open.** | Import committed audit artifacts; render explicit pass/fail/retracted labels through an authenticated read-only contract. |
| V8-08 adjusted leaderboard | **Open.** No full leaderboard exists. | Create only after audit data; show retracted contaminated rows and keep them out of any official ranking. |

## Immediate scientific corrections

> The previous sorting run demonstrated that the bounded interpreter, event capture, checkpoint artifact path, and reporting path executed. It **did not** demonstrate evolutionary discovery of a sorting algorithm, because the allowed primitive set included a direct complete sort operation.

The valid v6/v7 Manhattan evidence remains a narrower compositional claim: no `manhattan_distance` primitive is registered, while the task allows generic arithmetic components. Its 10,000-generation extension has not been run and cannot be claimed.

## Measured first-pass audit result

`python3 scripts/run_v8_contamination_audit.py --output docs/v8-contamination-audit.json --baseline-population-size 500` completed with the current 36-primitive default profile, three evaluator-owned direct-check suites of 50 cases each, and an initialized 500-organism baseline at seed 1729. The complete machine-readable result is [`v8-contamination-audit.json`](v8-contamination-audit.json); the generated tabular report is [`v8-contamination-audit.md`](v8-contamination-audit.md).

| Task | Classification | Direct finding / contract result | Baseline best | Perfect initial organisms |
|---|---|---|---:|---:|
| Sorting | **Retracted** | `sort1(x)` and `sort1(input)` pass all audit suites. | 1.000000 | 8/500 |
| String reverse | **Retracted** | `reverse1(x)` and `reverse1(input)` pass all audit suites. | 1.000000 | 25/500 |
| Game strategy | **Invalid evaluator contract** | Population uses `batch_evaluate`, while its substantive logic is in an `evaluate` override. | 0.000000 | 0/500 |
| Prime | No one-operation match observed | Enumeration is negative at one operation only. | 0.750000 | 0/500 |
| Fibonacci | No one-operation match observed | Enumeration is negative at one operation only. | 0.150000 | 0/500 |
| Maximum subarray | No one-operation match observed | Enumeration is negative at one operation only. | 0.450000 | 0/500 |
| Absolute difference | No one-operation match observed | Enumeration is negative at one operation only. | 0.050000 | 0/500 |
| Manhattan distance | No one-operation match observed | Enumeration is negative at one operation only. | 0.838667 | 0/500 |
| Compression | No one-operation match observed | Enumeration is negative at one operation only. | 0.150000 | 0/500 |
| Pathfinding | No one-operation match observed | Enumeration is negative at one operation only. | 0.600000 | 0/500 |

> “No one-operation match observed” is intentionally narrower than “uncontaminated.” It records what the enumerator tested; near-direct compositions and unsuitable task definitions require separate review before any claim of algorithm discovery.

## Clean sorting profile decision

The historical default sorting evaluator remains preserved and retracted. A new `clean-sorting-v1` profile now separates structural list construction, ordering controls, and composition across generation boundaries 0, 200, and 1,000. Its manifest excludes `sort1`, `map_sq`, `filter_pos`, `unique`, `reverse1`, and `sum1`; its added `choose_list` and `concat_lists` operators are typed generic controls rather than task-complete sorting operators.

The preregistered 500-organism audit at seed 2026 produced **no one-operation direct match**, no perfect program, best initial fitness **0.050000**, mean initial fitness **0.009700**, and median initial fitness **0.000000**. The direct-solution and baseline gates therefore pass for the stated profile. The machine-readable artifact is [`v8-clean-sorting-baseline.json`](v8-clean-sorting-baseline.json). This establishes eligibility for a future preregistered experiment; it is not itself an algorithm-discovery result.

## Exact checkpoint-fidelity decision

Checkpoint schema version 2 now preserves the active primitive-profile names, recursive typed tree payload, full genome metadata, full `FitnessResult`, generation history, hall of fame, and random-number-generator state. A custom clean-sorting tree containing both `choose_list` and `concat_lists` round-trips bit-for-bit under the declared profile; an unavailable primitive is rejected rather than silently replaced by a fallback terminal. The checkpoint-resume proof then runs an uninterrupted and restored clean-sorting population through ten further generations and requires identical `GenerationStats`, organism identities, parentage, genome payloads, and history at every step.

`pytest -q evolution/test_checkpoint_fidelity.py evolution/test_clean_sorting.py evolution/test_gp_population.py` completed with **16 passed**. Legacy v1 checkpoints remain readable through explicit evaluator refresh for compatibility, but their missing saved `FitnessResult` data means they are excluded from v8 exact-resume claims.

## Dependency order

1. Construct the measurement and adversarial enumeration harness.
2. Audit every evaluator that actually exists; publish results including failures.
3. Introduce a separate clean sorting profile rather than silently changing historical v7 artifacts.
4. Strengthen exact checkpoint tests.
5. Pre-register seeds and success rules before any clean long-running experiment.
6. Only then expose contamination status and valid results in the observatory.

The directory `reports/sorting_marathon/` remains preserved as a historical operational artifact. Any new benchmark table or observatory surface must label it **Retracted — direct sort primitive available** until an uncontaminated profile is independently measured.
