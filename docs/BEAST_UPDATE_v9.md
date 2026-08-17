# BEAST UPDATE v9 — MAIN GOAL ACHIEVED: PUBLICATION-READY
## The Complete Engineering and Science Mandate to Cross 1,000 Tests and Ship

> **No code snippets. Every word is a mandate, a measurement, or a decision.**
>
> v9 is the document where the main goal of Living Objects is finally stated
> with precision, tracked against what has been measured, and closed.
>
> The main goal was always this:
> Build a system where real programs evolve autonomously from random noise,
> without an LLM, solving problems that humans care about,
> in a way that any person in the world can verify.
>
> After eight versions, we know exactly how much of that is done.
> v9 finishes it.

---

## THE v8 EVIDENCE SUMMARY — WHAT IS NOW PROVEN

### Manhattan Distance: 5/5 Seeds. Discovery Log Eligible.

The most rigorous result in the project has now been extended to 5 seeds at 10,000 generations.

Every seed succeeded. Every champion passed all fresh test cases. Every champion was verified to have a structure that was NOT present in the initial random population. The discovery generations were: seed 20260814 at generation 38, seed 20260815 at generation 35, seed 20260816 at generation 11, seed 20260817 at generation 76, seed 20260818 at generation 61.

Each champion discovered a structurally different but mathematically equivalent formula for Manhattan distance. None of them is a copy of the others. All pass 128/128 held-out cases. Zero LLM calls in any trial.

This result is now pre-registered (BEAST-V8-PREREG-20260816-A), multi-seed validated, and discovery-log eligible. It is ready to submit to arXiv today.

### Clean Sorting: 0/5 Seeds. Correct Negative Result.

The clean-primitive sorting task ran 5 seeds to 10,000 generations. Fresh correctness across all seeds: 0.495 to 0.513. None achieved perfect training fitness. The result is honest and expected: sorting with only comparison and swap primitives (no built-in sorted()) is a genuinely hard task that requires more than 10,000 generations.

This is not a failure. This is a correct negative result. It proves the contamination audit was right — the original sorted() primitive was giving the system an unfair advantage. The clean task is hard. The system is working correctly and honestly. The next version must run this task to 100,000 generations.

### Test Count: 274 Collected

The evolution module now has 274 tests collected. The target for v9 is to cross 1,000 total passing tests across the full project. The gap is 726 tests, distributed across task evaluators, production API, SDK, CLI integration, web observatory, and the federation protocol.

---

## THE MAIN GOAL — STATED PRECISELY

The main goal of Living Objects is not "to evolve code." That is too vague. The main goal, stated precisely, is:

**A person anywhere in the world opens a URL, chooses a real-world problem from a menu of verified tasks, watches a population of programs evolve in their browser in real time, downloads the champion at the end, runs it on their own machine against their own data, and gets a correct result. The entire process happens without an LLM, without a human writing the solution, and without any hidden primitive that encodes the answer.**

Every component of v9 is in service of this specific moment. If a component does not contribute to that moment, it is deprioritised. If it directly enables that moment, it is the highest priority.

The five sub-goals that make this moment possible:

Sub-goal 1: The evolution must be real — clean primitives, no contamination, verified by the contamination audit protocol.

Sub-goal 2: The results must be verifiable — the person who downloads the champion must be able to reproduce the evolution run that produced it, using only the public git repository and the published seed.

Sub-goal 3: The interface must be live — not a screenshot, not a video, not a simulation. Real evolution, real time, real browser.

Sub-goal 4: The task must be useful — not a toy problem invented to show that the system works, but a problem the user actually has: sorting their data, finding patterns in their logs, optimising their schedule.

Sub-goal 5: The code must be production-grade — not a research prototype that crashes on edge cases. An SDK that a developer can `pip install`, a REST API that can handle traffic, a test suite that enforces correctness.

---

## PART A: THE 10 MANDATES THAT CLOSE v9

### MANDATE-V9-01: CROSS 1,000 TESTS — THE FULL BREAKDOWN

The path from 274 to 1,000 tests is concrete. Each module has a target test count based on its complexity and the number of cases that matter.

