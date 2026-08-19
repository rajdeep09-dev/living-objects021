# BEAST-BRAIN Provenance and Experiment Contract

> **Status:** local research foundation. This contract does not train a model, call a teacher, download a model, make a network request, collect data, or start an agent loop.

The BEAST-BRAIN research direction requires decision trajectories rather than generic conversation text. That makes provenance part of the data model: a record must distinguish a local measured BEAST outcome from a schema fixture or a future teacher label. `living_objects.beast_brain.provenance` implements this contract using only the Python standard library and persisted local artifacts.

## Record origins

| Origin | Permitted content | Prohibited content | Verification rule |
|---|---|---|---|
| `real_beast_run` | A task, finite action vocabulary, observation, outcome, and two score references. | Teacher metadata, invented scores, unreferenced fitness numbers. | Each score points to an existing local JSON artifact, a JSON field path, and the SHA-256 digest of the exact artifact bytes. |
| `synthetic` | Schema, serialization, tokenizer, or parser fixtures labelled as synthetic. | Measured fitness before/after values and artifact references. | The record validator rejects every attached `ArtifactMeasurement`. |
| `teacher_generated` | A future proposal or explanation with model, version, and prompt-template identifiers. | Measured BEAST fitness values until an independent local execution produces them. | The validator requires complete teacher metadata and rejects artifact references and fitness measurements. |

This division follows the research brief’s requirement that synthetic examples be labelled and that real fitness be copied only from actual BEAST execution. It avoids treating a teacher’s text or a convenient fixture as experimental evidence.

## Measured score reference

An `ArtifactMeasurement` has four fields: `artifact_path`, `artifact_sha256`, `field_path`, and `value`. Construction reads the artifact, extracts a finite score in the inclusive range `[0, 1]`, and stores the artifact digest. Verification rereads the bytes, checks the digest first, re-extracts the field, and checks equality with the recorded score. A changed, missing, malformed, or mismatched artifact fails closed.

The initial regression uses the persisted v11 Manhattan artifact only as a local provenance fixture. It does not create a new performance claim; it proves that the contract can bind to an already recorded `training_fitness` or held-out `fresh.correctness` field.

## Preregistered comparisons

`ExperimentPlan` is the minimal comparison protocol for later BEAST-versus-BEAST-BRAIN work. It fixes the experiment ID, task, distinct non-negative seeds, generation budget, population size, and the two condition labels before results exist. `write_new()` performs an exclusive local create with owner-only permissions and refuses overwrite. `ExperimentResult` accepts only a planned seed and a verified artifact-backed primary score.

| Contract condition | Why it exists |
|---|---|
| Baseline and assisted labels differ. | Prevents comparing a condition with itself under two names. |
| Seeds are fixed and unique. | Stops post-hoc seed selection from being represented as a planned comparison. |
| A result seed must appear in the plan. | Keeps the reported set aligned with the original budget. |
| Scores are artifact-backed. | Prevents manually typed “improvements.” |
| Plans are create-once. | Preserves the distinction between preregistration and a rewritten result plan. |

## Local collection foundation

`living_objects.beast_brain.collectors` converts three existing local sources into canonical JSON-ready cards. It does not call a model, execute a champion, score a population, contact a service, or write a running dataset unless the caller explicitly gives it a previously unused destination path.

| Collector | Source | Output | Fail-closed rule |
|---|---|---|---|
| `collect_primitive_cards` | The declared primitive approval profile. | Primitive name, type signature, tier, execution environment, and approved profiles. | Refuses a primitive that declares side effects, network, or filesystem access. |
| `collect_evaluator_case_cards` | One approved local evaluator and a fixed seed. | Deterministic input/expected-output cases with evaluator identity and case index. | Reuses the existing evaluator approval gate and does not evaluate any candidate program. |
| `collect_champion_card` | One persisted SDK artifact. | Champion source audit, primitive lineage, separately named training/fresh score references, and the recorded execution boundary. | Requires zero recorded network/LLM calls and `generated_source_executed: false`; it does not pretend the two scores are an action trajectory. |
| `write_jsonl_new` | Valid cards supplied by the caller. | Canonically encoded, owner-only JSONL. | Refuses empty input, altered record IDs, duplicate IDs, and overwriting an existing dataset. |

The first collector run should remain deliberately small and reviewable. A larger corpus is an empirical deliverable, not a number to predeclare as already complete. Every card has a content-derived record ID, so a later normalizer or trainer can retain source lineage rather than flattening it into untraceable text.

## Deliberate exclusions

The contracts do not select primitives, execute a model, mutate an organism, persist a long-running queue, fetch a URL, handle a credential, or write to an external service. Those are later capabilities subject to the v12 operational authorization gate and separate evidence. The next implementation step is a safe local collector that can normalize existing artifacts into these records; a CPU smoke model follows only after that collector and its tests are complete.
