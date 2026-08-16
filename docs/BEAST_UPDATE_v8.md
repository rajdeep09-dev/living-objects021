# BEAST UPDATE v8 — THE HONEST RECKONING
## What Is Real, What Is Fake, and How We Fix Everything

> **This document has no code snippets.**
> It is a pure engineering and science mandate.
> Every section is based on what was literally measured and run, not what was planned.
>
> After the v7 audit, 259 evolution tests pass. Three are skipped. Zero are failing.
> The GP engine is real. The WebSocket is wired to a live population. The market verifies fitness.
> But the marathon result contains the most important flaw in the project so far.
> v8 fixes it and builds the next civilisation on an honest foundation.

---

## THE v7 AUDIT FINDINGS — WHAT WAS MEASURED

### FINDING 1 — The 259/262 Test Result Is Genuinely Good

When the full evolution test suite runs on this device, 259 tests pass and 3 are skipped. Zero fail. This covers gp_engine, gp_population, fitness evaluators, bug fixer, program market, polyglot export, cellular, v7 sorting marathon, and the live GP stream capture. The core evolution infrastructure is working correctly.

The 3 skipped tests are the Rust and Go polyglot runtime correctness tests — skipped because those compilers are not installed on this Termux device. The JavaScript polyglot test runs and passes. This is honest and correct behaviour — skipped is not failed.

The 8 FastAPI-dependent production tests cannot collect because `fastapi` is not installed in this environment. They are not evolution logic — they are API integration tests that require a server environment. They do not indicate a broken evolution engine.

### FINDING 2 — THE SORTING MARATHON IS MEANINGLESS (THE CRITICAL FLAW)

This is the most important finding in the entire audit. Read it carefully.

The sorting marathon ran for 1,000 generations and reported a champion with fitness 1.000000 that correctly sorted 100/100 fresh test cases. The report presents this as a success. It is not.

Look at the champion's source code: it calls Python's built-in `sorted()` function, wrapped in a two-node GP tree. Look at the fitness curve: best_fitness is already 1.000000 at generation 0. The champion was found before a single generation of evolution ran.

The reason is that `sort1` — which compiles to `sorted(list(x))` — is explicitly included in the `LIST_PRIMITIVES` of the GP engine. The primitive set contained the exact answer to the task. The GP engine, which initialises populations randomly, found this primitive by chance in the initial random population. It then propagated it through 1,000 generations, producing no meaningful change at all.

This is equivalent to testing whether a student can write "Hello World" when "Hello World" is one of the allowed symbols they can pick from. They will pass the test in one try. The test proves nothing about their programming ability.

The 1,000-generation sorting marathon produced zero scientific value because the answer was available as a primitive from the start. The claim in the milestone reports that evolution "discovered" a sorting algorithm is false. It selected one from a menu.

### FINDING 3 — What The Non-LLM Manhattan Distance Proof Does NOT Have This Problem

The Manhattan distance proof from v6 is genuinely valid. The primitive set did NOT include Manhattan distance as a primitive. It included only generic arithmetic: subtraction, absolute value, addition, maximum. The population had to compose those primitives into the correct formula from scratch. That is real evolution.

The proof that seeds 20260814, 20260815, 20260816 all independently discovered the correct formula — with different tree structures — is scientifically valid. This distinction matters enormously. The Manhattan distance result is real. The sorting marathon result is contaminated.

### FINDING 4 — The WebSocket Is Now Genuinely Wired to Real Evolution

The v7 broadcaster in `production/api/v6/websocket.py` holds a real `GPPopulation` instance, calls `pop.step()` in a loop, and emits events from the actual `GenerationStats` object. The live stream capture in `reports/v7_live_gp_stream.json` shows 10 real generation events with distinct champion codes changing across generations. The WebSocket is no longer mocked. This is real progress.

### FINDING 5 — The Market API Now Verifies Fitness

