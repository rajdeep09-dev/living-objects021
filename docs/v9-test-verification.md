# V9 Test Verification Record

**Recorded date:** 2026-08-17
**Repository:** `rajdeep09-dev/living-objects021`
**Test environment:** `APP_ENV=dev JWT_SECRET='v7-local-test-secret'`

> **Result:** The current repository collected **1,731 tests** and the complete suite passed **1,731 tests** in **101.93 seconds**. This is an observed numerical coverage-gate result; it does not establish a new scientific benchmark result, launch a long-running campaign, or convert any v8 retraction or negative result into a success claim.

## Measured status

| Measure | v9 audit baseline | Latest observed value | Change | Target status |
|---|---:|---:|---:|---|
| Collected tests | 473 before the coverage release | 1,731 | +1,258 | 731 above 1,000 |
| Passed tests | 473 at the v9 foundation release | 1,731 | +1,258 | 731 above 1,000 |
| Full-suite run time | 97.58 seconds | 101.93 seconds | +4.35 seconds | Informational only |
| Failures | 0 | 0 | 0 | Pass |

The numerical delta is the difference between the v9 audit baseline and the current collection run. It is not a quality score and does not imply that adding tests alone establishes a new scientific result.

## Commands and captured outcomes

```bash
# Test inventory
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest --collect-only -q
# 1,731 tests collected in the coverage-release inventory

# Complete regression
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q
# 1,731 passed, 12 warnings in 101.93s
```

## v9-specific coverage added to the bounded evidence surface

| Area | Regression modules | What the tests establish | What they do not establish |
|---|---|---|---|
| Public SDK | `living_objects/test_sdk.py` | Bounded evolution, persisted audit, deterministic reproduction, isolated install, and source-only export contracts | General-purpose evolution or safe execution of exported source |
| Five-stage curriculum | `evolution/test_v9_sorting_curriculum.py` | Primitive exclusions, mastery thresholds, cultural-seed events, and exact checkpoint-state behavior | A successful 100,000-generation clean-sorting campaign |
| Signed discovery exchange | `evolution/test_v9_federation.py` | Local signature, tamper, replay, and local-evidence admission rules | A live federation, remote peer transport, or a global discovery network |
| Bounded API and CLI | `production/test_v9_api.py`, `living_objects/test_cli.py` | Validation, rate-policy boundary, bounded inline results, and console behavior | An always-on worker, deployed service, or external write action |
| Publication boundaries | `evolution/test_v9_documentation.py` | Links and wording preserve retractions, negative results, artifacts, and gates | Independent scientific replication |
| Observatory | Observed in `living-objects-platform-ui` test suite | Artifact-backed server and component contracts for the authenticated v9 panel | Public deployment or a live evolution stream |
| Typed interpreter contract matrix | `evolution/test_gp_engine_contract_matrix.py` | 311 fixed primitive-input, tree-construction, normalization, mutation, crossover, serialization, and source-audit contracts | Safety of executing exported source or a claim that all primitives belong in clean benchmark profiles |
| Objective evaluator contract matrix | `evolution/test_fitness_contract_matrix.py` | 946 fixed exact-oracle, deterministic-suite, recursive-correctness, malformed-output, context, and checkpoint-state contracts | An additional evolutionary discovery or a claim that evaluator tests replace independent reproduction |

## Warnings retained for follow-up

The full run reported 12 warnings and no test failures. The warnings include a FastAPI `TestClient` deprecation notice, several legacy tests returning booleans instead of using assertions, and insecure-default-JWT configuration warnings emitted by configuration-contract tests. These warnings do not turn into a release success claim; their cleanup is future maintenance work unless a security or framework upgrade changes their severity.

## 1,000-test target boundary

The v9 guide’s 1,000-test threshold is a **met numerical coverage gate** in this release: the declared command collected and passed 1,731 tests. The 1,258 additional cases come from fixed, separately named input-domain and contract partitions in the two modules listed above. They execute the typed interpreter and evaluator contracts directly; they are not generated score fixtures, repeated no-op assertions, or timing-based checks.

Meeting this test-count gate does **not** change the scientific status of any experiment. The clean-sorting 0/5 result remains negative, the contaminated tasks remain retracted, the 100,000-generation campaign remains unlaunched, and independent reproduction remains a separate gate.
