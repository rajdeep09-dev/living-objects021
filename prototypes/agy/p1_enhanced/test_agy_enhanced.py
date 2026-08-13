"""
AGY Enhanced Tests — 25 tests (18 claw-inherited + 7 AGY-specific)

Structure:
  P1 Baseline (from claw)    : create, state, memory, audit, capability      5 tests
  Lifecycle (claw + mimo)    : dormancy, peer comms, intelligent routing      3 tests
  AGY-2 Adaptive EMA         : threshold self-tuning                          1 test
  AGY-3 EVR Scheduler        : reasoning gate                                 1 test
  AGY-4 Tiered Engine        : tier selection, cost tracking                  1 test
  AGY-5 Auto-routing         : __init_subclass__ direct call                  1 test
  AGY-6 Z-score anomaly      : dual-gate, severity, resolution                1 test
  AGY-7 Cross-restart        : anomaly patterns survive restart               1 test
  AGY-8 Schema Factory       : validation, class generation, lifecycle        11 tests
"""
import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, MockReasoningEngine, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject, AnomalyRecord, IntelligenceScheduler, TieredReasoningEngine,
)
from prototypes.agy.p1_enhanced.agy_schema_factory import (
    AGYSchemaFactory, SchemaValidator, SchemaValidationError,
    ObjectSchema, PropertyDef, MethodDef,
    CUSTOMER_SCHEMA, ORDER_SCHEMA, SUPPORT_AGENT_SCHEMA,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rt(tmp_path):
    store = EventStore(str(tmp_path / "agy_test.db"))
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine(mock=MockReasoningEngine())
    yield store, registry, engine


@pytest.fixture
def factory():
    return AGYSchemaFactory()


# ===========================================================================
# P1 BASELINE (Claw-compatible)
# ===========================================================================

def test_create(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="Obj")
    assert obj.object_id is not None
    assert obj.name == "Obj"
    assert obj.is_alive and not obj.is_dormant


def test_state_persistence(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="S",
                                 initial_state={"x": 1, "nested": {"a": [1, 2]}})
    obj.set_state("x", 42)
    obj.set_state("tags", ["alert", "hot"])
    obj.save()
    loaded = AGYLivingObject.load(obj.object_id, store, registry, engine)
    assert loaded.get_state("x") == 42
    assert loaded.get_state("tags") == ["alert", "hot"]
    assert loaded.get_state("nested") == {"a": [1, 2]}


def test_memory_persistence(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="M")
    obj.memory.record_episode("saw spike", "cooled", "temp dropped", "success", "cooling works")
    obj.memory.record_fact("lab insulation poor", 0.9, "observation")
    obj.memory.record_strategy("rapid_cool", "override fan first", 0.88)
    obj.save()
    loaded = AGYLivingObject.load(obj.object_id, store, registry, engine)
    assert len(loaded.memory.recall_episodes()) == 1
    assert len(loaded.memory.recall_facts()) == 1
    assert len(loaded.memory.recall_strategies()) == 1


def test_event_audit_trail(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="A")
    obj.set_state("v", 1)
    obj.save()
    loaded = AGYLivingObject.load(obj.object_id, store, registry, engine)
    types = {e.event_type for e in store.get_events(obj.object_id)}
    assert "created" in types
    assert "state_change" in types
    assert "loaded" in types


def test_capability_registry(rt):
    store, registry, engine = rt
    a = AGYLivingObject.create(store, registry, engine, name="A")
    b = AGYLivingObject.create(store, registry, engine, name="B")
    registry.grant(a.object_id, b.object_id, ["read"])
    assert registry.check(a.object_id, b.object_id, "read")
    assert not registry.check(b.object_id, a.object_id, "read")
    registry.revoke(a.object_id, b.object_id, "read")
    assert not registry.check(a.object_id, b.object_id, "read")


# ===========================================================================
# LIFECYCLE (Claw dormancy + Mimo peer comms)
# ===========================================================================

def test_dormancy_and_wake(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="Sleepy",
                                 initial_state={"val": 0.5})
    obj.expected_state["val"] = 0.5
    for _ in range(8):
        obj.tick()
    assert obj.is_dormant
    result = obj.observe({"val": 0.95})
    assert not obj.is_dormant
    assert result["surprise"] > 0.1


def test_peer_communication(rt):
    store, registry, engine = rt
    a = AGYLivingObject.create(store, registry, engine, name="A")
    b = AGYLivingObject.create(store, registry, engine, name="B")
    # Without capability
    assert not a.communicate(b.object_id, {"msg": "hi"})["success"]
    # With capability
    registry.grant(a.object_id, b.object_id, ["communicate"])
    assert a.communicate(b.object_id, {"msg": "hi"})["success"]
    b.receive_message({"from": a.object_id, "msg": "hi"})
    assert b.idle_steps == 0


def test_intelligent_method_detection(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="Detect")

    class S:
        def ellipsis(self): ...
        def empty_doc(self):
            """Only a docstring."""
        def real(self): return 42

    assert obj._is_intelligent_method(S.ellipsis)
    assert obj._is_intelligent_method(S.empty_doc)
    assert not obj._is_intelligent_method(S.real)


# ===========================================================================
# AGY-2  Adaptive EMA
# ===========================================================================

def test_adaptive_ema(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="EMA",
                                 initial_state={"m": 0.5})
    initial_thr = obj.surprise_threshold
    # Low surprises → threshold decreases
    for _ in range(15):
        obj._update_ema(0.01)
    assert obj.surprise_threshold < initial_thr
    # High surprises → threshold increases
    for _ in range(15):
        obj._update_ema(0.9)
    assert obj.surprise_threshold > 0.08
    assert obj._surprise_ema > 0.3


# ===========================================================================
# AGY-3  EVR Scheduler
# ===========================================================================

def test_evr_scheduler():
    sched = IntelligenceScheduler(base_cost=0.05)
    # Critical always reasons regardless of budget
    ok, evr = sched.should_reason(0.01, anomaly_severity="critical", budget=0.0)
    assert ok and evr == 999.0
    # Dormant + low surprise → no reasoning
    ok2, _ = sched.should_reason(0.01, is_dormant=True, budget=1.0)
    assert not ok2
    # High surprise + high budget → reason
    ok3, evr3 = sched.should_reason(0.9, anomaly_severity="high", budget=1.0)
    assert ok3 and evr3 > 0


# ===========================================================================
# AGY-4  Tiered Engine
# ===========================================================================

def test_tiered_engine():
    engine = TieredReasoningEngine(mock=MockReasoningEngine())
    # Short prompt → tier 0
    r1 = engine.reason("hi", {"return_type": "str"}, {"state": {}})
    assert "tier" in r1 and "result" in r1
    assert r1["tier"] == "local-8b"
    # Long complex prompt → tier 2 or 3
    r2 = engine.reason(
        "x" * 2000, {"return_type": "dict"},
        {"state": {f"k{i}": i for i in range(50)},
         "memory_summary": "x" * 600, "anomaly_count": 10, "budget_remaining": 1.0},
    )
    assert r2["tier"] in ("claude-3-5-sonnet", "o3")
    stats = engine.stats()
    assert stats["total"] == 2
    assert stats["cost_usd"] >= 0


# ===========================================================================
# AGY-5  __init_subclass__ auto-routing
# ===========================================================================

def test_auto_routing(rt):
    """Direct method call routes to LLM without _call_method boilerplate."""
    store, registry, engine = rt

    class Sensor(AGYLivingObject):
        def diagnose(self, symptom: str) -> str:
            """Diagnose the symptom from readings and memory."""
            ...

    s = Sensor.create(store, registry, engine, name="AutoSensor",
                      initial_state={"temp": 22.0})
    # Direct call — no _call_method needed (AGY-5)
    result = s.diagnose("Temperature spike detected")
    events = store.get_events(s.object_id)
    assert any(e.event_type == "reasoning" for e in events)


# ===========================================================================
# AGY-6  Z-score dual-gate anomaly detection
# ===========================================================================

def test_zscore_anomaly(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="Zscore",
                                 initial_state={"t": 22.0})
    # Build z-score window
    for v in [22.1, 21.9, 22.0, 22.2, 21.8, 22.1, 22.0, 22.3, 21.9, 22.1]:
        obj.detect_anomaly("temp", v, expected=22.0)
    # Normal reading → no anomaly
    assert obj.detect_anomaly("temp", 22.1, expected=22.0) is None
    # Spike → detected
    anomaly = obj.detect_anomaly("temp", 38.0, expected=22.0)
    assert anomaly is not None
    assert anomaly.severity in ("high", "critical")
    assert anomaly.z_score > 2.0
    assert anomaly.metric == "temp"
    # Resolution
    assert obj.resolve_anomaly(anomaly.anomaly_id, "Cooling activated")
    assert anomaly.resolved


# ===========================================================================
# AGY-7  Cross-restart anomaly pattern learning
# ===========================================================================

def test_cross_restart_anomaly_learning(rt):
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="Learner",
                                 initial_state={"temp": 22.0})
    # Build window then spike
    for v in [22.1, 21.9, 22.0, 22.2, 21.8, 22.1, 22.0, 22.3, 21.9, 22.1]:
        obj.detect_anomaly("temperature", v, expected=22.0)
    a1 = obj.detect_anomaly("temperature", 35.0, expected=22.0)
    assert a1 is not None
    assert obj._anomaly_patterns["temperature"] == 1
    obj.resolve_anomaly(a1.anomaly_id, "Fan override")
    a2 = obj.detect_anomaly("temperature", 38.0, expected=22.0)
    assert obj._anomaly_patterns["temperature"] == 2
    obj.save()
    oid = obj.object_id

    # Restart — patterns restored from episodic memory
    loaded = AGYLivingObject.load(oid, store, registry, engine)
    assert loaded._anomaly_patterns.get("temperature", 0) >= 2

    # Third spike — recognized as recurrence ≥ 3
    a3 = loaded.detect_anomaly("temperature", 40.0, expected=22.0)
    assert a3 is not None
    assert a3.cause.startswith("Recurrence")
    assert loaded._anomaly_patterns["temperature"] >= 3


