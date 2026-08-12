"""Mimo's improved tests — 8 tests, all passing."""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from prototypes.mimo.p1_continuity.living_object import EnhancedLivingObject
from living_objects import LivingObject, EventStore, MockReasoningEngine, CapabilityRegistry

@pytest.fixture
def runtime(tmp_path):
    db = str(tmp_path / "test.db")
    store = EventStore(db)
    registry = CapabilityRegistry()
    engine = MockReasoningEngine()
    yield store, registry, engine, db
    pass

def test_create(runtime):
    store, registry, engine, _ = runtime
    obj = EnhancedLivingObject.create(store, registry, engine, name="TestObj")
    assert obj.object_id is not None
    assert obj.name == "TestObj"
    assert obj.is_alive

def test_state_persistence(runtime):
    store, registry, engine, _ = runtime
    obj = EnhancedLivingObject.create(store, registry, engine, name="TestObj")
    obj.set_state("x", 42)
    obj.set_state("y", "hello")
    obj.save()
    loaded = EnhancedLivingObject.load(obj.object_id, store, registry, engine)
    assert loaded.get_state("x") == 42
    assert loaded.get_state("y") == "hello"

def test_memory_persistence(runtime):
    store, registry, engine, _ = runtime
    obj = EnhancedLivingObject.create(store, registry, engine, name="TestObj")
    obj.memory.record_episode("observation", "action", "result", "success", "lesson")
    obj.memory.record_fact("fact_1", 0.9, "source")
    obj.save()
    loaded = EnhancedLivingObject.load(obj.object_id, store, registry, engine)
    assert len(loaded.memory.recall_episodes()) == 1
    assert len(loaded.memory.recall_facts()) == 1

def test_event_audit_trail(runtime):
    """Fixed: properly tests loaded event by calling load()."""
    store, registry, engine, _ = runtime
    obj = EnhancedLivingObject.create(store, registry, engine, name="TestObj")
    obj.set_state("a", 1)
    obj.set_state("b", 2)
    obj.save()
    loaded = EnhancedLivingObject.load(obj.object_id, store, registry, engine)
    loaded.save()
    events = store.get_events(obj.object_id)
    event_types = [e.event_type for e in events]
    assert "created" in event_types
    assert "state_change" in event_types
    assert "loaded" in event_types

def test_intelligent_method_detection(runtime):
    store, registry, engine, _ = runtime
    obj = EnhancedLivingObject.create(store, registry, engine, name="TestObj")
    class Methods:
        def intelligent_one(self) -> str:
            """This is intelligent."""
            ...
        def deterministic_one(self) -> str:
            """This is deterministic."""
            return "hello"
    assert obj._is_intelligent_method(Methods.intelligent_one)
    assert not obj._is_intelligent_method(Methods.deterministic_one)

def test_capability_registry(runtime):
    store, registry, engine, _ = runtime
    obj_a = EnhancedLivingObject.create(store, registry, engine, name="A")
    obj_b = EnhancedLivingObject.create(store, registry, engine, name="B")
    registry.grant(obj_a.object_id, obj_b.object_id, ["read", "write"])
    assert registry.check(obj_a.object_id, obj_b.object_id, "read")
    assert registry.check(obj_a.object_id, obj_b.object_id, "write")
    assert not registry.check(obj_b.object_id, obj_a.object_id, "read")
    registry.revoke(obj_a.object_id, obj_b.object_id, "read"); registry.revoke(obj_a.object_id, obj_b.object_id, "write")
    assert not registry.check(obj_a.object_id, obj_b.object_id, "read")

def test_surprise_and_dormancy(runtime):
    """New: tests surprise-driven cognition and dormancy lifecycle."""
    store, registry, engine, _ = runtime
    obj = EnhancedLivingObject.create(store, registry, engine, name="Sensor", initial_state={"value": 0.5})
    assert not obj.is_dormant
    for _ in range(6):
        obj.tick()
    assert obj.is_dormant
    result = obj.observe({"type": "stimulus", "value_change": 0.5})
    assert not obj.is_dormant
    assert result["surprise"] > 0.2

def test_peer_communication(runtime):
    """New: tests peer-to-peer communication between objects."""
    store, registry, engine, _ = runtime
    a = EnhancedLivingObject.create(store, registry, engine, name="A", initial_state={"knowledge": 0})
    b = EnhancedLivingObject.create(store, registry, engine, name="B", initial_state={"knowledge": 0})
    registry.grant(a.object_id, b.object_id, ["communicate"])
    registry.grant(b.object_id, a.object_id, ["communicate"])
    comm = a.communicate(b.object_id, {"type": "insight", "data": 42})
    assert comm["success"]
    b.receive_message({"type": "insight", "data": 42, "from": a.object_id})
    assert b.surprise_score > 0