The market routes call `_evaluator_for(task)` and run the submitted code through the evaluator before creating any listing. The fitness score in the listing comes from the sandbox result, not from the caller. The VULN-V6-04 fix is genuine.

### FINDING 6 — The Bug Fixer Is Fixed

The full evolution test suite passes 259 tests. The `test_candidate_only_bug_fixer_returns_small_passing_proposal` test that was previously failing now passes. VULN-V6-01 is resolved.

### FINDING 7 — Checkpoint/Resume Is Partially Implemented

The v7 marathon runner saves population checkpoints. However, the checkpoint restores only organism fitness scores and metadata — not the full GP tree structure of each organism. On resume, trees are reconstructed from the recorded source code strings by re-parsing them, not by deserialising the exact tree structure. This means the resume is approximate. Small structural differences between the original tree and the re-parsed version are possible. This is not a critical bug — it is an approximation. But it must be clearly labelled as such in the documentation, and the full tree serialisation from VULN-V6-08 is still not complete.

---

## THE CENTRAL PROBLEM v8 MUST SOLVE

**The primitive contamination problem is the most fundamental scientific issue in this project.**

Every task in the existing suite risks the same contamination as the sorting marathon. If the primitive set contains a direct solution to the task, evolution will find it in generation 0 or 1 by random initialisation. The result is not evolution — it is lottery selection from a pre-stocked menu.

The Manhattan distance proof avoided this because it was designed correctly: the primitives were generic arithmetic operations, not Manhattan distance itself. Every other task must be held to the same standard.

v8's first and most important job is to audit every task evaluator, identify which ones are contaminated by the presence of direct-solution primitives, remove those primitives, and re-run the experiments. Every benchmark that has been published must be re-evaluated under this standard.

---

## PART A: THE 8 v7 FINDINGS THAT BECOME v8 MANDATES

### MANDATE-V8-01: Rebuild the Sorting Evaluator With Contamination-Free Primitives

The sorting task must be redesigned from the ground up. The primitive set for sorting must NOT include `sort1`, `sorted`, or any function that directly returns a sorted list. The allowed primitives must be the building blocks from which a sorting algorithm can be assembled: element comparison, conditional swap, indexing, list concatenation, list slicing, finding minimum or maximum of two values, and integer arithmetic for index manipulation.

The task must be redesigned so that a random initial population achieves average fitness near zero. If a random population achieves non-zero average fitness on the first generation, the primitive set is contaminated with partial solutions and must be further restricted.

The sorting task must be re-run to find the generation at which the population first achieves fitness above 0.50, above 0.90, and above 0.99. These are the real milestones. The fitness curve must show genuine improvement — not a flat line at 1.0 from generation 0.

The expected evolution trajectory based on the literature for uncontaminated sorting GP: fitness near 0 for the first 50–200 generations, then a rapid improvement phase as the population discovers a working comparison, then sustained refinement. If the curve does not look like this, the primitive set is still contaminated.

### MANDATE-V8-02: Audit Every Existing Task for Primitive Contamination

Every task evaluator must be audited using the following test: initialise a population of 50 organisms randomly using the task's primitive set. Run zero generations of evolution. Record the average fitness. If the average fitness is above 0.20, the primitive set is contaminated — a direct or near-direct solution is present in the primitive pool.

Apply this test to: sorting, primes, Fibonacci, max subarray, game theory, compression, pathfinding, and all 14 planned new domains. Publish the baseline fitness measurement for each task in `docs/task-contamination-audit.md`. Any task where random initialisation achieves average fitness above 0.20 must have its primitive set redesigned before the task is used in any published benchmark.

### MANDATE-V8-03: Re-run the Sorting Marathon With Clean Primitives to 10,000 Generations

After MANDATE-V8-01 is complete and the sorting evaluator is confirmed contamination-free, launch a new marathon run of 10,000 generations — not 1,000, not 100,000. Ten thousand is the minimum scale at which meaningful algorithm discovery can occur for an uncontaminated sorting task.