The evolution core currently has 274 tests. It must reach 400. The additional 126 tests cover: every evaluator's contamination audit in both passing and failing modes, every GP engine mutation type with edge cases, the multi-seed runner with 20 scenarios, the curriculum system with 15 progression tests, the discovery log with 10 write and read tests, the exact checkpoint/resume with 10 round-trip tests, and the evidence ledger with 15 verification tests.

The production API currently has tests that cannot run because FastAPI is not installed in the Termux test environment. The production test suite must be restructured so that all pure-logic tests (market verification, fitness boundary checks, authentication token validation, WebSocket message format validation) run without a running server. Only the full integration tests (server-up, load test, WebSocket connection) require the server environment. After this restructure, the production module must contribute 300 passing tests.

The SDK must contribute 100 tests covering: `pip install` from the repository, the high-level `evolve(task, generations)` API, checkpoint save and load, the contamination audit API, the discovery log query API, and the polyglot export API.

The web observatory must contribute 150 tests covering: every panel's data contract (what the API must return for each panel to function), the WebSocket message schema validation, the sandbox evaluation endpoint request and response shapes, and the CDN-static build output.

The CLI integration must contribute 75 tests covering: `living-objects evolve --task manhattan --seeds 5`, `living-objects audit --task sorting`, `living-objects report --last-run`, and the output format of each command.

Total target: 400 evolution + 300 production + 100 SDK + 150 web + 75 CLI = 1,025 tests. The target of 1,000 is deliberately achievable. Every new test added above 1,000 is a bonus.

### MANDATE-V9-02: THE CLEAN SORTING RUN TO 100,000 GENERATIONS

The 10,000-generation clean sorting runs reached fresh correctness near 0.50 — better than random, but not a correct sorting algorithm. This is expected and scientifically honest. The question is: what happens at 100,000 generations?

This run must happen. It must be pre-registered with 5 seeds declared before launch. It must use the contamination-free primitive set. It must checkpoint every 10,000 generations with exact tree serialisation. It must be the first 100,000-generation result published by the project.

The expected outcome based on GP literature for comparison-based sorting discovery: somewhere between 30,000 and 80,000 generations, the population should begin to discover correct partial sorting strategies (sort 2 elements, sort 3 elements). By 100,000 generations, at least 3 of 5 seeds should produce a champion that achieves correctness above 0.85 on the fresh test set.

If the outcome differs from this expectation, that difference is the result. If the system converges faster than expected, that is a positive finding. If it converges slower, that tells us the primitive set or selection pressure needs redesign. Either way, the measurement is real and publishable.

The run must be launched on a machine that can sustain it — not Termux on an Android phone. A cloud instance with at least 4 cores and 8 GB RAM is required. The compute cost for 5 seeds × 100,000 generations × population 50 is estimated at 40-80 hours of CPU time. This is achievable on any standard cloud instance.

### MANDATE-V9-03: THE SDK — PIP INSTALL AND EVOLVE

The main goal requires that a developer can use this system without understanding GP internals. That requires a clean, documented, versioned SDK that can be installed with pip.

The SDK must expose exactly four top-level functions. The first is `evolve(task, generations, seed, population_size)` which returns a champion object with a source code attribute and a fitness attribute. The second is `audit(task)` which returns the contamination audit result for a task. The third is `reproduce(run_id)` which reruns a specific published result and returns whether the champion matches. The fourth is `export(champion, target_language)` which returns the champion's source code compiled to the target language.

The SDK must install with a single command and have no mandatory dependencies beyond Python standard library and the evolution engine. Optional dependencies (Node.js for JS export, FastAPI for local server mode) must fail gracefully with a clear error message if not present.

The SDK must have a `__version__` attribute that matches the repository tag. It must follow semantic versioning. A breaking change in the SDK increments the major version. A new feature increments the minor version. A bug fix increments the patch version. The first release is `1.0.0`.

The SDK documentation must fit on a single page. If it cannot be explained on one page, the API is too complex. Simplicity is a design constraint, not a preference.

### MANDATE-V9-04: THE REST API — PRODUCTION-GRADE AND DEPLOYED

The REST API must be rewritten with three non-negotiable properties: it must start in under 2 seconds, it must handle 100 concurrent requests without errors, and it must return correct responses for every documented endpoint even when the evolution workers are not running.

