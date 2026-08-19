# BEAST-BRAIN Clean-Sorting Negative Control

> **Preregistered result interpretation:** The first BEAST-BRAIN comparison is intentionally capable of returning a neutral result. The v13 CPU smoke model emits an unconstrained byte preview. That preview must pass the controller’s exact existing-primitive contract before it can be considered; the clean-sorting grammar remains frozen even if a response passes.

The measurement runner is `agnes_brain/measure_clean_sorting.py`. It runs two independent `GPPopulation` instances with the same fixed seed, clean-sorting stage-0 primitive grammar, population size, generation count, and held-out evaluator seed. The baseline arm has no guidance. The guidance arm receives the controller decision, but cannot alter the preregistered grammar. When the response is rejected, the two arms are contractually identical and must produce identical metrics. A divergence is treated as an error, not an advantage.

| Element | Fixed contract | Reason |
|---|---|---|
| Task | `clean-sorting-v1`, stage 0 | Retains the existing contamination-audited, bounded task boundary. |
| Grammar | `PHASES[0].primitives`, `task-specific` profile | Prevents an unreviewed suggestion from adding a capability to the benchmark. |
| Evolution | 24 organisms, 12 generations, seed `20260819` | Makes the two-arm negative control reproducible. |
| Holdout | Seed `920260819`, 50 evaluator cases | Separates reported held-out scoring from population training seeds. |
| Guidance | Digest-only controller audit; no raw preview persisted | Treats model text as untrusted data and avoids presenting it as executable code. |

The output artifact states **`neutral_negative_control`** and explicitly says that no BEAST-BRAIN-assisted benchmark improvement was measured. It does not demonstrate model-guided primitive discovery, program synthesis, autonomous improvement, or general reasoning. Any future attempt to let an accepted guidance decision change a benchmark grammar requires a separately reviewed task design, a new preregistration, and an independent rerun.
