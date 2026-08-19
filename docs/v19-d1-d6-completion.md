# BEAST v19 D1–D6 guarded distillation completion record

**Status:** implementation and local evidence capture complete; no student fine-tuning, adapter export, GGUF conversion, binary publication, or SDK explanation call was admitted.  This record supersedes no earlier negative result.  It adds the required D1 standalone parser report and the D2–D6 fail-closed implementation evidence.

## Measured record

| Item | Implemented contract | Measured local result | Evidence |
| --- | --- | --- | --- |
| D1 | One raw loopback completion, independently parsed with Python JSON and a snake-case name regex | The output was wrapped in Markdown fences; strict JSON parsing therefore returned **INVALID**. | `reports/v15/teacher-baseline-test.txt`; `reports/v19/d1-teacher-baseline/run.json` |
| D2 | Resumable, append-only generator with five variations per approved *training* source, source digests, model-generated/unverified tags, and no invented task label | Corrected dry run selected **56** training sources and requested **280** variations, with **0** model calls and **0** retained rows.  `teacher_generated.jsonl` was not created because no valid generated record exists. | `reports/v19/d2-teacher-generation/manifest-source-disjoint-corrected.json` |
| D3 | Dependency-optional LoRA preflight requires a local model config, non-empty corpus, matching completed D2 manifest, absent output directory, and `torch`/`transformers`/`peft`/`trl` | **Blocked**: local model config, teacher data, and completed manifest are absent; `transformers`, `peft`, and `trl` are unavailable.  No download or training started. | `reports/v19/d3-lora-preflight.json` |
| D4 | Deterministic source-disjoint evaluator measures submitted, JSON-form, schema, exact-name, controller-admission, and exact-name-and-admission separately | Empty-submission baseline: **0/10** submitted, JSON-valid, schema-valid, exact-name, controller-admitted, and task-correct. | `reports/v19/d4-student-evaluation-empty-submission-corrected.json` |
| D5 | No-op GGUF handoff preflight requires adapter, conversion tool, fully task-correct D4 report, and explicit confirmation | **Blocked**: adapter and converter absent, D4 task-correctness did not pass, and no confirmation supplied.  No conversion, GGUF, network call, or release occurred. | `reports/v19/d5-gguf-handoff-preflight.json` |
| D6 | Optional `AgnesBrainClient` explanation facade is checked only after champion selection and only when the raw task-correct admission gate passes | Existing v18 raw task-correct admission is **0/10**, so the client remains unavailable and makes no request.  Tests verify it cannot affect selection, mutation, fitness, execution, or the primitive registry. | `agnes_brain/client.py`; `living_objects/sdk.py`; `tests/test_v19_d1_d6.py` |

> **Claim boundary:** These artifacts document guarded engineering behavior and negative admission results.  They do not show a trained student, improved controller, GGUF compatibility, coding capability, reasoning capability, or a model-mediated improvement to BEAST.

## Source-disjointness and provenance

D2 uses the existing deterministic v15 `sha256(source_record_id) modulo 5` partition and limits teacher-generation prompts to its 56 training records.  D4 independently rebuilds the complementary held-out partition and rejects any caller-declared source overlap.  A retained D2 row, if one is ever collected after an explicit run, has `model_generated: true`, `unverified_teacher_data: true`, source-record and source-file SHA-256 digests, and an explicit non-execution boundary.

The earlier `reports/v19/d2-teacher-generation/manifest.json` is retained but is superseded for source-count purposes: it was produced before the training-split restriction and listed 69 sources.  The corrected manifest is authoritative for this release.  Similarly, `reports/v19/d4-student-evaluation.json` is retained but superseded because it incorrectly counted omitted responses as JSON-valid; the corrected evaluator and corrected artifact record 0 JSON-valid responses.

## Release handoff rules

The D5 module never calls a converter.  A separate operator run may become eligible only if all of the following are true: a real locally trained adapter exists, a compatible conversion executable exists, D4 reports task-correct admission for every recorded case, and an explicit user confirmation is supplied.  Even then, the preflight is not a conversion or publication action.  Any actual external binary release requires a new, separately confirmed operation.

## Final source verification

The complete source suite was run after the D1–D6 implementation, corrected D2/D4 evidence, and completion record: **1,793 passed in 175.48 seconds**, with **12 retained warnings**. The warnings are retained rather than suppressed: one Starlette TestClient deprecation, one development-default JWT warning during contract tests, and legacy tests that return boolean values rather than `None`.

## Reproduction commands

```bash
APP_ENV=test python3 -m agnes_brain.d1_teacher_baseline
APP_ENV=test python3 -m agnes_brain.distill.generate_from_teacher
APP_ENV=test python3 -m agnes_brain.distill.finetune_student --base-model-directory /path/to/local-model --teacher-data-path agnes_brain/training_data/teacher_generated.jsonl --corpus-manifest-path /path/to/completed-d2-manifest --adapter-output-directory agnes_brain/adapter_student
APP_ENV=test python3 -m agnes_brain.distill.evaluate_student --report-path reports/v19/d4-student-evaluation.json
APP_ENV=test python3 -m agnes_brain.distill.release_handoff --adapter-directory agnes_brain/adapter_student --converter-path /path/to/converter --validation-artifact /path/to/d4-report
```

The D2 command is dry-run by default.  It requires an explicit `--execute` to make bounded local loopback calls; it performs neither downloads nor execution of returned text.
