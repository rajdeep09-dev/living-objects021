# BEAST UPDATE v11 — REAL-WORLD TESTS, VULNERABILITIES, AND THE LEAD SCRAPING QUESTION
## Code-by-Code Audit, Honest Error Analysis, and a Plain-English Answer on What This Can and Cannot Do

> No code snippets in the directives. No hype. Every claim backed by the code that exists right now.
>
> This document answers three things:
> 1. What does the v10 code actually do, module by module?
> 2. What breaks, what is vulnerable, and what are the real errors?
> 3. Can this system do lead scraping and enrichment — and how does it compare to Claude or Codex?

---

## PART A: MODULE-BY-MODULE CODE AUDIT

This section reads every major module and tells you exactly what it does, what it cannot do, and whether it is honest about itself.

---

### MODULE 1 — `evolution/gp_engine.py` — The Core DNA

**What it does:**
This is the heart of the entire system. It defines how organisms are built. An organism is a tree of operations — like a mathematical formula written as a tree instead of a line. The tree is made of "primitives" (allowed operations) and "terminals" (input variables or constants).

The primitive set contains:
- Arithmetic: add, subtract, multiply, divide, max, min, absolute value, square, square root, log
- Boolean: AND, OR, NOT, greater-than, less-than, equal
- List: get first element, get rest, prepend, get length, sort (contaminated — still in DEFAULT set), sum, square all, filter positives, deduplicate
- String: concatenate, uppercase, strip whitespace, split, join, starts-with, replace, length, reverse

**What it honestly cannot do:**
It cannot fetch data from a URL. It cannot read files from disk. It cannot call any external API. It cannot open a database connection. It cannot generate text longer than what string primitives can construct from input. It cannot access the internet in any form. Every primitive is a pure function — same input always gives same output, no side effects.

**Vulnerability found — `sort1` still in DEFAULT_PRIMITIVES:**
Despite the v8 contamination audit declaring `sort1` as a contaminated primitive for sorting tasks, `sort1` remains in `DEFAULT_PRIMITIVES`. This means any task that accidentally uses the default primitive set gets contamination for free. Only the curriculum's `PROHIBITED_PRIMITIVES` list and the clean-sorting evaluator actively exclude it. A new developer who creates a new sorting evaluator without reading the contamination docs will silently get a contaminated task.

**Error found — recursion depth on deep trees:**
The interpreter evaluates trees recursively. Python's default recursion limit is 1,000. A tree of depth 8 with branching factor 3 can reach depth 8 * 3 = 24 nodes deep — safe. But the `max_depth` check is on tree construction, not on crossover between two near-maximum-depth trees. Post-crossover trees can exceed max_depth before the bloat brake runs. On a very long run (100k gens), a crossover between two depth-7 trees can produce a depth-14 tree that is immediately corrected by the bloat brake — but if the bloat brake fails, it hits a RecursionError.

---

### MODULE 2 — `evolution/fitness.py` — The Judge

**What it does:**
This module defines every task the system can evolve programs for. There are 10 evaluators:
SortingEvaluator, PrimeEvaluator, FibonacciEvaluator, StringReverseEvaluator, MaxSubarrayEvaluator, AbsoluteDifferenceEvaluator, ManhattanDistanceEvaluator, CompressionEvaluator, PathfindingEvaluator, GameStrategyEvaluator.

