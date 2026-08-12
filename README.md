# Living Objects

> **What becomes possible when software objects can think?**

[![CI](https://github.com/rajdeep09-dev/living-objects021/actions/workflows/ci.yml/badge.svg)](https://github.com/rajdeep09-dev/living-objects021/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A research project exploring a new programming paradigm where software objects are persistent, intelligent entities capable of reasoning, acting, remembering, experimenting, learning, and evolving under explicit constraints.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run the combined prototype (best of Kimi + Mimo)
cd prototypes/combined/p1_continuity
python3 -m pytest test_living_object.py -v

# Run all tests
python3 -m pytest tests/ -v
```

## The Thesis

Current software has two models:

| Model | What it does | What it lacks |
|-------|-------------|---------------|
| **Traditional OOP** | Objects have data and methods | No intelligence, no learning |
| **AI Agents** | LLM orchestrates tools from above | Ephemeral, no persistence, no relationships |

**Living Objects proposes a third model:** Intelligence is a native property of persistent software objects.

```
Traditional:    Application → Agent → LLM → Tools
Living Objects: Intelligent Object → state + memory + reasoning + actions + relationships
```

## Architecture

```
┌─────────────────────────────────────────────┐
│ LIVING OBJECT                               │
├─────────────────────────────────────────────┤
│ Identity    UUID + SHA256 signature         │
│ State       Versioned, event-sourced        │
│ Memory      Episodic / Semantic / Procedural│
│ Surprise    Adaptive threshold              │
│ Dormancy    Auto-sleep, wake-on-stimulus    │
│ Methods     Deterministic + Intelligent     │
│ Comms       Capability-based relationships  │
├─────────────────────────────────────────────┤
│ EventStore  SQLite, WAL, connection pool    │
│ CapabilityRegistry                          │
│ ReasoningEngine (pluggable)                 │
└─────────────────────────────────────────────┘
```

## Key Mechanisms

### Surprise-Driven Cognition
Objects compute surprise (deviation from expected state). Only reason when surprised. Adaptive threshold adjusts based on history.

### Sparse Cognition
Most objects are dormant at any time. **10x objects → 8.8x tokens.** Cost scales sub-linearly.

### Peer-to-Peer Emergence
Two objects with different knowledge collaborate through capability-based relationships. No central orchestrator required.

### Intelligent Method Routing
AST parser detects method body: `...` → LLM-driven, normal code → deterministic. Both coexist in the same object.

## Project Structure

```
living-objects021/
├── core/                       ← Installable package
│   ├── living_object.py        ← LivingObject base class
│   ├── event_store.py          ← SQLite event sourcing
│   └── reasoning.py            ← Pluggable reasoning engine
├── memory/manager.py           ← Hierarchical memory
├── security/capability.py      ← Capability-based security
├── prototypes/
│   ├── kimi/p1_continuity/     ← Kimi's version (5/6 tests)
│   ├── mimo/p1_continuity/     ← Mimo's version (8/8 tests)
│   └── combined/p1_continuity/ ← Best of both (8/8 tests)
├── research/                   ← 21 research documents
├── docs/                       ← Architecture + paradigm
├── examples/                   ← Working demos
├── tests/                      ← Pytest suite
├── pyproject.toml              ← pip install -e .
├── README.md                   ← You are here
├── CONTRIBUTING.md             ← How to contribute
├── LICENSE                     ← MIT
└── .github/workflows/ci.yml   ← CI/CD
```

## Prototype Status

| Version | Tests | Status |
|---------|-------|--------|
| **Kimi** | 5/6 | 1 known bug (test_event_audit_trail) |
| **Mimo** | 8/8 | ✅ Fixed Kimi's bug + added dormancy + communication |
| **Combined** | 8/8 | ✅ Best of both |

## Research Findings

| Finding | Status |
|---------|--------|
| Persistent objects survive restart | ✅ Proven |
| Sub-linear scaling (dormancy) | ✅ Confirmed |
| Peer-to-peer emergence | ✅ Demonstrated |
| Schema-driven generation | ⏳ Phase 3 |
| Object graph self-coordination | ⏳ Phase 4 |

**Probability of paradigm shift:** 15%
**Probability of valuable negative results:** 85%

## Contributing

This repo uses a **three-model collaboration** structure:

- **Kimi** — Research and foundation building
- **Mimo** — Improvement, testing, and code quality
- **Combined** — Best of both, merged

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

## North Star

> What becomes possible when software objects can think?
