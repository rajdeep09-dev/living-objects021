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

## v13 local BEAST-BRAIN research foundation

Version 13 adds a **local, provenance-preserving research scaffold**, not a live AI service. The checked-in dataset has **78 complete local records** (69 approved primitive records and 9 deterministic evaluator-pattern records); a separate 513-record corpus clearly labels 345 template variants as synthetic and 90 evaluator reruns as zero-candidate diagnostics. The 16 report-derived champion records retain `FILL` explanations and are excluded from instruction data until separately reviewed.

The CPU smoke experiment is a small byte-bigram table trained only over the local base data. On its fixed 66/12 split it recorded held-out negative log likelihood **2.176272** versus **5.545177** for a uniform-byte baseline. This is a text-compression sanity check, **not** a downloaded, pre-trained, or fine-tuned LLM result.

| v13 item | Exact observed status | Boundary and evidence |
|---|---|---|
| Local data and provenance contracts | **Implemented and locally tested** | Source labels, artifact digests, create-once output, and incomplete-explanation exclusion are checked locally; there is no cloud explanation call or external dataset. [Data contract](docs/beast-brain-data-contract.md) |
| CPU smoke model | **Measured locally** | A custom byte-bigram table on a 66/12 split improved held-out NLL over a uniform-byte baseline; it is not an LLM, model download, or capability benchmark. [Smoke record](docs/beast-brain-cpu-smoke.md) |
| Controller admission gate | **Implemented and locally tested** | Untrusted generated text may name only existing approved primitives under an explicit profile; it cannot alter grammar or execute source. [Controller boundary](docs/beast-brain-controller-boundary.md) |
| Clean-sorting comparison | **Neutral negative control** | The CPU preview was invalid JSON and rejected; frozen-grammar baseline and guidance arms both scored **0.58** held-out correctness. No BEAST-BRAIN assistance result is claimed. [Negative control](docs/beast-brain-negative-control.md) |
| Ollama, cloud inference, internet, external data, workers, publishing, deployment | **Inactive and gated** | No local model service, network primitive, lead-data workflow, persistent autonomy, PyPI release, arXiv submission, or public observatory exists. [v13 audit](docs/v13-beast-brain-architecture-audit.md) |

See the exact release evidence and reproduction boundary in the [v13 final verification record](docs/v13-final-verification.md).

## v14 finite 28.9M local transformer attempt

Version 14 records one finite, from-scratch CPU training attempt for a **28,864,544-parameter** byte-level causal transformer. It used only the existing 78-record, provenance-labelled local base corpus, random initialization, a deterministic 66/12 split, and a 3,000-second time cap. It completed 10,000 steps in 2,197.54 seconds and reduced the declared held-out next-byte NLL from **325.017220** to **0.311103**.

This is evidence that the declared local training/checkpoint/evaluation pipeline ran. It is **not** evidence of a useful general LLM, a parent-model transfer from Manus or this assistant, language understanding, code generation, BEAST assistance, or autonomous self-improvement. A deterministic continuation was treated as untrusted controller input and rejected as `invalid_json`; no primitive was admitted or executed.

| v14 item | Exact observed status | Boundary and evidence |
|---|---|---|
| Finite local transformer attempt | **Measured locally** | One 28,864,544-parameter architecture, one small fixed corpus, one local CPU environment, and next-byte NLL only; it is not a downloaded, pre-trained, or general-purpose model. [Final verification](docs/v14-final-verification.md) |
| Post-training controller check | **Rejected untrusted continuation** | The continuation failed exact JSON admission. No grammar change, source execution, benchmark assistance, or improvement claim followed. [Evaluation boundary](docs/v14-28m-evaluation-boundary.md) |
| Ollama, parent-weight transfer, internet, cloud inference, persistent autonomy, publication, deployment | **Inactive and gated** | No model service, network action, external weight/data, persistent agent, PyPI upload, arXiv submission, or public observatory exists. [V14 final verification](docs/v14-final-verification.md) |

## v15 native JSON instruction-tuning attempt