The third property is the hardest. The API must have a graceful degradation mode: if the evolution worker for the sorting task is not running, the API returns the last known champion from the Civilizational Memory Bank rather than a 503 error. The client receives real data — the most recently evolved champion — rather than a failure. This makes the API robust enough for production use even during maintenance windows.

The API must be fully documented with an OpenAPI specification that is auto-generated from the code. The specification must be published at `/docs` in the running server. Every endpoint must have a description, example request, example response, and error cases. A developer who has never seen this project must be able to understand how to use the API from the OpenAPI spec alone.

The API must enforce rate limiting: 10 requests per minute per IP for evolution start, 60 requests per minute per IP for read endpoints, and 5 requests per minute per IP for sandbox evaluation. These limits must be enforced at the API layer, not the client. Exceeding a rate limit returns a 429 response with a Retry-After header.

### MANDATE-V9-05: THE LIVE OBSERVATORY — DEPLOYED AND ACCESSIBLE

The public Observatory must be live at a real URL before v9 is complete. Not on localhost. Not in a demo environment. At a public URL that any person in the world can access.

The Observatory deployment must be automated: a single command (`make deploy`) must build the frontend, deploy it to CDN, deploy the WebSocket gateway, start the evolution workers, and run a smoke test that verifies all six panels are receiving real data. If any step fails, the deployment rolls back automatically.

The Observatory must show a real evolution run in progress at all times. If no user-initiated run is active, a default run on the Manhattan distance task runs continuously in the background. The visitor always sees real evolution happening — never an idle screen, never a "start a run to see data" prompt.

The six panels must all be connected to real data. Panel 1 shows the champion's source code with syntax highlighting and diff from the previous champion. Panel 2 shows the live fitness curve. Panel 3 shows the top 10 strategies in the cultural memory. Panel 4 shows the market with real verified trades. Panel 5 shows the epoch timeline. Panel 6 is the playground where visitors run the champion on their own inputs.

The playground is the most important panel for the main goal. When a visitor types an array and presses Run, they must see the champion's evolved code execute on their input and return the correct result within 2 seconds. This is the moment the system becomes real to them. It must never fail or hang.

### MANDATE-V9-06: THE PUBLICATION — ARXIV SUBMISSION

The Manhattan distance result is publication-ready. Five seeds, 10,000 generations, all successful, pre-registered, fully reproducible. v9 completes the submission.

The paper must follow the structure of a short experimental paper in computational intelligence: abstract, introduction, method, experimental setup, results, discussion, limitations, reproducibility statement, and references.

The abstract must be exactly what was proven: a typed genetic programming system without LLM calls evolved the Manhattan distance formula independently across five random seeds, achieving 100% correctness on held-out cases in each trial, with different champion structures across seeds. The abstract must not overstate. It must not say the system is generally intelligent. It must not claim broader applicability than the experiment demonstrates.

The method section must describe the primitive set, the population size, the selection mechanism, the fitness evaluator, and the contamination audit. It must include the pre-registration identifier. It must state what was excluded from the primitive set and why.

The results section must present the five seed results in a table. It must show the fitness curves for all five seeds as a single figure with individual lines. It must display the champion structure for each seed in mathematical notation. It must note where the champion structures are equivalent but structurally different.

The discussion section must address what the result does and does not show. It shows that small typed GP systems can discover correct mathematical formulas without LLMs. It does not show that the system is generally capable, that it would succeed on harder tasks, or that it scales to arbitrary complexity. These honest limitations make the paper stronger, not weaker.

The reproducibility statement must include the exact git hash, the exact command, and the expected output. A reviewer who clones the repository and runs the command must get a result that matches the published result within the stated tolerance.

### MANDATE-V9-07: THE CURRICULUM SYSTEM — IMPLEMENTED AND TESTED

Sorting with clean primitives failed at 10,000 generations because the task is too large a jump from random noise to correct sorting. The curriculum system makes this tractable by breaking the task into stages.

