# BEAST v11 Foundation Audit

> **Audit date:** 2026-08-18. This record checks the v11 directives against the checked-out v10 implementation, rather than treating the guide as an executable specification. A guide finding is repaired only when the current source and its tests support it.

## Scope and classification rule

The audit covered the current primitive registry, typed-tree evaluator, population checkpoint path, public SDK, clean-sorting curriculum, signed discovery exchange, and assembled FastAPI application. “Verified” means the present code exhibits the issue. “Already repaired” means the current code contains the claimed remediation and a relevant regression. “Stale or misplaced” means the guide describes an earlier implementation or assigns a behavior to a different subsystem. “Operationally unmeasured” is not converted into a success claim.

| v11 assertion | Classification | Evidence in current repository | v11 action |
|---|---|---|---|
| `sort1` is in `DEFAULT_PRIMITIVES` | **Repaired in v11** | `sort1` now lives in `CONVENIENCE_PRIMITIVES`; clean defaults exclude it while `ALL_REGISTERED_PRIMITIVES` can decode historic artifacts. | `evolution/test_gp_engine.py` asserts the default/legacy boundary. |
| Crossover can make unbounded deep trees that reach Python recursion limits | **Stale** | `GPTreeBuilder.subtree_crossover()` rejects descendants outside `MAX_DEPTH=8` or `MAX_SIZE=96`; `GPNode.evaluate()` independently returns a typed fallback at evaluation depth 50. | Preserve both guards; add no separate speculative repair unless a new primitive changes the execution model. |
| Wall-clock efficiency can alter correctness selection | **Already repaired** | Shared evaluator scoring makes `score=correctness`; wall time and efficiency are reported metadata. The Manhattan objective is normalized numeric error, while its timing remains separate. | Keep timing out of proof verification and describe it as host-sensitive telemetry. |
| `GameStrategyEvaluator` awards perfect score to a `None` result | **Repaired / regression-covered** | Its single and population paths now use the same 100-round deterministic tournament against five opponents; a nonnumeric return maps to a defect move. | `evolution/test_fitness.py` proves population evaluation uses the tournament path; do not label it a published benchmark result. |
| A recursive primitive can hang current evaluation without a timeout | **Extension gate hardened in v11** | The admitted primitive set remains pure and nonrecursive. `GPGenome.execute()` now sets a 500 ms cooperative monotonic deadline checked at interpreter-node boundaries. | The deadline returns a typed fallback for expired evaluation. It is not a pre-emptive kill for arbitrary blocking Python callables; those remain outside the admitted grammar and require process isolation. |
| Population checkpoint restore loses `EvolutionResult.artifact_path` | **Stale / misplaced** | `GPPopulation` checkpoints engine state; it does not construct `EvolutionResult`. The SDK writes an artifact and returns its path, while its `reproduce()` regression uses that persisted record. | Preserve the SDK artifact regression; do not conflate engine checkpoints with SDK run artifacts. |
| SDK lacks `.fitness` and `.source_code` | **Already repaired** | `EvolutionResult` exposes read-only compatibility accessors that delegate to the champion record; `living_objects/test_sdk.py` covers direct and round-trip access. | Keep the documented SDK quick-start on those accessors. |
| Deterministic run identifiers can be guessed in a shared artifact directory | **Mitigated, local-scope only** | The identifier remains reproducible from canonical configuration, but persisted run artifacts are created owner-readable/writable only on supported filesystems. | Keep the local-only artifact-directory warning; do not market it as a multi-tenant artifact store. |
| Cultural seed injection aliases mutable genomes | **Stale** | The curriculum serializes the champion genome, restores a new `GPGenome` from that data, and rescoring occurs before selection. | Preserve serialized-copy injection regression. |
| Federation module loads a plaintext HMAC config file | **Stale; documented in v11** | `SignedDiscoveryExchange` accepts key bytes by constructor injection and does not parse or persist a configuration file. | `docs/v11-federation-secret-safety.md` now explicitly prohibits committing a signing secret or future key-file configuration. |
| v9 evolve endpoint is unauthenticated, unrestricted, and blocks the event loop | **Stale for the assembled API** | `production/api/main.py` mounts the v9 router behind operator JWT authentication. `production/api/v9/routes.py` uses a synchronous endpoint executed in FastAPI’s worker-thread path, limits runs to 25 generations, and rate-limits inline runs to 3/minute. | Retain the explicit “no worker” disclosure; do not represent the API as a general long-running service. |
| Live Observatory WebSocket streaming is proven | **Unmeasured / not deployed** | The v10 Observatory is an authenticated artifact-backed view with an explicit `NOT_DEPLOYED` / `NOT_CONFIGURED` disclosure. | No live-stream or public-URL claim may be made without deployment and an end-to-end authenticated event test. |

