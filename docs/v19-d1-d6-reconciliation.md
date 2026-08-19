# V19 — V15 D1–D6 Distillation Checklist Reconciliation

## Purpose

This record maps the repository's current **V15 D1–D6** pivot checklist to the
measured V18 local Ollama work. It is a scope and gate document, not evidence
that a distilled student exists.

## Starting evidence

The temporary local Ollama runtime has `qwen2.5-coder:1.5b` installed. V18
measured ten source-backed controller prompts in two modes:

| Mode | Valid JSON | Required fields | Exact expected primitive name | Exact-name-and-controller-admitted |
|---|---:|---:|---:|---:|
| Raw model completion | 0 / 10 | 0 / 10 | 0 / 10 | 0 / 10 |
| Ollama JSON Schema parameter | 10 / 10 | 10 / 10 | 0 / 10 | 0 / 10 |

The provider-constrained result establishes only that the local provider can
enforce response **form**. It does not establish task-correct primitive
selection, model reasoning, safe executable code, or a right to alter the GP
search process.

## Requirement mapping

| Checklist item | Current status | V19 action and admission rule |
|---|---|---|
| D1 — teacher installation and single raw JSON test | Model is installed, but the exact D1 prompt has not yet been captured in its requested standalone artifact. | Run one raw local completion through an independent JSON and snake-case parser. Record `VALID:` or `INVALID` verbatim; do not use a provider format parameter. |
| D2 — teacher-generated data | Unmet. The D1 plan's invented task names are not provenance-backed, and syntax-valid teacher text is not automatically correct training supervision. | Implement a resumable, source-backed generator. It may write only schema-valid responses tagged as unverified teacher data with source digests. It must exclude invented task labels and make no minimum-count claim before execution. |
| D3 — LoRA student | Unmet. No validated training corpus, adapter, or reproducible local training configuration exists. | Implement a validate-first, dependency-optional LoRA entrypoint. It must remain a dry run unless an explicit corpus manifest and local model path are supplied. |
| D4 — student evaluation | Unmet. No student adapter exists. | Implement a source-disjoint evaluator whose task-correctness metric is deterministic and separate from JSON parsing and schema validity. |
| D5 — GGUF release | Blocked. There is no verified adapter, merged student, conversion toolchain, or evaluated GGUF. | Implement only the guarded validation/handoff. Creating a GitHub Release or publishing a binary requires a successful trained-student evaluation and a separate explicit confirmation. |
| D6 — SDK integration | Blocked by V18's 0 / 10 task-correct admission outcome. | Implement no model-to-evolution path. At most, add an optional explanation-only interface after a measured task-correct admission gate is met. It cannot affect selection, mutation, fitness, or program execution. |

## V19 success criteria

1. D1 produces a standalone raw-result artifact with an independently parsed
   validity status.
2. D2–D5 are importable and tested without network download, model training,
   binary generation, or release publication.
3. A training run is permitted only when a versioned data manifest, local model
   path, and explicit run parameters are supplied.
4. No D6 integration is enabled unless the independently measured
   task-correct-and-controller-admitted rate is positive on a source-disjoint
   evaluation and passes its preregistered threshold.

## Explicit non-claims

V19 does not claim that the teacher is reliable for primitive selection, that a
student is trained, that a GGUF exists, that a GitHub Release exists, or that
Agnes-Brain approaches frontier-model reasoning or coding performance.