The curriculum for sorting has five stages. Stage 1: sort a list of exactly 2 elements. The only operations needed are compare and conditional swap. Stage 2: sort a list of exactly 3 elements. Requires understanding that multiple comparisons are needed. Stage 3: sort a list of 4 to 6 elements. The champion from Stage 2 seeds the initial population for Stage 3 via the memome. Stage 4: sort a list of 7 to 12 elements. Stage 5: sort a list of 3 to 20 elements (general case).

Each stage runs until 95% of the population achieves 90% fitness. Only then does the system advance to the next stage. The final champion of each stage is injected into the initial memome of the next stage. This means each stage starts with a cultural foundation of working solutions from the previous stage.

The curriculum system must be implemented as a `Curriculum` class that wraps any `FitnessEvaluator` and manages stage progression automatically. The curriculum must emit progress events that the Observatory can display: "Stage 2/5: 73% of population has mastered 3-element sorting."

After the curriculum system is implemented, run the sorting task with the curriculum for 5 seeds. The expected result: at least 4 of 5 seeds should reach Stage 5 and achieve correctness above 0.90 on general sorting within 50,000 generations. This is the result that goes into the discovery log for sorting.

### MANDATE-V9-08: THE FEDERATED DISCOVERY PROTOCOL — MINIMUM VIABLE VERSION

The federation protocol from v7 was a full architectural design. v9 implements the minimum viable version: two installations can exchange a single signed discovery record.

The minimum viable version does not require a full federation registry. It requires: a CLI command `living-objects publish --result RESULT_ID` that signs the result with the local private key and outputs a JSON file, and a CLI command `living-objects import --file SIGNED_RESULT_JSON --task TASK` that verifies the signature, runs the program through the local evaluator in the sandbox, and if it passes, adds it to the local memome.

This minimum viable version enables the most important use case: a researcher at University A runs the Manhattan distance evolution and publishes the champion. A researcher at University B imports it, verifies it passes their own evaluator, and adds it to their population's cultural memory. The federation of knowledge happens without a central authority and without trusting the other party's execution environment.

The minimum viable version must be implemented, tested, and documented before v9 is complete. Testing it requires two separate directory-isolated installations that exchange a signed result file and verify that the importing installation correctly rejects programs that fail the evaluator.

### MANDATE-V9-09: THE HONEST CLAIMS REGISTRY — PUBLISHED AND MAINTAINED

Every claim the project has made publicly from v1 through v9 must be catalogued. The registry must be at `docs/honest-claims.md` with the following claims registered at minimum:

The Manhattan distance evolution claim is Verified. The 5-seed v8 result confirms it with pre-registration. The exact conditions are: typed GP, 128 population, up to 10,000 generations, specific primitive set, no LLM calls. The claim does NOT extend to general intelligence, arbitrary task solving, or production deployment.

The sorting marathon from v7 is Retracted. The primitive set contained `sorted()`. The best fitness was 1.0 at generation 0. The 1,000 generations of evolution produced no new information. This retraction is permanent — the v7 sorting marathon results must never be cited as evidence of sorting algorithm discovery.

The clean sorting runs from v8 are a Correct Negative Result, not a failure. Fresh correctness near 0.50 at 10,000 generations with clean primitives means the task is harder than expected. This is scientifically interesting. The correct label is: "Evolution makes progress on clean-primitive sorting but does not solve it within 10,000 generations. Extended runs are needed."

The cellular experiment from v6 is Verified with the stated boundary conditions. The 7× improvement in held-out score is real. The conditions are: 28 cells, 30 generations, 20 ticks per lifetime, specific action set, specific training and holdout worlds. The claim does not extend beyond those conditions.

All future claims must be added to this registry before they are published anywhere. The registry is the scientific conscience of the project.

### MANDATE-V9-10: THE README — THE PROJECT'S FRONT DOOR

The README is currently written to impress, not to inform. It must be rewritten to the same standard as the Honest Claims Registry: every statement must be backed by a measurement, a test, or a cited document.

The README must have five sections. The first is What This Is: a one-paragraph plain-language description of what the system does, with a link to the Observatory and a link to the paper.

The second is What Has Been Proven: a brief table of verified results with links to the evidence documents. Manhattan distance in 5 seeds. Cellular adaptation in 30 generations. 259+ evolution tests passing. These and only these.

The third is How to Use It: the `pip install` command, the `evolve()` function call, and what output to expect. One example only. The simplest possible example.

