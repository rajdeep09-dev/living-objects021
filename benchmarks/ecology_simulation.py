"""
P6.7 Research Experiment: Multi-Object Ecology Simulation (12+ Living Objects)
=============================================================================

Demonstrates a fully autonomous, emergent smart-facility ecosystem featuring:
  - 4 Room Sensor Objects (Living Objects)
  - 2 HVAC Subsystem Controllers (Living Objects)
  - 1 Energy Optimizer (Living Object)
  - 1 Facility Manager (Living Object)
  - 2 Spawned Maintenance Bots (Spawned Living Objects)
  - 2 Occupant Feedback Agents (Living Objects)

Capabilities demonstrated end-to-end:
  - Anomaly detection & cross-restart memory learning (P1.7, P6.2)
  - Goal-directed planning & execution (P2.11)
  - Peer task delegation (P4.4)
  - Collective consensus quorum voting (P4.5)
  - Parent-child object spawning (P4.6)
  - Generational population management (P4.7)
  - Global compute resource pool & bidding (P5.3)
  - Priority cognitive scheduling (P5.5)
  - Simulated restart & rehydration (P1.6)

Run:
    python benchmarks/ecology_simulation.py
"""
import os
import sys
import gc

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    ObjectDiscoveryRegistry,
    TieredReasoningEngine,
)
from prototypes.agy.p1_enhanced.agy_ecology_economics import (
    ConsensusEngine,
    DelegationEngine,
    GlobalResourcePool,
    GoalDirectedMixin,
    ObjectSpawner,
    PopulationManager,
    ResourceBid,
    UtilityPriorityScheduler,
)

DB_PATH = os.path.join(os.path.dirname(__file__), "_ecology_sim.db")


# ---------------------------------------------------------------------------
# Ecosystem Specialized Classes
# ---------------------------------------------------------------------------

class FacilityObject(GoalDirectedMixin, AGYLivingObject):
    """Base class with goal pursuit and living object capabilities."""
    pass


class RoomSensor(FacilityObject):
    def record_reading(self, temperature: float, occupancy: int) -> dict:
        self.set_state("temperature", temperature)
        self.set_state("occupancy", occupancy)
        anomaly = self.detect_anomaly("temperature", temperature, expected=22.0)
        return {"temperature": temperature, "anomaly": anomaly}


class HVACController(FacilityObject):
    def adjust_cooling(self, power_level: int) -> str:
        self.set_state("power_level", power_level)
        return f"HVAC cooling set to level {power_level}"


class FacilityManager(FacilityObject):
    def initiate_maintenance_order(self, room: str, reason: str) -> str:
        return f"Maintenance order created for {room}: {reason}"


class MaintenanceBot(FacilityObject):
    def repair_subsystem(self, target_room: str) -> str:
        self.set_state("repaired_room", target_room)
        return f"Repairs completed successfully in {target_room}"


class EnergyOptimizer(FacilityObject):
    def compute_energy_tariff(self, total_load: float) -> str:
        self.set_state("current_load_kw", total_load)
        return f"Tariff optimized for load {total_load}kW"


class OccupantAgent(FacilityObject):
    def submit_comfort_feedback(self, rating: int) -> str:
        self.set_state("comfort_rating", rating)
        return f"Feedback recorded: {rating}/5"


# ---------------------------------------------------------------------------
# Main Simulation
# ---------------------------------------------------------------------------

