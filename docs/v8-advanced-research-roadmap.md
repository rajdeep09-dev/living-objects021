# BEAST v8 Advanced Research Roadmap

**Status:** Gated research plan; this document does **not** claim that any item below is implemented, measured, or ready for public benchmark claims.  
**Release boundary:** The v8 correction release consists only of the persisted contamination audits, exact checkpoint-fidelity proofs, pre-registered five-seed experiments, derived evidence ledgers, and the authenticated read-only observatory import. The relevant measured outcome is a retained clean-sorting negative result (0/5 eligible runs) and a bounded Manhattan-distance result (5/5 eligible runs), not a demonstrated evolved sorting algorithm.[^results]

> A roadmap item becomes a completed BEAST capability only after its stated prerequisites, implementation tests, persisted experiment artifacts, and claim-review gate have all passed. A design intention, a working UI placeholder, a runtime prototype, or an individual successful seed is not sufficient.

## 1. Current v8 Boundary

The contamination audit established that the historical sorting and string-reverse benchmarks are **retracted** because their primitive pools encoded direct solutions. The game-strategy evaluator is separately unavailable for benchmark claims because its evaluator contract is invalid. The clean-sorting replacement was executed under a declared five-seed protocol; it did not meet the discovery threshold. Manhattan distance meets the declared bounded eligibility rule, but it demonstrates a narrowly scoped composed-expression result only. The machine-derived ledger and discovery log are the sources of truth for those classifications.[^ledger] [^discovery]

| Area | Measured v8 state | Not a supported claim |
| --- | --- | --- |
| Sorting | Clean profile, baseline, checkpoints, and five 10,000-generation trials were run; 0/5 eligible successes were retained. | That BEAST evolved a sorting algorithm or reached a sorting milestone. |
| Manhattan distance | Five declared seeds met the bounded eligibility rule with fresh correctness of 1.000. | General-purpose program synthesis, autonomous science, or continued improvement beyond the stated evaluator. |
| Checkpointing | Recursive tree serialization, primitive-profile preservation, deterministic continuation, and unknown-primitive failure have tests. | Resilience of a distributed or long-running production fleet. |
| Observatory | Authenticated read-only panel imports persisted audit, ledger, and discovery artifacts and displays retractions and result boundaries. | A live reproducibility monitor, a public leaderboard of unaudited tasks, or continuous experiment execution. |

## 2. Gate Model Used for Every Future Directive

Each research item must pass the following sequence before it can be called complete. The mandatory order prevents a result from being promoted merely because it looks promising.

| Gate | Required evidence | Promotion decision |
| --- | --- | --- |
| **G0 — Design freeze** | Versioned task contract, typed primitive profile, evaluator definition, holdout partition, resource bounds, and preregistered seeds. | No execution before the manifest is committed. |
| **G1 — Adversarial contamination** | Exhaustive one-, two-, and three-operation search where expressible, random-initialization baseline distribution, and explicit exclusions. | Reject/redesign if a direct or near-direct program crosses the preregistered contamination threshold. |
| **G2 — Runtime fidelity** | Interpreter-only execution, exact checkpoint round trip, deterministic resume, and fail-closed unknown primitive behavior. | Do not launch long runs until all continuation tests pass. |
| **G3 — Bounded experiment** | All declared seeds, complete fitness curves, milestones, champions, train/holdout results, and retained failures. | A partial run cannot become a discovery. |
| **G4 — Independent reproduction** | Fresh environment run at the published revision and seed, with result comparison against declared tolerances. | Mark the record pending or failed until reproduction succeeds. |
| **G5 — Claim review** | Artifact-derived ledger entry, limitations, honest-claims registry update, and observatory visibility. | Only then may a result be described publicly as verified evidence. |

## 3. Explicitly Gated Research Directives

### 3.1 Curriculum-Guided Sorting

The current `CleanSortingCurriculum` is an experimental capability-phase profile. It is **not** evidence that a comparison-and-swap curriculum has taught an organism to sort. The completed five-seed clean-sorting experiment is a negative result and remains so until a newly preregistered task clears all gates.

