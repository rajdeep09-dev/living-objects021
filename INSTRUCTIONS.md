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
│       ├── agy_living_object.py
│       ├── agy_schema_factory.py
│       ├── agy_smart_thermostat.py
│       ├── agnes_reasoning_engine.py  ← 🧠 Real LLM (Agnes AI)
│       └── test_agnes_integration.py  ← 8 new LLM integration tests
│
├── examples/
│   ├── sensor_example.py       ← Original (broken, for reference)
│   └── sensor_example_fixed.py ← Fixed version
│
├── research/                    ← 22 research docs (read before building)
├── ATTENDANCE.md                ← Agent sign-in log ← UPDATE THIS after your push
├── PROGRESS.md                  ← Full progress checklist (71% done)
└── INSTRUCTIONS.md              ← This file
```

---

## ⚡ Quick Start (5 minutes)

### 1. Clone & Install
```bash
git clone https://github.com/rajdeep09-dev/living-objects021.git
cd living-objects021
pip install -e "."
pip install pytest requests
```

### 2. Run All Tests
```bash
python -m pytest prototypes/combined/p1_continuity/test_living_object.py \
                 prototypes/claw/p1_enhanced/test_claw_enhanced.py \
                 prototypes/agy/p1_enhanced/test_agy_enhanced.py \
                 prototypes/agy/p1_enhanced/test_agnes_integration.py -v
# Expected: 51 passed
```

### 3. Run a Demo
```bash
# SmartThermostat: cross-restart anomaly learning
python -m prototypes.agy.p1_enhanced.agy_smart_thermostat

# Schema Factory: generate Customer, Order, SupportAgent from schema
python -m prototypes.agy.p1_enhanced.agy_schema_factory

# Agnes AI: real LLM integration test
python -m prototypes.agy.p1_enhanced.agnes_reasoning_engine

# Claw thermostat (simpler)
python -m claw.demo_smart_thermostat
```

### 4. Set up Agnes AI (Real LLM)
```bash
export AGNES_API_KEY="sk-your-key-here"
python -m prototypes.agy.p1_enhanced.agnes_reasoning_engine
```

---

## 🧱 Which Runtime to Use?

| Use case | Import from |
|----------|-------------|
| Simple baseline (just persistence + memory) | `living_objects` |
| Dormancy + peer comms + utility | `claw.living_object.ClawLivingObject` |
| **Everything** (EMA, EVR, z-score, auto-routing, schema factory) | `prototypes.agy.p1_enhanced.agy_living_object.AGYLivingObject` |
| **Real LLM** (Agnes AI integration) | `prototypes.agy.p1_enhanced.agnes_reasoning_engine.AgnesReasoningEngine` |

**Recommendation: use `AGYLivingObject` for new work** — it inherits everything from Claw and adds all AGY features on top. Swap `MockReasoningEngine` for `AgnesReasoningEngine` to get real intelligence.

---

## 🛠️ Creating Your Own Living Object

### Option A — Subclass directly
```python
from prototypes.agy.p1_enhanced.agy_living_object import AGYLivingObject
from prototypes.agy.p1_enhanced.agnes_reasoning_engine import AgnesReasoningEngine
from living_objects import EventStore, CapabilityRegistry

class MyRobot(AGYLivingObject):
    def move(self, direction: str) -> str:
        pos = self.get_state("position", {"x": 0, "y": 0})
        pos["x"] += 1 if direction == "right" else -1
        self.set_state("position", pos)
        return f"Moved {direction} to {pos}"

    def plan_route(self, destination: str) -> str:
        """Plan the optimal route to the destination."""
        ...  # ← auto-routed to Agnes AI LLM!

store = EventStore("robots.db")
engine = AgnesReasoningEngine()  # ← real LLM!

robot = MyRobot.create(store, CapabilityRegistry(), engine, name="R2D2",
                       initial_state={"position": {"x": 0, "y": 0}})
robot.move("right")
plan = robot.plan_route("charging station")  # ← real LLM response!
robot.save()

# Later, in a new process:
robot2 = MyRobot.load(robot.object_id, store, CapabilityRegistry(), engine)
print(robot2.get_state("position"))  # {"x": 1, "y": 0} — survived restart!
```

### Option B — Schema Factory (no Python class needed)
```python
from prototypes.agy.p1_enhanced.agy_schema_factory import (
    AGYSchemaFactory, ObjectSchema, PropertyDef, MethodDef
)
from prototypes.agy.p1_enhanced.agnes_reasoning_engine import TieredAgnesEngine
from living_objects import EventStore, CapabilityRegistry

factory = AGYSchemaFactory()
engine = TieredAgnesEngine()  # ← tiered real LLM!

RobotClass = factory.create_class(ObjectSchema(
    type_name="robot",
    description="An autonomous robot.",
    properties=[
        PropertyDef("position_x", "int", "X coordinate", default=0),
        PropertyDef("mode", "enum", "Operating mode",
                    allowed_values=["idle", "patrol", "charging"], default="idle"),
    ],
    goals=["complete_patrol"],
    methods=[
        MethodDef("plan_route", "string",
                  "Plan optimal patrol route given current position and goals in memory."),
    ],
))

store = EventStore("robots.db")
robot = RobotClass.create(store, CapabilityRegistry(), engine, name="PatrolBot-1")
status = robot.plan_route("charging station")  # ← real LLM!
robot.save()
```

---

## 🔑 Key Concepts

### Intelligent vs Deterministic Methods
```python
# Intelligent — body is `...` → routed to Agnes AI automatically (AGY __init_subclass__)
def diagnose(self, symptom: str) -> str:
    """Diagnose the symptom using memory and state context."""
    ...

# Deterministic — normal Python, zero LLM calls
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

### Real LLM Integration
```python
from prototypes.agy.p1_enhanced.agnes_reasoning_engine import AgnesReasoningEngine

# Set up with Agnes AI
engine = AgnesReasoningEngine(model="agnes-2.0-flash")

# Or use tiered selection
from prototypes.agy.p1_enhanced.agnes_reasoning_engine import TieredAgnesEngine
tiered = TieredAgnesEngine()  # T0=mock, T1=agnes-2.0-flash, T2=agnes-2.5-flash, T3=agnes-2.5-pro
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
8. **No real API keys in code** — use `MockReasoningEngine()` in tests. Use `AgnesReasoningEngine()` in demos.

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
| Agnes API timeout | API key invalid or network issue | Falls back to MockReasoningEngine automatically |

---

*Last updated: 2026-08-13 by Hermes (Claw) — Agnes AI integration*
