# BEAST v13 and BEAST-BRAIN Architecture Audit

> **Audit date:** 2026-08-19
>
> **Inputs reconciled:** `docs/BEAST_UPDATE_v13.md` is the v13 implementation mandate; `Writing.docx` is an additional BEAST-BRAIN research direction, not a replacement.
>
> **Baseline:** the v12 engine release provides local containment reporting, primitive governance, evaluator approval gates, a tamper-evident local audit trail, fixed-name patterns, and a recorded 1,720-case verification run. It does **not** provide a network-enabled organism, a lead-data store, an always-on worker, cloud-model access, PyPI publication, a public observatory, or an arXiv submission.

## Decision

The two documents are compatible only when v13 is treated as a **research roadmap**, rather than a claim that every requested integration is ready to activate. The BEAST-BRAIN document makes the needed adjustment: the research target is not a 1B model that competes with frontier systems at general intelligence. It is a progressively validated, approximately 28.9M-parameter *specialized controller* whose value is measured by whether it improves bounded BEAST search under objective evaluation.

The first implementation target is therefore a much smaller CPU smoke experiment. It must prove an end-to-end local path—dataset record, tokenizer, bounded training, checkpoint, reload, and deterministic generation—before any parameter-count, routing, distillation, memory, or self-improvement claim. A failed or neutral comparison remains a valid result and must be retained.

## Reconciled architecture

| Layer | Reconciled responsibility | Evidence requirement | Current disposition |
|---|---|---|---|
| **Artifact dataset** | Transform existing local GP primitives, evaluator cases, and persisted champions into provenance-labelled records. | Every record identifies `real_beast_run`, `synthetic`, or `teacher_generated`; real fitness is copied from persisted execution artifacts only. | **Local and first.** |
| **Tiny-model smoke path** | Learn a narrow sequence task from a bounded local dataset, then save, reload, and generate deterministically. | Reproducible seed, checkpoint hash, reload equality test, generation contract, CPU/memory measurement. | **Local and second.** |
| **Controller adapter** | Propose from a finite, approved action vocabulary for a declared BEAST task. The GP engine and evaluator remain the decision authority. | Candidate rejection, primitive-profile validation, fresh-holdout evaluation, and no capability expansion. | **Local after smoke path.** |
| **Experiment ledger** | Record configuration, provenance, baseline, assisted result, resource use, and negative outcomes. | Preregistered budget and immutable result record. | **Local after adapter.** |
| **External-model teacher** | Optionally create teacher-labelled records or evaluate a local model. | Separate user authorization, secret configuration, cost disclosure, output provenance, and verification. | **Gated.** |
| **Internet/data layer** | Fetch domain-approved public content through a controlled runtime. | Every prerequisite in `docs/v12-operational-authorization-gate.md`, including lawful purpose, source policy, allowlist, request auditing, quotas, and a test server. | **Gated; not represented as a GP primitive.** |
| **Autonomous loop** | Schedule bounded goal evaluation over a durable queue. | Owner authorization, durable runtime, kill switch, cost budget, checkpoint restore, telemetry, incident runbook, and deployment decision. | **Gated; no background thread or scheduler.** |

## v13 mandate disposition

