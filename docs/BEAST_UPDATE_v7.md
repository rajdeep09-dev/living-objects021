# BEAST UPDATE v7 — THE OPERATIONAL CIVILIZATION
## From Proven Engine to Live Deployed World

> **v6 proved the engine is real.**
>
> Three independent trials. 128/128 holdout cases. Zero LLM calls.
> The population evolved Manhattan distance from scratch in 300 generations.
> The cellular experiment achieved 7× improvement in held-out score over 30 generations.
> 33/34 v6 tests pass. 141 new files. 65,412 new lines. The engine is real.
>
> **v7 is the operational guide for what happens next.**
>
> This document does not contain code snippets.
> It contains the engineering decisions, architectural directives, integration sequences,
> and innovation mandates that 1,000 engineers must execute simultaneously to take
> this proven engine and turn it into a living, deployed, self-sustaining digital
> civilization that anyone on Earth can access from a browser.
>
> Read every word. Every section is a concrete mandate, not a suggestion.

---

## THE HONEST STATE AFTER v6

Before prescribing v7, every engineer must understand exactly what is real and what is not.

### What Is Provably Real Right Now

The GP engine runs on real Abstract Syntax Trees. Not floats in a template. Real programs.

Three predeclared seeds evolved Manhattan distance independently. Each trial started from random noise. Each found the correct formula — `abs(dx) + abs(dy)` — within 300 generations. Each champion passed 128/128 held-out test cases that were never used in selection. Zero LLM calls were made in any trial. The artifacts are committed to `docs/artifacts/non-llm-proof-release/` and are independently verifiable.

The cellular experiment ran 28 cells for 30 generations on a resource-and-hazard grid. The promoted cell policy improved held-out environment score from 0.0715 to 0.5064 — a 7× gain. The held-out worlds were never in the training set.

`evolution/gp_engine.py`, `evolution/gp_population.py`, `evolution/fitness.py`, `evolution/bug_fixer.py`, `evolution/program_market.py`, and `evolution/polyglot_export.py` all exist. The GP infrastructure is scaffolded and largely working.

33 out of 34 v6 tests pass in 5 seconds on the test device.

### What Does NOT Work Yet

One bug fixer test fails: `test_candidate_only_bug_fixer_returns_small_passing_proposal`. The fixer returns `None` instead of a passing fix. This is a confirmed bug in the candidate pool generation logic.

The live WebSocket stream does not connect to a running `GPPopulation`. The Observatory panels show mocked or stale data. No real evolution is streaming to any browser right now.

The market API accepts user-supplied fitness scores. Anyone can list garbage code with a fake score via a direct API call. There is no sandbox verification at the API boundary.

The polyglot export compiles GP trees to JavaScript and Rust, but there is no cross-language correctness test. The JS and Rust outputs have never been executed and compared to the Python original.

The checkpoint system saves run statistics but does not serialise the organism tree structures. A 100,000-generation run that crashes at generation 80,000 must restart from generation 0 — losing all evolved structure.

No 100,000-generation marathon has been executed. The estimates in the docs are projections, not measurements.

No user has ever opened a browser, gone to a URL, and watched real evolution happen in real time. The Observatory is not publicly deployed.

**v7 closes every one of these gaps. Not in theory. In production.**

---

## PART A: THE 8 v6 VULNERABILITIES — MUST FIX BEFORE EVERYTHING ELSE

These are not optional polish items. They are correctness bugs and security flaws that invalidate v7 before it starts. Nothing else in this document may begin until all 8 are fixed and all 34 tests pass.

---

### VULN-V6-01: Bug Fixer Returns None for Simple Cases

**File:** `evolution/bug_fixer.py`
**Failing test:** `evolution/test_bug_fixer.py:15` — `test_candidate_only_bug_fixer_returns_small_passing_proposal`

**What is wrong:** The `fix()` method generates candidates by mutating `broken_code`. When the first round of mutations all fail, the second round still starts from the original `broken_code` — not from the best partial fixes. This means if the correct fix requires two mutations, the fixer never finds it because each round starts from the same broken baseline.

**What Manus must do:** Trace the path `fix()` takes when all candidates fail a round. Change the survivor selection so that after each failed round, the next round starts from the candidates with the best partial fitness — not from copies of the original broken code. The metric for "best partial" is the number of test assertions that pass, not just edit distance. After this fix, `pytest evolution/test_bug_fixer.py` must show all tests green.

---

### VULN-V6-02: No Bloat Emergency Brake in the GP Engine

**File:** `evolution/gp_engine.py` and `evolution/gp_population.py`

**What is wrong:** `point_mutate()` replaces a node with a new random subtree. The `max_depth` check prevents new trees from starting too deep, but it does not shrink trees that already exceed the limit from previous crossover events. Over 100,000 generations, organisms accumulate dead code. Trees grow to hundreds of nodes. Memory consumption climbs. Evolution slows down because evaluation of oversized trees dominates CPU time.

**What Manus must do:** Add a post-step bloat sweep inside `GPPopulation.step()`. After generating the new population and before evaluating fitness, every organism whose tree exceeds `MAX_SIZE` nodes must be forcibly hoisted to its largest valid subtree. This sweep is silent — it does not count as a mutation event. Add a test: `test_population_never_exceeds_max_size_across_100_generations`. Run 100 generations. Assert that no organism ever exceeds 64 nodes.