Version 15 instruction-tuned the native 28,864,544-parameter v14 byte transformer on **56** provenance-labelled, default-profile primitive JSON records and evaluated it on **10** source-disjoint records. The finite local run completed 1,000 steps in 352.30 seconds and reduced declared held-out byte NLL from **2.471145** to **0.096428**.

This is a narrowly measured byte-prediction result, **not** Claude-like reasoning, useful code generation, or usable BEAST guidance. The deterministic generated continuation had **0%** valid JSON, exact controller schema, default-profile compliance, and controller admission; it was rejected as `invalid_json` and never executed. The custom native byte transformer is not GGUF/Ollama compatible under the documented import path, so native checkpoint inference remains the only supported runtime and no `.gguf` exists to publish.

| v15 item | Exact observed status | Boundary and evidence |
|---|---|---|
| Native JSON instruction tuning | **Measured locally** | One finite 1,000-step CPU run over 56/10 source-disjoint local records; held-out byte NLL only. [Final verification](docs/v15-final-verification.md) |
| Structured output and controller check | **Negative result** | The one bounded deterministic continuation was invalid JSON and controller admission was 0%; no primitive or program was admitted. [JSON results](docs/v15-json-instruction-results.md) |
| GGUF and Ollama runtime | **Not supported** | The custom byte-transformer layout does not meet the documented import-path compatibility conditions; no fake export is supplied. [Feasibility audit](docs/v15-gguf-ollama-feasibility-audit.md) |

## v16 prompt-conditioned native JSON follow-up

Version 16 tested a single objective correction to the v15 JSON protocol: a
target-only loss over controller-JSON bytes while each declared holdout
instruction and input conditioned greedy decoding.  It started from the
read-only local v15 checkpoint, used the same **56 / 10** source-disjoint local
records, and stopped at its declared 1,800-second wall-clock limit after 3,248
steps.

The result remains negative.  Held-out target NLL **worsened** from
**0.2009989224** to **0.2654667787**.  Across all ten held-out prompts, valid
JSON, exact schema, and controller admission were **0%**; every candidate was
`invalid_json`, no primitive was admitted or executed, and task correctness
was not measured.  This is not evidence of prompt understanding, reasoning,
code generation, BEAST improvement, or a usable model runtime.

| v16 item | Exact observed status | Boundary and evidence |
|---|---|---|
| Prompt-conditioned target-only tuning | **Measured local negative result** | One 3,248-step finite CPU attempt over the local 56/10 split worsened held-out target NLL. [Result record](docs/v16-prompt-conditioned-json-results.md) |
| Per-prompt structured output and controller check | **Negative result** | Ten held-out prompts produced 0% valid JSON, exact schema, and admission; all were rejected as `invalid_json`. [Result record](docs/v16-prompt-conditioned-json-results.md) |
| GGUF/Ollama and general capability | **Not supported / not measured** | The runtime remains custom native PyTorch only; no conversion, service, general reasoning, coding, or benchmark claim is supplied. [v15 feasibility audit](docs/v15-gguf-ollama-feasibility-audit.md) |

## v17 source-disjoint lexical controller quality probe

Version 17 first audited why v16 could not establish a semantic result: its
records were uniformly labelled `general` and deliberately omitted the target
primitive, so byte NLL could not establish task selection. The follow-up
therefore measured a much narrower, source-backed **lexical recovery** probe:
given only an approved primitive name written with spaces, produce its existing
controller JSON. The cue was repeated immediately before the delimiter to fit
the audited 32-byte local prompt context. This is not a reasoning, coding, or
task-selection benchmark.

The corrected v15-checkpoint baseline recorded **0/10** valid JSON, exact
schema, exact target names, and controller admissions. A single finite native
candidate ran **3,396** steps to its **1,800-second** deadline and worsened
held-out target NLL from **0.1909823272** to **0.2141949013**. It again
recorded **0/10** for every structured-output, exact-name, and admission
measure; all candidates were `invalid_json` and none was admitted or executed.

