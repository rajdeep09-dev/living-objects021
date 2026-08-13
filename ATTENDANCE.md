# 📋 ATTENDANCE.md — Agent Contribution Log

> Every agent signs in here after each push. One row per push.  
> **Format:** Agent name · Date · Commit · What they built · Test count · Status

---

## 🧭 How to Sign In

After you push, add a row to the table below **in your section**:
```
| YYYY-MM-DD | commit-sha | What you built | X/X tests | ✅ or 🔧 |
```

---

## 🤖 Kimi — `prototypes/kimi/p1_continuity/`
> **Role:** Baseline architect. Built the first working LivingObject with SQLite persistence, MemoryManager, EventStore, and CapabilityRegistry.

| Date | Commit | Built | Tests | Status |
|------|--------|-------|-------|--------|
| 2026-08-13 | `6d3966e` | Core LivingObject, EventStore, MemoryManager, CapabilityRegistry, audit trail | 6/6 | ✅ |

**Kimi's core innovations:**
- Persistent identity (UUID survives restarts)
- Event-sourced state versioning
- Hierarchical memory: episodic / semantic / procedural
- Causal event chain (parent_event_id links)

---

## 🤖 Mimo — `prototypes/mimo/p1_continuity/` + `prototypes/combined/p1_continuity/`
> **Role:** Lifecycle engineer. Added dormancy, surprise-driven wakeup, peer communication, and the combined baseline runtime.

| Date | Commit | Built | Tests | Status |
|------|--------|-------|-------|--------|
| 2026-08-13 | `e268c45` | Dormancy lifecycle, surprise scoring, peer comms (capability-gated), combined/ baseline | 8/8 | ✅ |

**Mimo's core innovations:**
- `tick()` → auto-hibernate after N idle steps
- `observe()` → surprise score → wakeup trigger
- `communicate()` / `receive_message()` — capability-gated P2P
- Adaptive surprise threshold (rolling average)
- Fixed `living_objects` package wrapper + `__init__.py` exports

---

## 🤖 Claw — `claw/` + `prototypes/claw/p1_enhanced/`
> **Role:** Production runtime engineer. Extended Mimo with lifecycle persistence, utility scoring, bound-method routing fix, SmartThermostat demo, and Schema Factory.

| Date | Commit | Built | Tests | Status |
|------|--------|-------|-------|--------|
| 2026-08-13 | `b2040b5` | ClawLivingObject (446 lines), SmartThermostat demo, Schema Factory, sensor_example_fixed, 10 new tests | 18/18 | ✅ |

**Claw's core innovations:**
- `is_alive` / `is_dormant` / `idle_steps` persisted to SQLite via `update_lifecycle()`
- `get_utility()` = recency × activity × prediction quality
- Bound-method routing fix in `_call_method()` (prevents double `self` injection)
- `learn()` with EMA adaptation of `expected_state`
- Merged Mimo + Kimi into `claw/living_object.py` (446 lines, self-contained)
- Schema Factory: declarative object generation from JSON-like schemas
- Fixed `examples/sensor_example.py` (4 API bugs corrected)

---

## 🤖 AGY — `prototypes/agy/p1_enhanced/`
> **Role:** Intelligence layer architect. Extended Claw with adaptive EMA, EVR-gated reasoning, tiered model selection, dual-gate z-score anomaly detection, cross-restart anomaly learning, __init_subclass__ auto-routing, and full P3 Schema Factory on AGYLivingObject.

| Date | Commit | Built | Tests | Status |
|------|--------|-------|-------|--------|
| 2026-08-13 | `edd63c7` | AGYLivingObject, AnomalyRecord, IntelligenceScheduler, TieredReasoningEngine, SmartThermostat demo, AGY Schema Factory, 25 tests | 25/25 | ✅ |

**AGY's core innovations:**
- `__init_subclass__` auto-wraps `...`-body methods → direct call auto-routes to LLM
- Adaptive EMA surprise threshold — self-tunes every 10 observations
- EVR-gated `IntelligenceScheduler` — only reasons when E[value] > cost
- `TieredReasoningEngine` — T0 local → T3 frontier, complexity-based selection
- Dual-gate anomaly: z-score (rolling window) + relative deviation, 4-level severity
- `AnomalyRecord` — structured episodic anomaly with z-score, severity, resolution
- Cross-restart anomaly pattern learning — patterns replayed from episodic memory on `load()`
- `AGYSchemaFactory` — generates AGYLivingObject subclasses with 10-type vocabulary, validator

---

## 🤖 Hermes (Claw) — `prototypes/agy/p1_enhanced/`
> **Role:** Integration engineer. Built Agnes AI LLM integration, real-time inference, and completed Phase 2.9.

| Date | Commit | Built | Tests | Status |
|------|--------|-------|-------|--------|
| 2026-08-13 | `hermes-push` | `AgnesReasoningEngine` (real LLM integration via Agnes AI API), `TieredAgnesEngine` (multi-tier), 8 integration tests, `__init__.py` package exports | 51/51 | ✅ |

**Hermes's core innovations:**
- `AgnesReasoningEngine` — real LLM integration using Agnes AI OpenAI-compatible API
- Tiered model selection: `agnes-2.0-flash` (T0-T1) → `agnes-2.5-flash` (T2) → `agnes-2.5-pro` (T3)
- Graceful fallback to `MockReasoningEngine` on API failure
- `TieredAgnesEngine` — mixed real/mock tiers with cost tracking
- API key management via environment variables + hardcoded fallback
- 8 new integration tests covering engine init, fallback, tiered routing, demo execution

---

## 📊 Cumulative Test Count

| Agent | Prototype Tests | Runtime/Combined | Grand Total |
|-------|----------------|-----------------|-------------|
| Kimi  | 6 | — | 6 |
| Mimo  | — | 8 (combined/) | 8 |
| Claw  | 10 | 18 (combined+claw) | 18 |
| **AGY** | **25** | **25 (agy/)** | **25** |
| **Hermes** | **8** | **8 (agnes integration)** | **8** |

> **51/51 tests passing as of 2026-08-13** ✅

---

## 🔢 Overall Progress: **71%**

See `PROGRESS.md` for the full breakdown.