Document the full fitness curve, milestone by milestone at every 1,000 generations. Record the champion's code at each milestone. Record the generation at which the champion first produces a correctly sorted output for all test cases. Record the champion's code at that moment — what sorting approach did it independently discover? Is it a comparison sort? A selection sort? Something that has no name?

This run, executed honestly with clean primitives, will be the first genuine result in the project that can be cited as evolutionary algorithm discovery at scale.

### MANDATE-V8-04: Publish a Contamination-Aware Primitive Specification Standard

Every task in this project, now and in the future, must be defined with a formal primitive specification that includes a contamination section. The contamination section must list every primitive that is excluded from the task's primitive set and explain why that primitive is excluded. It must also list the expected baseline fitness of a random initial population, measured and recorded rather than estimated.

This standard must be published as `docs/primitive-specification-standard.md`. It is the scientific protocol that ensures every future benchmark is valid. Without this standard, every new task added to the system risks the same contamination as the sorting marathon.

### MANDATE-V8-05: Run the Manhattan Distance Proof at 10,000 Generations

The Manhattan distance proof is the most scientifically valid result in the project. It was conducted at 300 generations with population size 128. v8 must extend it to 10,000 generations to answer the follow-up question: does the system continue improving beyond the first correct solution? Does it find more elegant or smaller solutions? Does it find solutions that the describer can name as known mathematical identities?

At 300 generations, trial seed 20260814 found `max(|a−b|, |a+b|)` — an indirect route to Manhattan distance that is mathematically valid but less obvious. At 10,000 generations, does the population converge on the direct `|dx| + |dy|` form? Or does it maintain diversity of structurally different but semantically equivalent solutions? This is an open scientific question.

Run this extended proof, publish the results in `docs/manhattan-proof-10k.md`, and include the full champion taxonomy — every structurally distinct correct solution found across the entire run.

### MANDATE-V8-06: Complete the Full GP Tree Serialisation for Checkpoint/Resume

The VULN-V6-08 fix in v7 approximates tree restoration by re-parsing source code strings. This is not correct. The correct implementation serialises each `GPNode` as a recursive JSON structure: primitive name, children list, terminal value, terminal name. On load, it reconstructs each node by looking up the primitive by name in the registered primitive set. The reconstructed tree must be bit-for-bit identical to the original — not an approximation from source parsing.

This matters because source parsing is non-deterministic in edge cases. Two trees that produce the same source code string can have different internal structures if the compilation step collapses them. A resumed run using source-parsed trees may produce different evolution dynamics than the original run. For the 10,000-generation sorting marathon to be reproducible, the checkpoint system must be exact.

### MANDATE-V8-07: The Observatory Must Display the Contamination Status of Each Task

The public Observatory must show, for each task domain, a clearly labelled contamination audit panel. It must display: the task's primitive set, the expected baseline fitness of a random population, the measured baseline fitness from the audit, and whether the task passed or failed the contamination check.

If a task failed the contamination check, the Observatory must show its results with a visible warning: "This benchmark used primitives that partially encode the solution. Results should not be cited as evidence of algorithm discovery." This is the most important transparency feature in the entire project. Without it, the public will misinterpret contaminated results as genuine evolutionary breakthroughs.

### MANDATE-V8-08: The Benchmark Leaderboard Must Be Contamination-Adjusted

The competitive benchmark leaderboard introduced in v7 must now include a contamination column. For each task, the leaderboard shows: whether the task passed the contamination audit, what the baseline fitness was, and what fitness the champion achieved. If the task is contaminated, the leaderboard row is greyed out with a note that the result is not a valid benchmark.

Only uncontaminated tasks count in the official leaderboard. The sorting marathon result is greyed out until the clean-primitive re-run is complete. The Manhattan distance results remain in the active leaderboard as the only currently valid large-scale result.

---

## PART B: THE 10 INNOVATION DIRECTIVES FOR v8

