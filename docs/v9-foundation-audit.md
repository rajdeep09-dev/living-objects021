# BEAST v9 Foundation Audit

**Audit date:** 2026-08-17
**Baseline engine revision:** `e2ea116` (BEAST v8 evidence release)
**Observed test baseline:** 447 tests collected with `APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest --collect-only -q` on 2026-08-17.
**Scope:** This audit translates `BEAST_UPDATE_v9.md` into implementation work and scientific gates. It does not relabel proposed, unmeasured, or externally controlled work as complete.

> **Release rule.** The v8 retractions and negative result are immutable evidence boundaries. No v9 feature, interface, document, or test may relabel the contaminated v7 sorting marathon as discovery or conceal the clean-sorting 0/5 result.

## Verified v8 baseline

| Result | Measured status | Boundary | Source of truth |
|---|---|---|---|
| Manhattan distance | **5/5 eligible five-seed result** at up to 10,000 generations; reported fresh correctness is 1.000 for every declared seed | A bounded typed-AST, interpreter-only, evaluator-specific synthesis result; not a claim of general intelligence or arbitrary program synthesis | `docs/v8-experiment-results.md`, `reports/v8/manhattan-distance/summary.json` |
| Clean sorting | **0/5 eligible** at 10,000 generations; fresh correctness ranges from 0.495 to 0.513 | A retained negative result for `clean-sorting-v1`; it does not demonstrate general sorting discovery | `docs/v8-experiment-results.md`, `reports/v8/clean-sorting/summary.json` |
| Historical v7 sorting marathon | **Retracted** | `sort1` was available, so generation-zero populations could already be perfect; no historical score can be promoted as sorting discovery | `docs/v8-contamination-audit.md`, `docs/v8-benchmark-ledger.json` |
| Checkpoint fidelity | **Verified for the covered typed-tree and deterministic-trajectory cases** | Future profiles must preserve their full primitive manifest and use the same fail-closed decoder path | `evolution/test_checkpoint_fidelity.py` |
| Authenticated observatory evidence panel | **Verified locally** | It renders persisted evidence and does not itself make the observatory a publicly published service or execute a live v9 worker | `server/v8ContaminationEvidence.ts` in the observatory repository |

## Corrections to the v9 guide's starting assumptions

The guide's central scientific direction is compatible with the v8 evidence, but several wording and status claims need correction before they can become release criteria.

| Guide statement | Audit finding | Required v9 wording or action |
|---|---|---|
| “The evolution module now has 274 tests collected.” | **Stale.** The current repository collected 447 tests on the audit command above. | Use 447 as the observed baseline until a later collected-count command records a newer value. |
| “Each [Manhattan] champion [is] structurally different” and “128/128 held-out cases.” | The published v8 results establish absence of each final tree from its own generation-zero population and 1.000 fresh correctness. This audit does not find a cross-seed structural-inequality proof or a canonical `128/128` metric in the v8 results narrative. | Add an executable structural-comparison report before making a cross-seed uniqueness claim. Preserve evaluator-owned fresh-suite wording until the exact held-out denominator is artifact-derived. |
| “Ready to submit to arXiv today.” | A result can be manuscript-ready without being submitted. Submission requires an author account, author review, category selection, and an explicit external publishing action. | Produce a reviewable manuscript and submission checklist; do not claim submission until the author completes it. |
| “Production API … deployed” or public Observatory availability. | FastAPI routes, OpenAPI, JWT auth, metrics, and WebSocket paths exist locally. The observatory has a managed preview and checkpoint, but no public release is established by this audit. | Call this **local/preview-verified**, not deployed. A public URL remains an explicit publish and operations gate. |
| “Expected” clean sorting success by a certain generation. | No v8 measurement supports a numerical success expectation beyond the observed 0/5 at 10,000 generations. | Treat expected success rates as hypotheses, not conclusions; preregister a new run before executing it. |
| “SDK version 1.0.0.” | Packaging currently advertises `living-objects` version `0.1.0`, has mandatory FastAPI/Pydantic/Redis dependencies, and exposes no documented v9 top-level API or console entry point. | Implement the API, decide the distribution version from the compatibility policy, and test an isolated install before any 1.0.0 claim. |

## Mandate-by-mandate status matrix

