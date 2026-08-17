# BEAST v10 Clean-Sorting Campaign Launch Gate

> **Current status:** `BEAST-V9-PREREG-20260817-A` is **not launched**. This record prepares an authorization and recovery gate; it neither selects compute nor starts the five-seed, 100,000-generation campaign.

## Frozen research protocol protected by this gate

The campaign remains exactly the v9 preregistered protocol: five declared seeds (`20260901`–`20260905`), 100,000 generations per seed, a population of 50, a maximum tree depth of 8, mutation/crossover/elitism of `0.12`/`0.85`/`5`, a 100-generation curriculum probe cadence, and 10,000-generation checkpoint and milestone intervals. It uses the typed-AST interpreter only, with zero LLM calls, zero network calls in the generation loop, and no generated-source execution.

The retained clean-sorting baseline is **0/5 eligible successes after 10,000 generations**. This launch gate does not change that negative result, predict a different result, or permit shorter runs to be called campaign outcomes.

| Protocol element | Required state for a campaign result |
|---|---|
| Preregistration | `BEAST-V9-PREREG-20260817-A` unchanged |
| Seeds | All five declared seeds only |
| Completion threshold | Exactly 100,000 executed generations for each reported seed |
| Fresh evaluation | 1,000 general-stage cases per seed |
| Eligibility flag | `eligible_for_declared_campaign_analysis: true` |
| Shorter execution | `bounded_execution_completed`; never an eligible campaign result |
| Result reporting | Retain every failed, incomplete, low-correctness, and recovery outcome |

## Compute choices that require owner selection

The campaign needs durable storage, a restartable process, and enough headroom for measured checkpoints and artifact history. It must not use the hibernating development sandbox as a campaign host. The owner must select one of the following paths in writing; this document does not select one.

| Approach | Trade-offs | Cost | Setup complexity |
|---|---|---|---|
| Owner-managed workstation with at least 4 CPU cores, 8 GB RAM, and durable disk | Retains direct control and avoids a hosting migration, but the machine must stay powered, monitored, and backed up throughout each run. | Uses existing hardware and electricity; the owner controls any incremental cost. | Moderate: prepare a dedicated directory, verify backups, and keep an operator reachable. |
| Owner-authorized persistent compute instance with at least 4 CPU cores, 8 GB RAM, and a mounted durable volume | Supports an explicit operating window and recovery after interruption, but requires account access, provider budget approval, and host hardening. | Provider-dependent and must be approved before use. | Higher: provision the instance, attach storage, define access controls, and test recovery. |

The observatory may remain a lightweight authenticated evidence interface, but its current managed preview has no continuous worker and is not a campaign host. A long campaign must not be quietly attached to a web request or a browser session.

## Required owner authorization record

Before any pilot or campaign command is run, a human owner must record all of the following in the campaign handoff issue, signed runbook, or equivalent durable record:

1. The selected approach, machine or instance identifier, and an explicit statement that it is permitted to run uninterrupted.
2. The owner-approved resource envelope: CPU/RAM allocation, mounted durable path, allowed disk consumption, and maximum operating-cost or time budget.
3. A named recovery owner, an emergency contact method, and a stop authority for host failure, disk exhaustion, artifact corruption, or configuration drift.
4. The destination of a second copy of checkpoints and reports, plus the retention period for raw artifacts.
5. The exact commit hash, clean working-tree status, Python version, and a complete passing engine suite on the selected host.
6. Confirmation that publishing results requires a separate review; campaign execution itself does not authorize a public claim, deployment, PyPI upload, or manuscript submission.

## Mandatory 10,000-generation pilot

The selected host must first complete a **single-seed, isolated 10,000-generation pilot**. Its output directory must be separate from the final campaign directory, because the pilot is a bounded execution rather than a declared campaign result.

```bash
cd /path/to/living-objects021
git rev-parse HEAD
git status --porcelain
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q

mkdir -p "${PILOT_VOLUME}"
/usr/bin/time -v env APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
  python scripts/run_v9_clean_sorting_campaign.py \
  --output-dir "${PILOT_VOLUME}/clean-sorting-pilot" \
  --generations 10000 --seed 20260901
```

The pilot passes this gate only when all of the following are retained and reviewed:

| Pilot acceptance check | Required evidence |
|---|---|
| Protocol identity | `metadata.json` has the preregistration ID and frozen configuration. |
| Honest outcome label | `trial.json` says `bounded_execution_completed` and `eligible_for_declared_campaign_analysis` is `false`. |
| Artifact persistence | `checkpoint.json`, `fitness_history.json`, `milestone_10000.json`, `metadata.json`, and `trial.json` exist. |
| Resource envelope | Captured elapsed time, peak resident memory, CPU observations, disk use, and the host’s remaining capacity stay within the owner-approved envelope. |
| Restore drill | A copied pilot directory is resumed on the selected host, and the launcher accepts the frozen configuration. |
| Failure transparency | Any interruption, recovery event, non-advancement, or low correctness is retained as evidence rather than discarded. |

An example restore drill, performed **after** copying the complete pilot directory to a durable test location, is:

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
  python scripts/run_v9_clean_sorting_campaign.py \
  --output-dir "${RESTORE_VOLUME}/clean-sorting-pilot" \
  --generations 10000 --seed 20260901 --resume
```

## Full-campaign authorization and milestones

Only after the pilot gate passes and the owner grants a second explicit approval may the operator use a persistent, backed-up campaign directory. The command below is a **prepared handoff command**, not an instruction that has been executed in this repository.

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
  python scripts/run_v9_clean_sorting_campaign.py \
  --output-dir "${CAMPAIGN_VOLUME}/clean-sorting-curriculum" \
  --generations 100000
```

The launcher writes checkpoints and objective measurements at generations 10,000 through 100,000 for each seed. The operator must record each milestone’s existence, free disk, process health, and any recovery event; monitoring must not alter the population, evaluator, seed, or frozen configuration.

| Stage | Promotion condition | What may be claimed |
|---|---|---|
| Not launched | No selected host and no owner authorization | Only that a protocol and gate are prepared. |
| Pilot | One 10,000-generation run and restore drill pass the gate | A bounded pilot completed; never an eligible campaign analysis. |
| Campaign in progress | Owner-approved full command has started and artifacts are intact | The exact observed progress only; no outcome or success claim. |
| Completed seed | The seed reaches 100,000 generations with required artifacts | One eligible seed result, including any failure or low correctness. |
| Campaign report | All five declared seeds are completed or all interruptions are documented | The preregistered exploratory summary and all raw outcomes. |

The prespecified exploratory summary is the number of completed seeds with general-stage fresh correctness of at least `0.85`. It is an analysis rule, not a prediction. A low fitness result is a scientific result and not a stop rule; infrastructure failure, corrupted artifacts, exhausted disk, or frozen-configuration mismatch are stop conditions pending repair and a documented recovery decision.

## References inside this repository

| Source | Purpose |
|---|---|
| `docs/v9-clean-sorting-long-run-preregistration.md` | Frozen campaign protocol and honest short-run label. |
| `scripts/run_v9_clean_sorting_campaign.py` | Launcher, checkpoint, milestone, resume, and trial-artifact implementation. |
| `docs/v9-operational-and-submission-gates.md` | Existing persistence, recovery, public-observatory, and submission boundaries. |
| `evolution/test_checkpoint_fidelity.py` | Local proof of deterministic checkpoint/resume fidelity; not a substitute for host-level restore testing. |