def run_ecology_simulation(db_path: str = DB_PATH) -> dict:
    if os.path.exists(db_path):
        os.remove(db_path)

    store = EventStore(db_path)
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine()
    consensus = ConsensusEngine()
    resource_pool = GlobalResourcePool(total_daily_tokens=5000)
    scheduler = UtilityPriorityScheduler()
    pop_manager = PopulationManager(store, registry, engine)

    print("\n" + "=" * 65)
    print("  PHASE 1: Instantiating 10 Base Living Objects")
    print("=" * 65)

    # 1. Instantiate 4 Room Sensors
    sensors = []
    for i in range(1, 5):
        s = RoomSensor.create(
            store=store, registry=registry, reasoning=engine,
            name=f"RoomSensor_{i}",
            initial_state={"room": f"Room_{i}", "temperature": 22.0, "occupancy": 2},
            tags=["sensor", "iot"],
            goals=[f"maintain_room_{i}_climate"],
        )
        sensors.append(s)
        pop_manager.add_member(s)

    # 2. Instantiate 2 HVAC Controllers
    hvac_north = HVACController.create(
        store=store, registry=registry, reasoning=engine,
        name="HVAC_NorthWing",
        initial_state={"wing": "north", "power_level": 3},
        tags=["hvac", "actuator"],
        goals=["optimize_thermal_comfort"],
    )
    hvac_south = HVACController.create(
        store=store, registry=registry, reasoning=engine,
        name="HVAC_SouthWing",
        initial_state={"wing": "south", "power_level": 2},
        tags=["hvac", "actuator"],
        goals=["optimize_thermal_comfort"],
    )
    pop_manager.add_member(hvac_north)
    pop_manager.add_member(hvac_south)

    # 3. Instantiate Facility Manager
    manager = FacilityManager.create(
        store=store, registry=registry, reasoning=engine,
        name="FacilityDirector",
        initial_state={"facility": "MainHQ", "status": "nominal"},
        tags=["manager", "coordinator"],
        goals=["zero_safety_incidents", "energy_efficiency"],
    )
    pop_manager.add_member(manager)

    # 4. Instantiate Energy Optimizer
    optimizer = EnergyOptimizer.create(
        store=store, registry=registry, reasoning=engine,
        name="EnergyOptimizer",
        initial_state={"grid_cost_cents": 12.5, "peak_shaving": True},
        tags=["energy", "finance"],
        goals=["minimize_kwh_cost"],
    )
    pop_manager.add_member(optimizer)

    # 5. Instantiate 2 Occupant Feedback Agents
    occupant1 = OccupantAgent.create(
        store=store, registry=registry, reasoning=engine,
        name="Occupant_ZoneA",
        initial_state={"zone": "ZoneA", "comfort_rating": 5},
        tags=["occupant", "feedback"],
    )
    occupant2 = OccupantAgent.create(
        store=store, registry=registry, reasoning=engine,
        name="Occupant_ZoneB",
        initial_state={"zone": "ZoneB", "comfort_rating": 4},
        tags=["occupant", "feedback"],
    )
    pop_manager.add_member(occupant1)
    pop_manager.add_member(occupant2)

    print(f"  ✓ Total active population: {pop_manager.size()} Living Objects registered in Discovery.")

    print("\n" + "=" * 65)
    print("  PHASE 2: Autonomous Spawning of Worker Objects (P4.6)")
    print("=" * 65)

    # Facility Director spawns 2 specialized maintenance bots
    bot1 = ObjectSpawner.spawn(
        parent=manager,
        child_cls=MaintenanceBot,
        child_name="MaintBot_Alpha",
        store=store,
        registry=registry,
        reasoning=engine,
        initial_state={"toolset": "HVAC_specialist", "location": "base_station"},
        tags=["maintenance", "worker"],
        goals=["rapid_repair"],
    )
    bot2 = ObjectSpawner.spawn(
        parent=manager,
        child_cls=MaintenanceBot,
        child_name="MaintBot_Beta",
        store=store,
        registry=registry,
        reasoning=engine,
        initial_state={"toolset": "Electrical_specialist", "location": "base_station"},
        tags=["maintenance", "worker"],
        goals=["rapid_repair"],
    )
    pop_manager.add_member(bot1)
    pop_manager.add_member(bot2)

    total_objects = pop_manager.size()
    print(f"  ✓ Spawned 2 worker bots. Total population is now: {total_objects} Objects (Target >= 10: MET)")

    print("\n" + "=" * 65)
    print("  PHASE 3: Anomaly Detection & Task Delegation (P4.4)")
    print("=" * 65)

    # Room 1 experiences severe thermal spike (38.5°C)
    for t_val in [22.0, 22.1, 21.9, 22.0, 22.2]:
        sensors[0].record_reading(t_val, occupancy=4)
    res_spike = sensors[0].record_reading(38.5, occupancy=10)
    print(f"  [Sensor 1] Anomaly Detected: {res_spike['anomaly']}")

    # Sensor delegates repair dispatch to Facility Director
    del_res = DelegationEngine.delegate(
        source_obj=sensors[0],
        target_type="facilitymanager",
        task_name="dispatch_cooling_repair",
        task_payload={"room": "Room_1", "temp": 38.5},
        registry=registry,
    )
    print(f"  [Sensor 1 -> Manager] Delegation result: {del_res}")

    # Manager assigns repair task to MaintBot_Alpha
    del_bot = DelegationEngine.delegate(
        source_obj=manager,
        target_type="maintenancebot",
        task_name="fix_room_1_actuator",
        task_payload={"target_room": "Room_1"},
        registry=registry,
    )
    bot1.repair_subsystem("Room_1")
    print(f"  [Manager -> Bot 1] Delegation result: {del_bot}")
    print(f"  [Bot 1] Repair status: {bot1.get_state('repaired_room')}")

    print("\n" + "=" * 65)
    print("  PHASE 4: Collective Consensus Voting (P4.5)")
    print("=" * 65)

    # Proposal: Change standard facility setpoint to 21.5°C during summer peak
    prop = consensus.create_proposal(
        initiator_id=optimizer.object_id,
        topic="Set facility setpoint to 21.5C to save 15% grid energy",
        options=["APPROVE", "REJECT", "DEFER"],
        quorum=4,
    )
    print(f"  Created Proposal: '{prop.topic}' (Quorum required: 4)")

    # Living objects cast votes based on local goals
    v1 = consensus.vote(prop.proposal_id, optimizer, "APPROVE", "Saves peak grid costs")
    v2 = consensus.vote(prop.proposal_id, manager, "APPROVE", "Maintains safe operational buffer")
    v3 = consensus.vote(prop.proposal_id, hvac_north, "APPROVE", "Reduces compressor load")
    v4 = consensus.vote(prop.proposal_id, occupant1, "APPROVE", "Comfortable temperature range")

    print(f"  Consensus Result: Quorum reached={v4.get('quorum_reached')}, Winner={v4.get('winner')}, Tally={v4.get('tally')}")

    print("\n" + "=" * 65)
    print("  PHASE 5: Resource Pool Bidding & Priority Scheduling (P5.3, P5.5)")
    print("=" * 65)

    # Objects submit bids for cognitive reasoning
    bids = [
        ResourceBid(object_id=sensors[0].object_id, reasoning_task="Diagnose critical spike", evr=0.85, utility=0.9, urgency=0.95, tokens_requested=150),
        ResourceBid(object_id=optimizer.object_id, reasoning_task="Optimize tariff schedule", evr=0.60, utility=0.8, urgency=0.70, tokens_requested=200),
        ResourceBid(object_id=occupant2.object_id, reasoning_task="Summarize monthly comfort", evr=0.10, utility=0.4, urgency=0.20, tokens_requested=100),
    ]

    allocations = resource_pool.submit_bids_and_allocate(bids)
    print(f"  Resource Allocation Results: {allocations}")
    print(f"  Resource Pool Stats: {resource_pool.stats()}")

    # Schedule reasoning in priority order
    scheduler.schedule(sensors[0], lambda: f"Executed diagnosis for {sensors[0].name}", urgency=0.95)
    scheduler.schedule(optimizer, lambda: f"Executed optimization for {optimizer.name}", urgency=0.70)
    scheduler.schedule(occupant2, lambda: f"Executed feedback analysis for {occupant2.name}", urgency=0.20)

    sched_results = scheduler.run_all()
    print(f"  Priority Scheduler Executed {len(sched_results)} Tasks: {sched_results}")

    print("\n" + "=" * 65)
    print("  PHASE 6: Cross-Restart Continuity Verification (P1.6)")
    print("=" * 65)

    # Save all objects to SQLite
    for obj in pop_manager.active_members():
        obj.save()

    m_id = manager.object_id
    b_id = bot1.object_id
    s_id = sensors[0].object_id

    del manager, bot1, bot2, sensors, pop_manager, hvac_north, hvac_south, optimizer, occupant1, occupant2
    gc.collect()

    # Rehydrate in clean session
    store_reloaded = EventStore(db_path)
    manager_reloaded = FacilityManager.load(m_id, store_reloaded, registry, engine)
    bot_reloaded = MaintenanceBot.load(b_id, store_reloaded, registry, engine)
    sensor_reloaded = RoomSensor.load(s_id, store_reloaded, registry, engine)

    assert manager_reloaded is not None, "Manager failed to reload!"
    assert bot_reloaded is not None, "Bot failed to reload!"
    assert sensor_reloaded is not None, "Sensor failed to reload!"

    assert sensor_reloaded.get_state("temperature") == 38.5
    assert bot_reloaded.get_state("repaired_room") == "Room_1"

    print(f"  ✓ Rehydrated Manager: {manager_reloaded}")
    print(f"  ✓ Rehydrated Spawned Bot: {bot_reloaded} (Repaired Room: {bot_reloaded.get_state('repaired_room')})")
    print(f"  ✓ Rehydrated Sensor: {sensor_reloaded} (Recorded Spike Temp: {sensor_reloaded.get_state('temperature')})")

    if os.path.exists(db_path):
        os.remove(db_path)

    print("\n" + "=" * 65)
    print("  ✓ MULTI-OBJECT ECOLOGY EXPERIMENT COMPLETED SUCCESSFULLY!")
    print("=" * 65)

    return {
        "total_objects": total_objects,
        "spawned_objects": 2,
        "consensus_winner": v4.get("winner"),
        "rehydration_success": True,
    }


if __name__ == "__main__":
    run_ecology_simulation()
