# BEAST v12 Foundation Audit

> **Audit date:** 2026-08-18
> **Baseline:** v11 engine release on `master`, full suite reported as 1,737 collected cases
> **Status:** This document is an implementation scope and safety record. It does **not** certify v12 as complete, deploy a service, collect leads, make network requests, publish a package, submit a paper, or start an unattended process.

The v12 guide is an ambitious 12-phase roadmap. It combines locally testable interpreter and compiler work with requirements that need a permanent service, durable compute, credentials, legally governed data collection, public infrastructure, or multi-week observation. Treating every requested outcome as immediately available would be inaccurate. This audit therefore distinguishes **implemented baseline evidence**, **locally repairable work**, **platform- or authorization-gated work**, and **unmeasured claims** before code changes proceed.

## Evidence sources

| Source | What it establishes |
|---|---|
| `evolution/sandbox.py` | Generated source is placed in a subprocess with AST filtering, restricted builtins, bounded wall-clock execution, CPU/address-space limits where supported, and truncated output. It explicitly states that it is not a full OS/container security boundary. |
| `evolution/gp_engine.py` | The typed interpreter has a 500 ms cooperative execution deadline; default primitives exclude the direct `sort1` shortcut, while registered convenience primitives remain available only to explicit profiles. |
| `evolution/evaluator_safety.py` and `evolution/fitness.py` | `GameStrategyEvaluator` is centrally marked pending review and fails closed at construction and population entry. Its historic implementation is not an executable benchmark. |
| `evolution/primitive_registry.py` | The default primitive profile admits only the clean default grammar. The `legacy-artifact` profile is an explicit compatibility route for historic artifacts and convenience tests. |
| `evolution/audit_trail.py` | Local run events can be appended as a JSONL SHA-256/HMAC chain with owner-only POSIX permissions and tamper detection. This is tamper-evident, not a distributed immutable ledger. |
| `evolution/containment.py` | A machine-readable capability report states the enforced local controls and explicitly denies unavailable kernel namespace, seccomp, cgroup, dedicated-user, and read-only-root guarantees. |
| `evolution/v9_sorting_curriculum.py` | Cultural injection rehydrates a new `GPGenome` from serialized archive data before replacing an organism; it does not share the archived in-memory genome object. |
| `living_objects/sdk.py` and `living_objects/test_sdk.py` | SDK compatibility properties (`fitness`, `source_code`), artifact round-trip evidence, reproduction, and owner-only POSIX artifact permissions are already covered. |
| `production/api/v9/routes.py`, `production/api/main.py`, and `production/middleware/rate_limit.py` | The current API is an authenticated, Pydantic-bounded, inline research surface with coarse request limiting. It is not the v12 API-key public service or an always-on campaign worker. |
| `evolution/v9_federation.py` | The repository has a local signed discovery-envelope verifier with replay protection and local artifact verification. It has no peer transport, registry, background exchange job, or public federation. |

## Phase-by-phase status

