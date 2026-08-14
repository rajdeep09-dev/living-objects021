# BEAST v7 Operational Roadmap and Claim Boundary

## Purpose

This document records the engineering state after the v7 foundation repairs and the first bounded sorting execution. It is deliberately an **operational plan**, not a release announcement. A completed unit test, a local bounded run, a deployed web service, and a persistent public system are materially different claims; each row below states which level has actually been reached.

The authoritative implementation requirements are in [`BEAST_UPDATE_v7.md`](../BEAST_UPDATE_v7.md). This document translates those requirements into executable gates without replacing them.

## Measured work completed in this repository

| Evidence area | Completed, verifiable scope | Source artifact |
|---|---|---|
| Eight v6 foundation defects | Candidate survivor selection, bloat brake, seed rotation, evaluator-owned market scoring, cellular capabilities, real GP events, Node equivalence, and full-population resume each have focused regressions. | [`v7-foundation-audit.md`](v7-foundation-audit.md) |
| Cellular structural evolution | A 30-generation bounded run produced measured repertoire mutation and disjoint holdout evidence. | [`cellular-v7-results.md`](cellular-v7-results.md) |
| Real GP streaming | Ten completed interpreter-only sorting steps were captured from the real broadcaster, with one actual champion-code message per generation. | [`../reports/v7_live_gp_stream.json`](../reports/v7_live_gp_stream.json) |
| Bounded sorting execution | A 1,000-generation run using the v7 sorting configuration produced checkpoints, a complete curve, milestones, and an independent fresh-suite measurement. | [`../reports/sorting_marathon/run_result.json`](../reports/sorting_marathon/run_result.json) |
| Authenticated observatory evidence | The web project imports the persisted bounded-marathon and real-stream artifacts into a tested read-only evidence panel. | `living-objects-platform-ui/server/evidence/` and `V7GpEvidencePanel.test.tsx` |

> The 1,000-generation artifact has `claimed_public_100k_marathon_completed: false`. It is not the 100,000-generation public marathon, has no `FINAL_REPORT.md`, and must never be described as a completed public marathon.

## Directive-by-directive execution status

| v7 directive | Current state | Required next implementation | Measurable acceptance gate | Claim status today |
|---|---|---|---|---|
| 1. 100,000-generation marathon | Runner, resume artifacts, a 1,000-generation measured bounded execution, and checkpoint tests exist. | Execute the declared 100,000-generation configuration in a persistent worker; preserve every 10,000-generation milestone. | `FINAL_REPORT.md`; ten milestone reports; 1,000 fresh held-out cases; reproducibility rerun by an independent operator. | **Not completed.** |
| 2. Live public observatory | Authenticated artifact evidence and live API event tests exist. | Build the six real panels against live sources; make source failure visible; use a public-read deployment only after the worker source is live. | Browser integration test receives live events; each panel validates a non-synthetic backend source; outage path visibly says “Connection lost — reconnecting.” | **Not public or fully live.** |
| 3. Self-tuning deployment | `SelfImprovingEvolution` adjusts bounded scalar parameters in a small engine scope. | Implement a versioned deployment genome, offline shadow arena, promotion policy, and rollback record. | A/B arena uses equal seeds and reports fitness-per-second; promotion only when a candidate beats baseline with safety bounds enforced. | **Partial prerequisite only; no self-tuning deployment.** |
| 4. Federation protocol | Cultural-memory compatibility surfaces exist, but no signed v7 federation flow. | Add key management, signed records, local re-evaluation, quarantine, and opt-out. | End-to-end test rejects an altered signature and a locally failing record; accepts only a locally reverified record. | **Not implemented.** |
| 5. Twenty task domains | Existing bounded evaluators cover a smaller set of task types. | Specify and implement each missing domain independently, with fixed capability limits and train/holdout separation. | Per-domain evaluator tests, documented baseline, and a fresh-holdout run; financial domain must remain a simulation-only safety-controlled benchmark. | **Not implemented.** |
| 6. Civilizational Memory Bank | Checkpoints and related archive primitives exist; no public immutable, signed v7 archive claim is made. | Define append-only schema and trigger, hash canonical records, archive evaluator version, and publish a public hash mechanism after review. | Attempted public write/delete is denied; a verifier recomputes a known record hash; archive query returns only verified records. | **Not active.** |
| 7. Genome visualiser | Earlier observatory work includes lineage visualisation, not the required live D3 mutation/crossover visualiser. | Serialize event-level mutation/crossover provenance and render it from live source data. | Component test maps tree node types correctly; integration stream updates the selected organism without synthetic animation data. | **Not implemented at v7 scope.** |
| 8. Adversarial task generator | No declared task-generator population is active. | Implement a bounded task parameter genome and prove solvability before promotion. | Independent solver establishes achievable fitness above 0.50; generator changes only allowlisted parameters; adversarial changes improve robustness on a fresh suite. | **Not implemented.** |
| 9. Explanation engine | The AST remains inspectable but lacks the required verified pattern describer. | Add a deterministic pattern library with explicit “unrecognised combination” fallback. | Golden tests prove descriptions map to exact AST patterns; unknown structure never receives a fabricated semantic label. | **Not implemented.** |
| 10. Educational tour | No five-step public tour has been shipped. | Build the tour only after live panels and a sandboxed playground exist. | Accessibility and interaction tests cover all five steps; supervised usability evidence from ten non-expert participants. | **Not implemented.** |
| 11. Benchmark leaderboard | The bounded marathon has a curve but no six-domain human-baseline leaderboard. | Implement fixed baselines and common benchmark harnesses. | 1,000 fresh cases per listed domain; correctness, wall-time, and code bytes emitted from the same run manifest. | **Not implemented.** |
| 12. One-million-user hardening | Docker, Kubernetes, Redis-compatible, metrics, and control-plane artifacts exist. | Split the public gateway, evolution worker, sandbox-worker, and immutable archive processes; load-test the deployed topology. | Documented load-test evidence at each selected threshold, failure isolation tests, and persistent checkpoint recovery. | **Not deployed or load-tested at the stated scale.** |

