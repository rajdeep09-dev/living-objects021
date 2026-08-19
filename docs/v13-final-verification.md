# BEAST v13 Final Verification Record

**Verification date:** 2026-08-19
**Release scope:** provenance-preserving local training-data foundations, a bounded CPU byte-bigram smoke experiment, an approved-primitive controller admission filter, and a preregistered clean-sorting negative control.

> **Result:** this release adds tested local research infrastructure. It does **not** demonstrate a trained language model, model-assisted evolution improvement, general program synthesis, internet-enabled organisms, or autonomous operation.

## Integrated regression result

The complete repository suite was run with an explicit local test environment:

```bash
APP_ENV=test JWT_SECRET='v13-local-test-only-signing-value-0123456789abcdef' pytest -q
```

| Check | Observed result | Boundary |
|---|---:|---|
| Full engine suite | **1,756 passed** in **99.00 s** | Parameterized collected-case count, not a scientific-performance metric or a count of distinct test functions. |
| Retained warnings | **7** | One FastAPI/TestClient deprecation warning and six legacy `pytest` return-value warnings. |
| v13 local-data contracts | Passed | Provenance, artifact-digest, create-once JSONL, and source-label tests ran locally only. |
| v13 CPU smoke model | Passed | A custom byte-bigram table, not a downloaded, pre-trained, or fine-tuned LLM. |
| v13 controller gate | Passed | Untrusted text is parsed as data and may resolve only existing, approved primitives under an explicit profile. |
| v13 negative control | Preserved | Rejected CPU preview produced two identical frozen-grammar arms; no assistance claim is eligible. |

The shell inherited a production `APP_ENV`, which correctly caused the production API configuration to reject an absent production signing secret and an HTTP localhost CORS origin. The verification command therefore set `APP_ENV=test` and an ephemeral test-only signing value. No production configuration or credential was changed.

## Materialized local artifacts

| Artifact | Exact content | Claim boundary |
|---|---|---|
| [`agnes_brain/training_data/dataset.jsonl`](../agnes_brain/training_data/dataset.jsonl) | 78 complete records: 69 primitive records and 9 evaluator-pattern records | Local metadata and deterministic examples only; it has no real-world lead, browser, or cloud source. |
| [`agnes_brain/training_data/augmented_dataset.jsonl`](../agnes_brain/training_data/augmented_dataset.jsonl) | 513 separate records: 78 base, 345 explicitly synthetic templates, and 90 zero-candidate evaluator reruns | Synthetic variations are not new measured evolution runs. |
| [`reports/v13/cpu-smoke/`](../reports/v13/cpu-smoke/) | 66 train / 12 holdout records; held-out NLL 2.176272 against 5.545177 uniform-byte baseline | Text-compression smoke metric only; not a language-model capability benchmark. |
| [`reports/v13/clean-sorting-negative-control/`](../reports/v13/clean-sorting-negative-control/) | Baseline and rejected-guidance arms both at 0.58 held-out correctness | A neutral result; the invalid JSON preview was rejected before grammar admission. |

## Gated work remains inactive

The release introduces **no** Ollama service, model download, cloud inference, network primitive, web access, lead or personal-data collection, persistent worker, scheduler, external side effect, public deployment, PyPI upload, or arXiv submission. Those items remain subject to the separate [v12 operational authorization gate](v12-operational-authorization-gate.md) and the v13 [architecture audit](v13-beast-brain-architecture-audit.md).

The authenticated observatory evidence synchronization is checkpointed separately as `manus-webdev://49dc40de`; it remains a managed development preview, not a public service.