| v12 phase | Verified baseline | v12 gap | Classification and implementation boundary |
|---|---|---|---|
| 1. Safety architecture | Subprocess, AST checks, output cap, wall-clock timeout, `RLIMIT_AS`/`RLIMIT_CPU` where the host supports them, typed interpreter deadline, default/legacy primitive profiles, evaluator approval gate, HMAC-chained local audit trail, and containment capability report exist. | No seccomp-bpf policy, cgroup quota, dedicated OS user, mount namespace, read-only root, or externally audited sandbox. | **Locally completed in part.** The new contracts were regression-tested. Do not claim kernel isolation without a host that provisions it. |
| 2. String and pattern engine | Forty typed Tier 2 pure string primitives are registered with bounded inputs/outputs and per-primitive approval metadata. A 14-name fixed-pattern registry rejects arbitrary regex strings. | Fixed-pattern helpers are not yet interpreter-exposed Tier 3 primitives routed through the subprocess sandbox; no real anonymised lead dataset, lead evaluator, or contamination result exists. | **Locally completed in part.** Text transforms and fixed-name pattern detection are regression-tested. Never accept arbitrary runtime regex or execute user-provided source. |
| 3. Network primitive sandbox | Current sandbox defaults to `allow_network=False`; the production wrapper preserves that intent. | The flag is not a network namespace or outbound proxy. There is no allowlist, rate ledger, content-size enforcement at a network boundary, cache, or public-web task evidence. | **Platform and authorization gated.** A real outbound boundary needs a controlled service/worker, approved domains, lawful data policy, credential management, and observable request logging. No network primitive will be represented as operational before then. |
| 4. Knowledge base | Persisted run artifacts, curriculum archive entries, and signed local discovery records exist. | No SQLite provenance schema, task-version registry, source-trust model, or retention policy for externally fetched data. | **Locally repairable in part.** A local artifact index can be built later; real company data requires separately approved sources and privacy/legal review. |
| 5. Multi-task agent | Bounded CLI/API operations and an environment compatibility module exist. | No durable goal registry, task decomposition system, action planner, human approval queue, or cross-task campaign controller. | **Gated.** Building an autonomous action framework requires durable hosting, consented integrations, explicit action policies, and user authorization. |
| 6. Benchmark suite | Manhattan runs, deterministic reproduction, JavaScript runtime checks, and a recorded negative sorting Stage 0 result exist. | No 50-task public benchmark release, no 50,000-generation cloud run, no lead benchmark, and no independently reviewed suite. | **Partly local, partly persistent-compute gated.** Existing verified results remain narrow and must not be generalized. |
| 7. Stateful agent framework | No persistent loop or scheduler is represented as active. | No 72-hour goal state, retry policy, action journal, or approval-aware side-effect protocol. | **Persistent hosting and authorization gated.** The default sandbox cannot provide this assurance. |
| 8. Self-improvement | Existing evolution mutates programs and fixed run parameters; v11 contains bounded experiments only. | No ten-seed hyper-evolution study, primitive-set optimizer, or automatic curriculum generator meeting stated gates. | **Research work, not complete.** Candidate configuration experiments may be added only with predeclared budgets and retained negative results. |
| 9. Multi-language synthesis | Export support is limited to Python plus selected numeric Manhattan targets in JavaScript, Rust, and Go; JavaScript has a bounded runtime check. | No eight-language compiler, all-task Tier 1/2 mapping, 100-case runtime contracts for each target, or quality post-processor. | **Locally expandable but incomplete.** Add targets only when the relevant runtime is installed and a source-to-runtime equivalence test passes. |
| 10. Production deployment | Local API routes are bounded, input-validated, JWT-protected at the main application boundary, and rate-limited by client/path. The observatory explicitly says `NOT_DEPLOYED` and `NOT_CONFIGURED`. | No API-key registration flow, v12 quota classes, cached-read age header, permanent URL, TLS deployment confirmation, continuous worker, PyPI 1.0.0 release, or arXiv identifier. | **External-action gated.** Do not publish or claim public availability without owner-controlled deployment and account access. |
| 11. Federation network | Local signed discovery import checks issuer, signature, nonce replay, canonical record identity, and local evaluator agreement. | No public registry, second installation, remote transport, six-hour exchange, or public peer URLs. | **Infrastructure and opt-in gated.** No peer polling or network exchange will be started from this audit. |
| 12. Final capability gates | The project has reproducible local artifacts and an honest-claims registry. | The stated lead, HumanEval, 72-hour, comparison, and four-week reproducibility gates have not been run. | **Not measured.** None of the final-capability claims may be made. |

## Required v12 remediation status

| Mandate | Baseline finding | Status before v12 work | Required treatment |
|---|---|---|---|
| Disable `GameStrategyEvaluator` | It is now centrally recorded as pending `v12-game-strategy-review-pending`; construction and population entry fail closed with an actionable error. | **Completed locally.** | It remains disabled until a task-specific evaluator review records an approval. |
| Route async/sync isolation | The v9 endpoint is a synchronous FastAPI handler; the existing API regression shows concurrent snapshot reads remain reachable, but the v12 guide specifically asks for `asyncio.to_thread()`. | **Partial.** | Preserve the bounded inline-generation cap. Make isolation explicit or document the framework worker-thread contract with a concurrency regression; never turn the route into a campaign worker. |
| API-key authentication | Main API uses JWT bearer/operator authorization, not an email-verification/API-key issuance model. | **Partial.** | Do not claim v12 API-key registration. If implemented later, keys need storage, rotation, revocation, hashing, per-key quotas, and migration testing. |
| SDK result aliases | `.fitness` and `.source_code` properties exist and have regression coverage. | **Satisfied locally.** | Preserve tests and keep README/docstrings aligned with the compatibility contract. |
| Federation key pre-commit scan | Runtime key handling is environment based and v11 has a no-plaintext-file boundary test. A repository pre-commit scanner is not yet evidenced. | **Open.** | Add a local hook/scanner with documented pattern scope, test it against a non-secret synthetic sentinel, and avoid treating it as a substitute for secret revocation. |
| Evaluation timeout | A portable 500 ms cooperative interpreter deadline exists. It is not `signal.alarm`, which is unsuitable as a general cross-platform/threaded security control. | **Partial.** | Keep the current typed fallback behavior and add a subprocess-level wall-clock timeout for untrusted exported source. Do not claim an in-process timer can stop arbitrary blocking primitives. |
| Curriculum deep copy | Injection decodes serialized genome data into a fresh object, avoiding the stated shared-genome alias. | **Satisfied locally.** | Retain/extend the isolation regression; no shallow mutable archive object should be introduced. |
| Artifact path after resume | The SDK reproduces directly from persisted artifact metadata; existing round-trip coverage includes `artifact_path` compatibility. The alleged reconstruction path is not present as a current public flow. | **Satisfied for current SDK surface.** | Preserve artifact-reproduction regression and investigate only if a new checkpoint-to-`EvolutionResult` constructor is added. |

