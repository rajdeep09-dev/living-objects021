---
name: living-objects-paradigm
description: "Living Objects 021 project: persistent intelligent objects, multi-agent workflow, tests, pitfalls."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [living-objects, agents, persistent-objects, ai, research, multi-agent]
references:
  - references/eventstore-pytest-caching-bug.md
  - references/agy-v2-features.md
---

# Living Objects 021 — Project Guide

## What It Is

A research project exploring a new programming paradigm where software objects are **persistent, intelligent entities** capable of reasoning, acting, remembering, experimenting, learning, and evolving.

**Repo:** `/opt/data/living-objects021`
**GitHub:** https://github.com/rajdeep09-dev/living-objects021

## Core Thesis

> What becomes possible when software objects can think?

Traditional: App → Agent → LLM → Tools
Living Objects: Intelligent Object → state + memory + reasoning + actions + relationships

Objects are like cells, not data structures.

---

## Project Structure

```
living-objects021/
├── living_objects/              ← Core package (import from here)
│   ├── core/
│   │   ├── living_object.py    ← Base LivingObject class
│   │   ├── event_store.py      ← SQLite event sourcing
│   │   └── reasoning.py        ← ReasoningEngine + MockReasoningEngine
│   ├── memory/
│   │   └→ manager.py          ← Episodic / semantic / procedural memory
│   └── security/
│       └── capability.py       ← CapabilityRegistry
│
├── claw/                        ← Claw runtime (merged Kimi+Mimo+Claw)
│   ├── living_object.py        ← ClawLivingObject
│   ├── schema_factory.py       ← P3 Schema Factory
│   └── demo_smart_thermostat.py
│
├── prototypes/
│   ├── combined/p1_continuity/ ← Merged baseline (8 tests) ← START HERE
│   ├── claw/p1_enhanced/       ← Claw prototype (10 tests)
│   ├── agy/p1_enhanced/        ← AGY prototype (42 tests) ← MOST FEATURES
│   ├── kimi/p1_continuity/     ← Kimi baseline (6 tests)
│   └── mimo/p1_continuity/     ← Mimo additions
│
├── living_mesh/                 ← AGY's flagship: Autonomous OS (9 tests)
│   ├── mesh.py                  ← LivingMesh coordinator
│   ├── chaos.py                 ← Chaos/fault injection engine
│   ├── cli.py                   ← Interactive terminal mission control
│   ├── demo.py                  ← 7-scene cinematic demo
│   ├── server.py                ← HTTP API server (port 8080)
│   ├── nodes/                   ← 5 node types
│   ├── web/                     ← Web UI (HTML/CSS/JS)
│   └── tests/                   ← 9 tests
│
├── autonomous_sre/              ← Production SRE demo
│   ├── sre_system.py            ← Self-healing server cluster
│   └── test_sre.py              ← Tests
│
├── examples/                    ← Fixed sensor example
├── research/                    ← 22 research docs
├── ATTENDANCE.md                ← Agent contribution log
├── PROGRESS.md                  ← Full progress checklist (100%)
└── INSTRUCTIONS.md              ← Usage guide
```

---

## Running Tests

```bash
cd /opt/data/living-objects021

# All 85 tests
python3 -m pytest \
  prototypes/combined/p1_continuity/test_living_object.py \
  prototypes/claw/p1_enhanced/test_claw_enhanced.py \
  prototypes/agy/p1_enhanced/test_agy_enhanced.py \
  prototypes/agy/p1_enhanced/test_agnes_integration.py \
  prototypes/agy/p1_enhanced/test_advanced_schema.py \
  prototypes/agy/p1_enhanced/test_ecology_economics.py \
  prototypes/kimi/p1_continuity/test_living_object.py \
  prototypes/mimo/p1_continuity/test_living_object.py \
  living_mesh/tests/test_living_mesh.py \
  -v --tb=short

# Individual demos
PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH python3 prototypes/agy/p1_enhanced/demo_what_becomes_possible.py
PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH python3 autonomous_sre/sre_system.py
PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH python3 -m living_mesh.demo
```

