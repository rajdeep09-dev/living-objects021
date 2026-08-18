# BEAST / Living Objects

> **A bounded research system for evolving typed programs under explicit, reproducible evaluation.**

BEAST is not a general autonomous programmer, a conscious system, or a live self-improving service. It is a research codebase that tests a narrower question:

> Can a population of non-LLM typed programs improve from its initial population on a task with an objective evaluator, while the result remains inspectable and reproducible?

The current evidence answers **yes for one bounded Manhattan-distance synthesis task**, and **no eligible result for the current clean-sorting profile**. Both outcomes are retained. See the [claims registry](docs/v9-claims-registry.md) before reusing any statement from this repository.

## What the evidence currently supports

| Topic | Measured or implemented status | Exact boundary | Primary evidence |
|---|---|---|---|
| Manhattan distance | **5/5 eligible fixed-seed runs**; fresh correctness was **1.000** on each recorded 1,000-case suite | Typed AST interpreter, fixed evaluator, population 128, up to 10,000 generations; not arbitrary program synthesis or general intelligence | [v8 results](docs/v8-experiment-results.md), [trial summary](reports/v8/manhattan-distance/summary.json) |
| Clean sorting | **0/5 eligible runs** at 10,000 generations; retained negative result | Applies only to `clean-sorting-v1`; no numerical success expectation is implied | [v8 results](docs/v8-experiment-results.md), [trial summary](reports/v8/clean-sorting/summary.json) |
| v7 sorting marathon | **Retracted** | `sort1` made generation-zero perfection possible; its score is not sorting discovery evidence | [contamination audit](docs/v8-contamination-audit.md), [benchmark ledger](docs/v8-benchmark-ledger.json) |
| v10 SDK and local package artifacts | **Implemented, locally built, and tested** | Version `0.3.0` wheel/source artifacts were locally smoke-tested on Python 3.10–3.12; no PyPI project has been uploaded | [package release record](docs/v10-package-release.md), [`living_objects.sdk`](living_objects/sdk.py) |
| Five-stage sorting curriculum | **Implemented and tested, not yet measured in the planned long campaign** | No 100,000-generation result or expected success rate has been claimed | [curriculum module](evolution/v9_sorting_curriculum.py), [research roadmap](docs/v9-advanced-research-roadmap.md) |
| Signed discovery exchange | **Local verification MVP implemented and tested** | It signs and verifies persisted evidence locally; it is not a deployed federation or transport network | [federation module](evolution/v9_federation.py) |
| v11 bounded local checks | **Measured:** a 300-generation Manhattan run reached 1,000/1,000 held-out correctness; a 5,000-generation clean-sorting Stage 0 run did not advance | One local configuration and one negative single-seed curriculum measurement; neither establishes cloud capacity, production readiness, or the 100,000-generation campaign outcome | [v11 audit](docs/v11-foundation-audit.md), [`reports/v11/`](reports/v11/) |

## Install and run bounded workflows

The package is a repository-installable research SDK. Version `0.3.0` local wheel and source artifacts were built and smoke-tested on Python 3.10, 3.11, and 3.12. It is **not** represented as a published package registry release: a PyPI upload requires the publishing owner’s credentials and explicit confirmation. See the [v10 package-release record](docs/v10-package-release.md) for artifact checksums and the handoff gate.

```bash
git clone https://github.com/rajdeep09-dev/living-objects021.git
cd living-objects021
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

# Show the inspected contamination classification for a persisted task.
living-objects audit manhattan-distance

# Run one explicitly bounded local interpreter-only task and save its artifact.
living-objects --artifact-dir .living-objects/runs \
  evolve manhattan-distance --generations 100 --seed 20260814

# Then reproduce or export source only as an audit artifact.
living-objects --artifact-dir .living-objects/runs reproduce <run-id>
living-objects --artifact-dir .living-objects/runs export <run-id> python
```

To test the locally produced wheel rather than an editable checkout, build or obtain the audited `0.3.0` artifact and install it in a clean environment:

```bash
python -m pip install dist/living_objects-0.3.0-py3-none-any.whl
```

The evolution runtime is a typed AST interpreter. No language-model call is used in evaluation, selection, mutation, scoring, curriculum promotion, or discovery-import verification. Exported Python, JavaScript, Rust, and Go text is **not** the runtime for evolved behavior and should not be treated as safe executable code.

The programmatic SDK exposes compatibility accessors for the audited champion record. `fitness` is the persisted **training** fitness; it is not a general-quality score. `source_code` is a source-only Python audit export and is never executed by the SDK.

```python
from living_objects import evolve

result = evolve("manhattan", generations=100, seed=20260814)
print(result.fitness)
print(result.champion["fresh"]["correctness"])
print(result.source_code)  # review-only audit text; not the runtime
```

## Reproduce the v8 five-seed evidence

The published five-seed results were pre-registered as `BEAST-V8-PREREG-20260816-A`. The original evidence release was `e2ea116`; use that revision for a strict historical reproduction. The run is intentionally large: each task has five seeds and 10,000 generations, so plan the compute rather than treating it as a quick smoke test.