## Real-world test disposition

The following table records the status of the 20 proposed v12 tests at the point of audit. A test is not marked passed merely because related code exists.

| Tests | Status | Reason |
|---|---|---|
| 1, cold install | **Partial** | v10 wheel smoke checks cover Python 3.10–3.12 locally. There is no public PyPI install, no Python 3.13 evidence, and no claim that a clean external machine completed the workflow. |
| 2, real Stripe extraction | **Not run** | Requires approved live web access and a real extraction capability. |
| 3, email format inference | **Not run / prohibited without lawful dataset** | It would handle personal contact data and must not be developed against scraped or unconsented records. |
| 4, 1,000-input JavaScript runtime | **Partial** | A bounded Node.js runtime comparison exists for five fixed cases. The 1,000-random-input gate remains unrun. |
| 5, 30-day reproduction | **Not run** | Deterministic local reproduction has been checked; a 30-day observation has not elapsed. |
| 6–7, network quota and whitelist | **Not run** | There is no network primitive sandbox to exercise. |
| 8, 500-organism memory cap | **Unmeasured against stated cap** | A local capacity profile is not a portable 50 MB production-capacity proof. |
| 9, 50,000-generation curriculum | **Not run** | Requires authorized persistent compute and the preregistered campaign gate. |
| 10–11, lead pipeline/autonomy | **Not run** | No real lead pipeline or autonomous side-effect system is authorized. |
| 12, arXiv download/reproduction | **Not run** | The paper is locally compiled but unsubmitted and has no arXiv ID. |
| 13, federation import from second machine | **Not run** | Local envelope tests are not a separate installed peer. |
| 14, game evaluator blocked | **Passed locally** | Construction is blocked by the evaluator approval policy and active evaluator matrices no longer advertise the benchmark. |
| 15, API-key authentication | **Partial** | JWT/operator authorization exists; the requested API-key flow does not. |
| 16, live observatory update | **Not run** | The observatory is explicitly not public and has no continuous worker. |
| 17, claims completeness | **Unmeasured** | Registry discipline exists, but no automated README-to-registry completeness proof is currently recorded. |
| 18, SDK helpful typo | **Unmeasured** | Requires a dedicated contract test. |
| 19, rate-limit recovery | **Not run** | There are no network calls or hour-bound recovery workflow. |
| 20, public lead comparison | **Not run** | No lawful lead benchmark or Claude/Codex comparison has been published. |

## v12 execution order

The only safe next implementation sequence is deliberately narrower than the roadmap’s headline:

1. **Phase 1 local controls completed.** The central primitive approval registry, evaluator gate, tamper-evident local audit chain, and testable containment report are implemented. The unapproved game evaluator is disabled. The focused foundation/evaluator/population/contamination run passed **949 tests**.
2. **Phase 2 text subset completed.** The 40-operation Tier 2 grammar and 14-name fixed-pattern registry are tested. The pattern helpers are not yet GP Tier 3 sandbox primitives, and no Lead Record Evaluator is represented as complete because no lawful real anonymised dataset has been approved.
3. **Later-phase gate completed.** `docs/v12-operational-authorization-gate.md` sets concrete authorization, privacy, network, persistence, credential, public-service, and campaign prerequisites without starting a service or granting an external capability.
4. **Prove contracts before extending scope.** Add contamination, timeout, audit, and helpful-error regressions. Record both passing and negative results.
5. **Do not begin Phase 3 or beyond as an implicit consequence of this task.** Network, lead, scheduling, persistence, federation, public deployment, publication, and autonomous action each require separate owner authorization plus the relevant service, data, privacy, and credential setup.

### Post-governance compatibility repair

Initial profile enforcement correctly rejected declared clean-sorting grammars when their callers omitted a non-default label. That was a compatibility failure in the enforcement layer, not a reason to broaden the default grammar. The repair adds the explicit reviewed `task-specific` profile, records it in checkpoint configuration, infers it for compatible historic non-legacy checkpoint payloads, and requires clean-sorting curricula and their contamination baseline to name it deliberately. The default grammar remains strict and `sort1` remains legacy-only.

Focused post-repair verification on 2026-08-18 passed **17 tests** across checkpoint fidelity, clean sorting, v9 curriculum, and v12 foundation contracts.

## Non-claims retained for v12

BEAST does not currently have a kernel-enforced network sandbox, a public lead-generation system, real-company lead results, email-inference performance, a public Observatory URL, an always-on worker, a PyPI 1.0.0 release, an arXiv identifier, a federation registry, a 72-hour autonomous run, a HumanEval result, or a demonstrated advantage over Claude or Codex. The project remains an evidence-backed, bounded genetic-programming research platform with narrow verified results and documented negative findings.