---

### VULN-V6-03: Static Fitness Seeds Allow Test Case Memorisation

**File:** `evolution/fitness.py`

**What is wrong:** All fitness evaluators use the same fixed seed for test case generation across all organisms in all generations. By generation 10,000, organisms may have high fitness not because they generalised the function but because they return the right answers for the specific 20 fixed test inputs. This is the GP equivalent of memorising an exam rather than learning the subject.

**What Manus must do:** Change `batch_evaluate()` so it uses the generation number as the seed: `seed = generation_number`. The seed changes every generation, so test cases rotate. The seed is the same for all organisms within a generation, so the comparison remains fair. Every evaluator that has a hard-coded seed must be updated. Add a test: `test_fitness_seed_rotates_every_generation_but_is_consistent_within_one_generation`.

---

### VULN-V6-04: Market API Does Not Verify Fitness at the API Boundary

**File:** `production/api/v6/routes.py`

**What is wrong:** The `POST /market/list` endpoint accepts a JSON body that includes a `fitness_score` field provided by the caller. The endpoint creates the listing with that caller-provided score, never running the program through the evaluator. Any attacker can list broken code with a score of 1.0.

**What Manus must do:** Remove the `fitness_score` field from the `POST /market/list` request schema entirely. The endpoint must receive only the source code and the task domain. It must then run the source code through the appropriate evaluator in the sandbox. If the result is below the minimum threshold, the endpoint returns 422. If it passes, the listing is created with the sandbox-measured score. The score must never come from the caller. Add a test: `test_market_api_rejects_listing_with_caller_supplied_fitness`.

---

### VULN-V6-05: Cellular Action Space Is Fixed — No Structural Innovation Possible

**File:** `evolution/cellular.py`

**What is wrong:** The cellular experiment proves that cells can improve policy weights over 30 generations. But the action space — what cells are capable of doing — is a fixed constant: `move`, `harvest`, `repair`, `wait`, `broadcast`, `share`. No new action can ever emerge. This limits the cellular system to parameter optimisation over a static action vocabulary. That is valuable but it is not structural evolution.

**What Manus must do:** Make the action space evolvable. Each cell's genome must include an `action_capabilities` field — a frozenset of action identifiers selected from a larger universe. The universe must include at least 10 possible actions, of which each cell starts with 4–6. Mutations can add or remove an action capability from the genome. A cell with `cache_resource` in its genome can cache; one without it cannot. Selection will naturally favour cells that have the right action repertoire for their environment. This is the difference between "evolve how hard you try" and "evolve what you are capable of." Add at least 4 new actions to the universe: `signal_alarm`, `coordinate_with_neighbour`, `cache_resource`, `predict_hazard`. Run the cellular experiment again and publish the new results in `docs/cellular-v7-results.md`.

---

### VULN-V6-06: WebSocket Stream Is Disconnected from Real Evolution

**File:** `production/api/v6/websocket.py`

**What is wrong:** The WebSocket endpoint exists but it emits events from a timer loop that generates synthetic data. No `GPPopulation` instance is running behind it. The Observatory panels are showing fabricated numbers. This is the most critical deception in the current system.

**What Manus must do:** The WebSocket module must hold a reference to one running `GPPopulation` instance per task domain. Every time `pop.step()` completes, the `GenerationStats` object must be immediately pushed to the WebSocket broadcaster. The champion's actual Python source code — the real evolved tree compiled to a Python function — must be included in every WebSocket message. The JSON message format must include at minimum: `generation`, `best_fitness`, `avg_fitness`, `champion_code`, `champion_size_nodes`, `task_domain`, and `event_type`. Add a live integration test: start a real `GPPopulation` with the sorting evaluator, connect a mock WebSocket client, run 10 generations, and assert that exactly 10 messages were received and each contains a non-empty `champion_code` string.

---

### VULN-V6-07: Polyglot Export Is Untested for Runtime Correctness

**File:** `evolution/polyglot_export.py` and `evolution/test_polyglot_export.py`

**What is wrong:** The polyglot export tests verify that the output is syntactically valid code. They do not verify that the output computes the same result as the Python version for the same inputs. A JS function that compiles without errors but returns `undefined` instead of `3.0` is a passing test today. This is wrong.

**What Manus must do:** Add a runtime correctness test for each export target. For JavaScript, use `node -e` in a subprocess. For Rust, write a minimal `main.rs`, compile with `rustc`, and run. For Go, write a minimal `main.go`, compile, and run. All three must produce the same numeric output (within `1e-6` absolute tolerance) as the Python `tree.evaluate()` for 10 identical inputs chosen from the test primitive set. If the system does not have Rust or Go installed, those tests are skipped with an informative message — but the JavaScript test is mandatory because Node.js is required by the frontend build anyway.

---

### VULN-V6-08: Checkpoint System Does Not Preserve Organism Tree Structures

**File:** `evolution/gp_population.py` and `scripts/run_v6_marathon.py`

**What is wrong:** The checkpoint system saves a JSON file with run statistics: generation number, peak fitness, elapsed time. It does not save the population itself. On resume, the population is re-initialised from scratch using the original random seed. This means a 100,000-generation run that crashes at generation 80,000 effectively loses 80,000 generations of evolved structure. The resumed run starts over from random noise, not from the evolved population.