### DIRECTIVE 1: THE CURRICULUM — TEACH THE SYSTEM TO LEARN, NOT FIND

The contamination problem reveals a deeper architectural issue. The current system does not teach organisms to learn sorting. It gives them a primitive set that includes sorting, and the organisms find it. v8 introduces a curriculum — a structured progression of increasingly difficult sub-problems that guide evolution toward discovering an algorithm rather than selecting a primitive.

For sorting, the curriculum begins with: sort a list of 2 elements (trivially: compare and swap). Then sort a list of 3 elements. Then 5. Then 10. The primitive set at every stage contains only comparison, swap, and control-flow primitives — never sorted(). Each stage is only unlocked when the population achieves 95% fitness on the previous stage.

This curriculum approach is how humans teach algorithms. Nobody learns sorting by being told "here is sorted()." They learn by understanding comparison, then understanding that a sequence of comparisons can produce order. The curriculum makes the evolution system learn the same way.

The curriculum system generalises to every task. For primes: first learn to check divisibility by 2. Then by 3. Then identify the general pattern. For Fibonacci: first learn to produce any increasing sequence. Then learn that each element is the sum of the previous two. Curriculum-guided evolution is categorically more powerful than a single-task, all-primitives approach.

### DIRECTIVE 2: THE DISCOVERY LOG — RECORD EVERY GENUINE FIRST

v8 introduces a discovery log — a single, append-only file called `docs/discovery_log.md` that records every genuine algorithmic discovery made by the system. A discovery qualifies when: the primitive set is certified contamination-free, the champion achieves fitness above 0.95 on a fresh test set, and the champion's structure was not already present in the initial random population.

Each discovery entry records: the date, the task domain, the generation of discovery, the champion's GP tree expressed as a mathematical formula, what makes it novel (does it match a known algorithm? is it a previously unnamed approach?), and the seed required to reproduce it.

This log is the scientific record of the project. It is what gets cited in papers. It is what gets posted to Hacker News. Every entry must be verified by an independent reproduction run before it is added. The Manhattan distance discoveries from v6 are the first three entries.

### DIRECTIVE 3: THE COMPARATIVE SCIENCE FRAMEWORK — BEAT SPECIFIC BASELINES

v8 introduces a framework for comparing evolved algorithms to specific human-written baselines in a way that is scientifically rigorous. For each task, the comparison must control for: the allowed operations (an evolved algorithm that can call sorted() cannot be compared to Timsort unless Timsort is also allowed the same primitive set), the test distribution, and the evaluation metric.

The scientific question is not "can evolution find a sorting algorithm?" — that is trivially answerable by including sorted() in the primitive set. The scientific question is: "given the same primitive operations that a human programmer uses when writing a sorting algorithm, can evolution find a sorting algorithm of comparable quality to what a human would write?" That question is hard and interesting. That is the question v8 answers.

For every task in the contamination-free suite, define the human baseline as: the best algorithm a skilled programmer could write using only the same primitive operations allowed to the GP system. Then measure how many generations it takes evolution to reach that baseline. This is the generation-to-baseline metric. It is the first scientifically valid measurement of evolutionary algorithm discovery speed.

### DIRECTIVE 4: THE MULTI-SEED VALIDATION PROTOCOL

Every significant result must be replicated across at least 5 independent random seeds before it is published. The v6 Manhattan distance proof used 3 seeds — this was good but should be 5 as a standard. The clean-primitive sorting marathon must use 5 seeds. The 10,000-generation extended proof must use 5 seeds.

A result that only holds for one seed is not a result — it is a lucky run. A result that holds for all 5 seeds with similar fitness curves, similar discovery generations, and similar champion structures is a genuinely robust finding. The multi-seed protocol is the difference between a result and a fluke.

The protocol must specify: all seeds must be declared before any runs start. If a seed fails to produce a result (fitness below 0.50 after the target number of generations), that failure is published alongside the successes. Only results where at least 4 out of 5 seeds succeed may be promoted to the discovery log.

