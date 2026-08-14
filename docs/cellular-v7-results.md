# BEAST v7 Cellular Action-Capability Experiment

## Claim under test

This experiment tests a **bounded structural-evolution claim**, not arbitrary tool creation. Each cell carries an inheritable `action_capabilities` repertoire selected from a fixed, world-implemented universe. A descendant may add or remove one safe capability during reproduction; it cannot load code, register an arbitrary action, or bypass world-owned execution.

The result payload is the machine-readable source of truth: [`cellular-v7-results.json`](cellular-v7-results.json).

## Reproduction

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
python3 scripts/run_cellular_experiment.py \
  --generations 30 --population-size 28 --ticks 20 --seed 20260814 \
  --output docs/cellular-v7-results.json
```

## Runtime contract

| Boundary | Implemented rule |
|---|---|
| Capability universe | Thirteen preimplemented actions, including `signal_alarm`, `coordinate_with_neighbour`, `cache_resource`, and `predict_hazard`. |
| Initial repertoire | Every fresh cell receives 4–6 sampled capabilities. |
| Structural mutation | Every child adds or removes exactly one capability, never dropping below four capabilities. |
| Action selection | `AdaptiveCell.reason()` may select only an action inside its genome repertoire. |
| Execution | `CellWorld.apply()` rejects a direct action outside the repertoire with `capability_unavailable`; tissue mode applies the same restriction. |
| Evaluation | Training seeds and the `ExternalTruthLayer` holdout seeds are disjoint. Held-out rollouts are frozen: no policy update occurs while a candidate is measured. |
| Runtime boundary | Actions are enum-defined, world-owned transitions; no LLM, generated source, external network call, or arbitrary callable participates. |

## Measured outcome

The exact deterministic run used **30 generations**, **28 cells**, **20 ticks per lifetime**, training seeds `31, 47, 59, 71, 83, 97, 101, 113`, and independent holdout seeds `901, 907, 911, 919, 929`.

| Measurement | Observed value |
|---|---:|
| Safe action universe size | 13 |
| Initial average repertoire size (generation 0) | 5.178571 |
| Final average repertoire size (generation 29) | 5.928571 |
| Distinct repertoires at generation 0 | 28 |
| Distinct repertoires at generation 29 | 20 |
| Capability mutations per reproduction cycle | 23 |
| Capability mutations recorded across 30 cycles | 690 |
| Baseline independent holdout score | 0.090750 |
| Promoted champion independent holdout score | 0.211500 |
| Independent holdout delta | +0.120750 |
| Promotion accepted by external truth gate | Yes |

> The positive holdout delta shows that the independently promoted cell outperformed the run's initial baseline on the fixed disjoint holdout. It does **not** prove that a newly evolved action repertoire alone caused the improvement: the experiment also permits bounded policy and scalar-genome learning. The structural result demonstrated here is narrower and directly measured—safe repertoires vary, reproduce, persist in state, and remain enforced by the environment.

## Verifiable code proofs

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
pytest -q evolution/test_cellular.py evolution/test_cellular_experiment.py
```

The focused proof suite completed with **10 passed** on 2026-08-14. It covers policy inheritance, capability bounds, one-step repertoire mutation, direct execution rejection for unavailable actions, checkpoint state preservation, tissue-delayed credit, train/holdout separation, and experiment capability-diversity telemetry.