| Required future increment | Prerequisites | Required proof before promotion | Current status |
| --- | --- | --- | --- |
| Two-element compare/swap task | A total, typed comparison and conditional-control design without a direct ordering primitive. | G0–G3, including exhaustive minimal-tree audit and independent hidden cases. | Not implemented. |
| Stage unlock protocol | Frozen rule that unlocks the next list length only after at least 95% on the preceding independent validation set. | Tests that prohibit manual or fitness-leakage unlocks; persisted stage-transition events. | Not implemented. |
| List lengths 3, 5, and 10 | Re-audit each stage and ensure type-safe compositional expressiveness. | Five declared seeds for the complete curriculum; all failures retained. | Not implemented. |
| Sorting milestone report | A clean task that has passed contamination, fidelity, and replication gates. | First >0.50, >0.90, >0.99, and all-case-correct records tied to their stored champion trees. | Not eligible to create. |

The desired outcome of this research is not a particular named sorting algorithm. The falsifiable question is whether the specified primitive set and evolutionary configuration can improve on its clean baseline under a staged evaluator. An outcome of 0/5 successful seeds is publishable and would remain a negative result.

### 3.2 Comparative Science and Baseline Controls

No human-versus-evolution performance comparison has been conducted. A future comparison must prevent asymmetric access to capabilities: a human baseline and GP population must receive the same documented operation set, test distribution, time/resource budget, and scoring metric.

| Metric | Definition required before execution | Current status |
| --- | --- | --- |
| Generation-to-baseline | First generation at which a reproducible champion meets the predeclared human baseline under the identical primitive profile. | Not implemented. |
| Structural taxonomy | Semantic equivalence and tree-size grouping rules defined before inspecting results. | Not implemented. |
| Efficiency comparison | Explicit interpreter cost, operation-count, and memory measures—not source-code appearance. | Not implemented. |
| Multi-seed robustness | Five predeclared seeds with a result threshold declared in advance and a full failure table. | Applied to the v8 bounded experiments; not yet applied to a comparative study. |

### 3.3 Adversarial Primitive Auditing and Certified Primitive Library

The v8 audit currently performs deterministic one-operation enumeration plus random baselines. The more demanding one-, two-, and three-operation adversarial search must be implemented only with an explosion-control contract: typed enumeration, per-task search bound, timeout recording, and an explicit `INCONCLUSIVE_SEARCH_BOUND` state. Silence caused by an unsearched space is not a passing audit.

| Future deliverable | Completion evidence | Current status |
| --- | --- | --- |
| Length 1–3 typed-tree fuzzer | Tests enumerate all programs inside its declared bound and label any truncated search. | Not implemented. |
| CI admission gate | A new evaluator cannot enter the official benchmark registry without a stored audit artifact. | Not implemented. |
| Certified primitive-set library | For each profile: formal signature, allowed/excluded operations, expressiveness limits, task audit results, random baseline distribution, and provenance. | Not implemented. |
| Task expansion | Every new domain has a task contract and passes G0–G2 before a benchmark run. | Not implemented; the current audit is limited to implemented evaluators. |

### 3.4 Cross-System Cellular-versus-GP Experiment

The cellular and GP systems currently have different objective environments; they must not be compared. A proposed shared sequence-prediction task is only a hypothesis. It requires two semantically identical evaluator adapters, one immutable test-set generator, and a declared common resource/accounting model before either system runs.

| Research question | Required controls | Promotion criterion | Current status |
| --- | --- | --- | --- |
| Which system converges faster on the shared decision rule? | Identical train/holdout cases, scoring, seed protocol, and operation or action budget. | Five-seed comparison with complete curves and no selectively reported system. | Not implemented. |
| Which system generalizes better? | Frozen out-of-distribution generator separate from selection and tuning. | Independent reproduction with preset comparison statistics. | Not implemented. |
| Which output is more interpretable? | Predeclared representation and taxonomy rubric, reviewed before result inspection. | Report labels interpretation as analysis, not an objective fitness win. | Not implemented. |

### 3.5 Reproducibility Dashboard and Continuous Verification

The v8 observatory panel is an artifact-backed transparency view, not a live verification service. A future dashboard cannot report **Verified**, **Pending**, **Failed**, or **Stale** until an automated reproduction protocol exists and the dashboard reads its persisted outcomes.