### DIRECTIVE 5: THE ADVERSARIAL PRIMITIVE AUDIT

Introduce an automated test that, for each task, attempts to find primitive combinations of length 1, 2, and 3 that solve the task. If a single primitive solves the task, it is a direct contamination. If a two-primitive combination solves it, it is a near-direct contamination. If a three-primitive combination solves it within the first 10 generations of random evolution, it is a minor contamination that should be documented.

This audit must run as part of the CI pipeline for every new task. Before any task is added to the suite, it must pass the adversarial primitive audit. The audit is a fast computation: generate all single-node, two-node, and three-node programs from the primitive set and test each one against the fitness evaluator. If any such minimal program achieves fitness above 0.50, the task is contaminated and must be redesigned.

### DIRECTIVE 6: MAKE THE CELLULAR SYSTEM COMPETE AGAINST THE GP SYSTEM ON THE SAME TASKS

The cellular system and the GP system are currently evaluated on completely different tasks. The GP system is evaluated on mathematical algorithms. The cellular system is evaluated on a resource-and-hazard grid. There is no direct comparison between them.

v8 runs both systems on the same problem: discovering a decision rule. The problem is: given the last 5 elements of a sequence, predict whether the next element will be above or below the median. The GP system evolves an arithmetic expression tree that makes this prediction. The cellular system evolves a policy table that makes this prediction. Both systems are evaluated on the same 200-case test set.

This comparison is scientifically valuable because it asks: for decision-making tasks that require learning a pattern from history, which approach converges faster? Which produces more interpretable results? Which generalises better to new sequences? There is no known answer. Running both systems and comparing honestly is a genuine research contribution.

### DIRECTIVE 7: THE LIVE REPRODUCIBILITY DASHBOARD

The Observatory must include a reproducibility dashboard — a panel that shows, for every published result in the discovery log, a live status indicator. The status can be: Verified (a reproduction run completed within the last 7 days and matched the published result), Pending (a reproduction run is currently in progress), Failed (the most recent reproduction run did not match), or Stale (no reproduction run in the last 30 days).

The reproduction runs are triggered automatically by the CI pipeline on a schedule. For each published result, once per week: clone the repository at the published git hash, run the reproduction command with the published seed, compare the result to the published champion code and fitness score. If they match within tolerance, mark it Verified. If they do not match, raise an alert and investigate.

This dashboard is the public proof that the results are not retroactively fabricated. A result that was genuine will stay Verified across hundreds of weekly checks. A result that was fabricated will fail its first reproduction check. The dashboard makes fabrication impossible to hide.

### DIRECTIVE 8: THE PRIMITIVE SET LIBRARY — A COMMUNITY STANDARD

v8 introduces a formal library of certified primitive sets — vetted, documented, and ready for use in GP experiments. Each primitive set in the library has been audited for contamination against a standard set of benchmark tasks. The library includes:

A minimal arithmetic set for mathematical tasks. A comparison-and-swap set for sorting tasks. A boolean algebra set for logic tasks. A string manipulation set for text tasks. A graph traversal set for routing and pathfinding tasks.

Each primitive set in the library is accompanied by: the contamination audit results for 10 standard tasks, the expected baseline fitness of random programs drawn from that set, the known strengths and weaknesses of that set (what kinds of algorithms it can and cannot express), and the citation for any academic work that has used this primitive set.

This library becomes a community resource. Researchers who want to run GP experiments on a new task can look up the most appropriate primitive set from the library, use the pre-published baseline fitness as their random baseline, and focus their work on the evolution results rather than primitive set design.

### DIRECTIVE 9: THE HONEST CLAIMS REGISTRY

v8 introduces a single document, `docs/honest-claims.md`, that lists every claim this project makes publicly and the evidence supporting each claim. The format is:

