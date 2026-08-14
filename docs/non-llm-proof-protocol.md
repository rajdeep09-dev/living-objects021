# BEAST non-LLM evolutionary proof protocol

## Exact claim

> On the declared finite task, a population of randomly initialized, typed programs can evolve a program with objectively measured correctness greater than its generation-zero population, without an LLM, generated-source execution, network access, or a preloaded solution program.

This is a **benchmark claim**, not a claim of general intelligence, autonomous software engineering, universal novelty, or open-ended self-improvement.

## Benchmark contract

| Requirement | Enforced rule | Artifact that permits checking |
|---|---|---|
| Initial condition | Every individual is built from a seeded random typed-tree generator before any fitness evaluation. No champion or hand-written target AST is injected. | `initial_population.json` and manifest seed |
| Program language | Programs are typed trees built from a fixed pure primitive whitelist and bounded terminals. | Manifest primitive and terminal fingerprints |
| Execution boundary | Fitness invokes the AST interpreter only. Exported Python source is audit text and is never executed by benchmark code. | Runtime metadata and interpreter-only test |
| Objective score | The Manhattan task's primary score is one minus mean clipped absolute numeric error divided by 300, calculated from actual interpreter output. Exact-case correctness is separately reported and never substituted for the primary score. | Train/holdout case fingerprints and scores |
| Selection pressure | Tournament selection, crossover, mutation, and elitism use the recorded seed and population configuration. | Immutable run configuration |
| Independent test | A holdout seed is distinct from the training seed and must not participate in selection. Promotion is accepted only when holdout correctness improves over the recorded generation-zero champion. | Holdout result and promotion decision |
| Independent re-run | A separate process reruns the manifest from its seed and compares the baseline, champion AST digest, train score, and holdout score. | Verification result JSON |
| Bounded resources | The controller has finite generation, population, AST size/depth, interpreter-depth, and no-network limits. | Manifest bounds and checkpoint |

## Pass and failure criteria

The benchmark **passes** only if every fixed-seed trial satisfies all of the following conditions:

1. The generation-zero population is recorded before evolution and its best initial program is scored on the disjoint holdout.
2. The final champion is structurally different from the recorded baseline champion or achieves a strictly better objective score.
3. Final train correctness exceeds the generation-zero train correctness by the declared minimum delta.
4. Final held-out correctness exceeds generation-zero held-out correctness by the declared minimum delta.
5. A separate verification command recreates the same manifest results within exact deterministic comparison rules.
6. The benchmark emits no source execution, no network request, and no LLM invocation.

The benchmark is reported as a **failure**, not silently retried or averaged away, if any fixed-seed trial misses the holdout delta, encounters an invalid program, mismatches its rerun, or breaches the execution boundary. The raw manifest must retain both passes and failures.

## Task selection

The proof task is selected to require composition of multiple generic primitives. A task must not expose a primitive that directly implements the target function. For example, a two-dimensional Euclidean-distance task can use arithmetic composition, subtraction, squaring, addition, and protected square root, but it must not include a direct distance primitive.

The benchmark does not establish that evolved programs are globally optimal, novel in the historical sense, useful outside the evaluator distribution, or produced without any engineering knowledge in the **search language**. It establishes only the stated empirical fact: under these bounds, selection improved objectively scored program behavior beyond the recorded random initial population.
