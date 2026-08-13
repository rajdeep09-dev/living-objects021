# 📖 INSTRUCTIONS.md — How to Use Living Objects 021

> Quick guide for any agent or developer jumping into this repo.  
> Read this first. Then check `ATTENDANCE.md` to see what each agent has done.

---

## 🗂️ Repo Structure

```
living-objects021/
├── living_objects/              ← Core package (import from here)
│   ├── core/
│   │   ├── living_object.py    ← Base LivingObject class
│   │   ├── event_store.py      ← SQLite event sourcing
│   │   └── reasoning.py        ← ReasoningEngine + MockReasoningEngine
│   ├── memory/
│   │   └── manager.py          ← Episodic / semantic / procedural memory
│   └── security/
│       └── capability.py       ← CapabilityRegistry (grant/check/revoke)
│
├── claw/                        ← Claw runtime (merged Kimi+Mimo+Claw)
│   ├── living_object.py        ← ClawLivingObject (best production runtime)
│   ├── schema_factory.py       ← P3 Schema Factory
│   ├── demo_smart_thermostat.py
│   └── sensor_example_fixed.py
│
├── prototypes/
│   ├── kimi/p1_continuity/     ← Kimi's baseline (6 tests)
│   ├── mimo/p1_continuity/     ← Mimo's additions
│   ├── combined/p1_continuity/ ← Merged baseline (8 tests) ← START HERE
│   ├── claw/p1_enhanced/       ← Claw's prototype (10 tests)
│   └── agy/p1_enhanced/        ← AGY's prototype (25 tests) ← MOST FEATURES
│
├── examples/
│   ├── sensor_example.py       ← Original (broken, for reference)
│   └── sensor_example_fixed.py ← Fixed version
│
├── research/                    ← 22 research docs (read before building)
├── ATTENDANCE.md                ← Agent sign-in log ← UPDATE THIS after your push
├── PROGRESS.md                  ← Full progress checklist (63% done)
└── INSTRUCTIONS.md              ← This file
```

---

## ⚡ Quick Start (5 minutes)

### 1. Clone & Install

```bash
git clone https://github.com/rajdeep09-dev/living-objects021.git
cd living-objects021
pip install -e "."
pip install pytest
```

### 2. Run All Tests

```bash
python -m pytest prototypes/combined/p1_continuity/test_living_object.py \
                 prototypes/claw/p1_enhanced/test_claw_enhanced.py \
                 prototypes/agy/p1_enhanced/test_agy_enhanced.py -v
# Expected: 43 passed
```

### 3. Run a Demo

```bash
# SmartThermostat: cross-restart anomaly learning
python -m prototypes.agy.p1_enhanced.agy_smart_thermostat

# Schema Factory: generate Customer, Order, SupportAgent from schema
python -m prototypes.agy.p1_enhanced.agy_schema_factory

# Claw thermostat (simpler)
python -m claw.demo_smart_thermostat
```

---

## 🧱 Which Runtime to Use?

| Use case | Import from |
|----------|-------------|
| Simple baseline (just persistence + memory) | `living_objects` |
| Dormancy + peer comms + utility | `claw.living_object.ClawLivingObject` |
| **Everything** (EMA, EVR, z-score, auto-routing, schema factory) | `prototypes.agy.p1_enhanced.agy_living_object.AGYLivingObject` |

**Recommendation: use `AGYLivingObject` for new work** — it inherits everything from Claw and adds all AGY features on top.

---

## 🛠️ Creating Your Own Living Object

### Option A — Subclass directly

```python
from prototypes.agy.p1_enhanced.agy_living_object import AGYLivingObject
from living_objects import EventStore, CapabilityRegistry
from living_objects.core.reasoning import MockReasoningEngine

class MyRobot(AGYLivingObject):
    # Deterministic method — pure Python
    def move(self, direction: str) -> str:
        pos = self.get_state("position", {"x": 0, "y": 0})
        pos["x"] += 1 if direction == "right" else -1
        self.set_state("position", pos)
        return f"Moved {direction} to {pos}"

    # Intelligent method — body is ... → auto-routed to LLM
    def plan_route(self, destination: str) -> str:
        """Plan the optimal route to the destination given current position and obstacles in memory."""
        ...  # ← no code needed! AGY routes this to the reasoning engine

store = EventStore("robots.db")
registry = CapabilityRegistry()
engine = MockReasoningEngine()  # swap for real LLM

robot = MyRobot.create(store, registry, engine, name="R2D2",
                       initial_state={"position": {"x": 0, "y": 0}})

robot.move("right")
plan = robot.plan_route("charging station")  # ← direct call, auto-routed!
robot.save()

# Later, in a new process:
robot2 = MyRobot.load(robot.object_id, store, registry, engine)
print(robot2.get_state("position"))  # {"x": 1, "y": 0} — survived restart!
```

