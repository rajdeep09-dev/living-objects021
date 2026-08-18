# BEAST UPDATE v12 — THE CIVILISATION-SCALE UPGRADE
## 1,000+ Lines of Engineering Instruction to Reach Claude and Codex Level
## Every Capability Gap Closed. Every Real-World Task Enabled. No Code Snippets.

> This document is the complete engineering mandate for transforming Living Objects
> from a mathematical formula evolver into a general-purpose autonomous program
> synthesis engine that can compete with Claude and Codex on real-world tasks.
>
> It is written for engineers who will implement it — not for researchers who will
> study it. Every section is a specific, actionable instruction. Every capability
> is tied to a measurable success criterion. Every phase has a completion gate.
>
> After this document is fully implemented, the system will be able to:
> scrape leads, enrich them, write production code, optimise real-world functions,
> pass real programming benchmarks, and operate as a persistent autonomous agent
> that improves itself without human intervention.
>
> Current state: mathematical formula evolver, 12.4 generations/second, no internet.
> Target state: general-purpose autonomous program synthesiser with network access,
> knowledge retrieval, multi-agent coordination, and real-world task execution.

---

## FOUNDATIONAL PRINCIPLE

Every instruction in this document follows one rule: the system must earn each
new capability by proving the previous one works correctly and safely. A system
that can scrape the web unsafely is more dangerous than one that cannot scrape
at all. Every new primitive added to the engine must pass a safety gate before
it becomes available to evolution. Every new task domain must pass a contamination
audit before its results can be cited. Every new external connection must be
isolated in a sandbox before it can be called from an evolved program.

The path from the current state to Claude/Codex level is twelve phases. Each
phase unlocks the next. None can be skipped.

---

# PHASE 1 — THE SAFETY ARCHITECTURE
## Build the Containment Layer Before Adding Any New Power

### Why Phase 1 Must Come First

The current system is safe because it is limited. Programs run in a pure Python
interpreter with no external access. Adding internet primitives, file system
access, or database connections to an uncontained system would make it
immediately dangerous — an evolved program could exfiltrate data, exhaust
resources, or attack external services.

Phase 1 builds the containment layer that makes every subsequent phase safe.
Nothing in Phase 2 or later is permitted to operate outside this containment
layer.

### Instruction 1.1 — Build the Sandboxed Execution Runtime

The current system evaluates programs in the main Python process. This must
change. Every evolved program that runs during fitness evaluation must execute
in a separate OS process with the following restrictions enforced at the kernel
level using Linux seccomp-bpf syscall filtering:

Allowed syscalls for the sandboxed process: read (from pre-opened file
descriptors only), write (to pre-opened file descriptors only), mmap with
MAP_ANONYMOUS only, brk, exit, exit_group, sigreturn, rt_sigreturn, futex
(for threading primitives only), clock_gettime (read-only). Everything else
is denied with SIGSYS.

The sandbox must enforce a hard memory limit of 256 MB per evaluation using
Linux cgroups memory.limit_in_bytes. Any program that allocates more than 256
MB dies immediately with a fitness score of 0.

The sandbox must enforce a hard CPU time limit of 2,000 milliseconds per
evaluation. Any program that runs longer than 2 seconds receives fitness 0.
The timer is wall-clock time measured outside the sandbox, not CPU time
measured inside it, because CPU time can be manipulated.

The sandbox must enforce a hard output size limit: the program's return value,
when serialised to JSON, must not exceed 1 MB. Programs that return values
larger than 1 MB receive fitness 0.

The sandbox must run as a separate OS user with no filesystem write permissions
except to a tmpfs directory that is wiped between evaluations. The sandbox
user must have no network access at the OS level unless the evaluation task
explicitly requires it and the network primitive sandbox (Phase 3) is active.

This sandbox runtime must be implemented as a reusable component that any
fitness evaluator can call. The interface is: send program + inputs to sandbox,
receive output + resource usage metrics. The evolution engine never calls
program code directly in-process after Phase 1 is complete.

### Instruction 1.2 — Build the Primitive Approval Registry

Every primitive in the system must be registered in a central Primitive Approval
Registry. The registry records for each primitive: its name, its input and output
types, its implementation, whether it has side effects, whether it requires
network access, whether it requires file system access, which safety tier it
belongs to (Tier 1 through Tier 5 defined below), and the date it was approved.

Tier 1 primitives — Pure arithmetic and logic. No side effects. No external
access. Safe in the main Python process. Examples: add, subtract, abs, sqrt,
greater-than, less-than.