Claim: [exact text of the claim as it appears in documentation or posts]
Evidence: [what measurement supports this claim]
Conditions: [what conditions the evidence was gathered under]
Limitations: [what the evidence does NOT show]
Status: Verified / Disputed / Retracted

Every claim in the project's README, in the v1 through v8 docs, in any posts or publications must be registered here. If a claim is found to be unsupported or overstated, its status changes to Disputed or Retracted and the documentation is updated. This registry is the scientific integrity layer of the project.

The first entries to be added are: the Manhattan distance evolution claims (Verified), the sorting marathon claims (Retracted — contaminated primitive set), and the cellular experiment claims (Verified with the stated conditions and limitations from the v6 cellular report).

### DIRECTIVE 10: THE OPEN SCIENCE PUBLICATION PIPELINE

v8 introduces a pipeline for turning the project's genuine results into citable academic publications. The pipeline has five stages.

Stage 1 is data collection: results from production runs with full metadata committed to the repository.

Stage 2 is independent replication: a second instance of the system runs the same experiment with different infrastructure and confirms the result.

Stage 3 is peer review simulation: the methodology document for each result is reviewed by at least two researchers external to the project before the result is promoted to the discovery log.

Stage 4 is pre-registration: before running any new experiment, the hypothesis, primitive set, task design, success criteria, number of seeds, and reproduction command are publicly committed to a pre-registration document. This prevents cherry-picking results after seeing the data.

Stage 5 is publication: a structured report in the format of a short scientific paper, including abstract, methods, results, discussion of limitations, and reproduction instructions. Published to the repository and to arXiv.

The Manhattan distance result is ready for Stage 5 now. The clean-primitive sorting result, once it is complete, will be Stage 1–4 and then Stage 5. This pipeline transforms Living Objects from an impressive engineering project into a publishable scientific platform.

---

## PART C: WHAT MANUS MUST DO IN WHAT ORDER

### First Priority — Fix the Foundation Before Running Anything Else

The contamination audit of every task must happen before any new marathon runs. Running 100,000 generations on a contaminated task wastes computation and produces results that must later be retracted. The order is: audit first, fix primitive sets, then run.

The specific sequence is: first audit the sorting primitive set and confirm it is contaminated (takes one hour). Then redesign the sorting primitive set to exclude all direct solution primitives (takes one day). Then run 100 random-initialisation tests to confirm the baseline fitness is near zero (takes two hours). Only then launch the 10,000-generation clean sorting marathon.

Apply the same process to every other task. The entire contamination audit suite can run in parallel — one process per task domain. The results go into `docs/task-contamination-audit.md`. This document is the gate. Nothing in the benchmark leaderboard, the discovery log, or any publication may reference a result from a task that has not passed its contamination audit.

### Second Priority — Complete the Full GP Tree Serialisation

The marathon cannot produce trustworthy reproducible results until the checkpoint system is exact. Approximate checkpoint/resume via source parsing is acceptable for short runs. For a 10,000-generation run that may need to resume after an interruption, exact tree serialisation is mandatory.

Implement the recursive JSON serialisation of GPNode. Test it with a round-trip: serialise a population, load it, run 10 more generations, verify that the fitness trajectory continues from exactly where it stopped. This test must be in the test suite before the 10,000-generation marathon starts.

### Third Priority — Run the Clean Sorting Marathon

After the contamination audit passes and the checkpoint system is exact, launch the clean sorting marathon. Ten thousand generations. Population 50. Five independent seeds declared in advance. Milestone reports at every 1,000 generations. Full fitness curve JSON committed to the repository.

At completion, write the FINAL_REPORT.md for the clean sorting run. This report must include the contamination audit results, the baseline fitness, the generation of first correct sort, the champion's structure, and whether it matches any known sorting algorithm. This report goes into the discovery log if at least 4 of 5 seeds succeed.

### Fourth Priority — Extend the Manhattan Distance Proof to 10,000 Generations