# ===========================================================================
# AGY-8  Schema Factory (11 tests)
# ===========================================================================

def test_validator_valid(factory):
    schema = ObjectSchema(
        type_name="sensor", description="A sensor.",
        properties=[PropertyDef("value", "float", "Reading", default=0.0)],
        methods=[MethodDef("diagnose", "string", "Diagnose.")],
    )
    assert SchemaValidator().validate(schema) == []


def test_validator_catches_errors():
    bad = ObjectSchema(
        type_name="BAD NAME", description="", properties=[],
        methods=[MethodDef("m", "string", "", intelligent=True)],
    )
    errors = SchemaValidator().validate(bad)
    assert any("type_name" in e for e in errors)
    assert any("property" in e.lower() for e in errors)
    assert any("description" in e.lower() for e in errors)


def test_factory_raises_on_invalid(factory):
    bad = ObjectSchema(type_name="", description="", properties=[])
    with pytest.raises(SchemaValidationError):
        factory.create_class(bad)


def test_generated_class_has_accessors(factory):
    schema = ObjectSchema(
        type_name="device", description="A device.",
        properties=[
            PropertyDef("serial", "string", "Serial", default=""),
            PropertyDef("active", "bool",   "Active", default=True),
        ],
        methods=[MethodDef("diagnose", "string", "Diagnose the device state.")],
    )
    Cls = factory.create_class(schema)
    assert Cls.__name__ == "Device"
    assert hasattr(Cls, "get_serial") and hasattr(Cls, "set_serial")
    assert hasattr(Cls, "get_active") and hasattr(Cls, "set_active")
    assert hasattr(Cls, "diagnose")
    assert hasattr(Cls, "default_initial_state")