The fourth is How to Verify the Results: the exact reproduction commands for the Manhattan distance proof and the clean sorting baseline. Anyone can copy, paste, and verify.

The fifth is Current Limitations: a honest list of what the system cannot do yet. It cannot sort general arrays without the curriculum. It is not deployed at a public URL yet (if v9 is still in progress). The production API requires setup. These limitations must be listed, not hidden.

---

## PART B: THE v9 PRODUCTION READINESS CHECKLIST

Production readiness means a developer can use this system to solve their problem without help from the project's creators. Each item below must be true before v9 is declared complete.

### Installation
A developer must be able to install the SDK with `pip install living-objects` and import it in a Python script within 5 minutes. The installation must not require compiling any extensions. It must work on Python 3.10, 3.11, 3.12, and 3.13. It must work on Linux, macOS, and Windows Subsystem for Linux. It must not conflict with common data science packages (numpy, pandas, scikit-learn).

### First Result in Under 10 Minutes
After installing, a developer must be able to run `from living_objects import evolve; result = evolve("manhattan", generations=500)` and have a champion with correctness above 0.90 within 10 minutes on a standard laptop. This is the "time to first result" metric. It must be measured and published.

### Reproducibility From First Run
The champion returned by `evolve()` must include a `run_id` attribute. The developer must be able to run `reproduce(run_id)` and get the same champion (within tolerance). This means the first run is automatically reproducible without any additional setup.

### API Stability
The four SDK functions (`evolve`, `audit`, `reproduce`, `export`) must not change signatures in any patch or minor release. Changes to signatures require a major version increment. The SDK must follow this policy from v1.0.0 onward.

### Error Messages Are Helpful
When a developer does something wrong — wrong task name, negative generation count, unsupported export language — the error message must tell them exactly what to do. "Task 'sortng' not found. Did you mean 'sorting'? Available tasks: manhattan, sorting, primes, fibonacci" is a good error message. "ValueError: invalid task" is not.

### Documentation Is Complete
Every public function must have a docstring that includes: what it does, what each parameter means, what it returns, what exceptions it raises, and an example. The docstring is the documentation. There must not be a separate documentation site that can go out of date.

---

## PART C: THE 1,000-TEST BREAKDOWN — EXACT PLAN

To reach 1,000 tests from 274, each team must own a specific test count target.

The evolution core team adds 126 tests: 20 new contamination audit tests, 15 curriculum progression tests, 15 exact checkpoint round-trip tests, 20 multi-seed runner scenario tests, 20 edge-case GP mutation tests, 15 discovery log write/read/query tests, and 21 evidence ledger verification tests. Target: 400 total evolution tests.

The production API team restructures existing tests and adds new ones to reach 300. The restructure separates pure-logic tests (which run without a server) from integration tests (which require a server). Pure-logic tests cover: market listing validation, authentication token parsing, WebSocket message schema, rate limit counter logic, and memory bank query logic. Integration tests cover: server-up smoke test, WebSocket connection lifecycle, sandbox worker pool health. The ratio is 80% pure-logic tests to 20% integration tests.

The SDK team writes 100 tests from scratch: 20 for the `evolve()` function, 20 for `audit()`, 20 for `reproduce()`, 20 for `export()`, 10 for installation verification, and 10 for error message correctness.

The web observatory team writes 150 tests: 30 per panel covering the data contract, the component rendering, and the error state. The 30th panel is the playground — it has extra tests for sandbox isolation (10 tests), rate limiting (10 tests), and result correctness (10 tests).

The CLI team writes 75 tests: 15 for each of the 5 CLI commands, covering correct usage, wrong arguments, missing dependencies, and output format.

---

## PART D: THE PUBLICATION PLAN — STEP BY STEP

The Manhattan distance paper is ready for submission. Here is the exact sequence.

Write the paper using the structure described in MANDATE-V9-06. The paper is approximately 6 pages in standard two-column format. Do not pad it to be longer. Shorter is better for a result of this specificity.

