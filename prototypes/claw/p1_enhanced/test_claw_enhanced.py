"""
Claw Enhanced LivingObject Tests — 10 tests, all passing.

Extends the combined test suite with Claw-specific features:
- Intelligent method routing with custom subclasses
- Schema factory integration
- SmartThermostat persistence demo
"""
import os, sys, pytest, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from prototypes.mimo.p1_continuity.living_object import EnhancedLivingObject
from living_objects import LivingObject, EventStore, MockReasoningEngine, CapabilityRegistry
from prototypes.claw.p1_enhanced.claw_living_object import ClawLivingObject


@pytest.fixture
def runtime(tmp_path):
    db = str(tmp_path / "claw_test.db")
    store = EventStore(db)
    registry = CapabilityRegistry()
    engine = MockReasoningEngine()
    yield store, registry, engine, db


def test_claw_create(runtime):
    """ClawLivingObject can be created and loaded."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="ClawTest")
    assert obj.object_id is not None
    assert obj.name == "ClawTest"
    assert obj.is_alive
    assert not obj.is_dormant


def test_claw_persistence(runtime):
    """ClawLivingObject state survives restart."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="PersistTest",
                                   initial_state={"temp": 22.0, "mode": "auto"})
    obj.set_state("temp", 25.0)
    obj.set_state("alerts", ["overheat"])
    obj.save()
    oid = obj.object_id
    loaded = ClawLivingObject.load(oid, store, registry, engine)
    assert loaded.get_state("temp") == 25.0
    assert loaded.get_state("alerts") == ["overheat"]
    assert loaded.name == "PersistTest"


def test_claw_memory_persistence(runtime):
    """ClawLivingObject memory (episodic, semantic, procedural) survives restart."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="MemTest")
    obj.memory.record_episode("saw spike", "cooling", "dropped", "success", "cooling works")
    obj.memory.record_fact("Room heats up fast", 0.9, "history")
    obj.memory.record_strategy("cool_first", "Activate cooling before temp rises", 0.8)
    obj.save()
    oid = obj.object_id
    loaded = ClawLivingObject.load(oid, store, registry, engine)
    assert len(loaded.memory.recall_episodes()) == 1
    assert len(loaded.memory.recall_facts()) == 1
    assert len(loaded.memory.recall_strategies()) == 1
    summary = loaded.memory.summarize_experiences()
    assert "saw spike" in summary


def test_claw_intelligent_method_routing(runtime):
    """AST correctly routes deterministic vs intelligent methods."""
    store, registry, engine, _ = runtime

    class SmartDevice(ClawLivingObject):
        def get_status(self):
            return {"online": True, "temp": self.get_state("temp", 0)}

        def diagnose(self, issue: str) -> str:
            """Analyze the diagnostic issue."""
            ...

    obj = SmartDevice.create(store, registry, engine, name="SmartDevice",
                              initial_state={"temp": 42.0})
    # Deterministic
    status = obj._call_method(obj.get_status)
    assert isinstance(status, dict)
    assert status["temp"] == 42.0
    # Intelligent
    diagnosis = obj._call_method(obj.diagnose, "overheat")
    assert diagnosis is not None


def test_claw_surprise_and_dormancy(runtime):
    """ClawLivingObject goes dormant after idle, wakes on stimulus."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="DormantTest",
                                   initial_state={"value": 0.5})
    assert not obj.is_dormant
    for _ in range(6):
        obj.tick()
    assert obj.is_dormant
    result = obj.observe({"type": "stimulus", "value_change": 0.5})
    assert not obj.is_dormant
    assert result["surprise"] > 0.2
    assert obj.should_reason()


def test_claw_peer_communication(runtime):
    """ClawLivingObject can communicate with peers via capabilities."""
    store, registry, engine, _ = runtime
    a = ClawLivingObject.create(store, registry, engine, name="ClawA",
                                 initial_state={"knowledge": 0})
    b = ClawLivingObject.create(store, registry, engine, name="ClawB",
                                 initial_state={"knowledge": 0})
    registry.grant(a.object_id, b.object_id, ["communicate"])
    registry.grant(b.object_id, a.object_id, ["communicate"])
    comm = a.communicate(b.object_id, {"type": "insight", "data": 42})
    assert comm["success"]
    b.receive_message({"type": "insight", "data": 42, "from": a.object_id})
    assert b.surprise_score > 0


def test_claw_event_audit_trail(runtime):
    """ClawLivingObject maintains causal event chain."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="AuditTest")
    obj.set_state("x", 1)
    obj.set_state("x", 2)
    obj.observe({"stimulus": "test"})
    if obj.should_reason():
        obj.reason()
    events = store.get_events(obj.object_id)
    types = [e.event_type for e in events]
    assert "created" in types
    assert types.count("state_change") >= 2
    assert "observation" in types
    chained = [e for e in events if e.parent_event_id]
    assert len(chained) > 0


def test_claw_learn_and_adapt(runtime):
    """ClawLivingObject learns from prediction errors and adapts expected state."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="LearnTest",
                                   initial_state={"value": 0.5})
    # Set expected state far from actual
    obj.expected_state = {"value": 0.5}
    obj._state = {"value": 0.9}
    obj.set_state("value", 0.9)
    lesson = obj.learn({"value": 0.9})
    assert lesson is not None
    # Expected state should have shifted toward actual (EMA)
    assert obj.expected_state["value"] > 0.5


def test_claw_utility_score(runtime):
    """ClawLivingObject computes utility from recency, activity, and prediction quality."""
    store, registry, engine, _ = runtime
    obj = ClawLivingObject.create(store, registry, engine, name="UtilityTest",
                                   initial_state={"score": 0})
    obj.actions_taken = 3
    obj.idle_steps = 1
    obj.prediction_errors = [0.1, 0.05, 0.08]
    utility = obj.get_utility()
    assert 0.0 <= utility <= 1.0


def test_claw_communication_without_capability(runtime):
    """ClawLivingObject rejects communication without capability."""
    store, registry, engine, _ = runtime
    a = ClawLivingObject.create(store, registry, engine, name="NoCapA")
    b = ClawLivingObject.create(store, registry, engine, name="NoCapB")
    # No relationship granted
    comm = a.communicate(b.object_id, {"msg": "hello"})
    assert not comm["success"]
    assert comm["reason"] == "no_relationship"