**What Manus must do:** Implement `GPPopulation.save(path)`. It must serialise every organism's tree as a JSON-compatible nested dict. The dict representation of a `GPNode` must include the primitive name (not the callable — the name), terminal value, terminal name, and the serialised children list, recursively. Implement `GPPopulation.load(path)`. It must reconstruct the full population by looking up each primitive by name in the primitive registry. Add a test: `test_population_saves_and_loads_without_fitness_regression`. Run 100 generations, save, load, run 100 more. Assert that the fitness at generation 200 is at least as high as at generation 100 (no regression to random noise).

---

## PART B: THE 12 INNOVATION DIRECTIVES

These are the systems that make v7 genuinely new. Each directive is an engineering mandate. Each has a clear definition of done. Nothing here is a suggestion.

---

### DIRECTIVE 1: THE FIRST 100,000-GENERATION PUBLIC MARATHON

**This is the single most important deliverable in v7. Everything else is in service of this.**

The world needs to see a real GP run at scale. Not 300 generations. Not a proof of concept on Manhattan distance. One hundred thousand generations on a sorting algorithm, with the results committed, reproducible, and published.

**The sequence Manus must follow:**

Fix VULN-V6-03 first. The rotating seed is mandatory for the marathon to be scientifically valid — without it, the champion may be memorising test cases rather than sorting arrays generally.

Fix VULN-V6-08 next. Without full-population checkpointing, a crash at generation 50,000 means starting over.

Then launch the sorting task marathon: population size 50, max depth 8, tournament size 7, crossover rate 0.85, mutation rate 0.12, 5 elites. Run for 100,000 generations. Write a milestone report to `reports/sorting_marathon/milestone_gen_{N}.md` at every 10,000 generations. Each milestone report must include: the current champion's source code, its fitness score, the number of test cases it passes on 100 fresh inputs, and the fitness curve from generation 0 to that milestone.

At completion, write `reports/sorting_marathon/FINAL_REPORT.md`. It must include: the champion's source code, whether it correctly sorts every input in a 1,000-case fresh test run, the fitness curve, the reproduction command, and the git hash of the codebase used. It must be possible for any person who clones the repository and runs that command to get the same champion within random seed variance.

**Why this matters beyond the immediate result:** It will be the first publicly reproducible record of genetic programming discovering a novel sorting algorithm at 100,000-generation scale without an LLM. It can be cited. It can be verified. It changes the conversation about what this system is capable of.

---

### DIRECTIVE 2: THE LIVE PUBLIC OBSERVATORY

**The goal:** One URL. No login. Open it and watch real evolution happen.

The Web Observatory must have six panels. Every panel must show real data. If a panel cannot get real data, it must show "Connection lost — reconnecting" — never fake data.

**Panel 1 — The Code Theater.** Shows the champion's actual source code. Syntax highlighted. Every time a new champion emerges, the panel updates. The diff from the previous champion is highlighted — new lines in green, removed lines in red. A timestamp shows when the current champion was first discovered. A counter shows how many generations it has survived without being displaced.

**Panel 2 — The Fitness Heartbeat.** A live-updating line chart. Three lines: best, average, worst fitness. Shows the last 500 generations. Scrolls right as new generations arrive. Smooth animation — no jarring redraws. This is the visual pulse of the civilisation.

**Panel 3 — The Memome Browser.** Shows the top 10 strategies in the cultural memory. Each strategy card shows: the strategy's ID, who created it, what generation it emerged, how many organisms have adopted it, and the first 3 lines of its code. Clicking a strategy expands it to full view.

**Panel 4 — The Market Floor.** Shows currently listed programs and recent trades. Each listing shows the program's fitness score (measured by the sandbox, never user-supplied), the listing price in tokens, the task domain, and the generation it was born. A trade feed on the right shows the last 20 completed trades with buyer, seller, price, and code quality.

**Panel 5 — The Epoch Clock.** Shows the civilisation's current cultural era. Shows the name of the current epoch, how long it has lasted in generations, what changed at the start of this epoch, and a mini-timeline of all previous epochs from generation 0.

**Panel 6 — The Champion Playground.** A text input. The visitor types their own array (or number, or string, depending on the task). Presses "Run." The system sends the input to the sandbox, runs the champion's evolved code against it, and returns the result within 2 seconds. The visitor sees: the champion's code, the input, the output, and whether the output is correct. This is the moment the system becomes real to a new visitor.

**Infrastructure requirements:** A persistent server running the GP population 24/7. A WebSocket gateway that receives generation events and fans them out to all connected clients. A CDN serving the static frontend. A rate-limited sandbox worker pool for playground requests. None of these may use mock data in production.

---

### DIRECTIVE 3: THE SELF-TUNING DEPLOYMENT

**The goal:** The infrastructure that runs the evolution loop evolves its own operational parameters.

Right now every deployment parameter is a constant written by a human: population size 50, mutation rate 0.12, tournament size 7. These were chosen by educated guessing. They are probably not optimal.

v7 introduces a deployment genome. It is a set of tunable parameters represented as a vector of floats. An outer evolution loop runs one generation of the deployment genome for every 10,000 generations of the inner evolution loop. The fitness of a deployment genome configuration is: peak fitness achieved by the inner loop per unit time, summed across the first 1,000 inner generations after the configuration is applied.

