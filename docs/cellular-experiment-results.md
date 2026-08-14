# BEAST cellular-foundation experiment: measured result

## What this run demonstrates

This is a **bounded adaptation experiment**, not an assertion that the software is conscious. Each cell interacted with a deterministic resource-and-hazard grid, learned an action-value memory from outcomes produced by the world, passed a bounded policy-memory subset to offspring, and was selected using only the declared training worlds. Evaluator cells adapted their training-probe priorities, while promotion remained under a disjoint immutable holdout layer.

> **Result.** Under the declared fixed seed and 30-generation budget, the promoted cell policy improved held-out environment score from **0.071500** to **0.506375**, a **0.434875** absolute gain and a **7.0821×** multiple. The held-out worlds were not in the train-world selection set.

## Reproduction command

```bash
cd /home/ubuntu/living-objects021
python3 scripts/run_cellular_experiment.py \
  --generations 30 --population-size 28 --ticks 20 \
  --seed 20260814 \
  --output docs/cellular-experiment-results.json
```

The machine-readable evidence is committed alongside this report at `docs/cellular-experiment-results.json`. It contains every generation, the complete final policy table, exact seeds, configuration, and the final promotion decision.

## Declared experimental contract

| Element | Fixed measurement boundary |
|---|---|
| Training worlds | Seeds `31, 47, 59, 71, 83, 97, 101, 113` |
| Held-out worlds | Seeds `901, 907, 911, 919, 929` |
| Population / budget | 28 cells; 30 generations; 20 ticks per lifetime |
| Actions | Move, harvest, repair, wait; broadcast and share available only in tissue mode |
| Learned state | A capped 256-state action-value table, updated from actual action outcomes |
| Inheritance | Child receives mutated genome plus a bounded stochastic policy-memory copy |
| Selection input | Frozen-policy score on training worlds only |
| Promotion input | Frozen-policy score from disjoint held-out worlds; required margin `0.005` |
| State isolation | Each evaluation resets energy, age, position, cargo, delivery counters, history, and liveness; it retains only genome and learned policy |

The final state-isolation point is enforced by `test_independent_evaluation_resets_previous_lifetime_state`. A cell cannot inflate its held-out result by carrying a resource, keeping a positive energy balance, or preserving an earlier delivery count into a fresh evaluation.

## Observed trajectory

The trajectory is **not monotonic**, which is expected in a finite evolutionary search. The system retains only candidates that clear the independent verification gate; a strong temporary training candidate may still be rejected. The highlighted metrics below distinguish the first and final generation from the final independently promoted policy.

| Measurement | Generation 0 | Generation 29 | Final independently promoted policy |
|---|---:|---:|---:|
| Mean training score | 0.115151 | 0.361590 | — |
| Champion training score | 0.268281 | 0.427891 | — |
| Candidate held-out score at that generation | 0.048750 | 0.185625 | — |
| Mean learned policy states | 6.821429 | 35.214286 | — |
| Mean cell mutation rate | 0.098814 | 0.020403 | — |
| Mean evaluator mutation rate | 0.094754 | 0.016377 | — |
| Baseline held-out score | — | — | 0.071500 |
| Promoted held-out score | — | — | **0.506375** |
| Held-out delta | — | — | **0.434875** |

The best accepted policy was found before the final generation. Later candidates were measured but did not replace it when they failed the declared holdout margin. This is an intended safety property: the system reports search progress without claiming that every later generation is better.

## What was actually verified

| Claim | Evidence | Verification boundary |
|---|---|---|
| Lifetime learning occurs | A harvest outcome changes the same cell’s action value in `test_cell_learns_from_actual_harvest_outcome_and_inherits_policy_memory`. | Reward comes from `CellWorld.apply`, not a supplied score. |
| Learned behaviour is inheritable | A child receives the parent’s learned policy state in the same proof test. | Inheritance is a bounded data copy, not executed source. |
| Cells have a hard lifetime | `test_cell_world_enforces_energy_and_lifetime_bounds` verifies depletion, death, and no post-death reproduction. | World owns costs and damage. |
| Evaluators cannot grade themselves into success | `test_evaluator_cells_learn_probe_values_but_cannot_promote_an_unchanged_policy` rejects equal policies despite evaluator activity. | Disjoint `ExternalTruthLayer` owns promotion. |
| Signal use is tied to real collective results | `test_tissue_signal_produces_delayed_credit_only_after_real_neighbor_harvest` credits a broadcaster only after a neighbor harvests the signalled resource. | No credit exists for an empty broadcast. |

## Limits

This score applies only to the finite environment distribution and horizons defined above. It does not prove general problem solving, reliable behaviour on a new class of worlds, consciousness, or open-ended intelligence. The next engineering step is to run the same contract with a more difficult tissue benchmark, increase only one complexity dimension at a time, and retain the independent verifier as the immutable backstop.
