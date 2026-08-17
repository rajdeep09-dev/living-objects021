# BEAST / Living Objects

> **A bounded research system for evolving typed programs under explicit, reproducible evaluation.**

BEAST is not a general autonomous programmer, a conscious system, or a live self-improving service. It is a research codebase that tests a narrower question:

> Can a population of non-LLM typed programs improve from its initial population on a task with an objective evaluator, while the result remains inspectable and reproducible?

The current evidence answers **yes for one bounded Manhattan-distance synthesis task**, and **no result for the current clean-sorting profile**. Both outcomes are retained. See the [claims registry](docs/v9-claims-registry.md) before reusing any statement from this repository.

## What the evidence currently supports

| Topic | Measured or implemented status | Exact boundary | Primary evidence |
|---|---|---|---|
| Manhattan distance | **5/5 eligible fixed-seed runs**; fresh correctness was **1.000** on each recorded 1,000-case suite | Typed AST interpreter, fixed evaluator, population 128, up to 10,000 generations; not arbitrary program synthesis or general intelligence | [v8 results](docs/v8-experiment-results.md), [trial summary](reports/v8/manhattan-distance/summary.json) |
| Clean sorting | **0/5 eligible runs** at 10,000 generations; retained negative result | Applies only to `clean-sorting-v1`; no numerical success expectation is implied | [v8 results](docs/v8-experiment-results.md), [trial summary](reports/v8/clean-sorting/summary.json) |
| v7 sorting marathon | **Retracted** | `sort1` made generation-zero perfection possible; its score is not sorting discovery evidence | [contamination audit](docs/v8-contamination-audit.md), [benchmark ledger](docs/v8-benchmark-ledger.json) |
| v9 SDK and CLI | **Implemented and locally tested** | Bounded local workflows only; evolved source remains an audit export and is not executed as the evolved runtime | [`living_objects.sdk`](living_objects/sdk.py), [`living-objects` CLI](living_objects/cli.py) |
| Five-stage sorting curriculum | **Implemented and tested, not yet measured in the planned long campaign** | No 100,000-generation result or expected success rate has been claimed | [curriculum module](evolution/v9_sorting_curriculum.py), [research roadmap](docs/v9-advanced-research-roadmap.md) |
| Signed discovery exchange | **Local verification MVP implemented and tested** | It signs and verifies persisted evidence locally; it is not a deployed federation or transport network | [federation module](evolution/v9_federation.py) |

## Install and run bounded workflows

The package is currently a repository-installable research SDK. It is **not** represented as a published package registry release.

```bash
git clone https://github.com/rajdeep09-dev/living-objects021.git
cd living-objects021
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

# Show the inspected contamination classification for a persisted task.
living-objects audit manhattan-distance

# Run one explicitly bounded local interpreter-only task and save its artifact.
living-objects --artifact-dir .living-objects/runs \
  evolve manhattan-distance --generations 100 --seed 20260814

# Then reproduce or export source only as an audit artifact.
living-objects --artifact-dir .living-objects/runs reproduce <run-id>
living-objects --artifact-dir .living-objects/runs export <run-id> python
```

The evolution runtime is a typed AST interpreter. No language-model call is used in evaluation, selection, mutation, scoring, curriculum promotion, or discovery-import verification. Exported Python, JavaScript, Rust, and Go text is **not** the runtime for evolved behavior and should not be treated as safe executable code.

## Reproduce the v8 five-seed evidence

The published five-seed results were pre-registered as `BEAST-V8-PREREG-20260816-A`. The original evidence release was `e2ea116`; use that revision for a strict historical reproduction. The run is intentionally large: each task has five seeds and 10,000 generations, so plan the compute rather than treating it as a quick smoke test.

```bash
git checkout e2ea116
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q \
  evolution/test_checkpoint_fidelity.py evolution/test_clean_sorting.py \
  evolution/test_proof_benchmark.py

# Writes complete trials, checkpoints, and a new summary under /tmp/v8-reproduction.
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
  python scripts/run_v8_multiseed.py manhattan-distance --output-dir /tmp/v8-reproduction

# On the v9 release, render the included figure from the repository’s persisted trials.
python scripts/build_v9_paper_figure.py
```

Timing telemetry is host-dependent and excluded from deterministic artifact comparison. Fitness, tree structure, primitive profiles, checkpoint state, declared seeds, and fresh-evaluator outcomes remain the scientific evidence fields.

## Scientific boundaries

- **No hidden benchmark rescue:** sorting and string-reverse direct-primitive results remain retracted.
- **Negative results stay visible:** the clean-sorting 0/5 outcome is part of the release record.
- **No live-service claim:** the observatory is locally/preview verified and **not a public deployment**; publishing it and operating a continuous worker require a separate authorization and operations decision.
- **No long-run claim:** the clean-sorting 100,000-generation campaign is pre-execution work gated on declared hardware, durable checkpoints, compute budget, and operator oversight.
- **No publication claim:** the manuscript is reviewable preparation material, **not submitted**, and not peer reviewed.

## Repository map

| Location | Purpose |
|---|---|
| [`living_objects/sdk.py`](living_objects/sdk.py) | Versioned bounded SDK: `evolve`, `audit`, `reproduce`, and source-only `export` |
| [`evolution/gp_engine.py`](evolution/gp_engine.py) | Typed AST representation and interpreter |
| [`evolution/v9_sorting_curriculum.py`](evolution/v9_sorting_curriculum.py) | Five-stage clean curriculum and auditable mastery events |
| [`evolution/v9_federation.py`](evolution/v9_federation.py) | Local signed evidence-exchange MVP |
| [`production/api/v9/`](production/api/v9/) | Local authenticated bounded API contracts |
| [`docs/v9-paper.md`](docs/v9-paper.md) | Reviewable manuscript and reproduction appendix |
| [`docs/v9-claims-registry.md`](docs/v9-claims-registry.md) | Allowed claim wording and update rules |
| [`docs/v9-advanced-research-roadmap.md`](docs/v9-advanced-research-roadmap.md) | Explicit gates for long-running and deployment work |

## Development verification

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q
```

The exact collected/passed count is recorded for each release verification. Do not substitute a badge or a historical count for a fresh test run.

## License

MIT. See [LICENSE](LICENSE).