When the outer loop finds a configuration that produces measurably better evolution speed or peak fitness, it promotes that configuration to be the new default. The old configuration is archived. No configuration change is applied without first passing a safety check: population size must stay in [10, 500], mutation rate must stay in [0.01, 0.50], tournament size must stay in [2, 20].

Over time, the system learns its own optimal operational parameters. This is meta-learning without an LLM.

---

### DIRECTIVE 4: THE INTER-ECOSYSTEM FEDERATION PROTOCOL

**The goal:** Multiple independent Living Objects installations, running in different places, can exchange verified cultural strategies.

Each installation generates a public/private key pair on first run. The public key is the installation's identity. When an organism in installation A achieves fitness ≥ 0.90, installation A signs the organism's record (source code + fitness + lineage + evaluator version) with its private key and publishes a signed summary to a shared federation registry.

Installation B periodically queries the registry. For each new signed summary it finds, it: verifies the signature, downloads the source code, runs it through its own evaluator in its own sandbox with its own test cases, and if the result passes its own minimum threshold, adds it to its own memome. If the result fails, it discards it silently.

No installation can inject code into another's memome without that code passing the local evaluator. Signatures prove authenticity but do not bypass verification. An installation can opt out of federation at any time. A federated strategy that later fails the local evaluator (because the evaluator's test cases rotated to harder examples) is automatically quarantined and removed.

This is the architecture of scientific peer review applied to evolved algorithms: publish with a signature, and let each receiver verify independently before accepting.

---

### DIRECTIVE 5: EXPAND TO 20 REAL-WORLD TASK DOMAINS

**The goal:** The system evolves useful programs across 20 different problem domains, not just 6.

**The 14 new domains that must be added, with their definitions of fitness:**

**Domain 7 — Job Scheduling.** Input: a list of jobs with durations and deadlines. Output: a priority score for each job that determines scheduling order. Fitness: how much makespan the evolved scheduler reduces compared to first-come-first-served on 20 random instances. Fitness is 0 if the scheduler produces invalid orderings.

**Domain 8 — Time Series Anomaly Detection.** Input: a float value and 5 previous values (context). Output: 1 if anomaly, 0 if normal. Fitness: F1 score on a labelled dataset of 200 points with realistic anomalies. The dataset rotates every 1,000 generations to prevent memorisation.

**Domain 9 — Numerical Integration.** Input: a float x representing a point in [0, 1]. Output: an estimated integral weight. Fitness: how closely the weighted sum approximates a true integral reference for 10 different functions. The integrand changes every 500 generations.

**Domain 10 — Regular Expression Generator.** Input: a list of positive examples and negative examples (strings). Output: a string representing a regular expression. Fitness: fraction of positive examples matched minus fraction of negative examples matched. Penalise regexes that are longer than 50 characters.

**Domain 11 — Network Packet Router.** Input: (source node ID, destination node ID, load on each of 5 possible paths). Output: which path index (0–4) to use. Fitness: average delivery time across 1,000 routing decisions on a simulated 10-node network. Compare against shortest-path baseline.

**Domain 12 — Cache Eviction Policy.** Input: (item ID, item age, item access frequency, current cache size, cache capacity). Output: a score — higher means "evict this item first." Fitness: cache hit rate across a 10,000-request access trace. LRU achieves approximately 0.72 on the test trace — the evolved policy must beat this.

**Domain 13 — Boolean Circuit Simplifier.** Input: a circuit as a list of gate descriptions. Output: a semantically equivalent circuit with fewer gates. Fitness: gate count reduction percentage, with a hard requirement that the truth table is preserved exactly. Any simplification that changes the truth table scores 0.

**Domain 14 — Financial Signal.** Input: 20 days of normalised price returns and 20 days of normalised volume. Output: a score in [–1, 1] where positive means "buy" and negative means "sell." Fitness: Sharpe ratio on 2 years of held-out daily data. Mandatory kill condition: any organism that would produce a leveraged position exceeding 2× is eliminated from the population immediately, regardless of Sharpe ratio.

**Domain 15 — String Normaliser.** Input: a messy string. Output: a normalised string. Fitness: average edit distance reduction compared to ground truth across 100 examples with varying types of noise (extra spaces, mixed case, unicode punctuation). Zero score if the output contains any character not in the input's character set.

**Domain 16 — Cellular Automaton Rule Discoverer.** Input: a 1D neighbourhood of 3 cells (left, centre, right). Output: the new state of the centre cell. Fitness: how closely a 50-step run of the evolved rule matches a target pattern from a random initial state. The target pattern changes every 1,000 generations.

**Domain 17 — Assembly Peephole Optimiser.** Input: a 3-instruction window in a toy assembly language. Output: a replacement window of 1–3 instructions that is semantically equivalent but shorter or faster. Fitness: total instruction reduction across a 100-instruction benchmark program, with semantic correctness verified by running both versions against 20 test inputs.

**Domain 18 — Protein Folding Heuristic.** Input: an amino acid at a position in a sequence, its neighbours, and the current energy of the configuration. Output: which fold direction to try next (0–3). Fitness: minimum energy achieved on the 2D HP lattice model across 10 protein sequences. Compare against a random-fold baseline.

**Domain 19 — Cryptographic Resistance Control Experiment.** Input: a simplified 4-round hash function output. Output: a candidate preimage. Fitness: how close the evolved output is to the correct preimage as measured by Hamming distance. This domain is a control experiment. The expected result is that fitness plateaus near random baseline and never converges. If it does converge, that is a result worth publishing — it means the simplified hash has exploitable structure. If it does not converge, that proves the system is honest and does not "win" on tasks where evolution cannot help.