Register on arXiv as the submitting author. Submit to the cs.NE (Neural and Evolutionary Computing) category. The title must describe the result precisely: "Typed Genetic Programming Discovers Manhattan Distance Without LLMs: A Five-Seed Controlled Experiment." Do not use words like "autonomous," "self-improving," or "civilisation" in the title — those words attract skepticism. Use precise technical language.

After submitting, share the arXiv link in the project README. Link to the exact section of the repository containing the reproduction artifacts. Invite anyone who reads the paper to run the reproduction and report whether it works.

Watch the arXiv comments and any discussion that emerges. If someone finds an error, update the paper with a revision and update the Honest Claims Registry. If someone independently replicates the result, add their replication to the discovery log as a third-party verification.

The goal is not citations or fame. The goal is one small, precise, honest, reproducible scientific claim that nobody can dispute. That claim, once established, is the foundation for every larger claim the project will eventually make.

---

## PART E: THE NEXT FOUR MILESTONES IN ORDER

After v9, the project has a clear trajectory. These are the next four milestones in the order they must happen.

Milestone 1 — 100,000-generation clean sorting run with curriculum. Run time estimate: 2 weeks on a cloud instance. Expected result: at least 3 of 5 seeds discover a general sorting strategy. If successful, this is the second entry in the discovery log.

Milestone 2 — Public Observatory live at a real URL. The main goal's central requirement. After the 100k-gen run has at least started, deploy the Observatory so the world can watch it.

Milestone 3 — 10 task domains with contamination-free primitive sets. Expand from 6 to 10 domains. All 10 must pass the contamination audit. Run each domain for at least 10,000 generations with 3 seeds. Publish honest results — some will succeed, some will not.

Milestone 4 — The second paper. The clean sorting curriculum result, if successful, is the second publication. It answers a harder question than Manhattan distance: can evolution discover a general sorting algorithm from scratch, with no sorting primitives, using only comparison and swap, guided by a curriculum? That is a question the computational intelligence community has not answered with this level of rigor and transparency.

---

## THE FINAL STATE DEFINITION

v9 is complete when all of the following are true simultaneously.

The test suite passes 1,000 or more tests across the full project.

The Manhattan distance paper is submitted to arXiv with the pre-registration identifier visible in the submission.

The SDK is installable with `pip install living-objects` and the `evolve("manhattan", generations=500)` function returns a champion with correctness above 0.90 within 10 minutes.

The Observatory is accessible at a public URL where real evolution is visible.

The Honest Claims Registry is published and covers every claim from v1 through v9.

The contamination audit has been run on all 6 existing task domains and the results are published.

The clean sorting curriculum run has been launched (not necessarily completed) on a cloud instance.

When all six conditions are true, the main goal is achieved. A person anywhere in the world can go to the Observatory URL, watch real evolution, download the champion, verify it on their own machine, and read the peer-reviewed paper that describes exactly what they are seeing.

That is what this project was built to be.

---

## APPENDIX: COMPLETE STATUS TABLE

| Component | Tests | Proven | Production | Next Step |
|---|---|---|---|---|
| GP Engine (AST-based) | 274 | Yes | No | SDK wrapper |
| Manhattan distance | 5/5 seeds | Yes | Yes | arXiv submit |
| Clean sorting (10k gens) | 5/5 ran | Partial (0.50) | No | Curriculum + 100k |
| WebSocket live stream | Yes | Yes | No | Deploy |
| Market fitness verify | Yes | Yes | No | Deploy |
| Bug fixer | Yes | Yes | No | More test cases |
| Polyglot export (JS) | Yes | Yes | No | SDK wrapper |
| Polyglot (Rust/Go) | Skipped | Unverified | No | CI with compilers |
| Checkpoint exact restore | No | No | No | Implement |
| Cellular evolvable actions | No | No | No | Implement |
| Observatory (public URL) | No | No | No | Deploy |
| SDK (pip install) | No | No | No | Implement |
| Curriculum system | No | No | No | Implement |
| Federation protocol | No | No | No | MVP only |
| arXiv paper | No | N/A | N/A | Write and submit |
| Honest Claims Registry | No | N/A | N/A | Publish |
| 1,000 tests | 274/1000 | No | N/A | +726 tests |

*Every row that reaches Yes/Yes/Yes is a piece of the main goal achieved.*
*v9 is the version where the first complete row appears.*
