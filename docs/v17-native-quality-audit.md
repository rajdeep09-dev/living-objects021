# v17 Native Quality Gate: Failure-Mode Audit and Preregistered Follow-up

**Status:** Design and audit record. This document does not report a successful
model run. It records the evidence threshold required before another finite
native training attempt is permitted.

## Why v16 is not a quality milestone

The released v16 protocol did the right safety-critical things: it kept the
custom 28,864,544-parameter byte transformer local, supplied no network or
external data, executed no generated text, and sent every candidate through
the fail-closed controller. Its measured result was still negative: the
source-disjoint held-out target NLL worsened from `0.2009989224` to
`0.2654667787`, while all 10 greedy generations were invalid JSON.

The follow-up audit finds a more fundamental experimental limitation. The
existing 66-record primitive registry is entirely labelled `general`, and each
instruction asks for one arbitrary approved primitive. The target primitive's
name is deliberately omitted from the input `existing_primitives` list. This
makes the corpus a source-disjoint **metadata reconstruction** problem, not a
task-to-primitive selection problem: it supplies neither an objective task
criterion nor a ground-truth utility preference among the admitted primitives.
Consequently, training longer on the same format cannot substantiate reasoning,
coding, or BEAST-improvement claims.

| Observed v16 failure mode | Consequence | v17 control |
|---|---|---|
| All registry task labels are `general` | No task-specific selection signal | Do not call exact JSON recovery “semantic selection.” |
| Target name is absent from each prompt | The target is an arbitrary omitted registry item | Present only the source-backed target name in a separately labelled lexical-recovery probe. |
| At most 32 prompt bytes appear before supervised target windows | Long registry input is mostly outside the local supervised context | Use a short, declared prompt; report its byte length. |
| Greedy output collapsed to one 513-byte invalid string | Decoder cannot establish structured-output reliability | Measure raw completion, JSON parse, exact schema, admission, and exact name separately. |

## Preregistered lexical controller benchmark

The v17 probe may be created only from the checked-in primitive registry. For
each source record it presents the target primitive name as a deterministic
lowercase word sequence (for example, `remove punctuation` for
`remove_punctuation`) and asks for the exact source controller JSON. The source
metadata supplies the target; no model-generated explanation, outside dataset,
or invented task label is allowed. The split remains source-disjoint.

This probe tests a deliberately narrow capability: **can the local byte model
reconstruct registered controller metadata from a name-like lexical cue?** It
does not test task planning, evolution improvement, arbitrary code synthesis,
or general reasoning. Presenting the name removes the prior omitted-target
ambiguity but does not turn JSON validity into semantic correctness.

## Required evaluation and stop rule

The baseline and any candidate run must use the same held-out rows, greedy
unconstrained byte decoding, and bounded output limit. No grammar mask,
schema-filling template, retry repair, or output execution may be used. Each
held-out completion must be checked by the existing controller; its text stays
untrusted regardless of parse status.

| Metric | Baseline | Candidate success threshold |
|---|---:|---:|
| Exact held-out `name` recovery | Measured before tuning | At least 4 of 10 and strictly above baseline |
| Controller admission | Measured before tuning | At least 4 of 10 and strictly above baseline |
| Valid JSON and exact schema | Measured before tuning | Reported separately; neither alone constitutes success |
| Held-out target NLL | Measured before tuning | Must not worsen |
| Execution, network, downloads | `false`, `0`, `false` | Must remain unchanged |

One finite run can only be an exploratory measurement. A result meeting every
threshold still requires an independently seeded rerun before it is described
as a reproducible narrow capability. A failed run is a retained negative
result, not a reason to weaken the checks.

### Protocol correction before the scored baseline

The first no-training v17 diagnostic was retained at
`reports/v17/v15-baseline-lexical-controller/`. It confirmed the raw v15 model
produced 0/10 valid JSON, exact names, and controller admissions under a
256-byte raw-greedy limit. It is **not** the preregistered comparator because
the runner audit subsequently found that its 32-byte local prompt window did
not necessarily include the name cue. The corrected protocol repeats the same
declared `candidate_name_words` immediately before `controller_json:`. This
does not reveal controller metadata or add a syntax constraint; it makes the
narrow name-conditioned probe test the cue it claims to measure. A fresh
baseline and any candidate run must use this corrected serialization.

## Research basis

Grammar-constrained decoding can guarantee output-form compliance, but it is a
different intervention from learning and must be evaluated separately from
downstream accuracy. The v17 protocol therefore forbids grammar masking and
keeps exact name recovery and controller admission as independent metrics.[1]
Recent logical-parsing work likewise distinguishes syntactic correctness from
semantic errors that grammar constraints cannot capture.[2]

## References

[1] S. Geng et al., [*Generating Structured Outputs from Language Models: Benchmark and Studies*](https://arxiv.org/html/2501.10868v1), 2025.

[2] F. Raspanti, T. Ozcelebi, and M. Holenderski, [*Grammar-Constrained Decoding Makes Large Language Models Better Logical Parsers*](https://aclanthology.org/2025.acl-industry.34.pdf), ACL Industry Track, 2025.