Tier 2 primitives — Pure string and list operations. No side effects. No
external access. Safe in the main Python process. Examples: concat, split,
strip, sort (the contamination-clean version that sorts numbers from explicit
comparison steps, not Python's built-in sorted).

Tier 3 primitives — Deterministic operations with bounded resource use. Must
run in the sandboxed process. Must complete within 100ms and allocate under
10 MB. Examples: regular expression match, JSON parse, base64 encode, SHA-256
hash, HTML tag extraction from a pre-fetched string.

Tier 4 primitives — Operations with controlled external access. Must run in
the network sandbox (Phase 3). Must complete within 5 seconds. Must only
access pre-approved domains from the domain whitelist. Examples: HTTP GET to
a whitelisted domain, DNS lookup for a pre-specified hostname.

Tier 5 primitives — Operations with persistent state. Must run in the stateful
agent sandbox (Phase 7). Must use the distributed memory system. Examples:
write to the knowledge base, read from the lead database, call a registered
API with authentication.

A primitive cannot be added to any task's primitive set unless it has been
approved and registered at the appropriate tier. Any evolution task that uses
an unapproved primitive fails immediately with an error, not silently.

### Instruction 1.3 — Build the Fitness Evaluator Safety Gate

Every fitness evaluator must pass a safety gate before it can be used in any
evolution run. The safety gate checks: the primitive set contains only approved
primitives at the correct tier for the evaluator's execution environment, the
test case generator is deterministic given the seed, the expected output for
every test case is correct (checked by a separate verified reference
implementation), and the contamination audit has been run and passed.

The safety gate runs automatically in the CI pipeline when a new evaluator is
added or when an existing evaluator's primitive set changes. A failing safety
gate blocks the pull request — the evaluator cannot be merged into the main
branch until all checks pass.

### Instruction 1.4 — Build the Audit Trail for Every Evolution Run

Every evolution run must produce a machine-readable audit trail that records:
the primitive set used (with approval status for each primitive), the fitness
evaluator used (with safety gate result), the sandbox resource usage for every
generation (peak memory, peak CPU time, any sandbox violations), the champion's
fitness on both training and fresh test sets, and whether any sandbox escape
was attempted (even if blocked). The audit trail is immutable — it cannot be
modified after the run completes. It is signed with the local federation key.

Phase 1 is complete when: the sandboxed execution runtime passes 50 tests
covering memory limits, CPU limits, output size limits, and syscall blocking.
The primitive approval registry contains all current primitives with accurate
tier assignments. The fitness evaluator safety gate passes for all 10 current
evaluators. Every existing evolution run produces a signed audit trail.

---

# PHASE 2 — THE STRING AND PATTERN ENGINE
## Give the System the Ability to Parse and Transform Real Text

### Why Phase 2 Before Network Access

Real-world data is text. Lead records are text. HTML pages are text. API
responses are JSON, which is text. Before the system can usefully process
data from the internet, it needs a rich set of text processing primitives
that are safe (Tier 2 and Tier 3) and can be evolved into useful text
manipulation programs.

### Instruction 2.1 — Add the Full Tier 2 String Primitive Set

The current string primitive set has 9 operations. The target is 40 string
primitives, all Tier 2 (pure, no external access, safe in main process).

The additional 31 string primitives to add:

Extraction: extract_between(text, start_marker, end_marker) returns the
substring found between the two marker strings, empty string if not found.
extract_after(text, marker) returns everything after the first occurrence of
marker. extract_before(text, marker) returns everything before the first
occurrence of marker. nth_word(text, n) returns the nth space-separated word
(0-indexed), empty string if out of bounds. nth_line(text, n) returns the nth
newline-separated line, empty string if out of bounds.

Validation: is_email(text) returns True if the text matches the standard
email format (local@domain.tld with valid characters). is_url(text) returns
True if the text starts with http:// or https:// and has at least one dot in
the domain. is_phone(text) returns True if the text (stripped of spaces,
dashes, parentheses) contains 10 to 15 digits. is_numeric(text) returns True
if the text (stripped) represents a valid integer or float. contains_digit(text)
returns True if any character in the text is a digit. contains_alpha(text)
returns True if any character is a letter.

Normalisation: remove_punctuation(text) returns the text with all characters
outside letters, digits, spaces, and @ removed. collapse_whitespace(text)
returns the text with all sequences of whitespace replaced by a single space.
to_lowercase(text) returns the text in lowercase. to_titlecase(text) returns
the text with the first letter of each word capitalised. remove_html_tags(text)
returns the text with all HTML angle bracket tags removed (simple regex, not
a full parser). decode_html_entities(text) returns the text with common HTML
entities (&amp; &lt; &gt; &quot; &#39;) replaced by their characters.

Pattern: count_occurrences(text, substring) returns the number of non-overlapping
occurrences of substring in text. find_first(text, substring) returns the
index of the first occurrence of substring, or -1. find_last(text, substring)
returns the index of the last occurrence of substring, or -1. split_on(text,
delimiter) returns a list of strings split on the delimiter. join_with(list,
delimiter) returns a single string with the list elements joined by delimiter.
pad_left(text, width, pad_char) pads the text on the left to the specified
width with pad_char. pad_right(text, width, pad_char) pads on the right.
truncate(text, max_length) returns the text truncated to max_length characters.

Domain-specific: extract_domain(url) returns the domain part of a URL
(everything between :// and the next /). extract_email_domain(email) returns
the domain part of an email address (everything after @). extract_tld(domain)
returns the top-level domain (last segment after the last dot). strip_protocol(url)
returns the URL without the http:// or https:// prefix. normalise_company_name(text)
returns the text with common suffixes (Inc, LLC, Ltd, Corp, Co, GmbH) removed
and stripped of punctuation. extract_first_number(text) returns the first
sequence of digits found in the text as a float.

### Instruction 2.2 — Add the Tier 3 Regex Primitive Set

Five regex primitives that run in the sandboxed process (Tier 3) because
compiled regexes with user-controllable patterns can cause catastrophic
backtracking (ReDoS) that the sandbox timeout prevents:

regex_match(pattern, text) returns True if the pattern matches anywhere in
the text. The pattern is a string constant chosen by the evolved program from
a pre-defined list of approved patterns (listed in the Approved Pattern
Registry). Arbitrary user-controlled regex patterns are not permitted — only
patterns from the approved list.

regex_extract(pattern, text) returns the first match of the pattern in the
text, or empty string.

regex_extract_all(pattern, text) returns a list of all non-overlapping matches.

regex_replace(pattern, text, replacement) returns the text with all matches
of the pattern replaced by replacement.

The Approved Pattern Registry contains the following pre-vetted, ReDoS-safe
patterns: standard email pattern, standard URL pattern, US phone number
(parentheses or dashes or plain), LinkedIn profile URL, Twitter/X handle,
GitHub username, standard date (YYYY-MM-DD), standard time (HH:MM), IPv4
address, postal code (US 5-digit or UK alphanumeric), company registration
number, IBAN, credit card number (16 digits, spaces allowed, for format
detection only not validation), social security number format detection only.

### Instruction 2.3 — Build the Lead Record Evaluator

The Lead Record Evaluator is the first evaluator designed for real-world
business use. It does not require network access. It operates on pre-fetched
text records (the text of a company directory page, a LinkedIn profile snippet,
a news article) and measures how accurately an evolved program extracts
structured lead information.

The evaluator generates test cases from a pre-built dataset of 500 real
anonymised lead records. Each record consists of a raw text input (the kind
of text you would find on a company website's About page or a LinkedIn profile
snippet) and the expected structured output (a dict with fields: name, email,
company, title, phone, location, linkedin_url — any field may be None if not
present in the input).

The fitness function scores evolved programs on: recall (what fraction of
present fields were correctly extracted), precision (what fraction of extracted
fields were correct), format correctness (are extracted emails valid email
format? are extracted phones valid phone format?), and robustness (does the
program work on all 500 records or only on a narrow subset?).

The total score is (0.5 * recall + 0.3 * precision + 0.2 * robustness). A
perfect score requires extracting all fields correctly from all 500 records.

The lead record dataset must be built from real anonymised data — not from
synthetic examples. Using synthetic examples creates a contamination-equivalent
problem: the program may learn the pattern of the generator, not the pattern
of real lead data.

### Instruction 2.4 — Run the Lead Record Evaluator Contamination Audit

Before any evolution run on the Lead Record Evaluator, run the contamination
audit: initialise 100 random organisms using the evaluator's primitive set.
Run zero generations. Record the average fitness. If the average fitness is
above 0.10 (significantly above zero), investigate which primitives are
providing direct partial solutions and redesign the primitive set.

The expected baseline fitness of a random program on lead extraction is near
zero, because extracting a name requires knowing where names appear in text,
which random programs do not know.

Phase 2 is complete when: all 40 Tier 2 string primitives are implemented
and tested with 5 edge cases each (200 new tests). The 5 regex primitives are
implemented, sandbox-tested, and approved. The Lead Record Evaluator is built
with 500 real anonymised test cases, passes the safety gate, and achieves near-
zero baseline fitness with random programs. A 5-seed run of 10,000 generations
on the Lead Record Evaluator is completed and results are honestly reported.

---

# PHASE 3 — THE NETWORK PRIMITIVE SANDBOX
## Controlled Internet Access for Real-World Data Retrieval

### Why Phase 3 is the Most Important and Most Dangerous Phase

Giving the evolution engine access to the internet changes the nature of the
system entirely. Without internet access, the worst an evolved program can do
is consume CPU time. With internet access, an evolved program could: spam
hundreds of websites with requests, scrape data that site owners have prohibited,
leak sensitive inputs to third-party servers, or trigger rate limiting that
gets the server's IP banned from important services.

Phase 3 must be implemented with extreme caution. Every decision in this phase
prioritises safety over capability. If a capability cannot be implemented safely,
it is not implemented.

### Instruction 3.1 — Build the Network Primitive Sandbox

The network primitive sandbox is a separate OS process pool (minimum 4 workers,
maximum configured per deployment). Every Tier 4 primitive call goes through
this pool. The pool enforces:

Domain whitelist: the process can only connect to domains on a pre-approved
whitelist. Attempts to connect to any other domain fail with a network error
that returns an empty string to the evolved program (not an exception — the
program must handle unavailable data gracefully). The initial whitelist contains:
LinkedIn public profiles (not requiring login), Crunchbase public company pages,
Hunter.io API (with key), Clearbit API (with key), FullContact API (with key),
the project's own data cache server.

Rate limiting per domain: maximum 1 request per 2 seconds to any single domain,
maximum 10 requests per minute to any single domain, maximum 100 requests per
hour total across all domains. These limits are enforced per evolution run, not
per program. An entire evolution run gets a quota, not individual evaluations.

Request size limits: HTTP response bodies are truncated at 50 KB. Larger
responses return the first 50 KB. The evolved program must handle truncated
responses.

User-agent transparency: every request from the network sandbox sends a User-
Agent header that identifies this system by name and includes a contact email
and a link to the project's public page. The system does not pretend to be a
browser. Sites that block this User-Agent are excluded from the whitelist.

Robots.txt compliance: before requesting any URL, the network sandbox checks
the domain's robots.txt and refuses the request if the path is disallowed.
This check is cached for 24 hours per domain.

Request logging: every request made by the network sandbox is logged with:
timestamp, domain, path (truncated at 200 chars, no query parameters), response
code, response size, and the run_id of the evolution run that triggered it.
This log is publicly available — anyone can inspect what the system has fetched.

### Instruction 3.2 — Add the Tier 4 HTTP Primitive Set

Six Tier 4 HTTP primitives, all subject to the network sandbox rules above:

http_get(url) returns the response body as a string (truncated at 50 KB) or
empty string on error. The URL must be on the domain whitelist. The function
never raises an exception — errors return empty string.

http_get_json(url) returns the response body parsed as a JSON object (a dict
or list), or None on error. Same whitelist and size rules.

http_get_html_text(url) returns the response body with all HTML tags stripped,
leaving only the visible text content. This is the most useful primitive for
scraping because it removes the noise of HTML markup.

fetch_linkedin_company(company_name) constructs the appropriate LinkedIn company
search URL, fetches the first result's public profile page, and returns a dict
with the fields the public profile exposes: name, description, website,
industry, employee_count_range, headquarters, founded_year. Returns None if
not found or not accessible.

fetch_company_website_text(domain) fetches the homepage and the /about and
/contact pages of the given domain, strips HTML tags from each, and returns
the concatenated plain text (up to 50 KB total). This is the primary primitive
for extracting lead data from a company's own website.

fetch_email_guess(first_name, last_name, domain) calls the Hunter.io Finder
API with the provided name and domain and returns the guessed email address
and its confidence score as a dict, or None if not found or API quota exceeded.

### Instruction 3.3 — Build the Live Lead Scraping Evaluator

The Live Lead Scraping Evaluator is the first evaluator that requires Tier 4
primitives. It tests whether evolved programs can take a company name and domain
as input and return a verified lead record.

The evaluator uses a pre-registered dataset of 200 companies for which the
correct lead data is known and verified (collected manually and updated
quarterly). For each company, the input is (company_name, domain_string) and
the expected output is a dict with verified fields.

The fitness function scores: whether the email was found and is correct
(40 points), whether the decision-maker's name and title were found (20 points),
whether the phone number was found (15 points), whether the LinkedIn URL was
found and valid (15 points), whether the company's employee count was correctly
categorised (10 points). Total: 100 points normalised to 0–1 fitness.

The evaluator enforces a strict budget: each organism evaluation can make
at most 5 HTTP requests total across all primitives. An organism that tries
to make more than 5 requests has its remaining requests blocked and receives
a 10-point penalty per blocked request. This prevents runaway scrapers from
exhausting the rate limit quota.

The contamination audit: a random organism with Tier 4 access has approximately
10–30% baseline fitness because some primitives directly return useful data
(fetch_email_guess returns an email that may be correct). This is acceptable
contamination because the task is a multi-field extraction problem where no
single primitive returns all fields. The baseline is measured and published.

### Instruction 3.4 — Build the Lead Enrichment Evaluator

The Lead Enrichment Evaluator takes as input a partially-complete lead record
(name and company are known, other fields are missing) and measures how
accurately an evolved program fills in the missing fields.

The input is a dict with known fields and None for unknown fields. The expected
output is the complete dict with all fields correctly filled. The primitive set
includes all Tier 2 string primitives plus the Tier 4 HTTP primitives. The
fitness function is identical to the Live Lead Scraping Evaluator.

The enrichment task is harder than the scraping task because the program must
decide which APIs and sources to query based on what is already known, and must
reconcile conflicting information from different sources.

Phase 3 is complete when: the network sandbox passes 30 security tests covering
domain blocking, rate limiting, robots.txt compliance, request logging, and
size limits. All 6 HTTP primitives are implemented and approved at Tier 4. The
Live Lead Scraping Evaluator is built with 200 verified company records and
passes the safety gate. A 3-seed run of 5,000 generations is completed and
results are honestly reported. The request log for the test runs is published
and contains no blocked requests or policy violations.

---

# PHASE 4 — THE KNOWLEDGE BASE
## Give the System Memory That Persists Across Runs

### Why the Current System Has No Memory

Every evolution run starts from scratch. The champion found in run 1 is not
available to run 2 unless explicitly injected via the memome. There is no
persistent knowledge base that accumulates successful strategies across many
runs. This means the system cannot improve at lead scraping by remembering
which company domains have which email formats.

Phase 4 gives the system persistent memory that evolves with it.

### Instruction 4.1 — Build the Distributed Knowledge Store

The knowledge store is a key-value store with the following schema:

Task records: for each task domain (lead scraping, lead enrichment, sorting,
manhattan distance, etc.), the knowledge store holds: the current champion
program, the champion's fitness, the champion's tree hash, the run_id that
produced the champion, and the date. This record is updated whenever a new
champion beats the current one.

Domain records: for each domain that the network sandbox has fetched, the
knowledge store holds: the fetched text (last 3 fetches), the extracted lead
data (if any), the date of last fetch, and the rate limit status. This cache
prevents the system from re-fetching the same domain repeatedly.

Cultural memory: for each task domain, the knowledge store holds the top 20
partial solutions found across all runs — programs that achieved fitness above
0.7 even if they didn't reach champion level. These partial solutions seed the
initial population of future runs, giving them a cultural head start.

Company email pattern records: for each company domain (gmail.com, microsoft.com,
amazon.com, etc.), the knowledge store holds the email format pattern observed
from successfully verified emails: first.last@domain.com, f.last@domain.com,
firstlast@domain.com, etc. This pattern is used by the enrichment evaluator
to score email guesses more accurately.

The knowledge store must be persistent across server restarts. It must support
concurrent reads from multiple evolution workers. It must support atomic writes
(so two workers discovering the same champion simultaneously don't corrupt
the record). A standard embedded key-value store (LMDB or SQLite in WAL mode)
satisfies all these requirements without requiring a separate server process.

### Instruction 4.2 — Build the Cultural Memory Injection System

When a new evolution run starts, the system queries the knowledge store for
the cultural memory of the task domain. It injects the top 5 partial solutions
into the initial population as pre-seeded organisms. The remaining organisms
are initialised randomly as usual.

This injection must verify that each injected organism's tree hash matches the
hash stored in the cultural memory record. If they don't match (indicating the
knowledge store was corrupted or tampered with), the corrupted record is
discarded and the slot is filled with a random organism.

The injection is transparent: the run's audit trail records exactly which
organisms were injected from cultural memory and which were randomly initialised.

### Instruction 4.3 — Build the Champion Update Pipeline

When a run completes and a new champion is found, the system checks whether the
new champion beats the current knowledge store champion for that task. If it
does, the pipeline: signs the new champion record with the local federation
key, writes it to the knowledge store, broadcasts it to any connected federation
peers, and creates an entry in the discovery log if the fitness exceeds the
discovery threshold.

The pipeline must be idempotent — if the same champion is submitted twice, the
second submission is silently ignored. It must be atomic — the old champion
is not removed until the new champion is confirmed written.

### Instruction 4.4 — Build the Email Pattern Learning System

After each successful lead enrichment result (where a verified correct email
was found), the system extracts the email format from the result and adds it
to the domain's email pattern record in the knowledge store. The format is
represented as a pattern string: {first}.{last}@{domain}, {first_initial}
{last}@{domain}, {first}{last}@{domain}, etc.

Future enrichment runs for the same domain use this pattern to generate a
more accurate email guess before calling the API, saving API quota. The
system tracks how often each pattern is correct per domain and uses the
most-accurate pattern as the primary guess.

Phase 4 is complete when: the knowledge store is implemented and passes 25
tests covering concurrent reads, atomic writes, cultural memory injection,
champion update, and email pattern learning. A full pipeline test runs two
evolution runs in sequence and confirms the second run's initial population
includes cultural memory from the first run. The champion update pipeline
produces a signed discovery record for a run where the fitness exceeds 0.8.

---

# PHASE 5 — THE MULTI-TASK AGENT
## Coordinate Multiple Evaluators to Solve Complex Real-World Problems

### Why Single-Task Evolution Is Not Enough

Lead scraping is not a single task. It is a pipeline: find companies that match
a profile, extract decision-maker contact data, enrich with additional sources,
verify the data, and format it for the CRM. No single evolved program can do
all of this — the tasks are too different in nature. Phase 5 builds the
coordination layer that connects specialised evolved programs into a pipeline.

### Instruction 5.1 — Build the Task Pipeline Orchestrator

The Task Pipeline Orchestrator is a system that chains multiple evolved programs
together, where the output of one program is the input of the next.

A pipeline is defined as an ordered list of task references. For lead generation,
the pipeline is:

Step 1: Company Discovery — evolved program takes a target profile (industry,
size, location) and returns a list of company domains.

Step 2: Decision-Maker Extraction — evolved program takes a company domain
and returns the decision-maker's name and title.

Step 3: Contact Data Enrichment — evolved program takes a name, title, and
domain and returns a complete contact record.

Step 4: Data Verification — evolved program takes a contact record and returns
a verification score and flags for suspect fields.

Step 5: CRM Formatting — evolved program takes a verified contact record and
returns a dict formatted for import into HubSpot, Salesforce, or Pipedrive.

Each step in the pipeline is evaluated independently. The overall pipeline's
fitness is the product of all steps' fitness scores — a weak link brings down
the entire pipeline. This scoring encourages all steps to be strong, not just
one.

### Instruction 5.2 — Build the Pipeline Fitness Evaluator

The Pipeline Fitness Evaluator runs the full multi-step pipeline on 50 target
company profiles. It measures end-to-end accuracy: how many of the 50 targets
produced a verified, correctly-formatted lead record that could actually be
used to send a cold email?

This end-to-end measure is the only metric that matters to the business user.
Intermediate step metrics (accuracy of company discovery, accuracy of contact
extraction) are recorded but do not directly drive champion selection. The
champion is the pipeline variant that produces the most usable end-to-end lead
records per API call budget.

### Instruction 5.3 — Build the Budget-Aware Fitness Function

Real-world lead generation has a cost per lead. Each API call costs money
(Hunter.io charges per lookup, Clearbit charges per enrichment). The pipeline
fitness function must incorporate this cost:

Adjusted fitness = (leads verified correctly) / (total API calls made + 1)

A pipeline that finds 40 correct leads using 50 API calls scores higher than
one that finds 42 correct leads using 200 API calls. The +1 in the denominator
prevents division by zero and penalises pipelines that make no API calls but
also find no leads.

The budget-aware fitness function rewards efficiency, not just accuracy. This
is the same principle that drives real-world lead generation tools — more
leads per dollar is better than more leads total.

### Instruction 5.4 — Build the Parallel Pipeline Runner

Evolved pipelines must be evaluated in parallel across the 50 target companies.
The parallel runner uses a process pool (same as the sandbox pool from Phase 1)
with one worker per target company. The 50 evaluations run concurrently, subject
to the global rate limit quota (maximum 100 requests per hour total). The wall-
clock time for one fitness evaluation of a 50-company pipeline must not exceed
120 seconds.

Phase 5 is complete when: the Task Pipeline Orchestrator can chain two or more
evolved programs and pass data between them. The Pipeline Fitness Evaluator
runs correctly on 50 target companies. A 3-seed run of 2,000 pipeline-level
generations produces honest results. The Parallel Pipeline Runner reduces
evaluation wall-clock time to under 120 seconds for the 50-company test.

---

# PHASE 6 — THE BENCHMARK SUITE
## Prove the System Competes with Claude and Codex on Real Tasks

### Why Benchmarks Define Whether the System Has Reached Its Goal

Without a benchmark, "comparable to Claude or Codex" is a claim with no
evidence. Phase 6 defines the specific benchmarks the system must pass to
justify that claim, runs the benchmarks honestly, and publishes the results
whether they are good or bad.

### Instruction 6.1 — The HumanEval Benchmark

HumanEval is a standard programming benchmark consisting of 164 Python
programming problems with unit tests. Claude 3.5 Sonnet passes 92% of
HumanEval problems. Codex passes 72%. GPT-4 passes 87%.

To run HumanEval with this system: each problem is a fitness evaluator. The
input is the function's docstring (as a string). The output is Python source
code that passes the unit tests. The fitness is the fraction of unit tests
passed.

This is the hardest challenge for the current system because: the system
currently evolves programs from primitives, not from natural language. Converting
a docstring to a program specification requires understanding English, which
is outside the current capability.

However, for the subset of HumanEval problems that are mathematical or
algorithmic (not requiring string parsing of the docstring), the system can
compete. Identify the 40 HumanEval problems that are pure algorithmic
transformations (sort, find max subarray, count occurrences, etc.) and run
the system on those 40. Report: how many does the system solve in under 10,000
generations? How many does Claude solve on first attempt?

The honest expectation: the system will solve 15–25 of the 40 algorithmic
HumanEval problems within 10,000 generations. Claude solves all 40 on first
attempt. This is not a failure — it is an honest measurement of where the
system stands versus a state-of-the-art LLM.

### Instruction 6.2 — The Lead Generation Benchmark

This is the benchmark the system is designed to win over Claude and Codex.
Define 100 target company profiles: industry, size range, location. The task
is to produce a verified lead record (name, email, title, LinkedIn URL) for
the primary decision-maker at each company.

Compare three systems on this benchmark:

System A — This GP evolution system after Phase 5, running the full lead
generation pipeline with 5,000 generations of optimisation.

System B — Claude 3.5 Sonnet with web browsing enabled, given the same target
profile and asked to find the lead.

System C — A human researcher using LinkedIn and Hunter.io manually.

Measure for each system: accuracy (what fraction of produced leads are correct
when verified), cost (API calls + time), and how the accuracy changes when
the target company is obscure (not in the training data) versus well-known.

The expected result: for well-known companies, Claude will match or beat the
evolved system. For obscure companies outside Claude's training data, the evolved
system may perform comparably because it does not rely on memorised data — it
actually fetches and parses current data.

This benchmark is the honest answer to "can it compete with Claude at lead
generation?" If the evolved system achieves above 60% accuracy on obscure
company targets while Claude achieves below 40% (because Claude's training
data does not include those companies), then the system has demonstrated a
genuine advantage in a specific, real-world, measurable way.

### Instruction 6.3 — The Code Synthesis Benchmark

Define 50 programming tasks drawn from real freelancing job boards: data
cleaning, file format conversion, API integration patterns, data validation
rules, report generation from structured data. These tasks are chosen because
they are the kind of tasks that a business owner would pay a freelancer to
write, not the kind of abstract algorithmic problems in academic benchmarks.

For each task, the fitness evaluator provides: 20 input-output examples and
a test suite of 30 additional cases. The system runs 5,000 generations. The
evolved champion is tested against the full test suite.

Compare the evolved champion to: a Claude-generated solution (asked with the
same 20 examples as few-shot examples) and a human-written solution (written
by an experienced developer in 30 minutes).

Measure: test suite pass rate for each approach. Development time/cost for
each approach. Readability of the produced code.

The expected result: Claude will generally produce more readable code that
passes more tests on the first attempt. The evolved system will sometimes
produce less readable but correct code, and will occasionally find solutions
that neither Claude nor the human developer thought of. Publish all results
honestly.

### Instruction 6.4 — The Multi-Seed Robustness Benchmark

For each task in the benchmark suite, run 10 independent seeds (not 5). Report:
median performance (not best performance), worst-case performance (the seed
that performed worst), and the consistency ratio (how many of the 10 seeds
achieved fitness above 0.7). A system that scores 0.9 on the best seed but
0.3 on the worst is not production-ready. A system that scores 0.75 on every
seed is.

Phase 6 is complete when: the 40-problem algorithmic HumanEval subset has been
run with results published honestly. The Lead Generation Benchmark has been
run with 3 systems compared and results published. The Code Synthesis Benchmark
has been run with results published. The Multi-Seed Robustness Benchmark shows
consistency ratios above 0.7 for at least 3 of the 5 lead-related tasks.

---

# PHASE 7 — THE STATEFUL AGENT FRAMEWORK
## Give the System Persistent Goals That It Pursues Autonomously

### Why Statefulness Separates Agents from Programs

The current system is stateless. Each evolution run has a goal, runs to
completion, and stops. It cannot pursue a goal that spans multiple runs. It
cannot observe the results of a previous run and decide to change strategy.
It cannot maintain a task queue, assign sub-tasks to specialised evolved
programs, or report progress to a human operator.

Phase 7 gives the system agency: the ability to set goals, plan steps, execute
sub-tasks, observe results, adapt, and persist until the goal is achieved.

### Instruction 7.1 — Build the Goal Registry

The Goal Registry is a persistent queue of goals with the following structure
for each goal: a unique goal ID, a description in plain text, a success
criterion (a Python expression that evaluates to True when the goal is achieved,
run in a sandboxed process), a priority (1–10), a deadline (timestamp or None),
the list of sub-goals it depends on, and the current status (pending, running,
blocked, completed, failed).

The success criterion is crucial. It must be machine-evaluable. "Scrape 100
leads" is a valid success criterion because the system can count verified lead
records. "Understand what the user wants" is not a valid success criterion
because it cannot be measured.

A new goal is added to the Goal Registry via the CLI command
`living-objects goal add --description "..." --criterion "..." --priority 5`
or via the REST API endpoint POST /v9/goals with the same fields.

### Instruction 7.2 — Build the Sub-Goal Decomposer

The Sub-Goal Decomposer takes a high-level goal from the Goal Registry and
decomposes it into a sequence of sub-goals that correspond to task-level
evolution runs. For lead generation: the high-level goal "Find 100 verified
leads in the SaaS industry with 50–200 employees" decomposes into:

Sub-goal 1.1: Run the Company Discovery evolved program on SaaS industry
targets in the 50–200 employee range. Success criterion: 500 candidate
companies identified.

Sub-goal 1.2: Run the Decision-Maker Extraction pipeline on the 500 candidates.
Success criterion: 300 decision-maker names found.

Sub-goal 1.3: Run the Contact Data Enrichment pipeline on the 300 names.
Success criterion: 150 email addresses found with confidence > 0.8.

Sub-goal 1.4: Run the Data Verification step on the 150 email addresses.
Success criterion: 100 emails verified as deliverable.

Sub-goal 1.5: Format the 100 verified leads for CRM import.
Success criterion: JSON file produced with 100 records, all fields present.

The decomposer is implemented as a set of rules, not as an LLM. Each rule
maps a goal description pattern (using keyword matching and target field
extraction) to a sequence of sub-goals. The decomposer is honest about its
limitations: if it cannot match the goal description to a known pattern, it
returns an error and asks the human operator to define the sub-goals manually.

### Instruction 7.3 — Build the Autonomous Execution Loop

The Autonomous Execution Loop runs continuously as a background process. It:

Every 60 seconds: checks the Goal Registry for pending goals whose dependencies
are met. For the highest-priority eligible goal, starts an evolution run with
the appropriate task evaluator and configuration. Records the run_id against
the goal in the registry.

Every 5 minutes: checks all running evolution runs for completion. For completed
runs, evaluates the success criterion. If met, marks the goal as completed and
unlocks dependent goals. If not met, decides whether to: retry with the same
configuration, retry with an adjusted configuration (more generations, different
seed), escalate to the human operator (if the goal has failed 3 times), or
decompose into smaller sub-goals.

Every 24 hours: reviews all completed goals and checks whether the champions
found during those runs are still performing well on fresh test cases (not just
the original test set). Champions that degrade over time (because the data
distribution has shifted) are flagged for re-evolution.

### Instruction 7.4 — Build the Human Operator Interface

The Human Operator Interface is the dashboard where the human monitors the
autonomous system and intervenes when needed. It shows:

Goal status: a list of all active goals with their status, priority, deadline,
and progress toward the success criterion.

Resource usage: current API call rate (vs. hourly budget), current CPU
utilisation by evolution workers, current memory usage by the knowledge base.

Alert queue: goals that have failed 3 times and need human intervention,
champions that have degraded and need re-evolution, rate limits that have been
hit, domains that have blocked the system's requests.

Action buttons: approve a new goal, pause all evolution runs, change the
priority of a goal, manually supply a champion for a task (bypassing evolution),
expand the domain whitelist (requires human confirmation with justification).

The Human Operator Interface is a web page served by the same FastAPI server
as the Observatory. It requires authentication (unlike the Observatory which
is public). It is the command centre of the autonomous agent.

Phase 7 is complete when: the Goal Registry can store and query goals with
all required fields. The Sub-Goal Decomposer correctly handles the lead
generation goal pattern and produces the 5 sub-goals described above. The
Autonomous Execution Loop runs correctly for 24 hours on a test set of 3 goals
without human intervention and achieves all 3 success criteria. The Human
Operator Interface shows correct information for all running goals.

---

# PHASE 8 — THE SELF-IMPROVEMENT ENGINE
## Let the System Optimise Its Own Architecture

### Why Self-Improvement is the Final Frontier

Claude and Codex are improved by human researchers who study their failures
and redesign their architectures. This system can improve itself by observing
which configurations succeed and evolving better configurations. This is the
capability that no current LLM has: the ability to redesign its own fitness
evaluators, primitive sets, and evolution parameters based on empirical results.

### Instruction 8.1 — Build the Hyper-Evolution System

The Hyper-Evolution System treats evolution parameters themselves as evolvable.
The parameters that can be evolved: crossover rate (currently 0.85), mutation
rate (currently 0.12), tournament size (currently 7), elitism count (currently
5), maximum tree depth (currently 8), population size (currently 50).

The hyper-evolution fitness function is: run 10 evolution runs with the
candidate configuration, measure the median champion fitness across all 10
runs, return that as the hyper-fitness. A configuration that reliably produces
good champions has high hyper-fitness.

The hyper-evolution runs on a fast proxy task (not the full lead pipeline)
to keep the hyper-evolution time manageable. The proxy task must be
representative of the difficulty of the real task without requiring network
access (which would make hyper-evolution too slow).

After hyper-evolution completes, the best configuration is stored in the
knowledge base and used as the default for future evolution runs on that task.

### Instruction 8.2 — Build the Primitive Set Evolution System

Beyond evolving programs, the system can evolve which primitives to offer to
those programs. The Primitive Set Evolution System treats the set of available
primitives as a variable parameter. A configuration is: a subset of all
approved primitives. The fitness of a configuration is: how well can evolution
find a champion for the target task using only those primitives, measured across
5 seeds and 5,000 generations each?

The Primitive Set Evolution System searches for the minimal effective primitive
set — the smallest set of primitives that allows the system to achieve
fitness above 0.8 on the target task. Minimal primitive sets produce more
interpretable champions (smaller programs) and reduce the contamination risk
(fewer primitives means less chance of accidental direct solutions).

### Instruction 8.3 — Build the Curriculum Auto-Generator

The Curriculum Auto-Generator takes a target task and a primitive set and
automatically generates a curriculum (a sequence of sub-tasks of increasing
difficulty) using the following procedure:

Start with the simplest possible version of the task (the smallest inputs, the
fewest required operations). Run a fast evolution (1,000 generations, population
20) and measure the fitness achieved. If fitness is above 0.8, the sub-task
is too easy (possibly contaminated) — make it harder. If fitness is below 0.1,
the sub-task is too hard — make it simpler. The target baseline fitness for
a curriculum stage is 0.2–0.5 after 1,000 generations.

Continue generating progressively harder sub-tasks until the final sub-task
matches the full task difficulty. The resulting sequence of sub-tasks is the
auto-generated curriculum. Publish it in the curriculum registry alongside
manually designed curricula for comparison.

Phase 8 is complete when: the Hyper-Evolution System finds a better configuration
than the current defaults for at least one task (measured by median champion
fitness across 10 seeds). The Primitive Set Evolution System identifies a
minimal effective primitive set for the Manhattan distance task. The Curriculum
Auto-Generator produces a 5-stage curriculum for the lead extraction task that
achieves higher final fitness than evolution without a curriculum.

---

# PHASE 9 — THE MULTI-LANGUAGE SYNTHESIS ENGINE
## Produce Production Code in Any Language, Not Just Python

### Why Multi-Language Output Matters

Real-world software is not written in one language. A lead scraping pipeline
might need Python for data processing, JavaScript for a browser-based crawler,
Go for a high-performance server component, and SQL for database queries. If
the evolved champion can only be exported to Python and JavaScript (the current
state), the system cannot produce usable code for the full pipeline.

### Instruction 9.1 — Expand the Polyglot Compiler to 8 Languages

The current polyglot compiler supports Python, JavaScript, Rust, and Go for
the Manhattan distance task only. Phase 9 expands it to:

Python: all tasks, all primitive tiers (already supported)
JavaScript/TypeScript: all tasks with Tier 1 and Tier 2 primitives
Go: all tasks with Tier 1 and Tier 2 primitives
Rust: all tasks with Tier 1 and Tier 2 primitives
Java: all tasks with Tier 1 and Tier 2 primitives
C#: all tasks with Tier 1 and Tier 2 primitives
SQL: tasks that reduce to aggregation, filtering, and joining (Tier 1 list
primitives map to SQL WHERE, GROUP BY, ORDER BY, and JOIN clauses)
Bash/Shell: tasks that reduce to text processing pipelines (Tier 2 string
primitives map to sed, awk, grep, cut, and tr commands)

For each language, define a compilation rule for every approved primitive.
The rule maps the primitive's name and its compiled child expressions to
a language-specific expression string. The compiler recursively applies these
rules from leaves to root.

Every compiled output for every language must be validated by a runtime test
before the compilation rule is merged. The runtime test: compile a known
champion, execute the compiled code in the target language's runtime, compare
the output to the Python interpreter's output for 100 test inputs. If they
match within tolerance, the compilation rule is correct.

### Instruction 9.2 — Build the Code Quality Post-Processor

Evolved code is correct but not always readable. The Code Quality Post-Processor
takes a compiled program and applies language-specific transformations to
make it more maintainable:

Variable naming: replace auto-generated variable names (x, y, z, tmp0, tmp1)
with descriptive names derived from the primitive that generated the value
(e.g., a value produced by abs1 becomes abs_value, a value produced by concat
becomes concatenated_text).

Simplification: identify and simplify redundant sub-expressions. If the tree
contains add(x, 0), replace with x. If it contains mul(x, 1), replace with x.
These simplifications are valid only for Tier 1 arithmetic primitives where
the algebraic identities are guaranteed.

Documentation: add a docstring or comment at the top of every compiled program
that describes what the program does, derived from the task name and the champion's
performance metrics. Include the tree hash, the run_id, and the fitness score
as metadata comments.

The Code Quality Post-Processor must not change the program's output — only
its presentation. Every post-processed program must pass the same test suite
as the original compiled program.

Phase 9 is complete when: all 8 language targets are implemented with at least
one compilation rule per currently-approved primitive. All compilation rules
have passing runtime tests. The Code Quality Post-Processor correctly renames
variables and simplifies trivial expressions for at least Python and JavaScript
outputs.

---

# PHASE 10 — THE PRODUCTION DEPLOYMENT
## Make It Actually Available to Real Users

### Instruction 10.1 — Harden the REST API for Production

Fix the five critical issues identified in the v11 audit before any public
deployment:

Fix 1: async/sync mismatch. All evolution endpoints must use
asyncio.to_thread() to run the evolution loop in a thread pool, preventing
the event loop from blocking.

Fix 2: authentication. All endpoints except the public Observatory panels
must require an API key in the Authorization header. API keys are issued
via a registration flow (email + verification).

Fix 3: rate limiting. Enforce at the FastAPI middleware level: 10 evolution
starts per hour per API key, 60 read requests per minute per API key,
5 sandbox evaluations per minute per API key.

Fix 4: input validation. All endpoint parameters must be validated using
Pydantic models with explicit bounds. Any parameter outside the specified
bounds returns a 422 error with a clear message.

Fix 5: graceful degradation. All read endpoints (get champion, audit status,
discovery log) must return cached data if the live computation is unavailable,
with a clear header indicating the data age.

### Instruction 10.2 — Deploy the Observatory to a Permanent URL

The Observatory must be at a permanent URL with a SSL certificate, deployed
on a server that is always on. The minimum acceptable deployment: one cloud
VPS running the FastAPI backend and the WebSocket gateway, with a static
frontend served from a CDN. The frontend assets are built once and uploaded
to the CDN. They never need to be rebuilt unless the frontend code changes.

The deployment pipeline (make deploy) must: build the frontend, upload to CDN,
deploy the backend Docker container, run a smoke test that verifies all six
Observatory panels are receiving real data, and send a notification to the
team if any step fails. The entire deployment must complete in under 10 minutes.

### Instruction 10.3 — Publish the SDK to PyPI

The package must be published to PyPI as `living-objects` with version 1.0.0.
Before publication: all four top-level functions (evolve, audit, reproduce,
export) must have correct docstrings with the accurate attribute names
(result.champion["training_fitness"] not result.fitness, or add the property
aliases that make result.fitness work). The package must install on Python
3.10, 3.11, 3.12, and 3.13. The installation must not require compiling
any C extensions (pure Python only). The package must include all data files
needed by the audit() function (the benchmark ledger JSON) as package data.

### Instruction 10.4 — Submit the arXiv Paper

The Manhattan distance paper (docs/v10-arxiv-submission-package/main.tex) is
ready. The submission steps: compile the LaTeX to PDF, verify all figures
render correctly, register on arXiv, submit to cs.NE, wait for moderation
(typically 1 business day), commit the arXiv ID to the repository.

After submission, post the arXiv link to: the README, the Observatory's About
panel, the Honest Claims Registry, and the SDK's package description on PyPI.

Phase 10 is complete when: all five API issues are fixed and tested. The
Observatory is live at a public URL where anyone can watch real evolution.
`pip install living-objects` works from any internet-connected machine. The
arXiv paper has an arXiv ID.

---

# PHASE 11 — THE FEDERATION NETWORK
## Connect Multiple Installations to Share Discoveries

### Instruction 11.1 — Build the Public Federation Registry

The Public Federation Registry is a public list of Living Objects installations
that have opted in to sharing their discovery records. Each entry contains:
the installation's public key (for verifying signed records), the installation's
public Observatory URL (for humans to visit), and the tasks the installation
is actively evolving.

The registry is a static JSON file hosted in the main repository. Any
installation can submit a pull request to add itself to the registry. The
registry does not include any sensitive data — only the public key and URL.

### Instruction 11.2 — Build the Automated Discovery Exchange

Every installation that opts in to federation runs an exchange job every 6
hours. The job: downloads the discovery log from each peer in the registry,
verifies the signatures, runs each claimed champion through the local evaluator
in the sandbox, and adds verified champions to the local cultural memory if
they score above 0.8. Rejected champions (signature invalid or evaluator score
below 0.8) are logged with the reason and the peer's public key.

The exchange is pull-based (each installation pulls from peers) rather than
push-based (peers broadcasting to each other). This means an installation can
participate in federation without accepting incoming connections — it can be
behind a firewall and still benefit from peer discoveries.

Phase 11 is complete when: the Public Federation Registry has at least 2
entries (the main installation and one test installation). The Automated
Discovery Exchange correctly imports a champion from the test installation and
adds it to the main installation's cultural memory. The import is logged in
the audit trail.

---

# PHASE 12 — THE FINAL CAPABILITY GATES
## Verify the System Has Reached Its Goal

### Capability Gate 1 — Lead Generation End-to-End

Run the full lead generation pipeline on 50 real company targets. The pipeline
must produce at least 35 verified lead records (70% success rate) using fewer
than 300 API calls total. The champions at each pipeline step must have fitness
above 0.7 on the fresh test set. The entire pipeline must complete in under
4 hours.

If this gate passes: the system can do what Claude cannot — generate verified
leads for obscure companies by actually fetching and parsing current data.

### Capability Gate 2 — HumanEval Algorithmic Subset

Run the 40-problem algorithmic HumanEval subset. The system must solve at
least 25 of the 40 problems within 10,000 generations each. Publish the results
per-problem with the fitness curve and the champion's code.

If this gate passes: the system can solve real programming problems at
approximately the level of a junior developer, without using an LLM.

### Capability Gate 3 — Continuous 72-Hour Autonomous Operation

Run the Autonomous Execution Loop for 72 hours without human intervention on
a set of 10 active goals. The loop must: complete at least 8 of the 10 goals,
handle at least 2 goals that fail and retry with adjusted configuration, and
produce a complete audit trail that accounts for every decision made.

If this gate passes: the system can operate as a production autonomous agent.

### Capability Gate 4 — Honest Comparison to Claude and Codex

Publish the Lead Generation Benchmark results comparing the evolved system to
Claude and Codex. The comparison must be honest: report where Claude wins,
where the system wins, and where they are comparable. If the system does not
win on any dimension, say so clearly and explain what would need to change.

### Capability Gate 5 — Public Verifiability

Every result in the discovery log must be reproducible by anyone who clones
the repository. Run the weekly reproducibility check for 4 consecutive weeks.
If any result fails to reproduce, investigate and either fix the issue or
retract the result.

---

# REAL-WORLD TEST SUITE FOR v12

The following 20 real-world tests must pass before v12 is declared complete.
These tests are designed to be run by someone who has never seen this project
before, following only the public README.

### Test 1 — Cold Install Test
Clone the repository on a clean machine with only Python 3.11 installed. Run
the full setup in under 15 minutes. Run `pip install living-objects` and call
`evolve("manhattan", generations=300, seed=42)`. Verify fitness above 0.9.

### Test 2 — Lead Extraction from a Real Company Website
Given the domain "stripe.com", run the evolved lead extraction champion on
the Stripe website and verify that it correctly identifies at least 3 of:
company name, industry, employee count range, headquarters city, primary
product description.

### Test 3 — Email Format Detection
Given 20 verified emails from 10 companies (2 per company), the evolved email
pattern system must correctly identify the email format for 8 of the 10
companies and use that format to correctly guess the email address for a new
employee at each company (with confidence above 0.7).

### Test 4 — JavaScript Export Runtime Correctness
Export the current Manhattan distance champion to JavaScript. Run the JS
function in Node.js against 1,000 random inputs. Verify that the JS output
matches the Python interpreter output for all 1,000 inputs within tolerance.

### Test 5 — Reproduction Stability Across 30 Days
Take the Manhattan distance champion from the 5-seed v8 run. Re-run the
reproduction script. Verify that the tree hash matches the published hash.
This test verifies that the codebase has not silently changed the evolution
algorithm in a way that breaks determinism.

### Test 6 — Rate Limit Enforcement
Attempt to make 200 HTTP requests in one minute through the network sandbox.
Verify that the sandbox blocks requests above the rate limit and logs the
blocking events. Verify that the evolution run that exceeded the limit still
completes (with degraded fitness due to blocked requests, not with a crash).

### Test 7 — Domain Whitelist Enforcement
Attempt to fetch a URL from a domain not on the whitelist (e.g., wikipedia.org).
Verify that the network sandbox returns an empty string and logs the blocked
attempt. Verify that the evolution run continues without crashing.

### Test 8 — Large Population Memory Safety
Run an evolution with population_size=500 for 100 generations. Verify that
peak memory does not exceed 50 MB. Verify that all 100 generations complete
without a MemoryError.

### Test 9 — Curriculum Stage Progression
Run the sorting curriculum for 50,000 generations on a cloud instance. Verify
that the population advances at least through Stage 1 (sort 3-element lists).
Record the generation at which Stage 1 is first achieved.

### Test 10 — Pipeline End-to-End for 10 Companies
Run the full lead generation pipeline on 10 well-known tech companies. Verify
that the pipeline produces verified lead records for at least 7 of the 10.
Report the number of API calls used.

### Test 11 — Autonomous Goal Completion
Add a goal to the Goal Registry: "Find one verified lead at a Series B SaaS
company headquartered in London." Run the Autonomous Execution Loop. Verify
that the goal is completed within 6 hours without human intervention.

### Test 12 — arXiv Paper Download and Reproduce
Download the arXiv paper. Follow the reproduction instructions in the paper.
Verify that running the reproduction command produces a champion that matches
the published tree hash within the stated tolerance.

### Test 13 — Federation Import from Test Installation
Set up a second test installation on a different machine. Run the Manhattan
distance task on the second installation. Export the signed discovery record.
Import it to the main installation. Verify that the main installation's cultural
memory now contains the imported champion and that it passes the local evaluator.

### Test 14 — GameStrategyEvaluator Disabled
Attempt to start an evolution run using the GameStrategyEvaluator. Verify
that the safety gate blocks the run with a clear error message explaining that
the evaluator has not passed the safety gate.

### Test 15 — API Authentication Enforcement
Attempt to call POST /v9/evolve without an Authorization header. Verify that
the server returns a 401 Unauthorized response. Attempt with an invalid API
key. Verify 403 Forbidden. Attempt with a valid API key. Verify the run starts.

### Test 16 — Observatory Live Data Verification
Open the Observatory URL in a browser. Wait 60 seconds. Verify that Panel 2
(fitness graph) has updated at least once with a new data point. Verify that
Panel 1 (champion code) shows Python source code that actually compiled from
a GP tree (not placeholder text).

### Test 17 — Honest Claims Registry Completeness
Download docs/v9-claims-registry.md. Verify that every claim in the README
appears in the registry with a status of Verified, Disputed, or Retracted.
Verify that no claim is present in the README but absent from the registry.

### Test 18 — SDK Error Messages Are Helpful
Call evolve("sortng", generations=300, seed=42) with a typo in the task name.
Verify that the error message includes: the misspelled name, a suggestion for
the correct spelling, and the list of valid task names.

### Test 19 — Rate Limit Error Recovery
Start an evolution run that exhausts the hourly API quota. Verify that the
run does not crash — it continues with fitness scores of 0 for the remainder
of the hour rather than raising an exception. Verify that at the start of the
next hour, the run automatically resumes using API calls.

### Test 20 — Benchmark Result Honesty Check
Review the published Lead Generation Benchmark results. Verify that the
publication includes: the number of targets where Claude performed better,
the number where the evolved system performed better, and the number where
they were within 10% of each other. Verify that the worst-performing seeds
are included in the results, not just the best.

---

# VULNERABILITY REMEDIATION MANDATES

The following vulnerabilities from the v11 audit must be fixed before Phase 3
begins. None of these are optional. Each has a verification test.

REMEDIATION 1 — GameStrategyEvaluator: Disable the evaluator immediately.
Add a check in the safety gate that blocks any run using this evaluator until
it is rebuilt from scratch with a correct Prisoner's Dilemma simulation and
approved by the safety gate. Verification: running `living-objects evolve
--task game-strategy` returns a clear error.

REMEDIATION 2 — Async/Sync Mismatch: Refactor the evolve endpoint to run
the evolution loop in asyncio.to_thread(). Verification: run 3 concurrent
evolve requests and confirm all 3 complete within expected time (not 3x
sequentially).

REMEDIATION 3 — No Authentication: Add Pydantic-based API key validation
as FastAPI middleware. Verification: the 3-test sequence in Test 15 above.

REMEDIATION 4 — SDK Attribute Names: Add `.fitness` and `.source_code`
as properties on `EvolutionResult` that correctly delegate to `champion
["training_fitness"]` and `champion["source_audit_export"]`. Update all
docstrings and README examples. Verification: the live evolve call in
Test 1 uses `result.fitness` without AttributeError.

REMEDIATION 5 — Federation Key Safety: Add a pre-commit hook that scans
all files for strings matching the federation key pattern and blocks commits
that would expose a key. Verification: attempt to commit a file containing
a fake federation key and confirm the hook blocks it.

REMEDIATION 6 — Evaluation Timeout: Wrap every tree evaluation in a
500ms timeout using signal.alarm (Unix) or a threading.Timer (cross-platform).
Any evaluation that times out receives fitness 0. Verification: add a
deliberately slow primitive (sleep) in a test, confirm the timeout fires.

REMEDIATION 7 — Deepcopy in Curriculum Injection: Replace the shallow copy
in cultural memory injection with deepcopy. Verification: confirm that
mutating an injected organism in the new stage does not affect the original
cultural memory record.

REMEDIATION 8 — artifact_path After Resume: Fix the EvolutionResult
reconstruction after checkpoint load to pass the artifact directory path.
Verification: save a run, load it, call reproduce(), confirm it does not
raise FileNotFoundError.

---

# THE HONEST TIMETABLE

Phase 1 — Safety Architecture: 3 weeks
Phase 2 — String and Pattern Engine: 2 weeks
Phase 3 — Network Primitive Sandbox: 4 weeks (most complex phase)
Phase 4 — Knowledge Base: 2 weeks
Phase 5 — Multi-Task Agent: 3 weeks
Phase 6 — Benchmark Suite: 2 weeks (mostly running experiments)
Phase 7 — Stateful Agent Framework: 3 weeks
Phase 8 — Self-Improvement Engine: 4 weeks
Phase 9 — Multi-Language Synthesis: 2 weeks
Phase 10 — Production Deployment: 1 week
Phase 11 — Federation Network: 1 week
Phase 12 — Final Capability Gates: 2 weeks (mostly running tests)

Total: approximately 29 weeks from the start of Phase 1.

This timetable assumes one experienced engineer working full-time. With three
engineers, Phases 1–5 can run in parallel with reduced total time. With ten
engineers, the full 12 phases can complete in approximately 12–15 weeks.

---

# WHAT "CLAUDE AND CODEX LEVEL" ACTUALLY MEANS

Claude and Codex are not the same kind of system as this one. Saying "reach
Claude level" requires being specific about which capability on which task.

On natural language understanding: this system will never reach Claude level.
Claude was trained on the entire internet. This system does not process natural
language — it evolves programs from primitive operations. These are
fundamentally different paradigms. This system will not be asked "explain quantum
mechanics" — that is not its domain.

On lead generation from the open web: after Phase 3 and 5, this system has
a real chance to match or exceed Claude for obscure targets. The reason:
Claude's knowledge of a company called "FinTech Startup X founded in 2024 in
Lagos" is zero because the company did not exist when Claude was trained. This
system fetches current data and extracts it fresh. Claude guesses. This system
looks.

On algorithmic code synthesis: after Phase 6, this system will solve 25–35
of the 40 algorithmic HumanEval problems. Claude solves 40. The gap reflects
Claude's advantage in language understanding and memorised algorithms. The
system's advantage: it produces code that is provably correct on the test
suite, not just plausible-looking. Claude's code can fail edge cases.

On cost and reproducibility: after Phase 10, a verified lead generated by
this system comes with a signed audit trail that proves exactly how it was
found and can be reproduced. A lead found by Claude comes with no such proof.
For regulated industries (financial services, healthcare) where the provenance
of data matters, reproducible provenance is a genuine competitive advantage.

---

# THE COMPLETION DEFINITION

v12 is complete when all of the following are simultaneously true:

The 20 real-world tests all pass.
The 8 vulnerability remediations are implemented and tested.
All 12 phases are complete (each phase's completion gate is met).
The Lead Generation Benchmark is published with honest comparison to Claude.
The HumanEval algorithmic subset benchmark is published.
The Observatory is live at a public URL.
`pip install living-objects` works.
The arXiv paper has been submitted.
The Autonomous Execution Loop has run for 72 hours unattended.
The Federation Registry has at least 2 entries.

When all ten conditions are simultaneously true, the system has achieved
its goal: a real-world autonomous program synthesis engine that competes
with Claude and Codex in the specific domains where its architectural
advantages apply, with honest published benchmarks that specify exactly
where it wins, where it loses, and why.

That is what v12 builds.
