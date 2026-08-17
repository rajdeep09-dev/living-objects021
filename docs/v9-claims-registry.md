# BEAST Claims Registry

**Purpose.** This registry separates measured results, tested implementation surfaces, retractions, and externally gated work. It is the authoritative wording guide for repository documentation, the observatory, presentations, and any future publication.

> A feature being implemented is not evidence that its intended scientific outcome occurred. A measured result remains task-, evaluator-, configuration-, and artifact-specific.

## Status vocabulary

| Status | Meaning | Permitted language |
|---|---|---|
| **MEASURED** | A declared run or test produced persisted evidence and is reproducible under its stated contract | “Measured in the stated bounded experiment” |
| **IMPLEMENTED_TESTED** | Code and regressions exercise the contract, but no claimed research outcome follows | “Implemented and locally tested” |
| **RETRACTED** | Earlier result violated a now-explicit validity boundary | “Retracted; do not cite as discovery” |
| **NEGATIVE_RESULT** | A declared measurement did not meet its promotion criterion | “Observed negative result” |
| **GATED** | Work requires a new experiment, durable compute, publishing action, or other external authorization | “Planned only; no result or deployment claim” |

## Registry

| ID | Version | Claim | Status | Exact boundary | Evidence | Update rule |
|---|---|---|---|---|---|---|
| C-01 | v1 | Lifetime learning, Lamarckian inheritance, cultural persistence, meta-evolution, novelty accounting, and guarded behavior replacement exist as mechanism demonstrations | **IMPLEMENTED_TESTED** | These unit-level mechanisms do not establish open-ended intelligence, autonomous production operation, or general task improvement | `evolution/lamarckian.py`, `evolution/test_lamarckian.py` | Update only with new tests and an explicit evaluator-specific experiment |
| C-02 | v2 | Cumulative-culture, federation, DSL, ancestry, and multi-species modules exist | **IMPLEMENTED_TESTED** | Legacy mechanism modules are not a live distributed service or a general software civilization | `evolution/test_beast_v2.py`, `evolution/test_v2.py` | Any performance or deployment claim needs its own artifact and reproducibility command |
| C-03 | v3–v4 | Signal Loom observatory revisions provide local evidence views | **IMPLEMENTED_TESTED** | A UI/checkpoint is not a public deployment or continuously operating worker | Observatory checkpoint history and source | Update only after a user-authorized publish plus operations validation |
| C-04 | v5 | A bounded local organism workspace can persist lifecycle/checkpoint state | **IMPLEMENTED_TESTED** | Goal text maps to fixed profiles; arbitrary natural-language goals are not autonomously solved | `docs/v5-autonomous-workspace.md`, `evolution/test_v5.py` | New task domains need declared evaluators and separate evidence |
| C-05 | v6 | Typed AST GP can improve on a finite, objectively scored arithmetic task | **MEASURED** | Bounded evaluator-specific evidence; generated source is an audit artifact, not the runtime | `docs/v6-benchmark-results.md`, `evolution/test_v6_benchmarks.py` | Preserve the task, seed, evaluator, and holdout definition in any comparison |
| C-06 | v7 | Historical sorting-marathon performance showed sorting discovery | **RETRACTED** | `sort1` allowed direct success; generation-zero perfection invalidated the claim | `docs/v8-contamination-audit.md`, `docs/v8-benchmark-ledger.json` | May not be promoted; only a new clean profile with new evidence can support a sorting statement |
| C-07 | v8 | Clean sorting achieved an eligible discovery | **NEGATIVE_RESULT** | `clean-sorting-v1` completed 0/5 eligible runs at 10,000 generations; fresh correctness ranged 0.495–0.513 | `reports/v8/clean-sorting/summary.json`, `docs/v8-experiment-results.md` | Retain in every benchmark comparison; replace only with separately preregistered result data |
| C-08 | v8 | Manhattan distance has a multi-seed non-LLM compositional synthesis result | **MEASURED** | Five declared seeds; all promotion eligible; 1.000 fresh correctness on each recorded 1,000-case evaluator suite; not general synthesis or intelligence | `reports/v8/manhattan-distance/summary.json`, `docs/v8-discovery-log.json` | Any extension must publish seed-level artifacts and contamination audit before stronger wording |
| C-09 | v8 | Exact GP checkpoint restoration is supported for the tested typed-tree profiles | **MEASURED** | Covered profiles preserve primitive manifests and deterministic state; unknown primitives fail closed | `evolution/test_checkpoint_fidelity.py` | New primitive profile requires a fidelity test before claiming resume support |
| C-10 | v9 | Bounded SDK, CLI, API contracts, five-stage curriculum, and signed discovery exchange are available | **IMPLEMENTED_TESTED** | Local/repository contracts only; this is **not a deployed federation**, autonomous worker, remote transport, executed source, or long-run discovery result | `living_objects/sdk.py`, `living_objects/cli.py`, `production/api/v9/`, `evolution/test_v9_sorting_curriculum.py`, `evolution/test_v9_federation.py` | A behavior claim requires a measured experiment separate from implementation coverage |
| C-11 | v9 | Clean sorting will solve the planned five-stage 100,000-generation campaign | **GATED** | No such campaign has executed; there is no predicted success rate | `docs/v9-long-run-preregistration.md` when approved | Requires frozen preregistration, declared hardware, durable checkpoints, all seed artifacts, and retained failures |
| C-12 | v9 | BEAST is publicly deployed or has an arXiv paper | **GATED** | Preview/local testing and a manuscript draft do not constitute public deployment or submission | `docs/v9-submission-and-deployment-gates.md` | Requires explicit user authorization and external completion evidence |

## Maintenance rules

1. Every new claim must have an ID, status, exact boundary, evidence path, and update rule before it appears in a public-facing surface.
2. A test count, a UI card, or an implementation commit cannot change a **GATED**, **RETRACTED**, or **NEGATIVE_RESULT** status.
3. An experiment may change a **GATED** status only after its complete declared artifacts, including failed trials, are committed and independently rerunnable.
4. Retractions are append-only. A new clean experiment can support a new claim but cannot overwrite the historical contaminated record.
5. Generated source is an audit artifact. No registry item may imply that exported source was executed as the evolved runtime unless a separate sandboxed-execution contract and evidence exist.