**Domain 20 — Emergent Communication Protocol.** Two organisms evolve simultaneously. Agent A receives a hidden integer in [0, 15]. It must produce a signal (a float in [0, 1]). Agent B receives only Agent A's signal and must output its best guess at the hidden integer. Fitness for both agents is Agent B's accuracy. The two agents are co-evolved: improvements in A's signal encoding improve B's decoding ability, and vice versa. Starting from random noise, the pair must evolve a communication protocol from scratch. This is the compressed origin of language.

---

### DIRECTIVE 6: THE CIVILIZATIONAL MEMORY BANK

**The goal:** Every evolved program that achieves fitness ≥ 0.90 on any task is permanently recorded in a public, immutable, cryptographically verifiable archive.

When any organism reaches the fitness threshold, the system captures: its source code, its complete GP tree serialised to JSON, its fitness result on 128 fresh test cases, its generation number, its organism ID, its parent lineage, and the exact git hash of the evaluator used. It computes a SHA-256 hash of this entire record. It appends the record to a local SQLite database in WAL mode with an append-only constraint (deletes are rejected by a trigger). It immediately publishes the hash to a public GitHub gist.

Any researcher in the world can take a claimed champion, compute the hash, and check it against the public gist to verify authenticity. The gist timestamp proves when the result was recorded — it cannot be backdated.

The archive must be queryable. An API endpoint: `GET /archive?task=sorting&min_fitness=0.95` returns a list of champions sorted by fitness, with their source code, lineage, and generation. Over time, this becomes the first public database of non-human-written algorithms, searchable by task, fitness level, and generation of discovery.

---

### DIRECTIVE 7: THE GENOME VISUALISER

**The goal:** Any visitor can click any organism in the Observatory and see its genome as an animated tree that mutates in real time.

The rendering must use D3.js with a force-directed tree layout. Each node in the GP tree is a circle. The colour of the circle encodes the primitive category: arithmetic operations are blue, boolean operations are orange, list operations are green, string operations are purple, terminals are white. The label inside the circle is the primitive name. Connections between circles represent parent-child relationships in the expression tree.

When a mutation event occurs, the affected node flashes yellow. When crossover occurs, the two contributing subtrees are highlighted in contrasting colours, then animated merging into the child tree. The animation takes 800 milliseconds — fast enough to feel alive, slow enough to be legible.

Below the tree is a running readout: "This program has N nodes, depth D, and currently performs [auto-description from the Explanation Engine]."

A visitor who has never heard of genetic programming must be able to look at this visualiser for 30 seconds and understand intuitively that: organisms are programs, programs are trees, trees mutate, and better trees survive. This is the most important piece of communication in the entire project.

---

### DIRECTIVE 8: THE ADVERSARIAL TASK GENERATOR

**The goal:** Tasks evolve to stay hard. When organisms get too good, the task gets harder.

For each task domain, define a set of parameters that control difficulty. For sorting: array length and value range. For primes: the range of numbers to test. For game theory: which opponent strategies are active. For pathfinding: the maze layout.

The task generator runs as a second evolution loop, separate from the organism population. It is slower — one task generation per 1,000 organism generations. Its fitness function is the inverse of the organism population's average fitness: when organisms score high, the task generator scores low. The task generator evolves to find configurations where the current champion population struggles.

The safety constraint: the task generator cannot make the task unsolvable (fitness must remain achievable above 0.50 in principle). It can only shift the difficulty within the pre-defined parameter space.

The result is a perpetual arms race. Organisms never fully solve the task because the task is always adapting to expose their weaknesses. This produces organisms that are not just good at one difficulty level but robustly capable across the full parameter space. That robustness is generalisation — the most valuable property an evolved program can have.

---

### DIRECTIVE 9: THE EXPLANATION ENGINE

**The goal:** When a visitor asks "what does the champion do?", the system gives a correct, human-readable answer. Without an LLM. Using the program's own AST structure.

Build a rule-based describer that walks a GP tree and produces a natural language description by pattern matching on known structures. The describer has a library of named patterns: `add(x, y)` → "adds x and y", `abs(sub(a, b))` → "the absolute difference of a and b", `max(abs(a), abs(b))` → "the maximum absolute value of a and b." Named identities are recognised: when the pattern for Manhattan distance appears (`abs(sub(x1, x2)) + abs(sub(y1, y2))`), the describer names it "Manhattan distance."

When the describer encounters a structure it cannot name, it says "an unrecognised combination of [list of all primitives used in the subtree]." When that happens, it is a signal that evolution may have discovered a novel structure — one worth examining by a human researcher.

The describer is not trying to be a general NLP system. It is trying to be correct. Every description it produces must be provably accurate for the subtree it describes. Incorrect descriptions — even grammatically fluent ones — are worse than "I don't recognise this structure." Correctness is the only standard.

---

### DIRECTIVE 10: THE EDUCATIONAL TOUR

**The goal:** A student with no programming background completes a 10-minute interactive tour and understands what genetic programming is.

The tour has five steps. It activates when a new visitor arrives — detected by absence of a session cookie. They are offered "Start the 10-minute tour." If they decline, they see the full Observatory normally.