def test_schema_lifecycle(factory, rt):
    store, registry, engine = rt
    schema = ObjectSchema(
        type_name="device", description="A device.",
        properties=[PropertyDef("serial", "string", "Serial", default="")],
        methods=[],
    )
    Cls = factory.create_class(schema)
    obj = Cls.create(store, registry, engine, name="dev",
                     initial_state={"serial": "SN-001"})
    assert obj.get_serial() == "SN-001"
    obj.set_serial("SN-002")
    obj.save()
    loaded = Cls.load(obj.object_id, store, registry, engine)
    assert loaded.get_serial() == "SN-002"


def test_schema_type_validation(factory, rt):
    store, registry, engine = rt
    schema = ObjectSchema(
        type_name="light", description="A light.",
        properties=[
            PropertyDef("colour", "enum", "Colour",
                        allowed_values=["red", "green", "blue"], default="red"),
            PropertyDef("brightness", "float", "0-1",
                        default=0.5, min_value=0.0, max_value=1.0),
        ],
        methods=[],
    )
    Cls = factory.create_class(schema)
    obj = Cls.create(store, registry, engine, name="L")
    obj.set_colour("green")
    assert obj.get_colour() == "green"
    with pytest.raises(ValueError, match="must be one of"):
        obj.set_colour("purple")
    with pytest.raises(ValueError, match=">= 0"):
        obj.set_brightness(-0.1)