| ID | Mandate | Current evidence | Classification | Evidence-first completion gate |
|---|---|---|---|---|
| V9-01 | Cross 1,000 tests | 447 tests currently collect; 447 passed in the v8 release verification. | **Open, measurable** | Add meaningful behavior and regression coverage, run the full suite, and publish the actual collected/passed count. The numerical target alone is not a completion claim. |
| V9-02 | Five clean sorting seeds to 100,000 generations | Five clean 10,000-generation negative trials are persisted. No 100,000-generation campaign has run. | **Externally compute-gated** | Publish a new pre-registration, reserve sustained compute, preserve 10,000-generation checkpoints, execute declared seeds, and publish all outcomes. No predicted success threshold is assumed. |
| V9-03 | Installable SDK | The package is installable as a research package but lacks the four required top-level APIs, stable version surface, and console contract. | **Open, implementable** | Isolated-install test plus documented and typed `evolve`, `audit`, `reproduce`, and `export` APIs backed by persisted artifacts and bounded evaluator execution. |
| V9-04 | Production REST API | Local FastAPI has OpenAPI, JWT, health, metrics, organisms, archive, and WebSocket routes. It lacks the requested last-known-champion fallback, sandbox endpoint, and full endpoint rate-limit policy. | **Partially implemented** | Add pure validation contracts, bounded-result fallback, rate-limit policies, and server/integration tests. Deployment remains separate. |
| V9-05 | Live public Observatory | The authenticated Signal Loom preview renders real persisted evidence locally. It is not a published public service with a continuous worker or a fully verified playground. | **Partially implemented; deployment-gated** | Build only artifact-backed interface behavior that can be tested locally; publish only after user authorization and an operations plan. A continuous run requires durable compute. |
| V9-06 | Manhattan paper and arXiv submission | The v8 evidence supports a narrow manuscript. No paper, author sign-off, or external submission is recorded. | **Manuscript implementable; submission externally gated** | Generate a precise manuscript and reproduction appendix. Submission must be performed or explicitly approved by a named submitting author. |
| V9-07 | Five-stage sorting curriculum | `CleanSortingCurriculum` supplies generation-based primitive phases and a four-length evaluator transition. It does not establish population mastery, the five requested domains, per-stage cultural injection, event logs, or a five-seed curriculum result. | **Partially implemented** | Implement a bounded staged curriculum with a fixed evaluator contract, 95% population/90% fitness gate, evidence events, full checkpoint state, and tests before any run claim. |
| V9-08 | Signed discovery federation MVP | No v9 publish/import CLI or signed record verifier is present. | **Open, implementable** | Implement two-directory isolated exchange, signature verification, local evaluator re-check, reject-on-failure behavior, and admission provenance tests. |
| V9-09 | Honest claims registry | v8 has evidence and standards documents, but no registry covering historical claims from v1 through v9. | **Open, implementable** | Publish a registry containing a claim, status, exact boundary, evidence paths, and update rule; test references against persisted artifacts where practical. |
| V9-10 | Evidence-linked README | The current README contains stale test counts, legacy interfaces, and claims broader than the v8 evidence. | **Open, implementable** | Replace it with measured results, the stable SDK once it exists, exact reproduction commands, and visible limitations. |

## Architecture decision for long-running work

The 100,000-generation campaign and “always active” browser stream are deterministic, compute-heavy background workloads. They must not be represented as a scheduled conversational task or run opportunistically in this session. The available operating choices are deliberately kept open until an operator commits resources.

| Option | Suitable use | Constraint and gate |
|---|---|---|
| Managed web application with a persistent worker | A real-time interface and lightweight stream if its worker fits the managed single-instance resource envelope | Requires a persistent-hosting decision, an approved cost, durable state, and evidence that the worker remains within the platform limit. |
| Operator-run reproducibility campaign | The new five-seed 100,000-generation study on a machine selected by the research operator | Requires declared hardware, budget, pre-registration, checkpoint storage, exit criteria, and an operator to keep the run online. |
| Local contributor run | A lower-cost replication or short pilot | Requires the contributor's own always-on machine and cannot establish a globally live service by itself. |

## v9 implementation order

The release will first build reproducible local capabilities: SDK, staged clean curriculum, signed import/export, CLI/API validation, claims registry, README, and manuscript. It will then test these capabilities and report the observed count. Only after this foundation will the project prepare the 100,000-generation campaign and public publication materials. This order ensures the audience can verify a bounded result before any operation claims are made.

## Non-negotiable v9 boundaries

The evolution loop remains non-LLM: no language model calls may enter evaluation, selection, mutation, scoring, curriculum promotion, or import verification. The typed AST interpreter remains the only execution runtime for evolved behavior. Test count, deployment, arXiv presence, and long-run outcomes must be measured and published from their own artifacts, never inferred from code intent.