## Measured v11 real-world checks

| Check | Exact outcome | Evidence artifact | Claim boundary |
|---|---|---|---|
| Local Manhattan end-to-end | **Measured:** 300 generations, seed `20260814`, population 128, 57.170 s; held-out 1,000/1,000 correct; champion hash `04a3…99bc5`. | `reports/v11/manhattan-real-world-test.json` | One local run, not a fresh-machine, cloud-VM, multi-seed, or production-readiness benchmark. |
| Exact replay | **Verified:** the saved run reproduced the same `04a3…99bc5` hash in 57.894 s with no mismatches. | `reports/v11/manhattan-reproduction.json` | Verifies the saved bounded configuration on this environment only. |
| JavaScript runtime export | **Verified:** a 50-generation Manhattan champion containing `sqrt` exported to JavaScript; Node.js matched the typed interpreter on five fixed inputs. | `reports/v11/javascript-export-runtime.json` | Five inputs and one target runtime do not certify all source targets or primitives. |
| Clean sorting Stage 0 | **Measured negative:** 5,000 generations, seed 42, population 50; Stage 0 did not advance. Mean correctness was `0.3956`; no organism reached the 0.95 individual-mastery threshold in the final 100-case check. | `reports/v11/sorting-stage0-5000.json` | This is a negative single-seed Stage 0 result, not proof of a fundamental impossibility or a completed 100k campaign. |
| Local capacity profile | **Measured:** 25-generation local runs recorded 12.44, 8.59, 4.15, and 1.39 generations/s for populations 50, 100, 200, and 500; isolated-process peak RSS was 24,640–35,216 KiB. | `reports/v11/local-capacity-profile.json` | Local sandbox observations only; they do not establish a standard cloud-VM rate, a 1 GB maximum-safe population, or production capacity. |
| Bounded API concurrent read | **Verified in-process:** while an authenticated bounded run waited in Starlette’s worker thread, an authenticated `/v9/snapshot` response completed in under 0.5 s. | `production/test_v9_api.py` | A controlled in-process test; it does not establish external HTTP latency, queue durability, multi-instance behavior, or a public deployment. |

## Resulting v11 scope

The locally actionable v11 repairs are complete for the default-primitive contamination boundary, portable `sqrt` export, cooperative interpreter deadline, artifact permissions, package-release version sync, and federation-secret documentation. The assembled API remains authenticated, rate-limited, generation-bounded, and deliberately worker-free. Long campaigns, a public Observatory URL, PyPI upload, arXiv submission, and external lead enrichment remain separately gated.

The audit did start one bounded 5,000-generation Stage 0 measurement and retained its negative outcome. It did **not** start the preregistered 100,000-generation campaign, a public deployment, a background worker, or lead scraping. Those operations continue to require the specific resource, source, authorization, and output-provenance gates documented elsewhere in the repository.

## Lead-research boundary

The evolutionary interpreter has no HTTP, browser, file-read, database, or external-API primitive. It therefore cannot presently perform lead collection or enrichment. Adding arbitrary network primitives to evolved programs would alter the system’s safety and evaluator model; it is not an incremental extension of the current mathematical-function benchmark.

If a future owner authorizes a lead-research product, it must be implemented as a separate, conventional workflow with documented public or licensed sources, a per-source permission and rate-limit policy, explicit records of provenance and retrieval time, a reviewable database schema, and a human-approved export. No claim that BEAST evolves a web scraper, extracts private contact data, bypasses a login or CAPTCHA, or outperforms general code-generation systems is supported by the present code.

## Verification references

| Behavior | Source | Regression evidence |
|---|---|---|
| Primitive admission and tree bounds | `evolution/gp_engine.py` | `evolution/test_gp_engine.py`, `evolution/test_gp_population.py` |
| Evaluator scoring and game tournament | `evolution/fitness.py` | `evolution/test_fitness.py`, `evolution/test_proof_benchmark.py` |
| Checkpoint behavior | `evolution/gp_population.py` | `evolution/test_gp_population.py` |
| SDK accessors and reproducibility | `living_objects/sdk.py` | `living_objects/test_sdk.py` |
| Curriculum serialization and cultural seed | `evolution/v9_sorting_curriculum.py` | `evolution/test_v9_sorting_curriculum.py` |
| Local signed exchange | `evolution/v9_federation.py` | `evolution/test_v9_federation.py` |
| Authenticated bounded v9 API | `production/api/main.py`, `production/api/v9/routes.py` | `production/test_v9_api.py` |
| Runtime measurement commands | `scripts/run_v11_*`, `scripts/verify_v11_*` | committed JSON records in `reports/v11/` |