| Future capability | Required system behavior | Gating evidence | Current status |
| --- | --- | --- | --- |
| Scheduled reproduction job | Checkout declared revision, execute the published command, compare artifacts against explicit tolerances, persist provenance and outcome. | At least one end-to-end deterministic trial, failure-path test, and no in-memory-only status. | Not implemented. |
| Dashboard status model | Compute status solely from persisted reproduction records and recorded timestamps. | Contract tests for Verified, Pending, Failed, and Stale; an absent record must not render Verified. | Not implemented. |
| Alerts and investigation workflow | Route a failed reproduction to a durable investigation record, without retroactively changing evidence. | Explicit authorization, retry, and immutable-audit tests. | Not implemented. |

## 4. Long-Running Execution and Deployment Boundary

No persistent production evolution deployment is part of the v8 release. The committed experiments are bounded local executions with stored artifacts. A system that runs many generations, periodic reproductions, WebSocket streaming, queues, or worker coordination requires a separately designed operations project rather than treating the present development server as an autonomous scientific runtime.

| Execution shape | Appropriate future approach | Why it is gated | Evidence required before enabling |
| --- | --- | --- |
| Periodic, bounded deterministic reproductions that fit a request/job time budget | Managed scheduled backend job with artifact storage and database-backed job state. | Requires secret management, idempotency, run ownership, observability, and retry behavior. | Job lifecycle tests, concurrency/idempotency tests, stored output hashes, and a costed load pilot. |
| Continuous bounded worker or real-time event stream within a small single-process resource envelope | Always-on managed application process with durable state externalized from memory. | Requires a restart-safe queue, backpressure, rate limits, and durable stream sequencing. | Crash/restart tests, load profile, resource ceiling report, and authentication/authorization review. |
| Parallel or compute-heavy multi-seed campaigns, custom runtimes, or containerized workers beyond a small managed-process envelope | Dedicated persistent compute infrastructure, selected only after a measured workload profile identifies the managed-runtime limit. | Deployment is an operations and cost commitment, not an evolution milestone. | Capacity plan, job isolation, artifact retention, incident recovery drill, and independent reproduction from a clean host. |

The infrastructure choice must be made from a measured workload envelope: organisms, evaluator cost, population size, generation rate, memory, checkpoint size, concurrency, and recovery time. A dashboard, a WebSocket, or a request for “millions of generations” does not by itself establish that a persistent deployment is valid or necessary.

## 5. Open-Science and Claims-Governance Work

The JSON evidence ledger and discovery log are the current artifact-derived records. The following governance work remains separate and incomplete.

| Directive | Preconditions | Definition of done | Current status |
| --- | --- | --- | --- |
| Append-only discovery-log process | G0–G4 evidence and a frozen entry schema. | Independent replication is attached before a record gains verified status. | Protocol and bounded records exist; independent external replication workflow is not implemented. |
| Honest claims registry | Repository-wide claim inventory and explicit wording-to-artifact links. | Every public claim has a Verified, Disputed, or Retracted label plus limitations; retracted claims remain visible. | Not implemented. |
| Open-science publication packet | A single verified result with complete raw metadata and independent reproduction. | Structured methods, results, limitations, raw artifact index, and reproduction command reviewed by external readers. | Not implemented. |
| External review | Named review process that records conflicts, methods comments, and disposition. | At least two independent reviewers; no automatic promotion based solely on internal tests. | Not implemented. |

## 6. Release Discipline and Next Safe Increment

The next safe engineering increment is **not** a larger run. It is a narrowly scoped preregistration for either the two-element clean sorting subtask or the length-1-to-3 typed adversarial primitive search. The selection must be recorded before implementation, and its first output must be a pass/fail audit artifact—not a promotional chart.

Before any new result appears in a public leaderboard, README claim, discovery record, dashboard status, or external announcement, it must provide an artifact chain from G0 through G5. Until then, the v8 observatory must continue to display the current retractions, negative sorting result, and bounded Manhattan evidence exactly as classified.

[^results]: [v8 experiment results](v8-experiment-results.md)
[^ledger]: [v8 benchmark ledger](v8-benchmark-ledger.json)
[^discovery]: [v8 discovery log](v8-discovery-log.json)
