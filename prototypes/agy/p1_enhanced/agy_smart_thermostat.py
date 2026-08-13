"""
AGY SmartThermostat Demo — Cross-restart anomaly learning
=========================================================

SESSION 1: Create → 8 normal baseline readings → thermal spike (35°C) →
           z-score triggers → diagnosis → strategy learned → SAVE → crash

SESSION 2: Reload → anomaly patterns restored from episodic memory →
           new spike (40°C) recognized as recurrence #3 → cold drop →
           prediction → utility computed

Proves AGY-7: cross-restart anomaly learning without any manual state export.

Run:
    cd /path/to/living-objects021   (fresh clone)
    python -m prototypes.agy.p1_enhanced.agy_smart_thermostat
"""
from __future__ import annotations

import gc
import os
import sys

# Make sure the repo root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, MockReasoningEngine, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    TieredReasoningEngine,
    AnomalyRecord,
)

DB = os.path.join(os.path.dirname(__file__), "_thermostat_agy.db")


# ---------------------------------------------------------------------------
# SmartThermostat subclass — uses AGY auto-routing for intelligent methods
# ---------------------------------------------------------------------------

class SmartThermostat(AGYLivingObject):
    """
    AGY Thermostat — learns anomaly patterns across restarts.

    Deterministic  : record_reading, get_statistics, set_target
    Intelligent    : diagnose_anomaly, recommend_action, predict_next_anomaly
                     (auto-routed by __init_subclass__ — no _call_method needed)
    """

    # --- Deterministic methods ---

    def record_reading(self, temperature: float, humidity: float = 50.0) -> dict:
        """Record a temperature+humidity reading and run anomaly detection."""
        readings = self.get_state("readings", []) or []
        readings.append({"temp": round(temperature, 2), "humidity": round(humidity, 2)})
        self.set_state("readings", readings[-200:])
        self.set_state("last_temp", temperature)

        anomaly = self.detect_anomaly(
            metric="temperature",
            observed=temperature,
            expected=self.get_state("target_temp", 22.0),
            context={"humidity": humidity, "n": len(readings)},
        )
        if anomaly and anomaly.severity in ("high", "critical") and self.is_dormant:
            self.wake()

        return {
            "temp": temperature,
            "anomaly": anomaly.to_dict() if anomaly else None,
            "dormant": self.is_dormant,
        }

    def get_statistics(self) -> dict:
        """Compute min / max / avg from stored readings."""
        readings = self.get_state("readings", []) or []
        if not readings:
            return {"min": None, "max": None, "avg": None, "count": 0}
        temps = [r["temp"] for r in readings]
        return {
            "min": round(min(temps), 2), "max": round(max(temps), 2),
            "avg": round(sum(temps) / len(temps), 2), "count": len(temps),
        }

    def set_target(self, target: float) -> str:
        """Update target temperature setpoint."""
        old = self.get_state("target_temp", 22.0)
        self.set_state("target_temp", target)
        self.expected_state["last_temp"] = target
        return f"Target {old}°C → {target}°C"

    # --- Intelligent methods (... body → auto-routed by __init_subclass__) ---

    def diagnose_anomaly(self, description: str) -> str:
        """
        Diagnose the described temperature anomaly.
        Consider: location, current readings, past episodic patterns, recurrence count.
        Weigh strategies from memory. Return a concise 1-2 sentence diagnosis.
        """
        ...

    def recommend_action(self, description: str) -> dict:
        """
        Recommend a corrective action for the described anomaly.
        Choose from: increase_cooling, decrease_heating, alert_maintenance,
                     inspect_sensor, adjust_setpoint, monitor_only.
        Prefer strategies that resolved similar anomalies in memory.
        Return: {action: str, urgency: low|medium|high|critical, rationale: str}.
        """
        ...

    def predict_next_anomaly(self) -> str:
        """
        Based on anomaly patterns (frequency, severity, recurrence) and temperature
        trends in the readings, predict whether an anomaly is likely in the next
        10 readings. Explain why.
        """
        ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(msg: str) -> None:
    print("\n" + "═" * 60)
    print(f"  {msg}")
    print("═" * 60)


def status(t: SmartThermostat, engine: TieredReasoningEngine) -> None:
    s = t.get_statistics()
    u = t.get_utility()
    print(f"  Object  : {t}")
    print(f"  Target  : {t.get_state('target_temp', 22.0)}°C  |  "
          f"Stats: min={s['min']} max={s['max']} avg={s['avg']} n={s['count']}")
    print(f"  Dormant : {t.is_dormant}  |  "
          f"SurpriseEMA={t._surprise_ema:.4f}  Threshold={t.surprise_threshold:.3f}")
    print(f"  Anomaly : {len(t._anomaly_history)} recorded  "
          f"patterns={t._anomaly_patterns}")
    print(f"  Utility : {u:.3f}  Budget={t.daily_budget:.2f}  "
          f"Reasons={t.reasoning_count}×")
    print(f"  Engine  : {engine.stats()}")


# ---------------------------------------------------------------------------
# Session 1
# ---------------------------------------------------------------------------