### Option B — Schema Factory (no Python class needed)

```python
from prototypes.agy.p1_enhanced.agy_schema_factory import (
    AGYSchemaFactory, ObjectSchema, PropertyDef, MethodDef
)
from living_objects import EventStore, CapabilityRegistry

factory = AGYSchemaFactory()

RobotClass = factory.create_class(ObjectSchema(
    type_name="robot",
    description="An autonomous robot.",
    properties=[
        PropertyDef("position_x", "int",   "X coordinate", default=0),
        PropertyDef("position_y", "int",   "Y coordinate", default=0),
        PropertyDef("mode",       "enum",  "Operating mode",
                    allowed_values=["idle", "patrol", "charging"], default="idle"),
    ],
    goals=["complete_patrol", "maintain_charge"],
    methods=[
        MethodDef("plan_route", "string",
                  "Plan optimal patrol route given current position and goals in memory."),
        MethodDef("report_status", "dict",
                  "Report current position, mode, battery, and last action."),
    ],
))

store = EventStore("robots.db")
robot = RobotClass.create(store, CapabilityRegistry(), MockReasoningEngine(),
                          name="PatrolBot-1")
robot.set_mode("patrol")     # schema-generated setter with enum validation
status = robot.report_status()  # intelligent method, auto-routed
robot.save()
```

---

## 🔑 Key Concepts

### Intelligent vs Deterministic Methods
```python
# Intelligent — body is `...` → routed to LLM automatically (AGY __init_subclass__)
def diagnose(self, symptom: str) -> str:
    """Diagnose the symptom using memory and state context."""
    ...

# Deterministic — normal Python
def record(self, value: float) -> str:
    self.set_state("last", value)
    return f"Recorded {value}"
```

### Anomaly Detection (z-score + severity)
```python
anomaly = obj.detect_anomaly("temperature", observed=38.0, expected=22.0)
if anomaly:
    print(anomaly.severity)    # "high"
    print(anomaly.z_score)     # 3.2
    obj.resolve_anomaly(anomaly.anomaly_id, "Cooling activated")
```

### Cross-Restart Learning
```python
# Session 1: obj detects anomalies → saved to episodic memory
obj.detect_anomaly("cpu", 95.0, expected=40.0)
obj.save()

# Session 2: patterns loaded automatically on .load()
obj2 = MyClass.load(obj.object_id, store, registry, engine)
print(obj2._anomaly_patterns)  # {"cpu": 1} — learned from memory!
```

---

## 🤖 Agent Rules (READ BEFORE PUSHING)

1. **Sign in to `ATTENDANCE.md`** after every push — add a row with your name, commit, what you built, and test count.
2. **Update `PROGRESS.md`** if you complete or add checklist items.
3. **Your prototype lives in `prototypes/<your_name>/p1_enhanced/`** — do not modify other agents' prototypes.
4. **All tests must pass** before pushing: run `pytest` and confirm green.
5. **Build on top of the previous layer** — AGY extends Claw, Claw extends Mimo/Kimi. Don't duplicate.
6. **Write `__init__.py`** files for every new package directory.
7. **DB paths** — use `os.path.dirname(__file__)` for demo databases, not `/tmp/`.
8. **No real API keys in code** — use `MockReasoningEngine()` in tests.

---

## 📚 Research Docs to Read First

Before implementing anything new, read these:

| File | What it covers |
|------|---------------|
| `research/architecture.md` | Overall LivingObject architecture decisions |
| `research/intelligence_scheduler.md` | EVR scheduling theory |
| `research/lifecycle_model.md` | Dormancy / wake / retire lifecycle |
| `research/object_generation.md` | Schema factory theory (P3) |
| `research/object_economics.md` | Utility and budget theory (P5) |
| `research/mathematical_model.md` | Formal math behind surprise/EMA |
| `research/breakthrough_ideas.md` | Wild ideas to explore next |

---

## 🐛 Common Issues & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `unable to open database file` | `/tmp/` doesn't exist on Termux | Use `os.path.dirname(__file__)` for DB path |
| `No module named pytest` | pytest not installed | `pip install pytest` |
| `No module named living_objects` | Package not installed | `pip install -e "."` from repo root |
| `CapabilityRegistry(store)` TypeError | Old API — registry takes no args | Use `CapabilityRegistry()` |
| `summarize()` AttributeError | Old method name | Use `summarize_experiences()` |
| `_call_method` double-self | Passing bound method | Use AGY `__init_subclass__` auto-routing instead |

---

*Last updated: 2026-08-13 by AGY*
