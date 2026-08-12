"""
Example: Smart Sensor with Living Objects

Demonstrates a persistent intelligent sensor that:
- Records readings (deterministic)
- Diagnoses anomalies (intelligent)
- Learns from experience
- Survives process restart
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from living_object import EventStore, CapabilityRegistry, MockReasoningEngine, LivingObject


class SmartSensor(LivingObject):
    """A sensor that monitors, reasons, and learns."""

    def record_reading(self, value: float, unit: str = "celsius") -> str:
        """Deterministic: record a sensor reading."""
        readings = self.get_state("readings", [])
        readings.append({"value": value, "unit": unit})
        self.set_state("readings", readings[-100:])  # keep last 100
        self.set_state("last_reading", {"value": value, "unit": unit})
        return f"Recorded {value}{unit}"

    def diagnose(self, symptom: str) -> str:
        """Intelligent: analyze a symptom and provide diagnosis."""
        ...

    def predict_trend(self, metric: str) -> str:
        """Intelligent: predict future trend of a metric."""
        ...


def main():
    DB = "sensor_example.db"

    # Create sensor
    store = EventStore(DB)
    registry = CapabilityRegistry(store)
    engine = MockReasoningEngine()

    sensor = SmartSensor.create(
        store=store, registry=registry, reasoning=engine,
        name="LabSensor_7", type_name="sensor",
        initial_state={"location": "lab_7", "readings": [], "mode": "monitoring"}
    )
    print(f"Created: {sensor}")

    # Record some readings
    sensor.record_reading(23.5)
    sensor.record_reading(24.1)
    sensor.record_reading(45.2)  # anomaly!
    print(f"Readings: {sensor.get_state('readings')}")

    # Record an experience
    sensor.memory.record_episode(
        observation="Temperature spiked to 45.2C",
        action="Triggered cooling",
        result="Dropped to 38.5C",
        outcome="success",
        lesson="Rapid cooling works for thermal spikes"
    )

    # Save and "terminate"
    sensor.save()
    sensor_id = sensor.object_id
    del sensor, store, registry
    import gc; gc.collect()
    print("\nProcess terminated. Restarting...\n")

    # Restart and rehydrate
    store2 = EventStore(DB)
    registry2 = CapabilityRegistry(store2)
    sensor2 = SmartSensor.load(sensor_id, store2, registry2, MockReasoningEngine())

    print(f"Rehydrated: {sensor2}")
    print(f"Location: {sensor2.get_state('location')}")
    print(f"Readings: {sensor2.get_state('readings')}")
    print(f"Memory: {sensor2.memory.summarize()}")

    # Cleanup
    os.remove(DB)
    print("\nDone. Sensor survived restart with full continuity.")


if __name__ == "__main__":
    main()