| v17 item | Exact observed status | Boundary and evidence |
|---|---|---|
| Lexical controller probe | **Measured local negative result** | One 56/10 primitive-name-disjoint metadata-recovery probe; it does not measure semantic primitive selection, reasoning, coding, or BEAST improvement. [Result record](docs/v17-lexical-controller-results.md) |
| Raw structured output and controller check | **Negative result** | Raw greedy decoding had no opening-byte seed or grammar mask; baseline and candidate both produced 0/10 valid JSON, exact schema, exact target names, and admissions. [Result record](docs/v17-lexical-controller-results.md) |
| Runtime and capability boundary | **Native-only / not supported or measured** | No GGUF/Ollama artifact, parent-weight transfer, external data/weights, network call, generated-text execution, persistent worker, reasoning, coding, or benchmark claim is supplied. [Quality audit](docs/v17-native-quality-audit.md) |

## v18 local Ollama controller-form diagnostic

Version 18 separately measured a temporary local downloaded `qwen2.5-coder:1.5b` model on ten source-backed records held out from the v15 instruction-training split. Raw local decoding at `temperature=0` produced **0/10** valid JSON, required controller contracts, exact expected names, and accepted controller decisions. A separately labelled Ollama provider-side JSON Schema diagnostic produced **10/10** JSON and required-field records, but **0/10** exact expected primitive names and **0/10** records that were both exact and controller-accepted. Two responses were controller-accepted only because they named a different already registered primitive; neither passed the task-correctness gate.

| v18 item | Exact observed status | Boundary and evidence |
|---|---|---|
| Raw local instruction-tuned model output | **Measured negative result** | Ten records, one temporary local model, raw decoding; 0/10 JSON, contract, exact-name, and controller-acceptance outcomes. No generated text was executed. [Result record](docs/v18-ollama-controller-results.md) |
| Provider-constrained JSON form | **Measured form-only result; task gate failed** | Ollama JSON Schema produced 10/10 valid-form responses but 0/10 exact names and 0/10 exact-name-and-controller-accepted records. It is not raw model capability, reasoning, coding, or an evolution-assistance result. [Result record](docs/v18-ollama-controller-results.md) |
| SDK, evolution, and deployment | **Not enabled** | The exact-name-and-admission gate failed. There is no Ollama SDK guidance call, evolution integration, deployed service, persistent worker, tracked model weight, GGUF conversion of the native byte transformer, or frontier-model claim. [Result record](docs/v18-ollama-controller-results.md) |

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
| [`agnes_brain/transformer_28m.py`](agnes_brain/transformer_28m.py) | Exact 28,864,544-parameter local byte-transformer specification; no downloaded weights |
| [`reports/v14/`](reports/v14/) | Persisted finite 28.9M training, calibration, checkpoint, and post-training evaluation evidence |
| [`docs/v14-final-verification.md`](docs/v14-final-verification.md) | Exact finite-run metrics and non-capability boundaries |
| [`docs/v15-final-verification.md`](docs/v15-final-verification.md) | Exact native JSON-tuning metrics, zero-admission result, and native-only runtime boundary |
| [`docs/v16-prompt-conditioned-json-results.md`](docs/v16-prompt-conditioned-json-results.md) | Target-only prompt-conditioned follow-up, ten-prompt zero-admission result, and retained negative outcome |
| [`docs/v17-native-quality-audit.md`](docs/v17-native-quality-audit.md) | v17 failure-mode audit, narrow lexical-probe preregistration, and promotion criteria |
| [`docs/v17-lexical-controller-results.md`](docs/v17-lexical-controller-results.md) | v17 corrected-baseline comparison and zero-admission negative result |
| [`docs/v18-ollama-controller-results.md`](docs/v18-ollama-controller-results.md) | v18 local instruction-tuned raw and provider-constrained controller-form measurements |

## Development verification

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q
```

The exact collected/passed count is recorded for each release verification. The v14 verification passed **1,765 collected cases** in 100.40 seconds; the v15 verification passed **1,772 collected cases** in 127.98 seconds; the v16 verification passed **1,774 tests** in **204.81 seconds**; and the v17 verification passed **1,777 tests** in **172.81 seconds**, each with 12 retained warnings. A parameterized collection count is not a count of distinct test functions. Do not substitute a badge or a historical count for a fresh test run.

## License

MIT. See [LICENSE](LICENSE).
