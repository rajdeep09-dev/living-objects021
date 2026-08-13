"""
Claw Demo: SmartThermostat — Learning from Past Anomalies Across Restarts

Demonstrates a persistent intelligent thermostat that:
1. Monitors temperature readings
2. Detects anomalies (spikes, drops)
3. Reasons about what to do
4. Learns strategies from experience
5. SURVIVES PROCESS RESTART — remembers everything

Usage: python3 demo_smart_thermostat.py
"""
import sys, os, json
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from living_objects import EventStore, MockReasoningEngine, CapabilityRegistry
from claw.living_object import ClawLivingObject

DB_FILE = "thermostat_demo.db"


class SmartThermostat(ClawLivingObject):
    """
    A thermostat that monitors, reasons about anomalies, and learns strategies.
    Deterministic methods handle readings and control.
    Intelligent methods handle diagnosis and strategy selection.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_temp = 22.0  # default target

    # ------------------------------------------------------------------
    # Deterministic Methods (normal Python)
    # ------------------------------------------------------------------

    def record_reading(self, temperature: float, unit: str = "celsius") -> str:
        """Record a temperature reading and track recent history."""
        readings = self.get_state("readings", [])
        readings.append({"value": temperature, "unit": unit, "step": len(readings)})
        self.set_state("readings", readings[-50:])  # keep last 50
        self.set_state("last_reading", temperature)
        self.set_state("reading_count", len(readings))
        return f"Recorded {temperature}{unit}"

    def set_target(self, temperature: float) -> str:
        """Set the target temperature."""
        old = self.get_state("target_temp", 22.0)
        self.set_state("target_temp", temperature)
        return f"Target changed: {old} -> {temperature}°C"

    def get_status(self) -> dict:
        """Get current thermostat status."""
        return {
            "name": self.name,
            "last_reading": self.get_state("last_reading"),
            "target": self.get_state("target_temp", 22.0),
            "reading_count": self.get_state("reading_count", 0),
            "strategies": self.get_state("learned_strategies", []),
            "dormant": self.is_dormant,
            "surprise": self.surprise_score,
        }

    def detect_anomaly(self) -> dict:
        """Detect if current reading is anomalous compared to recent history."""
        readings = self.get_state("readings", [])
        if len(readings) < 3:
            return {"anomaly": False, "reason": "insufficient_data"}

        recent = [r["value"] for r in readings[-10:]]
        current = readings[-1]["value"]
        avg = sum(recent[:-1]) / len(recent[:-1])
        std = (sum((x - avg) ** 2 for x in recent[:-1]) / len(recent[:-1])) ** 0.5 or 0.5

        deviation = abs(current - avg)
        z_score = deviation / std

        is_anomaly = z_score > 2.0 or deviation > 5.0
        return {
            "anomaly": is_anomaly,
            "z_score": round(z_score, 2),
            "deviation": round(deviation, 2),
            "current": current,
            "average": round(avg, 2),
            "std": round(std, 2),
        }

    def apply_correction(self, action: str, magnitude: float = 1.0) -> dict:
        """Apply a heating/cooling correction."""
        corrections = self.get_state("corrections", [])
        corrections.append({"action": action, "magnitude": magnitude, "step": len(corrections)})
        self.set_state("corrections", corrections[-20:])
        self.set_state("last_correction", {"action": action, "magnitude": magnitude})
        return {"applied": action, "magnitude": magnitude}

    # ------------------------------------------------------------------
    # Intelligent Methods (LLM-driven via docstring)
    # ------------------------------------------------------------------

    def diagnose_anomaly(self, anomaly_data: dict) -> str:
        """
        Analyze the anomaly and determine root cause.
        Consider: temperature spike vs gradual drift vs sensor error.
        Return a diagnosis with confidence.
        """
        ...

    def select_strategy(self, anomaly_type: str, history: list) -> str:
        """
        Select the best control strategy based on anomaly type and past experience.
        Consider previously learned strategies and their success rates.
        """
        ...

    def predict_outcome(self, strategy: str, current_state: dict) -> str:
        """
        Predict the outcome of applying this strategy.
        Consider the current temperature, target, and recent trends.
        """
        ...


def demo_session_1():
    """First session: create thermostat, collect data, detect anomaly, learn."""
    print("=" * 70)
    print("  SESSION 1: Creating SmartThermostat & Learning")
    print("=" * 70)

    store = EventStore(DB_FILE)
    registry = CapabilityRegistry()
    engine = MockReasoningEngine()

    thermo = SmartThermostat.create(
        store=store,
        registry=registry,
        reasoning=engine,
        name="Thermo_Lab7",
        initial_state={
            "target_temp": 22.0,
            "readings": [],
            "last_reading": None,
            "reading_count": 0,
            "learned_strategies": [],
            "corrections": [],
            "last_correction": None,
        }
    )
    print(f"  🏠 Created: {thermo}")
    print(f"  📍 Location: Lab 7, Target: {thermo.get_state('target_temp')}°C")

    # Phase 1: Normal readings (establish baseline)
    print("\n  📊 Phase 1: Establishing baseline...")
    for temp in [21.8, 22.0, 22.1, 21.9, 22.0, 22.2, 21.8, 22.0]:
        thermo.record_reading(temp)
        status = thermo.detect_anomaly()
        print(f"    Reading {temp}°C → anomaly={status['anomaly']}")

    # Phase 2: Anomaly! Temperature spike
    print("\n  ⚠️  Phase 2: Anomaly detected!")
    thermo.record_reading(35.0)  # Big spike!
    anomaly = thermo.detect_anomaly()
    print(f"    Reading 35.0°C → anomaly={anomaly['anomaly']} (z={anomaly['z_score']})")

    # Phase 3: Intelligent diagnosis
    print("\n  🧠 Phase 3: Intelligent diagnosis...")
    diagnosis = thermo._call_method(thermo.diagnose_anomaly, anomaly)
    print(f"    Diagnosis: {diagnosis}")
    thermo.reasoning_count += 1

    # Phase 4: Learn from the experience
    print("\n  📚 Phase 4: Recording experience...")
    thermo.memory.record_episode(
        observation="Temperature spiked from 22°C to 35°C (thermal event)",
        action="Triggered emergency cooling sequence",
        result="Temperature dropped to 28°C after 5 minutes",
        outcome="success",
        lesson="Rapid cooling works for thermal spikes; activate HVAC immediately"
    )
    thermo.memory.record_strategy(
        name="thermal_spike_response",
        description="On spike >5°C: trigger HVAC cooling, monitor for 5min",
        success_rate=0.95
    )
    thermo.memory.record_fact(
        "Lab 7 has thermal instability near the window (summer months)",
        confidence=0.85,
        source="historical"
    )
    # Store learned strategy name in state
    strategies = thermo.get_state("learned_strategies", [])
    strategies.append("thermal_spike_response")
    thermo.set_state("learned_strategies", strategies)

    # Phase 5: Apply correction and record recovery
    thermo.apply_correction("hvac_cooling", magnitude=3.0)
    thermo.record_reading(28.0)
    thermo.record_reading(24.0)
    thermo.record_reading(22.5)

    # Save
    thermo.save()
    print(f"\n  ✅ Session 1 complete!")
    print(f"  📖 Memory summary:")
    print(f"     {thermo.memory.summarize_experiences()}")
    print(f"  📊 Strategies learned: {thermo.get_state('learned_strategies', [])}")

    # Show events
    events = store.get_events(thermo.object_id)
    print(f"  📝 Total events: {len(events)}")
    event_types = [e.event_type for e in events]
    print(f"  📝 Event types: {set(event_types)}")

    thermo_id = thermo.object_id
    return thermo_id


def demo_session_2(thermo_id):
    """Second session: restart, load, show memory persists, learn more."""
    print("\n" + "=" * 70)
    print("  SESSION 2: RESTART — Thermostat Remembers Everything!")
    print("=" * 70)

    # "Terminate" process
    import gc; gc.collect()

    # Restart with fresh runtime
    store2 = EventStore(DB_FILE)
    registry2 = CapabilityRegistry()
    engine2 = MockReasoningEngine()

    thermo2 = SmartThermostat.load(
        thermo_id, store2, registry2, engine2
    )
    print(f"  🔄 Rehydrated: {thermo2}")
    print(f"  📍 Location: Lab 7 (preserved)")
    print(f"  🌡️  Last reading: {thermo2.get_state('last_reading')}°C")
    print(f"  📊 Total readings: {thermo2.get_state('reading_count')}")
    print(f"  🎯 Target temp: {thermo2.get_state('target_temp')}°C")
    print(f"  📚 Learned strategies: {thermo2.get_state('learned_strategies', [])}")

    # Verify memory survived
    print(f"\n  📚 Memory Check:")
    episodes = thermo2.memory.recall_episodes(limit=5)
    print(f"  📖 Episodic memories: {len(episodes)}")
    for ep in episodes:
        c = json.loads(ep["content"])
        print(f"     - {c.get('observation', '')[:60]}...")
        print(f"       Lesson: {c.get('lesson', '')}")

    facts = thermo2.memory.recall_facts(limit=5)
    print(f"  📖 Semantic memories: {len(facts)}")
    for f in facts:
        c = json.loads(f["content"])
        print(f"     - {c.get('fact', '')[:60]} (conf={f['confidence']:.2f})")

    strategies = thermo2.memory.recall_strategies(limit=5)
    print(f"  📖 Procedural memories: {len(strategies)}")
    for s in strategies:
        c = json.loads(s["content"])
        print(f"     - {c.get('name', '')}: {c.get('description', '')[:50]}...")

    # Phase 3: New anomaly after restart
    print(f"\n  ⚠️  Phase 5: New anomaly after restart!")
    thermo2.record_reading(15.0)  # Cold drop!
    anomaly2 = thermo2.detect_anomaly()
    print(f"    Reading 15.0°C → anomaly={anomaly2['anomaly']} (z={anomaly2['z_score']})")

    # Use learned strategies
    print(f"\n  🧠 Phase 6: Using learned strategies...")
    learned = thermo2.get_state("learned_strategies", [])
    print(f"    Strategies from past: {learned}")

    # Apply learned strategy
    thermo2.apply_correction("hvac_heating", magnitude=2.0)
    thermo2.record_reading(18.0)
    thermo2.record_reading(20.5)
    thermo2.record_reading(22.0)

    # Record new experience
    thermo2.memory.record_episode(
        observation="Temperature dropped from 22°C to 15°C (cold snap)",
        action="Triggered heating sequence",
        result="Temperature rose to 22°C after 8 minutes",
        outcome="success",
        lesson="Cold drops need gradual heating to avoid thermal shock"
    )
    strategies = thermo2.get_state("learned_strategies", [])
    strategies.append("cold_drop_response")
    thermo2.set_state("learned_strategies", strategies)

    thermo2.save()
    print(f"\n  ✅ Session 2 complete!")
    print(f"  📖 Updated memory summary:")
    print(f"     {thermo2.memory.summarize_experiences()}")

    # Final stats
    events2 = store2.get_events(thermo2.object_id)
    print(f"\n  📊 Final Stats:")
    print(f"     Total events: {len(events2)}")
    print(f"     Reasoning calls: {thermo2.reasoning_count}")
    print(f"     Actions taken: {thermo2.actions_taken}")
    print(f"     Strategies learned: {len(thermo2.get_state('learned_strategies', []))}")
    print(f"     Utility score: {thermo2.get_utility():.2f}")

    return thermo2


def main():
    print("\n🧬 LIVING OBJECTS — SmartThermostat Demo")
    print("   Learning from anomalies across process restarts\n")

    # Session 1
    thermo_id = demo_session_1()

    # Session 2 (restart)
    thermo2 = demo_session_2(thermo_id)

    # Cleanup
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print(f"\n  🧹 Cleanup complete. Demo finished! ✨")


if __name__ == "__main__":
    main()
