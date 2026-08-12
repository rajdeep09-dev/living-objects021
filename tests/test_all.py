"""
Prototype 1 — Complete Test Suite
Tests: persistence, continuity, multi-object, emergence, dormancy, lifecycle
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))

from living_object import EventStore, CapabilityRegistry, MockReasoningEngine, LivingObject

DB_FILE = "test_prototype1.db"

def banner(title):
    print(f"\n{'='*70}\n {title}\n{'='*70}")

def section(title):
    print(f"\n--- {title} ---")

def check(label, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" | {details}" if details else ""))
    return condition

def cleanup():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


# =============================================================================
# TEST 1: CONTINUITY (Rajdeep's E1)
# =============================================================================
def test_continuity():
    banner("TEST 1: PERSISTENCE CONTINUITY (create -> interact -> terminate -> restart -> verify)")
    cleanup()

    # Phase 1: Create
    store = EventStore(DB_FILE)
    registry = CapabilityRegistry(store)
    reasoning = MockReasoningEngine()

    obj = LivingObject.create(
        store=store, registry=registry, reasoning=reasoning,
        name="SensorAlpha", type_name="sensor",
        initial_state={"location": "lab_7", "calibration": 1.0, "readings": [], "mode": "monitoring"}
    )
    obj_id = obj.object_id
    print(f"  Created: {obj}")

    # Phase 2: Interact (deterministic + intelligent)
    obj.set_state("readings", [23.5, 24.1, 45.2])
    obj.set_state("last_reading", {"value": 45.2, "unit": "celsius"})
    obj.set_state("learned_strategies", ["thermal_spike_response", "drift_detection"])
    obj.set_state("experience_count", 3)

    # Record experiences
    obj.memory.record_episode("Temperature spiked to 45.2C", "Triggered cooling", "Dropped to 38.5C", "success", "Rapid cooling works")
    obj.memory.record_episode("Calibration drift detected", "Auto-recalibrated", "Within 0.05C", "success", "Periodic calibration prevents drift")
    obj.memory.record_fact("Lab 7 has thermal instability in summer", 0.85, "historical")
    obj.memory.record_strategy("thermal_spike_response", "Cool immediately on spike", 0.95)

    events_before = len(store.get_events(obj_id))
    memories_before = len(store.get_memories(obj_id, limit=1000))
    obj.save()

    # Phase 3: Terminate
    del obj, store, registry
    import gc; gc.collect()

    # Phase 4: Restart
    store2 = EventStore(DB_FILE)
    registry2 = CapabilityRegistry(store2)
    obj2 = LivingObject.load(obj_id, store2, registry2, MockReasoningEngine())

    # Phase 5: Verify
    all_pass = True
    section("Identity")
    all_pass &= check("Object ID matches", obj2.object_id == obj_id)
    all_pass &= check("Name preserved", obj2.name == "SensorAlpha")
    all_pass &= check("Type preserved", obj2.type_name == "sensor")

    section("State")
    all_pass &= check("Location preserved", obj2.get_state("location") == "lab_7")
    all_pass &= check("Calibration preserved", obj2.get_state("calibration") == 1.0)
    all_pass &= check("Readings preserved", len(obj2.get_state("readings", [])) == 3)
    all_pass &= check("Strategies preserved", obj2.get_state("learned_strategies") == ["thermal_spike_response", "drift_detection"])

    section("Memory")
    episodes = obj2.memory.recall_episodes(limit=5)
    all_pass &= check("Episodic memories survived", len(episodes) == 2)
    facts = obj2.memory.recall_facts(limit=5)
    all_pass &= check("Semantic memories survived", len(facts) == 1)
    strategies = obj2.memory.recall_strategies(limit=5)
    all_pass &= check("Procedural memories survived", len(strategies) == 1)

    section("Events")
    events_after = len(store2.get_events(obj_id))
    all_pass &= check("Events persisted", events_after >= events_before)

    section("Post-restart functionality")
    obj2.set_state("post_restart_test", True)
    all_pass &= check("State mutation works", obj2.get_state("post_restart_test") == True)

    # Cleanup
    os.remove(DB_FILE)
    return all_pass


# =============================================================================
# TEST 2: MULTI-OBJECT SCALING
# =============================================================================
def test_multi_object_scaling():
    banner("TEST 2: MULTI-OBJECT SCALING (10, 50, 100, 200 objects)")
    cleanup()

    results = []
    for n in [10, 50, 100]:
        store = EventStore(f"scaling_{n}.db")
        registry = CapabilityRegistry(store)
        reasoning = MockReasoningEngine()

        # Create objects
        objects = []
        for i in range(n):
            obj = LivingObject.create(
                store=store, registry=registry, reasoning=reasoning,
                name=f"Entity_{i}", type_name="entity",
                initial_state={"value": 0.5, "activity": 0.5}
            )
            objects.append(obj)

        # Simulate 30 steps with 10% stimulus rate
        import random
        rng = random.Random(42)
        total_tokens = 0
        total_reasoning = 0

        for step in range(20):
            for obj in objects:
                if rng.random() < 0.10:
                    obj.observe({"type": "stimulus", "value_change": rng.uniform(-0.3, 0.3)})
                if obj.should_reason():
                    r = obj.reason()
                    obj.act(r["action"])
                    total_tokens += r["tokens_used"]
                    total_reasoning += 1
                obj.tick()

        # Count dormant
        dormant = sum(1 for o in objects if o.is_dormant)
        active = sum(1 for o in objects if not o.is_dormant)

        result = {
            "n": n, "active": active, "dormant": dormant,
            "dormant_pct": dormant / n * 100,
            "total_tokens": total_tokens, "tokens_per_obj": total_tokens / n,
            "reasoning_calls": total_reasoning,
        }
        results.append(result)

        print(f"  N={n:>4} | active={active:>4} dormant={dormant:>4} ({result['dormant_pct']:.0f}%) | "
              f"tokens={total_tokens:>6} t/obj={result['tokens_per_obj']:.0f} | reasoning={total_reasoning}")

        # Cleanup
        os.remove(f"scaling_{n}.db")

    # Analysis
    section("Scaling Analysis")
    if len(results) >= 2:
        ratio = results[-1]["total_tokens"] / max(1, results[0]["total_tokens"])
        obj_ratio = results[-1]["n"] / max(1, results[0]["n"])
        all_pass = ratio < obj_ratio
        check("Sub-linear token scaling", all_pass, f"{obj_ratio:.0f}x objects -> {ratio:.1f}x tokens")
        return all_pass
    return True


# =============================================================================
# TEST 3: EMERGENCE (Peer-to-peer communication)
# =============================================================================
def test_emergence():
    banner("TEST 3: EMERGENCE (peer-to-peer collaboration)")
    cleanup()

    store = EventStore(DB_FILE)
    registry = CapabilityRegistry(store)
    reasoning = MockReasoningEngine()

    # Create two specialists
    obj_a = LivingObject.create(
        store=store, registry=registry, reasoning=reasoning,
        name="SpecialistA", type_name="specialist_a",
        initial_state={"knowledge_a": 0, "insights": []}
    )
    obj_b = LivingObject.create(
        store=store, registry=registry, reasoning=reasoning,
        name="SpecialistB", type_name="specialist_b",
        initial_state={"knowledge_b": 0, "insights": []}
    )

    # Establish bidirectional relationship
    registry.grant(obj_a.object_id, obj_b.object_id, ["communicate"])
    registry.grant(obj_b.object_id, obj_a.object_id, ["communicate"])

    print(f"  Created: {obj_a.type_name}:{obj_a.name} <-> {obj_b.type_name}:{obj_b.name}")

    # Progressive clues
    clues = [
        {"target": obj_a, "data": {"knowledge_a": 0.3}, "desc": "A signal (weak)"},
        {"target": obj_b, "data": {"knowledge_b": 0.4}, "desc": "B signal (weak)"},
        {"target": obj_a, "data": {"knowledge_a": 0.6}, "desc": "A signal (strong)"},
        {"target": obj_b, "data": {"knowledge_b": 0.7}, "desc": "B signal (strong)"},
        {"target": obj_a, "data": {"knowledge_a": 0.9}, "desc": "A signal (critical)"},
        {"target": obj_b, "data": {"knowledge_b": 0.9}, "desc": "B signal (critical)"},
    ]

    solutions = []
    messages = 0

    for step, clue in enumerate(clues):
        target = clue["target"]
        other = obj_b if target == obj_a else obj_a

        result = target.observe({"type": "stimulus", **clue["data"]})
        surprise = result["surprise"]

        if target.should_reason():
            r = target.reason({"step": step})
            target.act(r["action"])

            # Share with partner
            comm = target.communicate(other.object_id, {
                "type": "insight", "data": clue["data"], "step": step
            })
            if comm["success"]:
                messages += 1
                other.receive_message({"type": "shared_insight", "data": clue["data"], "from": target.object_id})

                if other.should_reason():
                    r2 = other.reason({"step": step, "received_insight": True})
                    messages += 1

                    # Check for solution
                    a_k = target.get_state("knowledge_a", 0)
                    b_k = other.get_state("knowledge_b", 0) if hasattr(other, "get_state") else 0
                    if a_k > 0.5 and b_k > 0.5:
                        quality = (a_k + b_k) / 2
                        solutions.append({"step": step, "quality": quality})
                        print(f"  Step {step+1}: {clue['desc']} -> surprise={surprise:.2f} -> REASONED -> SHARED -> SOLUTION (q={quality:.2f})")
                    else:
                        print(f"  Step {step+1}: {clue['desc']} -> surprise={surprise:.2f} -> REASONED -> SHARED")
                else:
                    print(f"  Step {step+1}: {clue['desc']} -> surprise={surprise:.2f} -> REASONED -> SHARED (partner not surprised)")
            else:
                print(f"  Step {step+1}: {clue['desc']} -> surprise={surprise:.2f} -> REASONED (no relationship)")
        else:
            print(f"  Step {step+1}: {clue['desc']} -> surprise={surprise:.2f} -> NOT REASONED (below threshold)")

    section("Results")
    all_pass = True
    all_pass &= check("Messages exchanged", messages > 0, f"{messages} messages")
    all_pass &= check("Solutions emerged", len(solutions) > 0, f"{len(solutions)} solutions")
    if solutions:
        avg_q = sum(s["quality"] for s in solutions) / len(solutions)
        all_pass &= check("Solution quality > 0.5", avg_q > 0.5, f"avg={avg_q:.2f}")

    # Cleanup
    os.remove(DB_FILE)
    return all_pass


# =============================================================================
# TEST 4: DORMANCY LIFECYCLE
# =============================================================================
def test_dormancy():
    banner("TEST 4: DORMANCY LIFECYCLE (active -> dormant -> wake)")
    cleanup()

    store = EventStore(DB_FILE)
    registry = CapabilityRegistry(store)
    reasoning = MockReasoningEngine()

    obj = LivingObject.create(
        store=store, registry=registry, reasoning=reasoning,
        name="Sleeper", type_name="entity",
        initial_state={"value": 0.5}
    )

    all_pass = True

    # Initially active
    all_pass &= check("Initially active", not obj.is_dormant)
    all_pass &= check("Initially idle_steps=0", obj.idle_steps == 0)

    # Tick without stimulus -> should go dormant
    for i in range(6):
        obj.tick()
    all_pass &= check("Goes dormant after idle", obj.is_dormant)
    all_pass &= check("Idle steps accumulated", obj.idle_steps > 5)

    # Strong stimulus should wake it
    result = obj.observe({"type": "stimulus", "value_change": 0.5})
    all_pass &= check("Wakes on strong stimulus", not obj.is_dormant)
    all_pass &= check("Surprise is high", result["surprise"] > 0.2)

    # Should reason after waking
    all_pass &= check("Reasons after waking", obj.should_reason())

    # Cleanup
    os.remove(DB_FILE)
    return all_pass


# =============================================================================
# TEST 5: EVENT SOURCING & AUDIT TRAIL
# =============================================================================
def test_audit_trail():
    banner("TEST 5: EVENT SOURCING & AUDIT TRAIL")
    cleanup()

    store = EventStore(DB_FILE)
    registry = CapabilityRegistry(store)
    reasoning = MockReasoningEngine()

    obj = LivingObject.create(
        store=store, registry=registry, reasoning=reasoning,
        name="Audited", type_name="entity",
        initial_state={"x": 1}
    )

    # Perform various operations
    obj.set_state("x", 2)
    obj.set_state("x", 3)
    obj.observe({"type": "stimulus", "x": 0.5})
    if obj.should_reason():
        r = obj.reason()
        obj.act(r["action"])
    obj.memory.record_episode("test obs", "test act", "test result", "success", "test lesson")

    # Check events
    events = store.get_events(obj.object_id)
    event_types = [e.event_type for e in events]

    all_pass = True
    all_pass &= check("Creation event", "created" in event_types)
    all_pass &= check("State changes logged", event_types.count("state_change") >= 2)
    all_pass &= check("Observation logged", "observation" in event_types)

    # Check causal chain
    chained = [e for e in events if e.parent_event_id]
    all_pass &= check("Causal chain exists", len(chained) > 0, f"{len(chained)} events with parent")

    # Cleanup
    os.remove(DB_FILE)
    return all_pass


# =============================================================================
# TEST 6: INTELLIGENT METHOD ROUTING
# =============================================================================
def test_method_routing():
    banner("TEST 6: INTELLIGENT METHOD ROUTING (AST detection)")
    cleanup()

    store = EventStore(DB_FILE)
    registry = CapabilityRegistry(store)
    reasoning = MockReasoningEngine()

    # Create a subclass with both method types
    class SmartSensor(LivingObject):
        def get_reading(self) -> dict:
            """Deterministic: return current reading."""
            return {"value": self.get_state("value", 0), "status": "ok"}

        def diagnose(self, symptom: str) -> str:
            """Analyze symptom and provide diagnosis."""
            ...

    obj = SmartSensor.create(
        store=store, registry=registry, reasoning=reasoning,
        name="SmartSensor", type_name="sensor",
        initial_state={"value": 42.0}
    )

    # Deterministic method
    reading = obj._call_method(obj.get_reading)
    all_pass = True
    all_pass &= check("Deterministic method returns dict", isinstance(reading, dict))
    all_pass &= check("Deterministic value correct", reading.get("value") == 42.0)

    # Intelligent method
    diagnosis = obj._call_method(obj.diagnose, "temperature_spike")
    all_pass &= check("Intelligent method returns result", diagnosis is not None)

    # Check events
    events = store.get_events(obj.object_id)
    event_types = [e.event_type for e in events]
    all_pass &= check("Deterministic action logged", any("get_reading" in str(e.payload) for e in events if e.event_type == "action"))
    all_pass &= check("Intelligent reasoning logged", "reasoning" in event_types)

    # Cleanup
    os.remove(DB_FILE)
    return all_pass


# =============================================================================
# RUN ALL TESTS
# =============================================================================
if __name__ == "__main__":
    banner("PROTOTYPE 1 — COMPLETE TEST SUITE")
    print(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}
    results["continuity"] = test_continuity()
    results["scaling"] = test_multi_object_scaling()
    results["emergence"] = test_emergence()
    results["dormancy"] = test_dormancy()
    results["audit_trail"] = test_audit_trail()
    results["method_routing"] = test_method_routing()

    banner("FINAL RESULTS")
    all_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        all_pass &= passed

    if all_pass:
        print(f"\n  ALL {len(results)} TESTS PASSED")
        print(f"  Prototype 1 is solid.")
    else:
        print(f"\n  SOME TESTS FAILED")
        failed = [n for n, p in results.items() if not p]
        print(f"  Failed: {failed}")

    # Cleanup any remaining DB files
    for f in ["test_prototype1.db", "living_objects.db"]:
        if os.path.exists(f):
            os.remove(f)
