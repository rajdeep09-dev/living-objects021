# BEAST cellular foundation: a measurable adaptive cell

## Scope

This module defines a **cell** as the smallest executable BEAST unit. It is an adaptive program in a bounded simulated environment, not a claim that it is biologically alive or conscious. A cell has local sensors, mutable internal state, finite memory, energy use, constrained actions, a repair path, reproduction, and messages to adjacent cells. Its policy can improve only when interaction outcomes change its stored estimates.

> A cell is considered improved only when a separately owned verifier measures a better result on withheld deterministic worlds. Its own self-report, its learned memory, and an evaluator-cell score are never sufficient evidence.

## Cell contract

| Part | Executable representation | Measured effect |
|---|---|---|
| Sensors | Local resource, hazard, energy, and neighbour-signal buckets | The policy receives only these bounded values. |
| Internal state | Energy, position, age, bounded procedural memory, and lineage | Energy loss, repair, movement, and learning are observable every step. |
| Reasoning | A finite action-value model updated from prediction error | Action preferences change after actual reward or damage. |
| Actions | Move, harvest, repair, broadcast, share, and wait | Each action is validated by the world and has an energy cost. |
| Lifetime learning | Incremental update of the memory estimate after an action outcome | The same cell can make different later decisions in the same world. |
| Reproduction | Genome mutation plus a bounded copy of learned policy memory | A child can inherit a strategy learned during its parent's lifetime. |
| Death | Energy depletion or age limit | A dead cell cannot act, but cultural records it published remain available. |

## Environment and truth layer

The environment is a finite grid containing resources, hazards, and a home location. Resources replenish on declared cycles; hazards cause direct energy loss. A cell's actions are interpreted by the environment—there are no hand-authored fitness points. The primary score is a function of **actual surviving energy, collected resource, repairs completed, and safe returns** after a finite rollout.

Training worlds are deterministic seeds that evaluator cells may inspect and select as probes. The external truth layer owns a disjoint set of held-out seeds. It evaluates a frozen candidate on those worlds, has no mutable strategy interface, and never accepts a score supplied by the candidate or evaluator cells. Promotion requires a strict holdout improvement subject to a minimum margin.

| Layer | May change during an experiment | Cannot change |
|---|---|---|
| Adaptive cell | Genome, policy-memory estimates, messages, position, energy | World rules, action limits, held-out cases |
| Evaluator cell | Training-probe preferences and predictor parameters | Truth-layer seeds, scoring formula, promotion decision |
| Tissue | Membership, messages, shared local signals, lineage | Per-cell action budget and world physics |
| Truth layer | Nothing during a run | Held-out worlds, score aggregation, acceptance threshold |

## Evaluator-cell role

Evaluator cells are useful as a **curriculum and disagreement detector**, not as final judges. They rank train-world probes that are likely to distinguish two policies, then expose a learner to those probes. Their usefulness is itself measured by whether their selected probes predict the relative ordering later measured by the independent verifier. An evaluator may be wrong; disagreement is recorded instead of overwritten.

This avoids the failure mode in which a system changes both its behaviour and the only grading rule until every result appears good.

## Tissue contract

A tissue is a bounded population of cells in one world. Cells can broadcast a local signal when they discover a resource or hazard, and can share energy with an adjacent cell. No central planner assigns targets. Tissue-level success is independently measured as verified total resource returned to home, survivor fraction, and energy efficiency. The comparison baseline is the same initial world with isolated cells that cannot communicate or share energy.

## Proof plan

The implementation will provide executable tests for lifetime learning, Lamarckian policy inheritance, hard energy/action bounds, evaluator–truth disagreement handling, holdout-gated promotion, and tissue performance compared with the communication-disabled baseline. A reproducible report will record the seed, configuration, generation-by-generation metrics, final held-out results, and whether the result was promoted.

## Non-claims and safety boundary

The cell has a narrow, task-specific reinforcement learner; calling that mechanism “reasoning” describes its stateful prediction-and-action loop, not human-like understanding. It cannot run arbitrary source code, access a network, write outside a supplied checkpoint location, modify the truth layer, or run indefinitely. Every experiment has finite cell, tick, generation, memory, and message limits.