Step 1, "Meet an organism": Shows one organism's GP tree rendered by the Genome Visualiser. A label points to one node: "This circle is a function — it adds two numbers." Another label points to the connections: "These lines connect functions to their inputs." A "Run it" button shows what happens when the tree is evaluated on a sample input.

Step 2, "Watch one generation run": Evolution is slowed to 1 generation per 3 seconds. A narration panel explains each phase as it happens: "All organisms are being tested — the fitness bars show their scores." "The lowest-scoring organisms are being removed — they didn't pass enough tests." "The surviving organisms are reproducing — their code is copied and mutated to create new organisms."

Step 3, "Watch the champion improve": Evolution returns to normal speed. The Code Theater highlights as the champion code changes. The narration says: "Each new champion is slightly better than the last. After thousands of generations, the code can look very different from where it started."

Step 4, "Test the champion yourself": The playground opens. The narration says: "Type in your own array below. The champion will sort it." The student types an array. The result appears. The narration says: "The champion sorted it correctly — and the champion's code was never written by a human."

Step 5, "Start your own evolution": A simple form lets the student choose one task and a population size between 10 and 100. They press "Evolve." A private session runs for 1,000 generations. They watch their own evolution in a mini-Observatory. At the end, they get a report showing their champion's code, how good it is, and an invitation to share the link.

---

### DIRECTIVE 11: THE COMPETITIVE BENCHMARK LEADERBOARD

**The goal:** A public, honest comparison between evolved champions and human-written implementations.

For each of the 6 current task domains, define the baseline — the best known human-written algorithm:

Sorting: Python's built-in `sorted()` (Timsort) on arrays of size 100.
Primality: Trial division up to the integer square root.
Fibonacci: Dictionary-memoised recursion.
Max subarray: Kadane's single-pass algorithm.
Game theory: Tit-for-Tat, the known optimal strategy for iterated Prisoner's Dilemma.
Compression: Standard run-length encoding on synthetic data.

After every 10,000-generation milestone, run the current champion and the corresponding baseline on 1,000 fresh test cases. Record three metrics: correctness (fraction of identical outputs), speed (wall-clock time on identical hardware), and code length (description length in bytes). Publish the result as a row in `reports/leaderboard.md`.

The leaderboard is completely honest. If the evolved solution is slower than Timsort, the table says so. If it produces incorrect output on 3 out of 1,000 test cases, the table says so. If it discovers a novel algorithm structure that achieves the same correctness with shorter code than the baseline, the table says that too.

The leaderboard is updated automatically by the CI pipeline after every 10,000-generation milestone. No human curates it. It is the objective record.

---

### DIRECTIVE 12: PRODUCTION HARDENING FOR 1 MILLION CONCURRENT USERS

**The goal:** When the Observatory is posted to Hacker News and 1 million people visit simultaneously, it stays online.

The current architecture collapses under that load. v7 replaces it with a five-layer architecture where each layer can scale independently.

**Layer 1 — Static CDN.** The HTML, CSS, and JavaScript are served from Cloudflare Pages or equivalent. A CDN handles 10 million requests per minute without any backend involvement. The frontend is a static build that connects to the WebSocket gateway — it has no direct dependency on any backend server.

**Layer 2 — WebSocket Gateway.** A dedicated server, separate from the evolution workers, handles all WebSocket connections from browsers. It does not run any evolution code. It subscribes to a Redis Pub/Sub channel where evolution workers publish generation events. It fans out those events to all connected clients. One gateway instance handles 50,000 concurrent connections. Horizontal scaling adds more gateway instances behind a load balancer. The gateway is stateless — any gateway instance can serve any client.

**Layer 3 — Evolution Workers.** One process per task domain. Each process runs a `GPPopulation` loop continuously. After every `step()`, it publishes the `GenerationStats` and the champion's source code to the Redis Pub/Sub channel. Evolution workers never accept HTTP requests. They only write to Redis and to the checkpoint storage. A crash in the sorting worker does not affect the primes worker.

**Layer 4 — Sandbox Workers.** A pool of isolated processes that evaluate user-submitted inputs from the Champion Playground. These processes run inside containers with no network access, 128 MB memory limit, 500 ms CPU timeout, and no file system write access outside a temporary scratch directory. They receive evaluation jobs from a work queue, execute them, and return the result. The pool can scale from 2 to 100 worker processes based on queue depth.

**Layer 5 — The Immutable Archive.** A read-only SQLite database served by a separate read-only API process. The archive database never accepts writes from the production API — only from the evolution workers, via a restricted internal write path. Any attempt to write to the archive via the public API returns 403.

This architecture ensures that a DDoS attack on the WebSocket gateway cannot slow the evolution workers, an abusive playground request cannot affect the market API, and a write to the archive cannot be triggered by any external caller.

---

## PART C: THE EXECUTION SEQUENCE

The directives above have dependencies. This is the correct order.

**Weeks 1–2: Fix the Foundation.**
VULN-V6-01 through VULN-V6-08 must all be fixed.
Target: 34/34 v6 tests passing. No exceptions. Nothing else starts until this is done.

**Weeks 3–4: Run the Marathon.**
Launch the sorting 100,000-generation run with the now-fixed checkpointing and rotating seeds.
Commit milestone reports at every 10,000 generations.
The run must be in progress before any public announcement.