```bash
git checkout e2ea116
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q \
  evolution/test_checkpoint_fidelity.py evolution/test_clean_sorting.py \
  evolution/test_proof_benchmark.py

# Writes complete trials, checkpoints, and a new summary under /tmp/v8-reproduction.
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
  python scripts/run_v8_multiseed.py manhattan-distance --output-dir /tmp/v8-reproduction

# On the v9 release, render the included figure from the repository’s persisted trials.
python scripts/build_v9_paper_figure.py
```

Timing telemetry is host-dependent and excluded from deterministic artifact comparison. Fitness, tree structure, primitive profiles, checkpoint state, declared seeds, and fresh-evaluator outcomes remain the scientific evidence fields.

## Scientific boundaries

- **No hidden benchmark rescue:** sorting and string-reverse direct-primitive results remain retracted.
- **Negative results stay visible:** the clean-sorting 0/5 outcome is part of the release record.
- **No live-service claim:** the observatory is locally/preview verified and **not a public deployment**; publishing it and operating a continuous worker require a separate authorization and operations decision.
- **No long-run claim:** the clean-sorting 100,000-generation campaign is pre-execution work gated on declared hardware, durable checkpoints, compute budget, and operator oversight.
- **No publication claim:** the LaTeX manuscript bundle is locally compiled review material, **not submitted** and not peer reviewed; the `0.3.0` package is locally built, **not uploaded to PyPI**.
- **No lead-research claim:** the evolutionary interpreter has no network, browser, file-read, database, or external-API primitive. It does not scrape, enrich, bypass websites, or process private contact data.

## v10 readiness record

Version 10 repairs the SDK’s top-level `EvolutionResult.fitness` and `EvolutionResult.source_code` compatibility accessors, builds distribution artifacts, prepares an arXiv-ready source bundle, and adds an authenticated Observatory status disclosure. It does not convert externally controlled actions into local claims.

| Prepared or verified item | v10 reality | Evidence |
|---|---|---|
| SDK contract | `fitness` and source-only `source_code` accessors are regression-tested in SDK version `0.3.0` | [foundation audit](docs/v10-foundation-audit.md), [`living_objects/test_sdk.py`](living_objects/test_sdk.py) |
| Distribution | Wheel/source artifacts locally validated on Python 3.10–3.12 | [package release record](docs/v10-package-release.md) |
| Manuscript | Submission-ready LaTeX source package and locally compiled review PDF preparation | [arXiv package](docs/v10-arxiv-submission-package/README.md), [submission checklist](docs/v10-arxiv-submission-checklist.md) |
| Observatory | Artifact-backed authenticated evidence route, explicit `NOT_DEPLOYED` and `NOT_CONFIGURED` operational state | [deployment package](docs/v10-observatory-deployment-package.md) |
| Long campaign | Exact owner authorization, 10,000-generation pilot, restore, and milestone gate documented | [campaign launch gate](docs/v10-campaign-launch-gate.md) |

> No arXiv identifier, PyPI package URL, public Observatory URL, continuous worker, or 100,000-generation campaign result exists at this release point.

## v11 measured checks and hardening

Version 11 audited the v10 guide against the checked-out source, rather than assuming historic findings were still present. It removes `sort1` from the default grammar, gives the game evaluator a deterministic tournament, adds a cooperative interpreter deadline, tightens local artifact permissions, synchronizes the package export version, and validates portable `sqrt` JavaScript output in Node.js. The bounded API remains authenticated, rate-limited, limited to 25 inline generations, and explicitly worker-free.

| v11 item | Exact result | Boundary and evidence |
|---|---|---|
| Manhattan end-to-end | 300 generations, seed `20260814`, population 128, **1,000/1,000** held-out correct in 57.170 s; exact replay matched the champion hash | One local configuration; [run record](reports/v11/manhattan-real-world-test.json), [replay record](reports/v11/manhattan-reproduction.json) |
| JavaScript export runtime | A 50-generation Manhattan champion with `sqrt` matched the typed interpreter on five fixed Node.js inputs | One target and five cases only; [runtime record](reports/v11/javascript-export-runtime.json) |
| Clean-sorting Stage 0 | **Negative:** 5,000 generations, seed 42, population 50; mean correctness `0.3956`, no final organism met individual mastery | Does not prove impossibility or complete the campaign; [measurement](reports/v11/sorting-stage0-5000.json) |
| Local capacity observation | 12.44, 8.59, 4.15, and 1.39 generations/s for populations 50, 100, 200, and 500 | Sandbox observations only, not cloud or production capacity; [profile](reports/v11/local-capacity-profile.json) |
| Bounded API isolation | An authenticated `/v9/snapshot` completed in under 0.5 s while an authenticated inline run waited in a worker thread | In-process regression only; no durable queue, public HTTP latency, or multi-instance claim; [`production/test_v9_api.py`](production/test_v9_api.py) |

