# BEAST v10 Foundation Audit

**Audit date:** 2026-08-17  
**Evidence baseline:** v9 coverage-gate release (`1,731` collected and passed pytest cases; `1,731` is a collection count, not a count of independently authored test functions)  
**Audit rule:** A mandate is complete only when its stated outcome is independently observable. Local code, a draft, or a preregistration is not treated as a deployment, publication, or completed experiment.

## User-Perspective Findings

| v10 finding | Evidence inspected | Status | Required correction or gate |
|---|---|---|---|
| `evolve()` returns an `EvolutionResult` but documented `.fitness` and `.source_code` fail | `living_objects/sdk.py` defines `champion` but no top-level compatibility properties | **Verified defect** | Add read-only compatibility accessors, retain the structured champion record, and execute documented examples in tests. |
| The reported 1,731 tests may imply 1,731 independently authored tests | `docs/v9-test-inventory.json`; parameterized contract matrices | **Verified framing risk** | Keep the exact collection result, state that it includes parameterized cases, and do not use it as a proxy for independent test-function count. |
| Observatory is not a public live service | Persisted v9 service evidence records no configured persistent worker; no deployed URL is recorded | **Verified external gap** | Build local operational packaging and status disclosure; a public URL requires an authorized deployment. |
| Paper is a real draft but has no arXiv identifier | `docs/v9-paper.md`; no submission receipt or identifier | **Verified external gap** | Prepare an arXiv-ready package and checklist; submit only through an authorized account after explicit confirmation. |
| `pip install living-objects` is not a verified public installation | `pyproject.toml` defines package metadata but no PyPI publication record is committed | **Verified external gap** | Build and test local distribution artifacts; publishing requires a package-owner account and explicit confirmation. |
| Manhattan result is real | Persisted five-seed v8 trial artifacts and discovery log | **Measured result retained** | Keep the result limited to the stated Manhattan task, evaluator, seeds, and held-out checks. |
| Clean sorting result is a real negative result | `reports/v8/clean-sorting/summary.json` | **Measured negative retained** | Keep the 0/5 clean-sorting result visible; do not treat the curriculum as a demonstrated general sorting solution. |
| Five-stage clean sorting curriculum is implemented | `evolution/v9_sorting_curriculum.py` and regressions | **Implemented, unmeasured at scale** | Launch only after a persistent-compute decision and retain any result, positive or negative. |
| Signed discovery exchange is federation | Local-only signing and verification modules | **Not demonstrated as multi-installation federation** | Describe it as a local signed-exchange MVP until two independently operated installations exchange and verify an artifact. |
| v9 API code is a served production API | `production/api/v9/routes.py` and local regressions | **Code tested locally, not deployed** | Preserve the bounded, no-worker API wording; live serving requires deployment and runtime monitoring. |

## Final-Mandate Classification

| v10 mandate | Classification | What can be completed locally now | What still needs authorization or external infrastructure |
|---|---|---|---|
| Submit Manhattan paper to arXiv | External publication gate | Prepare a reviewable manuscript package, source bundle, figure, and submission checklist | arXiv account access and explicit confirmation before upload/submit; arXiv identifier afterward |
| Publish SDK to PyPI | External publication gate | Repair public API, build sdist/wheel, inspect artifacts, test isolated installation where supported | Package-owner credentials and explicit confirmation before upload; public index verification afterward |
| Deploy a public Observatory URL | Deployment gate | Produce a locally verified real-data build and explicit operational-status panel | User-approved hosting/publish action and a supported runtime for any live evolution stream |
| Launch five-seed 100,000-generation sorting campaign | Persistent-compute gate | Retain preregistration, resumable launcher, checkpoint semantics, and milestone schema | Hardware/runtime authorization and an operating decision that survives the campaign duration |
| Update README with four real links | Dependent release gate | Maintain exact local status and placeholders only | Actual arXiv ID, PyPI URL, public Observatory URL, and started/completed campaign status |

## v10 Claim Boundary

> As of this audit, BEAST is a locally reproducible research repository with measured Manhattan and clean-sorting results, an installable-from-source SDK, and a browser observatory codebase. It is **not** an arXiv-published paper, a PyPI-published package, a public live Observatory, a completed 100,000-generation campaign, or a demonstrated multi-installation federation.

## Acceptance Criteria for a v10 Release

1. The documented `EvolutionResult` top-level compatibility fields execute successfully and are covered by regression tests.
2. Package artifacts build reproducibly; any Python versions unavailable in this environment are labeled unverified rather than inferred.
3. The public README and claims registry distinguish collected test cases from independent test functions.
4. The Observatory visibly discloses whether it has a public deployment and whether a continuous evolution worker is configured.
5. arXiv submission, PyPI publication, public deployment, and the 100,000-generation campaign remain unchecked until independently observable evidence exists.
