# BEAST v10 Final Verification Record

> **Release status:** Local verification is complete. This record does not represent an arXiv submission, PyPI upload, public Observatory deployment, continuous worker, or 100,000-generation campaign execution.

## Engine verification

On 2026-08-17, the repository root completed the following full engine command:

```bash
cd /home/ubuntu/living-objects021
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q
```

The result was **1,731 passed** in 99.95 seconds. The count is the repository’s collected pytest-case total; it includes parameterized cases and must not be presented as the number of distinct test functions. The run emitted 12 non-failing warnings, including FastAPI test-client deprecation, default-secret warnings in deliberately isolated contract tests, and legacy tests that return booleans. No test failed.

| Verification surface | Result | Evidence |
|---|---|---|
| Engine suite | **1,731 passed** | Full command and result above; collection inventory in `docs/v9-test-inventory.json` |
| SDK contract | Accessors `EvolutionResult.fitness` and `EvolutionResult.source_code` pass focused regressions | `living_objects/test_sdk.py` |
| Package metadata | Version `0.3.0`, zero mandatory runtime dependencies, and the `production` extra pass focused regressions | `living_objects/test_v10_packaging.py` |
| Python matrix | Local wheel smoke-tested on Python 3.10.20, 3.11.15, and 3.12.3 | `docs/v10-package-release.md` |
| arXiv source bundle | Source-package contract tests pass and `main.tex` compiled locally for review | `living_objects/test_v10_arxiv_package.py`, `docs/v10-arxiv-submission-package/REVIEW_NOTES.md` |
| Campaign gate | Authorization, pilot, restore, artifact, and no-launch wording contracts pass | `living_objects/test_v10_campaign_gate.py` |
| Observatory | 13 test files / 21 tests passed, production build passed, and desktop/mobile disclosure renders were checked | `docs/v10-observatory-deployment-package.md` |

## v10 corrections confirmed

The deterministic Observatory compiler was re-run after the SDK version change. The committed `docs/v9-observatory-evidence.json` now matches `scripts/build_v9_observatory_evidence.py` and records SDK version `0.3.0`. This repairs the only failure observed during final verification; the subsequent complete engine run passed.

The public README and claims registry now distinguish the local v10 package and manuscript preparation work from external publishing, deployment, and experiment execution. The v8 clean-sorting `0/5` negative result and historical sorting retractions remain visible.

## External-action ledger

| Action | Status at v10 verification | Required condition before status can change |
|---|---|---|
| Upload `living_objects` 0.3.0 to PyPI | **Not done** | Publishing owner credentials and explicit upload confirmation, followed by an independently checked project/version URL. |
| Submit manuscript to arXiv | **Not done** | A human submitting author’s account/category choice and explicit authorization, followed by the actual arXiv identifier. |
| Publish Observatory / assign public URL | **Not done** | Owner publication decision, domain assignment, post-publication access/authentication smoke test, and documented rollback/health evidence. |
| Configure continuous evolution worker | **Not done** | An owner-approved worker design, persistent host, resource limits, health checks, and operational runbook. |
| Start the five-seed 100,000-generation campaign | **Not done** | Owner-selected persistent compute, explicit resource/budget/recovery authorization, successful 10,000-generation pilot plus restore drill, and a second full-campaign approval. |

## Release handoff

The remaining v10 delivery actions are repository and project-state actions: preserve the tested Observatory source in a checkpoint and push the verified engine changes to the configured repository. Neither action changes the external-action ledger above.