**Weeks 5–6: Wire the Observatory to Real Data.**
Connect the WebSocket stream to a live GP population.
Fix the market API fitness verification.
Add polyglot cross-language runtime tests.
The Observatory must now show real numbers.

**Weeks 7–8: Deploy the Observatory Publicly.**
CDN-served static frontend.
WebSocket gateway (Layer 2).
Evolution workers (Layer 3) running continuously.
Sandbox worker pool (Layer 4).
One URL. Anyone can watch. No login.

**Weeks 9–10: Publish the Marathon Results.**
The sorting marathon completes.
`reports/sorting_marathon/FINAL_REPORT.md` is committed.
The competitive benchmark leaderboard is published with the first 6 domains.
The Civilizational Memory Bank is activated.

**Weeks 11–12: Add the Cellular Evolvable Action Space.**
VULN-V6-05 is implemented.
New cellular experiment runs with the expanded action space.
Results published in `docs/cellular-v7-results.md`.

**Month 4: 20 Task Domains.**
All 14 new evaluators are implemented, tested, and plugged in.
7-day evolution runs launch on each new domain.
All 20 domains appear in the Observatory and the leaderboard.

**Month 5: Education and Explanation.**
The 5-step interactive tutorial is live and tested with real users.
The Explanation Engine produces correct descriptions for all 6 original task domains.
The Genome Visualiser is live in the Observatory.

**Month 6 and beyond: The Strategic Layer.**
Self-tuning deployment (Directive 3).
Federation protocol (Directive 4).
Adversarial task generator (Directive 8).
Organism autobiography system (Paradigm 6).
Cross-domain transfer experiment (Paradigm 7).
The Failure Museum (Paradigm 8).
The Evolutionary Speedrun Challenge (Paradigm 10).

---

## PART D: THE QUALITY GATES

Nothing ships to master without passing all six gates.

**Gate 1 — All tests pass.** Every release must show 100% of existing tests passing. New modules must have at minimum 80% line coverage. The test count must increase by at least 20 per major release.

**Gate 2 — No mocked data in production.** Every Observatory panel must fetch from a live data source. If the source is unavailable, the panel shows "Connection lost" — never fake numbers. Any panel discovered to be showing synthetic data after deployment is a critical bug with the same priority as a security vulnerability.

**Gate 3 — Security audit signed off.** Every new API endpoint must be reviewed for authentication bypass, input injection, rate limiting bypass, and privilege escalation before merging. Each release must include a `docs/v7-security.md` with findings — even if the finding is "No new vulnerabilities identified."

**Gate 4 — Reproducibility verified.** Every published benchmark result must include the exact reproduction command, the random seed used, the git hash of the codebase, and the expected output range. A team member other than the one who ran the benchmark must execute the reproduction command and confirm the result before the result is published. A result that only one person can reproduce is not a result.

**Gate 5 — Documentation is honest.** No documentation may describe a capability the system does not have. No claim may be made about future performance without a clear label that it is a projection. The distinction between "works in tests," "works in production," "works in demo," and "planned but not implemented" must always be explicit and accurate.

**Gate 6 — Performance baseline does not regress.** After every release, run the sorting task for 1,000 generations and record: generations per second, peak memory in MB, and champion fitness at generation 1,000. Compare to the previous release. If any metric degrades by more than 10%, the release is blocked until the regression is identified and fixed.

---

## PART E: THE 10 NEW PARADIGMS — GENUINE RESEARCH CONTRIBUTIONS

These go beyond what the genetic programming literature has published. Building them is not just engineering — it is science.

**Paradigm 1 — Symbolic Regression as a Service.** When a champion achieves high fitness on a mathematical task, extract the symbolic formula from its GP tree and make it downloadable as LaTeX, Python, and plain English. This turns the Observatory into the world's first public evolutionary symbolic regression service. Users submit a dataset; evolution discovers the equation.

**Paradigm 2 — The Adversarial Co-Evolution Pair.** Two populations evolve simultaneously. Population A solves a problem. Population B generates adversarial test cases that expose A's failures. A's fitness improves. B's test cases become harder. This is the evolutionary analogue of GAN training, implemented without neural networks.

**Paradigm 3 — Personalised Pareto Front.** The Pareto archive stores non-dominated solutions across multiple objectives (correctness, speed, code brevity). A user specifies their preference weights (e.g., "I care 70% about correctness and 30% about brevity"). The system filters the Pareto front and presents the champions that best match. This is personalised algorithm discovery.

**Paradigm 4 — The Evolutionary Theorem Prover.** Define a task where the program must produce a valid proof of a simple mathematical statement (commutativity, transitivity) in a restricted proof calculus. Fitness is whether the proof is valid, not whether it matches a target proof. This tests whether evolution can discover logical reasoning without being given logical rules.

**Paradigm 5 — The Living Constitution.** A meta-fitness function scores not just individual programs but the health of the evolutionary dynamic itself: is selection pressure too high (premature convergence)? Is mutation rate too low (stagnation)? Is the population too homogeneous (diversity collapse)? A second evolution loop evolves the selection rules to maintain a healthy dynamic. The constitution evolves to prevent civilisational failure modes.

**Paradigm 6 — The Organism Autobiography.** Every organism tracks its own history: strategies learned, generations survived, parents, offspring, and peak fitness. At the end of 100,000 generations, generate the autobiography of the champion — its evolutionary journey from random noise to a functional algorithm. This is the first machine-generated evolutionary biography of a non-human intelligence.