def test_deterministic_schema_method(factory, rt):
    store, registry, engine = rt
    Cls = factory.create_class(ORDER_SCHEMA)
    obj = Cls.create(store, registry, engine, name="Ord",
                     initial_state={"order_id": "O-1", "status": "pending",
                                    "quantity": 1, "total_amount": 10.0})
    msg = obj.advance_status()
    assert "confirmed" in msg
    assert obj.get_status() == "confirmed"


def test_intelligent_schema_method_routes(factory, rt):
    store, registry, engine = rt
    Cls = factory.create_class(CUSTOMER_SCHEMA)
    obj = Cls.create(store, registry, engine, name="Bob",
                     initial_state={"name": "Bob", "ltv": 200.0, "segment": "new"})
    obj.record_interaction("First login")
    obj.assess_churn_risk()
    events = store.get_events(obj.object_id)
    assert any(e.event_type == "reasoning" for e in events)


def test_schema_class_caching(factory):
    Cls1 = factory.create_class(CUSTOMER_SCHEMA)
    Cls2 = factory.create_class(CUSTOMER_SCHEMA)
    assert Cls1 is Cls2


def test_schema_anomaly_detection_in_generated_class(factory, rt):
    """Generated class inherits AGY anomaly detection."""
    store, registry, engine = rt
    Cls = factory.create_class(CUSTOMER_SCHEMA)
    obj = Cls.create(store, registry, engine, name="Risky",
                     initial_state={"name": "Risky", "ltv": 1000.0,
                                    "churn_probability": 0.1, "segment": "growth"})
    # Build baseline then spike
    for v in [0.1, 0.09, 0.11, 0.10, 0.12, 0.10, 0.11, 0.09, 0.10, 0.11]:
        obj.detect_anomaly("churn_probability", v, expected=0.1)
    anomaly = obj.detect_anomaly("churn_probability", 0.95, expected=0.1)
    assert anomaly is not None
    assert anomaly.severity in ("high", "critical")


def test_effort_reduction(factory):
    for schema in [CUSTOMER_SCHEMA, ORDER_SCHEMA, SUPPORT_AGENT_SCHEMA]:
        m = factory.measure_effort(schema)
        assert m["reduction_pct"] >= 30.0, (
            f"'{schema.type_name}' only saves {m['reduction_pct']}% — expected ≥ 30%"
        )
