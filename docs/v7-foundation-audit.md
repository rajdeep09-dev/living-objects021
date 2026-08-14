# BEAST v7 Foundation Audit

**Audit date:** 2026-08-14  
**Scope:** VULN-V6-01 through VULN-V6-08 in `BEAST_UPDATE_v7.md`  
**Rule:** A guide claim is treated as a hypothesis and checked against the current repository. A mismatch is documented; it is never papered over with simulated compliance.

## Result

| ID | Current status | Direct evidence | v7 disposition |
|---|---|---|---|
| VULN-V6-01 | **Closed — regression verified** | `CandidateOnlyBugFixer.propose()` now measures isolated per-assertion progress, retains the top four partial survivors for up to four bounded mutation rounds, and still returns only a fully passing source proposal. | `test_candidate_only_bug_fixer_promotes_partial_survivor_for_two_step_repair` proves a two-edit constant repair is discoverable only by carrying a partial survivor forward. |
| VULN-V6-02 | **Closed — regression verified** | `GPPopulation.step()` applies a deterministic, typed, post-reproduction hoist sweep before evaluation; oversized trees are replaced by their largest root-type subtree at or below 64 nodes. | `test_population_never_exceeds_max_size_across_100_generations` injects an 80-node tree, evolves for 100 generations, and asserts the 64-node ceiling for every organism after every step. |
| VULN-V6-03 | **Closed — regression verified** | `GPPopulation.TRAIN_SEED_OFFSET` makes the train seed contract explicit. One `batch_evaluate` call evaluates the full population on a shared generation suite, and the next generation shifts by one seed. | `test_fitness_seed_rotates_every_generation_but_is_consistent_within_one_generation` records both deterministic test suites and population batch sizes. |
| VULN-V6-04 | **Closed — safe boundary regression verified** | The guide's proposed `/market/list` route remains absent. `VerifiedProgramMarket.list_program()` accepts no fitness field, always invokes its verifier-owned `HELD_OUT_SEED`, and persists the resulting provenance in `ProgramOffer`. | `test_verified_market_derives_held_out_fitness_and_rejects_caller_score_argument` proves evaluator derivation and rejects an attempted `fitness` argument; the unverified-offer test also sets `genome.fitness = 1.0` and still rejects the genome. |
| VULN-V6-05 | **Closed — regression and experiment verified** | `CellGenome.action_capabilities` is a validated inheritable `frozenset` selected only from a 13-action safe universe. Reproduction adds or removes exactly one capability while retaining a minimum repertoire of four. `AdaptiveCell`, `CellWorld`, and `Tissue` enforce the repertoire at action-selection, learning, and execution boundaries. | `test_cell_action_capabilities_are_bounded_mutable_and_inherited`, `test_world_rejects_action_that_is_absent_from_cell_capabilities`, and the public experiment regression prove bounded action mutation, inheritance, enforcement, and recorded capability diversity. |
| VULN-V6-06 | **Closed — integration regression verified** | `LiveGPPopulationBroadcaster` owns bounded interpreter-only `GPPopulation` instances keyed by named task domain. It publishes only after each completed `population.step()`, and the authenticated `/ws/v6/evolution` endpoint subscribes to that live broadcaster rather than polling control-plane replay storage. | `test_v6_stream_emits_ten_real_population_generations_with_champion_code` runs ten real sorting steps through `/v6/runs`, receives ten WebSocket messages, and verifies ordered generations, real champion audit code, named task domain, and the 64-node ceiling. |
| VULN-V6-07 | **Closed — mandatory Node runtime regression verified** | Numeric GP exports remain audit artifacts, while `node -e` executes an independently generated JavaScript function only inside the regression subprocess. Its values are compared to the typed Python interpreter on the same declared inputs. | `test_javascript_export_matches_typed_python_interpreter_within_tolerance` requires Node, executes the generated function, and asserts each result agrees with `GPNode.evaluate()` within `1e-6`. Rust and Go remain optional targets rather than unverified claims. |
| VULN-V6-08 | **Closed — continuity regression verified** | Population checkpoint payload serialises full organisms via `GPGenome.to_dict()` alongside history, hall of fame, configuration, and RNG state. Restoration reevaluates the restored organisms under the exact resumed generation's train seed without rebuilding an initial population. | `test_population_saves_and_loads_without_fitness_regression` runs 100 generations, saves JSON, reloads a full population, runs 100 additional generations, and verifies generation 200 champion fitness is no lower than at generation 100. |

## Non-negotiable evidence rules