**Paradigm 7 — The Cross-Domain Transfer Proof.** Run two populations separately: one on sorting, one on pathfinding. After 10,000 generations, measure the sorting champion's fitness on the pathfinding task without additional training. If it exceeds a naive random baseline, publish the result. It is evidence of generalisation emerging from domain-specific evolution — the most fundamental open question in evolutionary computation.

**Paradigm 8 — The Failure Museum.** Archive every organism that achieved an interesting but ultimately wrong strategy — creative near-misses that use novel primitive combinations. Make the archive searchable. A wrong strategy that uses an unusual combination may be one mutation away from being correct. This is the first public database of failed evolutionary attempts, designed to be mined by future researchers.

**Paradigm 9 — The Human-Evolution Collaboration Interface.** A researcher can inject a hand-written strategy directly into the memome of a running population. The population then evolves around this injection. Some organisms adopt it. Some crossover with it. Some produce mutants that beat it. This makes Living Objects a tool for collaborative intelligence: human proposes, evolution refines, neither could have produced the result alone.

**Paradigm 10 — The Evolutionary Speedrun Challenge.** A public competition: who can evolve a correct sorting algorithm in the fewest generations? Participants tune population size, mutation rate, primitive set, and fitness function. They cannot inject the answer directly. Results are published on a public leaderboard. This community challenge generates scientific data about which GP configurations converge fastest — itself a publishable finding.

---

## v7 COMPLETE DELIVERABLES CHECKLIST

### Mandatory Foundation
- [ ] VULN-V6-01: Bug fixer test fixed and passing
- [ ] VULN-V6-02: Bloat emergency brake implemented and tested
- [ ] VULN-V6-03: Rotating fitness seeds across generations
- [ ] VULN-V6-04: Market API fitness verification at boundary
- [ ] VULN-V6-05: Cellular evolvable action space
- [ ] VULN-V6-06: WebSocket connected to real GP population
- [ ] VULN-V6-07: Polyglot runtime correctness tests
- [ ] VULN-V6-08: Full population checkpoint and resume
- [ ] 34/34 tests passing

### Marathon and Science
- [ ] Sorting 100,000-generation marathon completed
- [ ] Milestone reports committed every 10,000 generations
- [ ] `reports/sorting_marathon/FINAL_REPORT.md` published
- [ ] Competitive benchmark leaderboard active for all 6 domains
- [ ] All 20 task domain evaluators implemented and tested
- [ ] Adversarial task generator running on 3 domains
- [ ] Cellular v7 experiment (evolvable action space) results published
- [ ] Civilizational Memory Bank active with public hash gist
- [ ] Cross-domain transfer experiment run and published

### Observatory (Live, Public, No Mocks)
- [ ] Panel 1: Code Theater with real diff highlighting
- [ ] Panel 2: Live fitness graph — no page refresh
- [ ] Panel 3: Real memome browser
- [ ] Panel 4: Live market floor with real verified trades
- [ ] Panel 5: Real epoch timeline
- [ ] Panel 6: Champion Playground — user inputs, real results
- [ ] Genome Visualiser — D3.js animated GP tree
- [ ] Explanation Engine — correct AST descriptions
- [ ] CDN-served static frontend deployed
- [ ] WebSocket gateway deployed and load-tested
- [ ] Evolution workers deployed and running 24/7
- [ ] Sandbox worker pool deployed and isolated

### Education
- [ ] 5-step interactive tutorial implemented
- [ ] Tutorial tested with 10 non-expert users
- [ ] User session system for private 1,000-generation runs

### Infrastructure
- [ ] 5-layer architecture deployed
- [ ] Redis Pub/Sub between workers and gateway
- [ ] CI/CD pipeline enforcing all 6 quality gates
- [ ] Performance baseline regression test in CI
- [ ] Security audit document for all new v7 endpoints
- [ ] Monitoring dashboard covering all 5 layers

### Research Contributions
- [ ] Sorting marathon paper-ready results
- [ ] Adversarial co-evolution experiment results
- [ ] Cross-domain transfer experiment results
- [ ] Failure Museum populated with first 500 entries
- [ ] Organism autobiography for sorting champion
- [ ] Symbolic regression service live for mathematics domains

---

## THE v7 NORTH STAR

After v7 is complete, a researcher at a university, a student in a classroom, a developer with a problem to solve, and a security researcher — all four must be able to use this system in completely different ways and all find it useful.

The researcher watches a real evolution run, downloads the champion, verifies it independently, and cites the repository. The student completes the tutorial and understands what genetic programming is for the first time. The developer defines a fitness evaluator for their own problem and gets evolved solutions without writing any evolution code. The security researcher reviews the threat model, runs the test suite, and confirms the sandbox is safe.

One URL. Real evolution. Real code. Real results. No simulations. No mocks. No LLMs. No templates.

The engine is real. v7 makes it live.

---

*This document was written based on the verified v6 results:*
*3/3 trial seeds evolved Manhattan distance in ≤ 300 generations without an LLM.*
*128/128 holdout cases pass across all three trials.*
*Cellular experiment: held-out score improved 7.08× in 30 generations.*
*33/34 v6 tests pass in 5.07 seconds.*
*141 new files, 65,412 new lines added in the v6 push.*
*The proof of concept is done. The civilisation begins here.*
