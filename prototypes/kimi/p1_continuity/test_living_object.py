"""Kimi's original tests — 5/6 passing."""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from living_objects import LivingObject, EventStore, MockReasoningEngine, CapabilityRegistry

@pytest.fixture
def runtime(tmp_path):
    db = str(tmp_path / "test.db")
    store = EventStore(db)
    registry = CapabilityRegistry()
    engine = MockReasoningEngine()
    yield store, registry, engine, db
    pass  # Kimi EventStore has no close()

def test_create(runtime):
    store, registry, engine, _ = runtime
    obj = LivingObject.create(store, registry, engine, name="TestObj")
    assert obj.object_id is not None
    assert obj.name == "TestObj"

def test_state_persistence(runtime):
    store, registry, engine, _ = runtime
    obj = LivingObject.create(store, registry, engine, name="TestObj")
    obj.set_state("x", 42)
    obj.save()
    loaded = LivingObject.load(obj.object_id, store, registry, engine)
    assert loaded.get_state("x") == 42

def test_memory_persistence(runtime):
    store, registry, engine, _ = runtime
    obj = LivingObject.create(store, registry, engine, name="TestObj")
    obj.memory.record_episode("obs", "act", "res", "success", "lesson")
    obj.save()
    loaded = LivingObject.load(obj.object_id, store, registry, engine)
    assert len(loaded.memory.recall_episodes()) == 1

def test_event_audit_trail(runtime):
    """Fixed: calls load() so 'loaded' event exists before asserting."""
    store, registry, engine, _ = runtime
    obj = LivingObject.create(store, registry, engine, name="TestObj")
    obj.set_state("a", 1)
    obj.save()
    # Must call load() to generate the "loaded" event
    LivingObject.load(obj.object_id, store, registry, engine)
    events = store.get_events(obj.object_id)
    event_types = [e.event_type for e in events]
    assert "created" in event_types
    assert "state_change" in event_types
    assert "loaded" in event_types  # now valid — load() was called

def test_intelligent_method_detection(runtime):
    store, registry, engine, _ = runtime
    class Methods:
        def intelligent_one(self) -> str:
            """This is intelligent."""
            ...
        def deterministic_one(self) -> str:
            """This is deterministic."""
            return "hello"
    obj = LivingObject.create(store, registry, engine, name="Test")
    assert obj._is_intelligent_method(Methods.intelligent_one)
    assert not obj._is_intelligent_method(Methods.deterministic_one)

def test_capability_registry(runtime):
    store, registry, engine, _ = runtime
    obj_a = LivingObject.create(store, registry, engine, name="A")
    obj_b = LivingObject.create(store, registry, engine, name="B")
    registry.grant(obj_a.object_id, obj_b.object_id, ["read"])
    assert registry.check(obj_a.object_id, obj_b.object_id, "read")
    assert not registry.check(obj_b.object_id, obj_a.object_id, "read")