1. **No LLM invocation** participates in evaluation, selection, mutation, crossover, scoring, or benchmark reporting.
2. **No evolved source executes in-process.** The interpreter remains the runtime authority; generated source is an audit artifact.
3. **No UI number is manufactured.** A value shown in the observatory must originate from a persisted real run event or show a disconnected/empty state.
4. **Train, evaluator probe, and independent holdout channels remain distinct.** Evaluator-probe diagnostics cannot promote a champion.
5. **Unsupported guide assumptions are not recreated.** The absent vulnerable market endpoint will remain absent unless a safe evaluator-first design is implemented.

## Acceptance matrix for the foundation release

| Gate | Required proof |
|---|---|
| Candidate repair | A two-step repair retains high partial-assertion survivors and returns only a proposal after all assertions pass. |
| Bloat control | Across 100 generations, every emitted organism remains at or below the declared 64-node ceiling. |
| Rotating evaluation | Same-generation organisms receive identical train cases; the next generation receives a distinct seed; holdout remains separate. |
| Market boundary | No caller-controlled score can create a verified listing. |
| Capability evolution | Offspring mutate bounded action repertoires and can inherit an advantageous learned policy without gaining arbitrary actions. |
| Real stream | Ten real sorting population steps emit ten champion events containing non-empty exported audit source. |
| Polyglot validity | Python and target runtime outputs agree within `1e-6` on the same declared inputs. |
| Resume | A loaded population carries real organisms forward and does not restart from random noise. |

## Verified closure record

The first two gates were verified on 2026-08-14 using `APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q evolution/test_bug_fixer.py evolution/test_gp_population.py`, producing **10 passed**. The rotating-seed and market-boundary gates were then verified using `pytest -q evolution/test_gp_population.py evolution/test_program_market.py`, producing **11 passed**. A complete repository regression immediately afterwards produced **429 passed**. The cellular capability gate then produced **10 passed** from `pytest -q evolution/test_cellular.py evolution/test_cellular_experiment.py`. Its deterministic 30-generation evidence run is recorded in [`cellular-v7-results.json`](cellular-v7-results.json) and [`cellular-v7-results.md`](cellular-v7-results.md). The real-generation stream gate then produced **3 passed** from `pytest -q production/test_v6_api.py`, including the ten-message authenticated WebSocket integration proof. The runtime/export and resume gates then produced **11 passed** from `pytest -q evolution/test_polyglot_export.py evolution/test_gp_population.py`, including the mandatory Node numerical-equivalence and 100 + save/load + 100 continuity proofs. The pre-existing warnings concern FastAPI test-client deprecation, intentionally insecure test defaults, and legacy tests returning booleans; none are failures or introduced by these changes.

## Bounded sorting-run evidence

The v7 runner completed a **measured bounded run**, not the guide's unrun 100,000-generation public marathon: 1,000 generations, 50 organisms, seed 42, maximum depth 8, tournament size 7, crossover 0.85, mutation 0.12, and elitism 5. The typed AST interpreter made all selection-time evaluations; the recorded configuration states zero LLM calls and zero network calls in the generation loop. Its final champion had training fitness **1.000000** and evaluator-measured fresh-sort correctness **1.000000 (100/100)** on seed 901000. The invocation took **19.318 seconds** at Git revision `be7d22c2dd94d115bdede0678ff602417cf3cd3f`.

The source-of-truth result is [`../reports/sorting_marathon/run_result.json`](../reports/sorting_marathon/run_result.json), accompanied by the complete [`fitness_curve.json`](../reports/sorting_marathon/fitness_curve.json), four measured milestone reports, and [`BOUNDED_RUN_FINAL_REPORT.md`](../reports/sorting_marathon/BOUNDED_RUN_FINAL_REPORT.md). It records `claimed_public_100k_marathon_completed: false`; no public-marathon result is claimed.

## Scope boundary

The guide’s public 24/7 observatory, 100,000-generation marathon, multi-installation federation, public archival publishing, and multi-week research program require persistent compute, a configured deployment target, and operational authorization. This foundation release will implement the bounded, reproducible local proof mechanisms required before such claims can be made. No unmeasured marathon or public-live deployment will be represented as completed.

## Final foundation verification

On 2026-08-14, the full repository command `APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q` completed with **435 passed** in **88.08 seconds**. Twelve warnings remain: FastAPI's test-client deprecation, deliberate insecure-default warnings exercised by configuration tests, and legacy tests that return a boolean instead of asserting it. None were introduced by the v7 foundation changes. The release-boundary review is recorded in [`v7-security.md`](v7-security.md); it approves a bounded repository evidence release and explicitly does not approve public persistence, multi-replica streaming, a public sandbox playground, or a 100,000-generation completion claim.