| v13 area | Reconciled scope | Classification | Required treatment |
|---|---|---|---|
| A1 local dataset layout and collectors | Keep the collection idea, but source only checked-in code and existing local artifacts. Do not require 50 or 500 records as a success claim until the actual corpus exists. | **Locally repairable.** | Build contracts first; collectors must skip unsupported/disabled evaluators and preserve provenance. |
| A1.05 explanations via a cloud API | The BEAST-BRAIN document allows teacher examples, but requires explicit teacher metadata and verification. | **Credential and external-call gated.** | Do not call a cloud model or add a secret without a separate authorization and configured credential. |
| A2/A4 Ollama installation, pulls, and fine-tuning | A local-client interface can be mock-tested, but installing a runtime or downloading model weights requires external network activity; a 1B model is also contrary to the newer 2 GB research direction. | **Runtime/resource gated.** | Do not install or pull models in this release. Start with a repository-contained CPU smoke model; reassess a local pretrained model only after a resource measurement. |
| B1–B3 network sandbox and lead evaluator | The design requests real web fetching, contact extraction, and a 30-company lead corpus. | **Privacy, network, and data-authorisation gated.** | Preserve the v12 no-network/no-lead boundary. Mock-only protocol tests may be considered later, but no outbound primitive, scraping, collection, enrichment, or contact dataset is activated. |
| C1 HumanEval | Downloading the corpus and running a benchmark can be valuable, but it needs a source/license review, preregistration, and no generated expected outputs from an unverified teacher. | **External-source gated.** | No download or result claim until source approval and benchmark protocol are committed. |
| C2 lead benchmark | It evaluates real company and contact fields. | **Prohibited pending lawful dataset authorization.** | Do not create, infer, or scrape the proposed 30 entries. |
| C3 freelancing-board tasks and cloud-generated tests | It requires public-site collection and a cloud model. | **External-source and credential gated.** | Use only owner-supplied or clearly licensed local tasks after a separate protocol review. |
| D production fixes | Some requested fixes overlap current code: SDK result aliases and persisted-artifact reproduction already exist; JWT/operator authentication and route limiting already protect the current API. Replacing bounded inline execution with an in-memory async job queue would create uncheckpointed background work. | **Audit first; narrow repairs only.** | Add a defect only when a focused regression reproduces it. Preserve the inline-generation cap; do not substitute `ThreadPoolExecutor` timeout for a true termination boundary. |
| E PyPI publication | A local wheel can be built and verified without publication; upload is an external action. | **Partly local; publication gated.** | Package verification may be considered after the local research foundation; do not upload or claim PyPI availability. |
| F public observatory deployment | Local container/smoke work is distinct from a public URL. | **Deployment gated.** | Retain the `NOT_DEPLOYED` observatory disclosure until the owner makes an explicit hosting decision. |
| G external review and arXiv | Requires a real reviewer and an owner-controlled external submission account. | **Human/external-action gated.** | Do not fabricate review, submit, or claim an identifier. |
| H autonomous agent | A 60-second background loop is persistent autonomy even if its actions are initially bounded. | **Persistent-runtime and authorization gated.** | Do not start a background loop. A future controller experiment stays caller-invoked and resource-bounded. |
| I mocked integration | A mock-only integration can eventually verify interfaces, but it must not imply activated network or LLM capabilities. | **Local after foundation contracts.** | Name mocks explicitly and assert the no-network/no-side-effect boundary. |

## Safety and provenance invariants

The following invariants are binding for the first BEAST-BRAIN experiments.

1. A record with measured `fitness_before` or `fitness_after` must cite a persisted local BEAST artifact or an executed experiment identifier. The pipeline must reject invented numeric measurements.
2. Synthetic records are allowed only when labelled `synthetic` and may test serialization, tokenization, or schema behavior. They cannot support a claim about BEAST performance.
3. Teacher-generated records, if later authorized, must carry the teacher model, version, prompt template identifier, timestamp, verification state, and an explicit `teacher_generated` provenance label.
4. The controller may choose only from a finite, reviewed action vocabulary. It cannot introduce a primitive, evaluator, network operation, filesystem operation, subprocess, credential, or side effect by suggestion alone.
5. The local GP evaluator remains the objective scorer. A model explanation, proposal, or generated test case is not accepted as ground truth without independent validation.
6. Every baseline-versus-assisted comparison is preregistered with task, seeds, population size, generation budget, scoring split, hardware facts, and stopping criteria. Report all runs, including failure and no-improvement outcomes.

## Experimental sequence

| Order | Experiment | Success condition | Non-claim retained |
|---|---|---|---|
| 0 | Dataset and experiment schema | Provenance and measured-value rejection tests pass. | No model has been trained. |
| 1 | CPU smoke model | A small local model/tokenizer trains on a bounded corpus, checkpoint reloads, and deterministic generation matches its contract. | It is not a 28.9M model, a general LLM, or evidence of BEAST improvement. |
| 2 | Bounded controller adapter | A finite model proposal is independently validated and cannot expand the approved primitive profile. | A proposal is not automatically useful. |
| 3 | Baseline comparison | A preregistered local benchmark reports both baseline and assisted outcomes over fixed seeds. | One benchmark cannot establish general intelligence or superiority to external systems. |
| 4 | Scale/routing/distillation decision | Resource and result records justify—or reject—the next research increment. | No 28.9M, router, memory, code-execution, or feedback-training claim is made early. |

## Resource decision

The supplied research direction identifies an approximately 2 GB machine. That makes its stated usage—dataset preparation, lightweight experiments, local evaluation, and experiment tracking—appropriate for the first phases. It is not evidence that a 1B local model can be trained or reliably served there. The project will therefore measure the small smoke experiment before recommending any model download, local runtime, GPU workflow, persistent host, or external service.

## Explicitly inactive capabilities

This audit does **not** authorize or activate outbound requests, website scraping, lead data, contact enrichment, external-model API calls, model download, Ollama installation, a persistent agent, deployment, PyPI upload, arXiv submission, or a HumanEval/Claude/lead-comparison result. The v12 operational authorization gate remains in force.

## Next approved implementation step

Implement the **provenance-preserving dataset and experiment contracts**. They are local, testable, useful to both documents, and establish the evidence needed before a small-model smoke test can be meaningful.
