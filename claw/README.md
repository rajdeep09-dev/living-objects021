# Claw — Enhanced Living Objects Runtime

## What's Here

**Claw** is the merged, enhanced runtime combining the best of all prototype contributions:
- **Mimo** → dormancy lifecycle, surprise-driven cognition, peer communication
- **Kimi** → event sourcing, audit trail, full persistence
- **Claw** → intelligent method routing, schema factory, SmartThermostat demo

## Files

| File | Description |
|------|-------------|
| `living_object.py` | ClawLivingObject — full runtime with all features |
| `demo_smart_thermostat.py` | P1 Demo — thermostat learning across restarts |
| `schema_factory.py` | P3 Demo — declarative schema → executable objects |
| `sensor_example_fixed.py` | Fixed version of original broken example |
| `__init__.py` | Package exports |

## Quick Start

```bash
# Run the SmartThermostat demo (P1)
python3 claw/demo_smart_thermostat.py

# Run the Schema Factory demo (P3)
python3 claw/schema_factory.py

# Run the fixed sensor example
python3 claw/sensor_example_fixed.py

# Run all tests
python3 -m pytest prototypes/claw/p1_enhanced/test_claw_enhanced.py -v
```

## What ClawLivingObject Adds

1. **Dormancy Lifecycle** — Objects auto-sleep after idle, wake on stimulus
2. **Surprise-Driven Cognition** — Only reason when state deviates from expectations
3. **Peer Communication** — Objects message each other via capability tokens
4. **Intelligent Method Routing** — `...` body → LLM, normal code → deterministic
5. **Full Persistence** — State, memory, and events survive process restart
6. **Utility Scoring** — Objects compute their own value for retirement decisions

## Test Results

```
18/18 tests passing ✅
- 8 combined (original) tests
- 10 claw-enhanced tests
```

## P1 Demo: SmartThermostat

Demonstrates a thermostat that:
1. Records temperature readings
2. Detects anomalies (z-score > 2.0)
3. Uses LLM to diagnose issues
4. Learns strategies from experience (episodic memory)
5. **Survives process restart** — remembers everything
6. Handles new anomalies using past knowledge

## P3 Demo: Schema Factory

Demonstrates declarative object generation:
1. Define objects as JSON/YAML schemas
2. Factory generates LivingObject subclasses with methods
3. Supports deterministic + intelligent methods
4. Establishes relationships, goals, constraints
5. Full persistence across restarts

## Architecture

```
ClawLivingObject
├── Identity: UUID + SHA256 signature
├── State: versioned, event-sourced
├── Memory: episodic / semantic / procedural
├── Surprise: adaptive threshold
├── Dormancy: auto-sleep, wake-on-stimulus
├── Methods: deterministic + intelligent (AST routing)
├── Comms: capability-based relationships
└── Lifecycle: hibernate / wake / retire
```