Each evaluator generates test cases with a seed (rotating per generation since v7's VULN-V6-03 fix), runs the organism's tree against each case, and measures correctness. Correctness is the primary score — a fast wrong program scores lower than a slow correct one.

**What it honestly cannot do:**
It cannot evaluate programs that access external data. It cannot measure how well a program scrapes a website. It cannot score a program's ability to write an email or parse a PDF. Every evaluator works on fixed Python objects passed as inputs — lists of numbers, tuples, strings. The evaluation boundary is a pure Python function call with no I/O.

**Vulnerability found — timing side channels in efficiency score:**
The `efficiency` metric measures wall-clock time per evaluation (target: under 25ms). On a shared server (cloud VM with other tenants), wall-clock time is noisy — garbage collection, CPU context switches, and other processes can make a correct fast program appear slow and score lower than a slower correct program. This doesn't affect correctness (the primary score) but it distorts the efficiency metric. On a single-tenant machine this is fine. In production on a shared cloud instance it is scientifically unreliable.

**Error found — GameStrategyEvaluator generates zero test cases:**
`GameStrategyEvaluator.generate_test_cases(seed, n=1)` returns `[(None, None)]`. The evaluator's `_is_correct` method checks if `actual == expected` — but expected is `None`. Any program that returns `None` gets a perfect score on the game theory task. This is a contamination equivalent: `None` is the trivially reachable output (any crashed program returns `None` via the exception handler). The game theory evaluator is broken and must not be used in any benchmark.

---

### MODULE 3 — `evolution/gp_population.py` — The Gene Pool

**What it does:**
Manages a population of organisms. Each organism has a GP tree (genome) and a fitness score. Tournament selection picks parents. Crossover swaps subtrees between parents. Mutation replaces a random node with a new random subtree. Elitism keeps the best N organisms unchanged. The population runs in a loop: evaluate → select → reproduce → repeat.

**What it honestly cannot do:**
It cannot run in parallel across CPU cores. The evolution loop is single-threaded. For a population of 50 organisms evaluated 1,000 times each across 100,000 generations, the total evaluation count is 5 billion. At the measured rate of approximately 0.6–1 generation per second on a phone, that is 100,000 seconds — about 28 hours on a modern laptop, longer on Termux.

**Vulnerability found — no timeout on individual organism evaluation:**
If an organism's tree enters an infinite evaluation loop (theoretically impossible with the current pure primitive set, but possible if the primitive set is extended with any recursive operation), the entire evolution loop hangs. There is no per-organism evaluation timeout. A future developer who adds a recursive primitive without careful bounds checking could deadlock the entire run.

**Error found — checkpoint save writes population trees but `artifact_path` is not set on load:**
`GPPopulation.save()` serialises tree structures correctly (this was fixed in v7). But after loading a checkpoint, `result.artifact_path` is `None` because the EvolutionResult dataclass is reconstructed without passing the artifact directory path. The `reproduce()` SDK function then fails to find the artifact when called on a resumed run. The fix is to pass the artifact path explicitly through the load path.

---

### MODULE 4 — `living_objects/sdk.py` — The User-Facing API

**What it does:**
Wraps the GP engine in a clean four-function API: `evolve()`, `audit()`, `reproduce()`, `export()`. Each function enforces boundaries (max 10,000 generations, max 512 population), saves a JSON artifact for every run, and returns a typed result object.

The `EvolutionResult` dataclass has these real attributes (confirmed by live run):
`run_id`, `task`, `seed`, `generations`, `population_size`, `champion`, `initial_tree_contains_final`, `history`, `curriculum_events`, `execution_boundary`, `artifact_path`, `to_dict()`.

The champion data is at `result.champion` — a dict with `tree`, `tree_sha256`, `generation`, `training_fitness`, `fresh`, `nodes`, `depth`, `source_audit_export`.

**What it honestly cannot do:**
It cannot be installed with `pip install living-objects` — the package is not on PyPI. It cannot evolve a program that makes HTTP requests. It cannot be extended with custom task evaluators without editing the source code directly — there is no plugin API. The `export()` function only supports JavaScript, Rust, and Go for the Manhattan distance task specifically, not for any other task.

**Bug confirmed by live run — documented API is wrong:**
Every piece of documentation says `result.fitness` and `result.source_code`. The actual attributes are `result.champion["training_fitness"]` and `result.champion["source_audit_export"]`. This is a critical usability bug — a new user hits AttributeError on their first line of code after `evolve()`.

**Vulnerability found — run_id format is guessable:**
`run_id = f"BEAST-SDK-V1-{_digest(configuration)[:16].upper()}"` where configuration is `{task, seed, generations, population_size}`. Since all four parameters have limited ranges (task is one of 10 strings, seed is any int, generations is 1–10,000, population_size is 2–512), an attacker who knows a victim's likely parameters can pre-compute run_ids and read their artifact files if the artifact directory is shared. On a single-user local machine this is irrelevant. On a multi-user server it is a privacy vulnerability.

---

### MODULE 5 — `evolution/v9_sorting_curriculum.py` — The Teacher

**What it does:**
Implements a five-stage curriculum for teaching sorting without contaminated primitives. Stage 0: sort 2-element lists. Stage 1: sort 3-element lists. Stage 2: sort 3–5 elements with duplicates. Stage 3: sort 4–6 elements including negatives. Stage 4: sort 2–16 elements general case. Each stage unlocks when 95% of the population achieves 90% mean correctness on 100 test cases. The champion of each stage is injected into the next stage's memome.

**What it honestly cannot do:**
The curriculum has not run beyond unit tests. It has never been run for more than 10,000 generations. Whether it converges — whether Stage 4 is ever reached — is unknown. The five-stage curriculum is a scientific hypothesis, not a proven path to a sorting champion.

**Error found — stage transition uses mean correctness but memome injection copies by reference:**
When a stage champion is injected into the next stage's memome as a cultural seed, the injection copies the genome object. If the population's random generator later mutates one copy of the memome organism, it mutates both (because Python's deepcopy is not called — only a shallow copy). This is a subtle bug where the cultural seed can be unexpectedly modified mid-stage, causing unreproducible results across runs with the same seed.

---

### MODULE 6 — `evolution/v9_federation.py` — The Exchange Protocol

**What it does:**
Signs a discovery record using HMAC-SHA256 with a local secret key. Verifies that a signed record came from a known key. Checks that the record's tree hash matches the local trial artifact before admitting it to the local memome.

**What it honestly cannot do:**
It cannot communicate with another server. It cannot fetch records over the network. "Federation" in this codebase means: sign a JSON file on your machine, send it to another person manually (email, USB drive, whatever), and they run the verify function locally. There is no peer discovery, no registry, no network transport. This is a cryptographic audit trail, not a network protocol.

**Vulnerability found — HMAC secret is stored in plaintext in the config file:**
The federation key is read from a local config file. If the config file is committed to a public repository, the signing key is exposed and any attacker can forge valid-looking discovery records. The documentation must explicitly warn: never commit the config file containing the federation key.

---

### MODULE 7 — `production/api/v9/routes.py` — The HTTP API

**What it does:**
Defines FastAPI routes for evolve, audit, reproduce, export, and curriculum status. Enforces the same parameter bounds as the SDK. Returns JSON responses matching the SDK result types.

**What it honestly cannot do:**
It has never served a real HTTP request. It cannot start without FastAPI installed (`pip install fastapi uvicorn`). There is no authentication on any endpoint — anyone who can reach the server can start an evolution run, consume CPU, and write to the artifact directory. There is no rate limiting in the route code (the v7 doc specified rate limiting; it was never implemented in the routes).

**Vulnerability found — unauthenticated evolve endpoint can exhaust server CPU:**
`POST /v9/evolve` with `generations=10000` and `population_size=512` launches a run that takes hours. There is no authentication, no per-IP limit, no queue — just a direct call to `_execute()`. On a public server, 10 concurrent requests at max parameters saturate any reasonable CPU for days.

**Error found — async endpoint calls sync evolution loop:**
The FastAPI route for `/v9/evolve` is defined as `async def`. But `_execute()` (the evolution loop) is a synchronous function that blocks for the entire run duration. An async FastAPI handler that calls a synchronous blocking function blocks the entire event loop for the duration of the run. This means: one evolution request blocks all other API requests — market queries, audit calls, WebSocket events — until the evolution completes. This must be fixed with `asyncio.to_thread()` or a background task queue before the API can serve more than one user.

---

## PART B: REAL-WORLD TASK TESTS

These are tests a real user cares about — not unit tests that check internal function signatures, but end-to-end verifications that prove the system does what it claims.

### REAL-WORLD TEST 1 — Manhattan Distance: Reproduce on a Fresh Machine

**Test:** Clone the repository, install dependencies, run `python -m pytest evolution/test_gp_engine.py -q` and confirm >50 tests pass. Then run `from living_objects import evolve; r = evolve("manhattan", generations=300, seed=20260814)` and confirm `r.champion["fresh"]["correctness"] >= 0.90`.

**Expected result:** Pass on any machine with Python 3.10+, no internet, no GPU.
**Status:** Should pass. This is the project's most reliable result.
**Failure mode:** If `evolution/` directory is missing from `sys.path`, import fails silently. Fix: run from repository root or set PYTHONPATH.

### REAL-WORLD TEST 2 — Audit a Task for Contamination

**Test:** `from living_objects import audit; result = audit("sorting")`. Inspect `result.status`. It should be "contaminated" or "retracted."

**Expected result:** The audit confirms sorting is contaminated.
**Status:** Depends on the v8-benchmark-ledger.json being up to date. If Manus regenerated the ledger incorrectly, the audit might return a wrong status. Manual verification: check whether `sort1` appears in the sorting evaluator's primitive set.
**Failure mode:** If the ledger JSON key names don't match what the SDK's `audit()` function expects, it raises `KeyError`.

### REAL-WORLD TEST 3 — Export a Champion to JavaScript

**Test:** Run 50 generations of manhattan, then call `from living_objects import export; result = export(champion_result, "javascript")` and check that the returned source is valid JavaScript that computes the same number as the Python version for 5 inputs.

**Expected result:** Valid JavaScript function returned. Must compute correctly.
**Status:** Partially verified — the polyglot export passes syntax tests. Runtime correctness against Node.js is skipped on Termux (no Node.js installed). Not confirmed to actually produce correct results when executed.
**Failure mode:** The JavaScript output uses variable names derived from the Python AST. If the GP tree uses a primitive that has no JavaScript translation, the export crashes with `KeyError`.

### REAL-WORLD TEST 4 — The Sorting Curriculum Stage 0

**Test:** Run `FiveStageSortingCurriculum()` for 5,000 generations on seed 42. Check whether Stage 0 (pairs) is mastered. The mastery criterion is 95% of organisms achieving 95% individual correctness on 2-element sort.

**Expected result:** Stage 0 should be achievable — sorting a 2-element list with comparison and swap primitives is a small problem space.
**Status:** Not yet run at this scale. Unit tests verify the stage logic but not convergence.
**Failure mode:** If the structural primitives (head, tail, cons) are not expressive enough to construct a conditional swap for 2 elements, Stage 0 never converges. This would be a fundamental design flaw in the curriculum primitive set.

### REAL-WORLD TEST 5 — Reproduce a Published Run Exactly

**Test:** Take seed 20260814, run 300 generations on manhattan with population 128. Save. Run again with the same parameters. Compare `result.champion["tree_sha256"]` between the two runs.

**Expected result:** Both runs produce the identical tree hash. The evolution is deterministic given the same seed.
**Status:** Should pass — the GP engine uses Python's `random.Random(seed)` and all operations are deterministic given the same seed.
**Failure mode:** If any primitive uses `time.time()`, `os.urandom()`, or any non-deterministic source, the reproduction fails. Current primitives are all deterministic. Future extensions must be checked for non-determinism before adding.

### REAL-WORLD TEST 6 — GameStrategyEvaluator Returns Correct Score

**Test:** Create a `GameStrategyEvaluator` and evaluate any GP organism against it. Check whether it assigns fitness based on actual game strategy behaviour, not just whether the organism returns `None`.

**Expected result:** Should score organisms based on their strategy quality against a Prisoner's Dilemma opponent.
**Status:** FAILS. The evaluator generates `[(None, None)]` test cases. Any program that returns `None` (the exception-handler fallback) gets perfect correctness. The evaluator is broken.
**Action required:** The `GameStrategyEvaluator` must be disabled and labelled "not ready for use" in the documentation. It must not appear in any benchmark leaderboard.

### REAL-WORLD TEST 7 — Observatory Panel 2 Shows Live Fitness Data

**Test:** Start the production API server, connect to the WebSocket endpoint, run one GP step, verify that a message arrives with `generation`, `best_fitness`, `champion_code` fields.

**Expected result:** One JSON message per generation.
**Status:** Cannot test — FastAPI not installed, server never started, no public URL.
**This is the most important test and it cannot be run today.**

---

## PART C: VULNERABILITY SUMMARY — ALL 8 FOUND IN THIS AUDIT

| ID | Location | Severity | What it is |
|---|---|---|---|
| VULN-V11-01 | `gp_engine.py` | Medium | `sort1` still in DEFAULT_PRIMITIVES — silent contamination for new tasks |
| VULN-V11-02 | `fitness.py` | Critical | `GameStrategyEvaluator` broken — `None` return gets perfect score |
| VULN-V11-03 | `fitness.py` | Low | Wall-clock timing in `efficiency` score is host-noise on shared servers |
| VULN-V11-04 | `gp_population.py` | Medium | No per-organism evaluation timeout — recursive primitive could deadlock |
| VULN-V11-05 | `gp_population.py` | Low | `artifact_path` is `None` after checkpoint resume — `reproduce()` fails |
| VULN-V11-06 | `sdk.py` | Low | `run_id` is deterministic from parameters — guessable on shared servers |
| VULN-V11-07 | `v9_federation.py` | High | HMAC key stored in plaintext config — key exposure if config is committed |
| VULN-V11-08 | `production/api/v9/routes.py` | Critical | Async endpoint calls sync evolution — one request blocks entire server |
| VULN-V11-09 | `production/api/v9/routes.py` | Critical | No auth on evolve endpoint — anyone can exhaust server CPU |

---

## PART D: THE LEAD SCRAPING QUESTION

### Can this system do lead scraping and enrichment for you?

**Short answer: No. Not today. Not without fundamental changes.**

Here is the honest explanation, in plain terms.

### What lead scraping requires

Lead scraping means: go to a website, find email addresses, phone numbers, company names, and LinkedIn URLs, extract them, store them in a list, and then for each lead, go find more information about them (enrichment) — their job title, company size, tech stack, social media — and return a structured record.

That requires: making HTTP requests to URLs, parsing HTML, matching patterns (regex on raw text), handling errors (404s, CAPTCHAs, rate limits), managing state (which leads have been processed), and writing to a database.

### What this system actually does

The GP engine runs pure functions. It takes a Python value as input and returns a Python value as output. It cannot make HTTP requests — there is no network primitive. It cannot read files — there is no file I/O primitive. It cannot store data between calls — every evaluation is stateless. The only string operations it has are: concat, uppercase, strip, split, join, starts-with, replace, get-length, reverse.

So if you gave it a raw HTML string as input, the best it could do is strip whitespace, split on spaces, and rejoin parts. It cannot parse `<a href="mailto:...">` tags. It cannot follow links. It cannot handle pagination. It cannot authenticate to LinkedIn.

### Why this matters

The system is a mathematical function evolver. It is very good at evolving pure functions that transform inputs to outputs according to a measurable fitness criterion. It proved this with Manhattan distance — give it four numbers, return the correct distance. It failed at sorting without a curriculum because sorting is harder to express as a pure function from scratch.

Lead scraping is not a function — it is a workflow. It involves multiple tools, multiple HTTP calls, state, error handling, and domain-specific knowledge (what does a valid email look like? what is a professional title format?). No amount of genetic programming generations can evolve a scraper from pure arithmetic and string primitives, because the scraper's actions (HTTP requests) are not in the primitive set and cannot be added without completely redesigning the safety model.

### What would need to change to make scraping possible

The primitive set would need HTTP primitives: `fetch(url)`, `parse_html(html)`, `extract_links(html)`, `match_regex(pattern, text)`. These primitives would need to be safe in a sandbox — which means rate limiting, domain whitelisting, timeout enforcement, and result size limits. That is a significant engineering project, distinct from everything currently in the repository.

Even then, evolving a correct scraper would require a fitness evaluator that measures scraping quality — which means you need labelled data (for 100 companies, here are the correct lead records) to compare evolved programs against. Generating that labelled dataset is itself a significant task.

### Can it ever beat Claude or Codex at lead scraping?

No. Not in any number of generations. Here is why, clearly stated.

Claude and Codex generate text that is code. They use billions of parameters trained on the entire public internet including every scraping library, every CRM integration, every API documentation page. When you ask Claude to write a scraper, it draws on examples of hundreds of thousands of real scrapers written by real developers.

This GP system evolves programs from scratch using only the primitives you give it. It has no knowledge of HTML, no knowledge of email formats, no knowledge of LinkedIn's structure. It starts from random noise and builds upward using only comparison, arithmetic, and string manipulation.

The comparison is not "evolution versus LLM at the same task." The comparison is more like: "a person who is blind and can only feel shapes versus a person who can see" — for a task that requires sight. Evolution is extremely powerful for tasks where you can define a clear measurable fitness function and the answer can be assembled from the allowed primitive set. It is zero for tasks that require tools not in the primitive set.

### What this system IS genuinely better at than Claude or Codex

Discovering novel mathematical formulas. The Manhattan distance result proves this in a narrow sense: the system found three structurally different but mathematically equivalent correct formulas independently across five seeds. Claude would write one formula. The GP system found all three. For symbolic regression — discovering the equation underlying a dataset — evolved GP systems have historically outperformed LLMs, because LLMs memorise known formulas while GP searches the space of novel expressions.

For tasks with a clear measurable correctness criterion, no ambiguity, and a well-designed primitive set, this system can find solutions that no human would think to write because it explores the entire search space systematically. That is valuable. It is just not useful for scraping.

### The Realistic Use Case

The honest use case for this system today is:

Give it a mathematical or algorithmic task with a measurable correctness function. Tasks like: find the equation that fits this dataset, find a routing heuristic that minimises delivery time on these test graphs, find a signal processing function that removes noise from this type of data. Define fitness. Run evolution. Inspect the champion. Verify it on fresh data.

This is genuine value that Claude and Codex are not designed to provide. It is niche, it is scientific, and it is real.

---

## PART E: THE v11 MANDATES — FIX BEFORE NEXT VERSION

### MUST FIX (blocks production use)

MANDATE 1: Fix `GameStrategyEvaluator`. Either implement it correctly with real Prisoner's Dilemma simulation, or remove it from `DEFAULT_PRIMITIVES` and mark it "not ready." Do not leave a broken evaluator in the codebase that awards perfect scores to crashed programs.

MANDATE 2: Fix async/sync mismatch in the production API. The evolve endpoint must use a background task queue (Celery, ARQ, or asyncio.to_thread) so one long-running evolution does not block all other API calls.

MANDATE 3: Add authentication to the production API. At minimum: an API key in the Authorization header. Until this exists, the production API must not be publicly deployed.

MANDATE 4: Fix the `result.fitness` / `result.champion["training_fitness"]` mismatch. Add top-level `fitness` and `source_code` properties to `EvolutionResult` that delegate to the champion dict. Update all documentation to show the correct API.

### SHOULD FIX (improves reliability)

MANDATE 5: Remove `sort1` from `DEFAULT_PRIMITIVES`. Move it to an `opt-in` set called `CONVENIENCE_PRIMITIVES`. New evaluators will not accidentally get it.

MANDATE 6: Add per-organism evaluation timeout (500ms max). Wrap every `tree.evaluate(inputs)` call in a timeout context. This prevents any future recursive primitive from deadlocking the run.

MANDATE 7: Add `deepcopy` in the curriculum's memome injection to prevent shared-reference mutation bugs.

MANDATE 8: Add a warning to the federation documentation: "Never commit your federation config file. It contains your signing key."

### METRICS THAT MUST BE MEASURED BEFORE CLAIMING PRODUCTION READY

These four numbers must be measured and committed before the system is called production-ready:

Time to first result on a clean laptop: how many minutes from `git clone` to receiving a correct champion from `evolve("manhattan", generations=300, seed=42)`?

Generations per second on a standard cloud VM (2 CPU, 4 GB): the Termux device measures ~0.6–1 gen/sec for population 50. A cloud VM should be 5–10×. This number determines how long the 100k-gen run takes.

Maximum safe population size before memory exceeds 1 GB: each organism holds a tree of up to 64 nodes. Measure peak memory for population sizes 50, 100, 200, 500.

API request latency for read endpoints (audit, reproduce) when an evolution run is in progress: this is currently zero (they're blocked by the sync/async bug). After the fix, measure the actual latency.

---

## THE STATE TABLE — v11 EDITION

| Component | Works Today | Proven by Test | Production Safe |
|---|---|---|---|
| GP engine — tree evolution | Yes | Yes (1,558 pass) | Yes |
| Manhattan distance discovery | Yes | Yes (5/5 seeds) | Yes |
| `evolve()` SDK function | Yes (local) | Yes | No (wrong API docs) |
| `audit()` SDK function | Yes | Partially | No (ledger format fragile) |
| `reproduce()` SDK function | Yes | Yes | No (artifact_path bug) |
| `export()` to JS | Code exists | Syntax only | No (runtime unverified) |
| GameStrategyEvaluator | Broken | Fails real-world test | No |
| Production API | Code exists | Never run | No (async/sync bug, no auth) |
| Observatory (live URL) | Does not exist | N/A | N/A |
| Lead scraping | Impossible today | N/A | N/A |
| pip install | Not on PyPI | N/A | N/A |
| 100k-gen sorting run | Not started | N/A | N/A |

---

## THE FINAL PLAIN-ENGLISH SUMMARY

**What this is:** A real, working system that evolves mathematical programs from scratch without using an AI language model. It genuinely proved it can discover the formula for Manhattan distance independently across five random experiments.

**What this is not:** A web scraper, an AI assistant, a general-purpose code writer, or a replacement for Claude or Codex. It operates only within the boundary of operations you explicitly allow it, on the data you explicitly give it, with no ability to reach outside those boundaries.

**Lead scraping answer:** No. Not today. The system needs HTTP primitives, HTML parsing, and a scraping fitness evaluator — none of which exist. Building those would take months and is a separate project.

**Beat Claude at lead scraping:** Never, in any number of generations, without adding HTTP primitives. With HTTP primitives, possibly better at narrow specialised scraping tasks after 100,000+ generations — but this is speculative and has never been tested.

**The one thing it beats Claude at right now:** Finding novel mathematical formulas by exhaustive search of program space. Manhattan distance. Symbolic regression. Algorithm discovery in constrained primitive sets. That niche is real, useful in science and engineering, and provably demonstrated.

**Three things that would make this ready for the world:** Fix the SDK API docs (one day). Deploy the Observatory (one week). Submit the arXiv paper (one day). Everything else is science that improves it over time.