This is the project's best scientific result extended to a larger scale. Run it, measure what happens after the correct solution is found, and publish the results.

### Fifth Priority — Build the Honest Claims Registry

Go through every document from v1 to v8. List every claim. Categorise each one as Verified, Disputed, or Retracted based on the audit findings. Publish the registry. Update the README to reflect the accurate state of the project.

### Sixth Priority — Launch the Observatory With Contamination Transparency

The Observatory must be live with the contamination status panel before it is publicly shared. A public announcement of the Observatory without the contamination transparency would be misleading. The contamination transparency is not optional polish — it is a scientific and ethical requirement.

---

## PART D: THE v8 QUALITY GATES

### Gate 1 — No Result Is Published Without a Passed Contamination Audit

This is the most important gate in v8. Every task must pass the contamination audit before its results can appear in the discovery log, the leaderboard, the README, or any external communication. A result from a contaminated task is labelled Retracted in the honest claims registry.

### Gate 2 — Every Result Must Be Replicated Across 5 Seeds

No single-seed result may be promoted to the discovery log. Five seeds, all declared before the runs start, all within the acceptable success threshold.

### Gate 3 — Every Claimed Discovery Must Be Named or Acknowledged as Unknown

When a result enters the discovery log, the champion's mathematical structure must be described. If it matches a known algorithm, name it. If it does not match any known algorithm, explicitly state that and describe what makes it structurally novel. "An unknown combination of primitives" is not acceptable — there must be a genuine attempt to characterise the structure.

### Gate 4 — All Previous Gates Still Apply

Test coverage, no mocked Observatory data, security audit sign-off, reproducibility verification, performance baseline non-regression. These gates from v7 remain in force.

---

## THE v8 NORTH STAR

After v8 is complete, a researcher who finds this project must be able to:

Read the honest claims registry and understand exactly what has been proven and what has not. Read the contamination audit and understand why each task's primitive set is designed the way it is. Run the clean sorting marathon reproduction command and get the same result. Read the discovery log and understand that every entry has been independently replicated.

The system will be smaller in its claims than v1 through v7. The sorting marathon will be labelled Retracted until the clean-primitive re-run is complete. The number of verified discoveries will be small — just the Manhattan distance family and whatever the clean sorting run produces.

But every claim that remains will be true. Every result will be reproducible. Every benchmark will be free of contamination. Every discovery will be genuine.

A smaller set of honest results is worth infinitely more than a large set of contaminated ones.

The engine is real. The proof of concept is real. The scientific standard is now real too.

---

## APPENDIX: THE STATE SUMMARY AS OF v7 AUDIT

| Component | Status | Evidence |
|---|---|---|
| GP Engine (AST-based) | Real and working | 259 tests pass |
| Manhattan distance evolution | Genuinely proven | 3/3 seeds, 128/128 holdout |
| Sorting marathon (1000 gens) | Retracted — contaminated | `sort1` primitive was in set; fitness=1.0 at gen 0 |
| WebSocket live evolution | Real | `GPPopulation.step()` wired to broadcaster |
| Market fitness verification | Real | evaluator called before listing |
| Bug fixer | Fixed | All bug fixer tests pass |
| Polyglot JS export | Verified | Node.js runtime test passes |
| Polyglot Rust/Go export | Unverified | Skipped — compilers not installed |
| Checkpoint/resume | Approximate | Source-parsing restore, not exact tree restore |
| Cellular experiment (v6) | Real | 7× improvement, documented conditions |
| Cellular evolvable actions | Not yet implemented | V6-05 still open |
| 100,000-gen marathon | Not run | Blocked on contamination fix |
| Observatory (public) | Not deployed | Infrastructure not live |
| Federation protocol | Not implemented | Directive only |
| 20 task domains | 6 of 20 exist | 14 new domains not yet built |

*This table is the truth. v8 is the work of making more rows say Real and fewer say Retracted or Not yet.*