---

## Key Classes

| Class | Location | What It Does |
|-------|----------|-------------|
| `ClawLivingObject` | `claw/living_object.py` | Base runtime: persistence, memory, dormancy, utility |
| `AGYLivingObject` | `prototypes/agy/p1_enhanced/agy_living_object.py` | Extends Claw: EMA, EVR, z-score, auto-routing, schema factory |
| `EventStore` | `living_objects/core/event_store.py` | SQLite event sourcing with snapshot support |
| `MemoryManager` | `living_objects/memory/manager.py` | 4-tier memory: episodic, semantic, procedural, relational |
| `CapabilityRegistry` | `living_objects/security/capability.py` | Permission model for object communication |
| `TieredReasoningEngine` | `prototypes/agy/p1_enhanced/agy_living_object.py` | T0=mock → T3=agnes-2.5-pro, auto-selects by complexity |
| `AgnesReasoningEngine` | `prototypes/agy/p1_enhanced/agnes_reasoning_engine.py` | Real LLM via Agnes AI API with fallback |
| `AGYSchemaFactory` | `prototypes/agy/p1_enhanced/agy_schema_factory.py` | Declarative object generation from schemas |
| `LivingMesh` | `living_mesh/mesh.py` | Autonomous OS coordinator with 5 node types |

---

## Agent Collaboration Workflow

5 agents contributed: Kimi → Mimo → Claw → AGY → Hermes

**Rules:**
1. Each agent's work lives in `prototypes/<agent_name>/p1_enhanced/`
2. Always `git pull --rebase origin master` before pushing
3. Update `ATTENDANCE.md` and `PROGRESS.md` after each push
4. Your prototype must not break existing tests
5. Build on top of previous layers — AGY extends Claw, Claw extends Mimo/Kimi

**Sign-in format:**
```markdown
| YYYY-MM-DD | commit-sha | What you built | X/X tests | ✅ or 🔧 |
```

---

## Common Pitfalls

### 🐛 EventStore pytest caching bug
When running tests via pytest, `EventStore` sometimes lacks `update_lifecycle` due to stale imports.

**Symptoms:** `AttributeError: 'EventStore' object has no attribute 'update_lifecycle'`

**Workarounds:**
1. Clear cache: `rm -rf .pytest_cache && find . -name '__pycache__' -exec rm -rf {} +`
2. Use `PYTHONPATH` explicitly: `PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH python3 ...`
3. Import directly: `from living_objects.core.event_store import EventStore` (not `from living_objects import EventStore`)
4. Reinstall: `pip install -e ".[dev]" --force-reinstall --no-deps`

### 🐛 Test import paths
When creating new test files that import from `prototypes.agy`, always add:
```python
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
```

### 🐛 Bound method double-self
When calling `_call_method(obj.method)`, if method is already bound, don't pass `self` again:
```python
if hasattr(method, '__self__'):
    result = method(*args, **kwargs)
else:
    result = method(self, *args, **kwargs)
```

---

## Progress Status

- **Overall:** 100% (52/52 checklist items)
- **Tests:** 85/85 passing
- **Agents:** 5 (Kimi, Mimo, Claw, AGY, Hermes)
- **Code:** 12,800+ lines across 40+ Python files

---

## Economic Value Proposition

For demos and pitches, use these numbers:
- Downtime cost: $300K/hour (mid-size tech)
- MTTR improvement: 900x faster (45min → 30sec)
- Annual savings per engineer: $350K+
- On-call burnout reduction: 80%
- Savings per incident: $287,500

---

## See Also

- `references/eventstore-pytest-caching-bug.md` — Pytest module caching issue with EventStore
- `references/agy-v2-features.md` — AGY v2 feature list and economic impact numbers