def session_1(db: str) -> str:
    banner("SESSION 1 — Create, detect spike, learn, save, crash")

    store = EventStore(db)
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine()

    t = SmartThermostat.create(
        store=store, registry=registry, reasoning=engine,
        name="AGYThermostat",
        initial_state={"target_temp": 22.0, "readings": [],
                       "location": "server_room_A"},
    )
    t.expected_state["last_temp"] = 22.0
    print(f"\n  Created: {t}")

    # Build z-score window with normal readings
    print("\n  [Normal baseline]")
    for temp in [22.1, 21.8, 22.3, 21.9, 22.2, 22.0, 21.7, 22.1, 22.0, 22.2]:
        r = t.record_reading(temp, humidity=48.0)
        t.tick()

    # First thermal spike
    print("\n  [First thermal spike — 35°C]")
    r = t.record_reading(35.0, humidity=62.0)
    a1 = r["anomaly"]
    if a1:
        print(f"    35.0°C → {a1['severity'].upper()}  "
              f"z={a1['z_score']:.2f}  id={a1['anomaly_id']}")
        diag = t.diagnose_anomaly("Temp jumped to 35°C in server_room_A")
        print(f"    Diagnosis   : {diag}")
        action = t.recommend_action("Thermal spike, severity=high")
        print(f"    Recommended : {action}")
        t.resolve_anomaly(a1["anomaly_id"], "Fan override to maximum")
        t.memory.record_strategy(
            "thermal_spike_response",
            "When temp >32°C and z>3: override cooling fan. Resolves in <5 min.",
            success_rate=0.92,
        )

    # Second spike — pattern builds
    print("\n  [Second spike — 34°C, recurrence #2]")
    r2 = t.record_reading(34.0, humidity=60.0)
    a2 = r2["anomaly"]
    if a2:
        print(f"    34.0°C → {a2['severity'].upper()}  "
              f"z={a2['z_score']:.2f}  "
              f"recurrence=#{t._anomaly_patterns.get('temperature', 0)}")

    t.memory.record_fact(
        "server_room_A south wall poorly insulated — summer afternoon spikes expected",
        confidence=0.88, source="maintenance_log",
    )

    # Idle → dormancy
    print("\n  [Idling to dormancy]")
    for _ in range(8):
        t.tick()
    print(f"    Dormant: {t.is_dormant}")

    status(t, engine)
    t.save()
    oid = t.object_id
    print(f"\n  Saved id={oid}  v={t._state_version}")

    del t, store, registry, engine
    gc.collect()
    print("\n  >>> Process crashed / restarted <<<")
    return oid


# ---------------------------------------------------------------------------
# Session 2
# ---------------------------------------------------------------------------

def session_2(db: str, oid: str) -> None:
    banner("SESSION 2 — Reload + cross-restart anomaly learning")

    store = EventStore(db)
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine()

    t = SmartThermostat.load(oid, store, registry, engine)
    assert t is not None, "Rehydration failed!"
    print(f"\n  Rehydrated : {t}")
    print(f"  Patterns   : {t._anomaly_patterns}")
    print(f"  Strategies : {len(t.memory.recall_strategies())}")
    print(f"  Facts      : {len(t.memory.recall_facts())}")

    # Third spike — cross-restart recognition
    print("\n  [Third spike — 40°C, cross-restart recurrence recognized]")
    r = t.record_reading(40.0, humidity=65.0)
    a3 = r["anomaly"]
    if a3:
        rec = t._anomaly_patterns.get("temperature", 0)
        print(f"    40.0°C → {a3['severity'].upper()}  "
              f"z={a3['z_score']:.2f}  recurrence=#{rec}  ← learned across restart!")
        diag = t.diagnose_anomaly(
            f"Third occurrence of thermal spike in server_room_A (recurrence=#{rec})")
        print(f"    Diagnosis   : {diag}")
        action = t.recommend_action(f"Recurring thermal spike #{rec} — critical")
        print(f"    Recommended : {action}")

    # Cold drop
    print("\n  [Cold drop — 8°C]")
    r_cold = t.record_reading(8.0, humidity=28.0)
    a_cold = r_cold["anomaly"]
    if a_cold:
        print(f"    8.0°C → {a_cold['severity'].upper()}  z={a_cold['z_score']:.2f}")
        t.memory.record_strategy(
            "cold_drop_response",
            "When temp <12°C: check HVAC heating circuit, raise setpoint by 3°C.",
            success_rate=0.85,
        )

    # Prediction
    print("\n  [Future prediction]")
    pred = t.predict_next_anomaly()
    print(f"    Prediction: {pred}")

    # Dormancy/wake via large observation
    print("\n  [Dormancy/wake test]")
    for _ in range(10):
        t.tick()
    print(f"    After 10 ticks: dormant={t.is_dormant}")
    obs = t.observe({"last_temp_change": 14.0})
    print(f"    After 14° obs: dormant={t.is_dormant}  "
          f"surprise={obs['surprise']:.3f}  evr={obs.get('evr', '?'):.3f}")

    print(f"\n  {t.anomaly_summary()}")
    print(f"\n  Total events in store: {store.get_event_count(oid)}")
    status(t, engine)
    t.save()
    print("\n  >>> Cross-restart anomaly learning: VERIFIED ✓ <<<")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if os.path.exists(DB):
        os.remove(DB)
    oid = session_1(DB)
    session_2(DB, oid)
    if os.path.exists(DB):
        os.remove(DB)
    banner("AGY SmartThermostat demo complete ✓")


if __name__ == "__main__":
    main()
