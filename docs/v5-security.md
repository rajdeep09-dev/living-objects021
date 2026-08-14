# BEAST v5 Safety and Security Notes

BEAST v5 adds durable execution controls, but it does not make unrestricted self-modifying code safe. The design therefore limits the worker to task profiles, state mutation, local scoring, and bounded artifact serialization.

| Risk | Control | Test surface |
|---|---|---|
| User goal becomes code execution | Goal text is keyword-routed to a fixed `EvolutionTask`; it is never evaluated. | `evolution/test_v5.py` task-routing tests. |
| Endless background compute | Finite budget, batch stepping, pause/cancel checks, host quotas, and explicit persistent-host requirement. | Worker lifecycle tests. |
| Process crash loses cultural state | Atomic checkpoint manifest and deterministic resume metadata. | Checkpoint/resume proof tests. |
| Parallel universe shares mutable archive | Branch uses an isolated memome snapshot. | Physics regression tests. |
| Temporal revision causes unbounded recomputation | Causal depth and butterfly budget cap the revision. | Temporal v5 safety test. |
| Morphogenesis loops indefinitely | State-cycle detection and neuron/synapse ceilings stop growth. | Morphogenetic v5 safety test. |
| Translation silently corrupts meaning | Unknown tokens use explicit fallbacks with quality reporting. | Writing-system v5 safety test. |
| Huge substrate payload exhausts workers | Strategy count and emitted binary size are capped. | Substrate v5 safety test. |

The local worker makes **no network call per generation**, but this is a performance and dependency boundary, not a security boundary. A deployed worker must still use a least-privilege service account, read-only application image, non-root UID, resource limits, a dedicated checkpoint volume, encrypted backups, and no credentials inside evolution artifacts. Generated source-code execution remains research-only and requires an external sandbox.

## Operational response

Pause a run when metrics diverge, when quota alarms fire, or when a task description does not match a registered profile. Cancel writes a final checkpoint rather than erasing data. Keep append-only event logs and preserve the source commit, task configuration, seed, checkpoint hash, and host resource limits with any reported result.