## Persistent-marathon launch plan

The current sandbox is intentionally unsuitable as the evidence source for a 24/7 public run: it may hibernate and cannot establish a durable process guarantee. A truthful launch therefore requires a persistent process and durable checkpoint storage.

| Stage | Workload | Required durability and evidence | Promotion condition |
|---|---|---|---|
| 0. Reproduce locally | Re-run the committed 1,000-generation bounded command. | Capture the commit hash, seed, result JSON, fresh-suite score, and environment version. | A second operator obtains a result in the declared expected range. |
| 1. Persistent pilot | A continuous 10,000-generation sorting worker. | Atomic checkpoint after at most 1,000 generations; restart drill resumes the exact population and preserves event order. | Restart drill succeeds and a 10,000-generation milestone is independently inspected. |
| 2. Marathon | The guide configuration through generation 100,000. | Every 10,000-generation report, immutable run manifest, full checkpoint lineage, and a 1,000-case fresh suite at completion. | Independent reproduction review and all v7 quality gates pass. |
| 3. Public worker/gateway | One real task worker plus a separately deployable broadcast gateway. | Redis or equivalent ephemeral fan-out, durable archive/checkpoints, rate-limited sandbox lane, and outage behavior. | Security review, load test at an explicitly stated target, and no fallback synthetic panel state. |

For a stateful single-process pilot, a persistent managed service is suitable only if its single-process capacity is measured against the workload. A multi-process, multi-domain, or high-concurrency deployment requires the separate worker/gateway/archive topology described in Directive 12. The existing scaling design remains a roadmap, not evidence of one million active organisms; see [`scale-to-1m-organisms.md`](scale-to-1m-organisms.md).

## Release gates for the next implementation slice

The next slice should be the persistent **10,000-generation pilot**, not a public claim. It may start only when its owner provides a persistent execution target and durable storage configuration. The code change must include a run manifest, restart test, atomic checkpoint test, and a bounded event fan-out test. It must then pass the following release gates.

| Gate | Evidence required | Failure response |
|---|---|---|
| Correctness | Full suite green plus pilot-specific resume, duplicate-event, and seed-rotation regressions. | Block the run and repair before relaunch. |
| Reproducibility | Exact command, commit, seed, environment version, result hash, and independently run verification. | Keep the report unpublished. |
| Security | Endpoint threat review for authentication, input validation, rate limits, and sandbox separation. | Disable the public endpoint or worker control route. |
| Performance | Generations/second, peak memory, checkpoint duration, and event lag measured at generation 1,000 and 10,000. | Do not increase target generation or concurrency. |
| Honesty | UI and documents label the run as pilot, in-progress, or completed according to its actual terminal artifact. | Remove or correct the misleading surface immediately. |

## Research-paradigm queue

The ten paradigms in Part E are **research programs**, not features implied by the current foundation. The first safe research sequence is: deterministic Explanation Engine (Directive 9 dependency), a fixed-baseline Pareto evaluation harness, adversarial task generation restricted to allowlisted parameter spaces, and only then cross-domain transfer. Federation, human injection, public competitions, symbolic-regression-as-a-service, and theorem-prover work require separately approved task specifications and threat models.

No research result should be named a discovery until it has an objective evaluator, disjoint holdout data, an archived seed/configuration, and an independent rerun.
