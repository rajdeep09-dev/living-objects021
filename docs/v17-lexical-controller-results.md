# v17 lexical controller quality result

## Status

**Observed negative result.** This release tested whether the native 28.9M
byte transformer could recover an approved primitive name and produce the
corresponding controller JSON on a narrow, source-disjoint lexical probe. It
did not meet any preregistered promotion criterion.

The probe is intentionally not represented as general reasoning, task
selection, code generation, or BEAST benchmark improvement. It exposes only a
primitive name written with spaces (`candidate_name_words`) and requires the
existing controller JSON for that primitive. It does not ask the model to infer
which primitive solves a task.

## Data and evaluation contract

| Item | Declared value |
|---|---:|
| Source | Approved checked-in primitive metadata only |
| Train / holdout | 56 / 10 primitive-name-disjoint records |
| Cue | `candidate_name_words`, repeated immediately before `controller_json:` so it remains in the audited 32-byte prompt context |
| Decoder | Raw greedy prompt-conditioned bytes, 256-byte cap, no opening-byte seed, no grammar mask |
| Held-out measures | Valid JSON, exact controller schema, exact target primitive name, controller admission |
| Generated-text handling | Digests only; no generated text persisted, admitted, or executed |

The initial diagnostic at
`reports/v17/v15-baseline-lexical-controller/` is retained but is not the
scored comparator because the cue was not guaranteed to be in the short local
prompt window. The corrected baseline and candidate below use the same
tail-cue serialization.

## Corrected baseline and finite candidate

The corrected no-training baseline loaded the read-only v15 native checkpoint
and recorded a held-out target NLL of **0.1909823272**. It produced **0/10**
valid JSON, exact schema, exact target names, and controller admissions.

The one finite candidate started from that same v15 checkpoint, trained on the
56 declared rows, and stopped at its **1,800-second** deadline after
**3,396/6,000** steps. Its held-out target NLL **worsened** from
**0.1909823272** to **0.2141949013**. On the ten source-disjoint prompts, it
again produced **0/10** valid JSON, exact schema, exact target names, and
controller admissions. Every raw candidate was rejected as `invalid_json`.

| Measure | Corrected baseline | Finite candidate | Promotion threshold |
|---|---:|---:|---:|
| Held-out target NLL | 0.1909823272 | 0.2141949013 | Candidate must not worsen |
| Valid JSON | 0/10 | 0/10 | Reported separately; no syntax repair allowed |
| Exact controller schema | 0/10 | 0/10 | Reported separately |
| Exact target primitive name | 0/10 | 0/10 | At least 4/10 and above baseline |
| Controller admission | 0/10 | 0/10 | At least 4/10 and above baseline |

## Interpretation and boundary

The candidate failed its exact-name, controller-admission, and NLL gates. No
guidance was admitted to the evolutionary system; no primitive registry,
grammar, evaluator, or source was changed; and no BEAST benchmark was rerun.
The result therefore provides no evidence of useful name recovery, prompt
understanding, semantic task selection, reasoning, coding, or general
capability.

The experiment used only local native PyTorch checkpoints and checked-in
source-labelled records. It made zero network calls, downloaded no data or
weights, did not start a persistent worker, did not execute generated text,
and did not create a GGUF/Ollama artifact. Its binary checkpoints remain
excluded from Git history.

## Evidence

- Preregistration and failure-mode audit:
  [`v17-native-quality-audit.md`](v17-native-quality-audit.md)
- Source-backed benchmark contract:
  [`agnes_brain/lexical_controller_data.py`](../agnes_brain/lexical_controller_data.py)
- Corrected baseline artifact:
  [`reports/v17/v15-baseline-lexical-controller-tailcue/run.json`](../reports/v17/v15-baseline-lexical-controller-tailcue/run.json)
- Candidate artifact:
  [`reports/v17/lexical-controller-tailcue-tuning/run.json`](../reports/v17/lexical-controller-tailcue-tuning/run.json)

Any future claim requires a new, independently rerun task-specific evaluation
and may not treat constrained syntax or this lexical probe as evidence of
reasoning or coding ability.

## Verification

Focused lexical-data, raw-decoder, and masked-loss regressions passed **13**
tests. The complete engine suite then passed **1,777** tests in **172.81
seconds**, with 12 retained warnings. The test count is a release verification
record, not a model-quality or capability metric.
