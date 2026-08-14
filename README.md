# Living Objects

> **AI agents that remember what worked, pass it to their successors, and improve as a population.**

[![CI](https://github.com/rajdeep09-dev/living-objects021/actions/workflows/ci.yml/badge.svg)](https://github.com/rajdeep09-dev/living-objects021/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-101%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Living Objects is an open research and engineering platform for **persistent, evolving software organisms**. The idea is simple:

1. An organism tries to solve a task.
2. It learns a useful strategy.
3. The strategy is saved as reusable knowledge.
4. The organism creates a child that inherits the strategy.
5. The child tries new variations.
6. The best discoveries become shared culture for later generations.

This is not a claim that the software is conscious or biologically alive. “Living” means that each object has a **lifecycle, memory, behavior, lineage, and ability to change**.

## The problem with starting every task from zero

Most AI workflows look roughly like this:

```text
User request → prompt → model → tool calls → answer
```

The workflow can be very powerful, but repeated work often repeats repeated context. A model may need to read the same files, rediscover the same workflow, and receive the same instructions again. If the task is run thousands of times, the repeated context can become expensive in tokens, latency, and infrastructure.

Living Objects changes the loop:

```text
First attempt → learned strategy → compact memory → cheap reuse
                                      ↓
                               improved descendants
```

The goal is not to eliminate model calls. The goal is to use a model for **discovery, uncertainty, and difficult cases**, then reuse verified strategies as ordinary executable behavior when possible.

## Explain it like I am a beginner

Imagine a restaurant with a team of cooks.

The first cook experiments and discovers that one recipe produces better results. The cook writes down the recipe. The next cook receives it on their first day, so they do not need to rediscover it. That cook improves the recipe and writes down the new version. Even when the first cook leaves, the recipe remains in the kitchen.

In Living Objects:

| Restaurant idea | Living Objects idea |
|---|---|
| Cook | Organism |
| Recipe | Learned strategy or behavior |
| New cook | Offspring |
| Recipe book | Shared memome, or cultural archive |
| Recipe improvement | Mutation and recombination |
| Taste test | Fitness and reliability evaluation |
| New recipe category | Novelty |

The important difference is that knowledge is not trapped inside one chat session. It becomes **portable, testable, inheritable software state**.

## What is already working

The repository contains a runnable proof of the core mechanism and a production-oriented control plane.

| Capability | What it means in plain English | Implementation |
|---|---|---|
| Lamarckian inheritance | A parent learns during life and passes the learned behavior to a child. | `evolution/lamarckian.py` |
| Persistent culture | A strategy survives after its original creator dies. | `evolution/cumulative.py` |
| Meta-evolution | The population can change its own mutation and exploration settings. | `evolution/self_improving.py` |
| Novelty | New behavior is measured instead of rewarding only one fixed answer. | `evolution/lamarckian.py` and `evolution/scalable.py` |
| Multiple species | Producers create knowledge, consumers use it, and decomposers archive retired knowledge. | `evolution/multi_species.py` |
| Large populations | Batch evolution, memory-mapped state, and sharded memomes are available for scale testing. | `evolution/scalable.py` |
| API and realtime stream | Operators can create organisms, inspect archives, read metrics, and watch evolution events. | `production/api/` |
| Monitoring | Prometheus metrics, Grafana dashboard configuration, and alert rules are included. | `production/monitoring/` |
| Deployment | Docker, Compose, Kubernetes, and Helm artifacts are included. | `Dockerfile`, `docker-compose.yml`, `production/k8s/`, `production/helm/` |
| Control surface | A browser dashboard shows population state, fitness, culture, novelty, species, and live events. | `web/` |

The core proof suite demonstrates learning, inheritance, cultural persistence, changing mutation rates, novelty growth, safe behavior replacement, scaling contracts, and multi-species survival. Run the tests yourself instead of trusting the marketing:

```bash
pip install -e ".[production,test]"
python3 -m pytest -q
```

## BEAST v2: ten phases of cumulative software evolution

BEAST v2 adds a second layer above individual Lamarckian organisms: the **rules, language, culture, defenses, goals, tools, and energy economics of the population can all be inspected and evolved**. Every phase has a named Python module and runnable proof coverage.

| Phase | Beginner translation | Module |
|---|---|---|
| Evolving constitutions | The population can change its own rulebook. | `evolution/constitution.py` |
| Morphogenetic code growth | Organisms grow new Python modules from templates. | `evolution/morphogenome.py` |
| Red-team defense | Attackers try to break strategies; defenses adapt. | `evolution/red_team.py` |
| Goal synthesis | Organisms discover intrinsic value from environmental observations. | `evolution/goal_synthesis.py` |
| Federated memome | Independent nodes gossip strategies and preserve lineage. | `evolution/federated_memome.py` |
| Embodied tools | Organisms use restricted tools and record outcomes. | `evolution/embodied.py` |
| Ancestry credit | Descendants can credit ancestor strategies that still matter. | `evolution/ancestry_credit.py` |
| Emergent DSL | Strategies gain a compact, evolving notation. | `evolution/dsl.py` |
| Thermodynamic fitness | Useful work per operation matters, not only raw quality. | `evolution/thermodynamic.py` |
| Observatory v2 | Humans can inspect, edit, attack, and translate the live system. | `web/` and `living-objects-platform-ui/` |

Run the v2 proof suite and regenerate its evidence table:

```bash
python3 -m pytest -q evolution/test_beast_v2.py evolution/test_v2.py production/test_v2_api.py
python3 scripts/run_v2_benchmarks.py --output docs/benchmark-results.md
```

The current deterministic run records seven constitutional fields diverging after 100 generations, an 11× DSL vocabulary expansion after 50 mutations, a 9.4× operation reduction in the thermodynamic harness, and adaptive immune strength under 10-prey/3-attacker pressure. These are **mechanism benchmarks**, not universal claims about intelligence or production throughput. See [docs/v2-architecture.md](docs/v2-architecture.md), [docs/api-v2-reference.md](docs/api-v2-reference.md), [docs/benchmark-results.md](docs/benchmark-results.md), and [research/dsl-emergence-notes.md](research/dsl-emergence-notes.md).

## The five core ideas

### 1. Learning becomes inheritable

```python
parent.learn("bridge", strategy_code)
child = parent.reproduce()

assert child.has_behavior("bridge")
```

The child did not discover the strategy by luck. The parent learned it, and the runtime deliberately transferred it.

### 2. The rules of evolution can evolve

The genome includes values such as `mutation_rate`, `inheritance_rate`, and `novelty_bonus`. A child may inherit these values and receive small changes. This lets one lineage explore aggressively while another lineage preserves proven behavior.

### 3. Culture survives individual lifetimes

The memome is a shared archive. Organisms publish successful behaviors into it. A later organism can retrieve the behavior even after the original organism has been deleted or its process has stopped.

### 4. New behavior matters

If the system only rewards one fixed score, it may find one narrow trick and stop exploring. Living Objects tracks behavioral descriptors and gives novelty a measurable place in evaluation. This is inspired by novelty-search research, which studies exploration beyond a single objective.[1]

### 5. Self-modification is possible, but guarded

An organism can store a behavior as code, compile it, and route future calls through it. If compilation or execution fails, the runtime falls back to the base behavior. In a real deployment, generated code must run inside a stronger sandbox with restricted filesystem, network, and credential access.

## Why this is different from today’s AI agents

Today’s coding and assistant tools are valuable. Living Objects is not pretending that one project replaces every existing agent. The difference is the **unit of progress**.

| Tool category | Main unit of work | Typical strength | Living Objects difference |
|---|---|---|---|
| Personal agents such as [Hermes](https://hermes-agent.nousresearch.com/) | A long-lived assistant with tools and memory | Personal automation and tool use | We make the unit a population of descendants whose learned behaviors can be inherited. |
| Coding agents such as [OpenAI Codex](https://openai.com/codex/) | A coding task, repository, or engineering session | Writing, reviewing, and changing software | We are building the evolutionary memory layer that can preserve strategies between tasks and lifetimes. |
| Interactive coding partners such as [Claude Code](https://www.anthropic.com/claude-code) | A developer-agent loop inside a codebase | Fast interactive engineering | We optimize for repeated workflows that improve across generations, not only the current conversation. |
| Living Objects | A lineage and population | Cumulative learning, cultural reuse, and adaptive exploration | The organism inherits behavior, the memome survives the organism, and the population changes its search strategy. |

The strongest future workflow may combine them:

```text
Codex / Claude Code / Hermes discover a strategy
                    ↓
        Living Objects tests and stores it
                    ↓
        descendants reuse and improve it
                    ↓
          humans approve production changes
```

So the message is not “throw away every current agent.” The message is: **give agents a durable evolutionary memory layer instead of making every task start from a blank page.**

## How this can reduce token and infrastructure cost

Tokens are often spent on context, explanations, repeated instructions, and rediscovery. Living Objects can reduce that repetition by converting a proven solution into a compact strategy that can be called directly.

| Repeated workflow without cultural memory | With Living Objects |
|---|---|
| Send the full task history again. | Send a strategy identifier and the current inputs. |
| Ask the model to rediscover the same procedure. | Reuse the previously verified procedure. |
| Pay model cost for every routine case. | Reserve model calls for uncertainty, novelty, or failure recovery. |
| Keep knowledge in a prompt or chat transcript. | Store versioned behavior, lineage, fitness, and provenance. |

This is a **cost-efficiency thesis, not a guaranteed percentage**. Real savings depend on task repetition, model price, strategy reliability, storage, evaluation, and the cost of failures. The repository includes an EVR benchmark reporting **84.6% compute savings in that benchmark**, but that result should not be presented as a universal token-saving guarantee. Run your own workload benchmark before making a business claim.

The economic idea is simple:

```text
Pay a larger discovery cost once
→ verify the result
→ reuse the result many times
→ call the model again only when the situation is new or uncertain
```

## A real-world example

Consider an online store receiving 100,000 delivery-support tickets every month.

The first organisms use a reasoning model to discover which response sequences resolve delayed-shipment cases safely. Successful procedures are stored with evidence: the input pattern, strategy version, result, fitness, safety checks, and lineage.

Later organisms can apply the verified routine directly for ordinary cases. A model is called when the case is unusual, ambiguous, or outside the archive. New strategies are tested in a controlled evaluation arena before they become part of the shared culture.

The same pattern could support infrastructure alerts, warehouse routing, data-cleaning pipelines, compliance triage, game agents, or scientific experiment planning. The value is not that every organism is smarter than a large model. The value is that the whole population can become **less repetitive and more capable over time**.

## Quick start

### Run the Python platform

```bash
git clone https://github.com/rajdeep09-dev/living-objects021.git
cd living-objects021
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[production,test]"
python3 -m pytest -q
```

### Run the evolution demo

```bash
python3 evolution/lamarckian.py
```

### Run the API

```bash
export LIVING_OBJECTS_JWT_SECRET='replace-this-in-production'
export LIVING_OBJECTS_OPERATOR_PASSWORD='replace-this-in-production'
uvicorn production.api.main:app --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API documentation. The API includes organism CRUD, archive queries, metrics, token issuance, and a WebSocket evolution stream.

### Run the platform with Docker

```bash
docker compose up --build
```

For Kubernetes and cloud deployment, read [production/README.md](production/README.md). For the one-million-organism capacity plan, read [docs/scale-to-1m-organisms.md](docs/scale-to-1m-organisms.md).

### Run the browser control surface

```bash
cd web
pnpm install
pnpm build
```

The `web/` directory contains the Signal Loom observatory dashboard. Its local simulation makes the interaction model visible without credentials. Production wiring should connect its controls to the authenticated API and WebSocket endpoint.

## Architecture in one picture

```text
┌──────────────────────┐       ┌─────────────────────────┐
│ Browser control UI   │──────▶│ FastAPI control plane   │
│ web/                 │◀──────│ JWT + WebSocket + /metrics│
└──────────────────────┘       └───────────┬─────────────┘
                                           │
                         ┌─────────────────┼─────────────────┐
                         ▼                 ▼                 ▼
                 ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                 │ Organisms    │  │ Memome shards│  │ Evolution    │
                 │ 10k+ batches │  │ SQLite/PG    │  │ policies     │
                 └──────────────┘  └──────────────┘  └──────────────┘
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                       Redis hot cache            Prometheus/Grafana
```

## What is production-ready and what still needs proof

The repository now contains production-shaped interfaces and deployment artifacts. That does not mean every cloud environment has been load-tested. Before a real customer deployment, operators should run a staging load test, choose managed PostgreSQL and Redis, isolate generated code, configure secret rotation, add backups, and define human approval for self-improving policy changes.

The safest rollout is:

| Stage | Goal |
|---|---|
| Local | Run tests, API, UI, and Docker Compose. |
| Staging | Use managed PostgreSQL and Redis with realistic traffic. |
| Shadow mode | Let organisms make recommendations without changing production systems. |
| Limited production | Allow approved strategies for one narrow workflow with rollback. |
| Expansion | Add more workflows only after reliability, cost, and safety are measured. |

## The future in one sentence

> **Today’s agents answer tasks. Living Objects aims to build populations of agents that remember, inherit, experiment, and become cheaper to run on repeated work.**

That is the bet: not a smarter prompt, but a software ecosystem where useful behavior compounds.

## Documentation

| Document | Purpose |
|---|---|
| [production/README.md](production/README.md) | API, authentication, Docker Compose, Kubernetes, Helm, Redis, and monitoring runbook. |
| [docs/scale-to-1m-organisms.md](docs/scale-to-1m-organisms.md) | Capacity model and staged path to one million organisms. |
| [INSTRUCTIONS.md](INSTRUCTIONS.md) | Guide to creating custom living objects and schemas. |
| [PROGRESS.md](PROGRESS.md) | Earlier continuity, cognition, ecology, economics, and research milestones. |
| [ATTENDANCE.md](ATTENDANCE.md) | Repository contribution record. |
| [research/](research/) | Architecture, implementation, and research notes. |

## License

MIT License. See [LICENSE](LICENSE).

## References

[1]: [Lehman and Stanley, “Novelty Search and the Problem with Objectives”](https://link.springer.com/chapter/10.1007/978-1-4614-1770-5_3)
[2]: [Nous Research, Hermes Agent](https://hermes-agent.nousresearch.com/)
[3]: [OpenAI, Codex](https://openai.com/codex/)
[4]: [Anthropic, Claude Code](https://www.anthropic.com/claude-code)