See the [v11 foundation audit](docs/v11-foundation-audit.md) for the full defect classification, repaired/stale distinctions, safety limits, and lead-research boundary.

## v12 safety foundation and bounded text work

Version 12 adds locally testable controls before any expansion toward networked or autonomous behavior. The default GP profile now has explicit per-primitive approval metadata, the pending-review game-strategy evaluator fails closed, a local HMAC-linked audit trail detects modification, and a capability report distinguishes enforced local controls from unavailable kernel isolation. These are **local contracts**, not a production security certification or an immutable distributed ledger.

The interpreter also provides forty bounded pure string transforms and a fourteen-name fixed-pattern helper registry. The registry rejects arbitrary regular-expression text. It does not ingest real leads, infer personal contact details, make requests, access a browser, read arbitrary files, or execute patterns as sandboxed organism primitives.

| v12 item | Exact implementation status | Boundary and evidence |
|---|---|---|
| Containment and audit records | Locally implemented and regression-tested | AST/interpreter/subprocess controls remain host-dependent; the audit chain is local and tamper-evident, not an immutable ledger or kernel sandbox. [Foundation audit](docs/v12-foundation-audit.md) |
| Primitive and evaluator approval | Locally implemented and regression-tested | The clean default profile is governed centrally; legacy profiles require explicit opt-in. `GameStrategyEvaluator` is disabled pending task-specific review. [Foundation tests](evolution/test_v12_foundations.py) |
| Text and fixed patterns | Forty pure string operations and fourteen named patterns are locally implemented and regression-tested | No arbitrary regex, Tier 3 sandboxed organism pattern execution, real lead dataset, lead evaluator, or business-quality result. [Text-pattern safety](docs/v12-text-pattern-safety.md) |
| Network, persistence, federation, and external action | Explicitly gated | No network organism primitive, persistent worker, scheduler, public API, external side effect, or multi-agent deployment. [Operational gate](docs/v12-operational-authorization-gate.md) |
| Final v12 regression | **1,720 collected cases passed** in 124.91 seconds | Parameterized collection count, not a count of distinct test functions; 12 existing test/dependency configuration warnings remain visible. [Final verification](docs/v12-final-verification.md) |

> The v12 roadmap is not a permission grant. External data, credentials, network access, persistent autonomy, public deployment, publishing, and campaign execution each remain owner-controlled and independently verifiable decisions.

## Repository map

| Location | Purpose |
|---|---|
| [`living_objects/sdk.py`](living_objects/sdk.py) | Versioned bounded SDK: `evolve`, `audit`, `reproduce`, and source-only `export` |
| [`evolution/gp_engine.py`](evolution/gp_engine.py) | Typed AST representation and interpreter |
| [`evolution/v9_sorting_curriculum.py`](evolution/v9_sorting_curriculum.py) | Five-stage clean curriculum and auditable mastery events |
| [`evolution/v9_federation.py`](evolution/v9_federation.py) | Local signed evidence-exchange MVP |
| [`production/api/v9/`](production/api/v9/) | Local authenticated bounded API contracts |
| [`docs/v10-arxiv-submission-package/`](docs/v10-arxiv-submission-package/) | Locally compiled arXiv-ready source bundle; external submission remains gated |
| [`docs/v9-claims-registry.md`](docs/v9-claims-registry.md) | Allowed claim wording and update rules |
| [`docs/v10-package-release.md`](docs/v10-package-release.md) | Local distribution evidence and PyPI handoff gate |
| [`docs/v10-observatory-deployment-package.md`](docs/v10-observatory-deployment-package.md) | Real-data observatory path and no-live-operation boundary |
| [`docs/v10-campaign-launch-gate.md`](docs/v10-campaign-launch-gate.md) | Persistent-compute authorization, pilot, recovery, and milestone gate |
| [`docs/v11-foundation-audit.md`](docs/v11-foundation-audit.md) | v11 code audit, measured local checks, and exact capability boundaries |
| [`reports/v11/`](reports/v11/) | Committed bounded-run, replay, runtime-export, Stage 0, and capacity evidence |
| [`docs/v12-foundation-audit.md`](docs/v12-foundation-audit.md) | v12 phase-by-phase safety, platform, privacy, and authorization audit |
| [`docs/v12-operational-authorization-gate.md`](docs/v12-operational-authorization-gate.md) | Required gates for data, network, persistence, credentials, public service, and external action |
| [`evolution/primitive_registry.py`](evolution/primitive_registry.py) | Per-primitive approval metadata and explicit profile governance |
| [`evolution/approved_patterns.py`](evolution/approved_patterns.py) | Fixed-name bounded pattern registry; arbitrary regex strings are refused |

## Development verification

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q
```

The exact collected/passed count is recorded for each release verification. The v11 verification passed **1,737 collected cases**; this is a parameterized collection count, not a count of distinct test functions. Do not substitute a badge or a historical count for a fresh test run.

## License

MIT. See [LICENSE](LICENSE).
