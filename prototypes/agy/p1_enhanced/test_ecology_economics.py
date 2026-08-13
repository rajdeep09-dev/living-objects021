"""
Tests for AGY Ecology & Economics (P2.11, P4.4, P4.5, P4.6, P4.7, P5.3, P5.4, P5.5)
"""
import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    TieredReasoningEngine,
)
from prototypes.agy.p1_enhanced.agy_ecology_economics import (
    ConsensusEngine,
    DelegationEngine,
    GlobalResourcePool,
    Goal,
    GoalDirectedMixin,
    ObjectSpawner,
    PopulationManager,
    ResourceBid,
    UtilityPriorityScheduler,
)


from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    ObjectDiscoveryRegistry,
    TieredReasoningEngine,
)


class MockGoalObject(GoalDirectedMixin, AGYLivingObject):
    pass


@pytest.fixture
def runtime(tmp_path):
    ObjectDiscoveryRegistry.clear()
    store = EventStore(str(tmp_path / "eco_test.db"))
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine()
    yield store, registry, engine
    ObjectDiscoveryRegistry.clear()


def test_goal_directed_reasoning(runtime):
    """P2.11: Test autonomous goal addition, progress evaluation, and planning."""
    store, registry, engine = runtime
    obj = MockGoalObject.create(store, registry, engine, name="GoalSeeker", initial_state={"efficiency": 50.0})

    goal = obj.add_goal(
        description="Reach 90% efficiency",
        target_metric="efficiency",
        target_value=90.0,
        priority=1.0,
    )
    assert goal.status == "active"

    # Pursue goal when not reached
    actions = obj.pursue_goals()
    assert len(actions) == 1
    assert actions[0]["status"] == "active"

    # Update state to reach goal
    obj.set_state("efficiency", 90.0)
    actions2 = obj.pursue_goals()
    assert actions2[0]["action"] == "completed"
    assert goal.status == "achieved"


def test_task_delegation(runtime):
    """P4.4: Test task delegation and capability auto-provisioning."""
    store, registry, engine = runtime
    mgr = AGYLivingObject.create(store, registry, engine, name="Manager", tags=["manager"])
    worker = AGYLivingObject.create(store, registry, engine, name="Worker", tags=["worker"])

    res = DelegationEngine.delegate(
        source_obj=mgr,
        target_type="worker",
        task_name="process_batch",
        task_payload={"batch_id": 42},
        registry=registry,
    )
    assert res["success"] is True
    assert res["target_id"] == worker.object_id


def test_consensus_engine(runtime):
    """P4.5: Test collective consensus proposal, voting, and quorum tallying."""
    store, registry, engine = runtime
    consensus = ConsensusEngine()

    a = AGYLivingObject.create(store, registry, engine, name="AgentA")
    b = AGYLivingObject.create(store, registry, engine, name="AgentB")
    c = AGYLivingObject.create(store, registry, engine, name="AgentC")

    prop = consensus.create_proposal(
        initiator_id=a.object_id,
        topic="Switch cooling mode to eco-mode",
        options=["YES", "NO"],
        quorum=3,
    )

    v1 = consensus.vote(prop.proposal_id, a, "YES", "Save power")
    assert v1["quorum_reached"] is False

    v2 = consensus.vote(prop.proposal_id, b, "YES", "Good temperature margins")
    assert v2["quorum_reached"] is False

    v3 = consensus.vote(prop.proposal_id, c, "YES", "Confirmed")
    assert v3["quorum_reached"] is True
    assert v3["winner"] == "YES"
    assert v3["tally"]["YES"] == 3


def test_object_spawning_and_lineage(runtime):
    """P4.6: Test parent object spawning child object with lineage & capabilities."""
    store, registry, engine = runtime
    parent = AGYLivingObject.create(store, registry, engine, name="ParentOrg")

    child = ObjectSpawner.spawn(
        parent=parent,
        child_cls=AGYLivingObject,
        child_name="ChildUnit",
        store=store,
        registry=registry,
        reasoning=engine,
        initial_state={"role": "assistant"},
    )

    assert child.get_state("_parent_id") == parent.object_id
    assert parent.object_id in child.get_state("_lineage")
    assert registry.check(parent.object_id, child.object_id, "control")
    assert registry.check(child.object_id, parent.object_id, "report")


def test_population_manager_and_auto_retire(runtime):
    """P4.7 & P5.4: Test population stepping, cloning, and auto-retirement."""
    store, registry, engine = runtime
    pop = PopulationManager(store, registry, engine)

    obj1 = AGYLivingObject.create(store, registry, engine, name="ActiveUnit", initial_state={"val": 1})
    obj2 = AGYLivingObject.create(store, registry, engine, name="IdleUnit", initial_state={"val": 2})
    pop.add_member(obj1)
    pop.add_member(obj2)

    assert pop.size() == 2

    # Clone obj1
    clone = pop.clone_with_mutation(obj1.object_id, "ActiveUnit_V2", {"val": 10})
    assert clone is not None
    assert clone.get_state("val") == 10
    assert clone.get_state("_cloned_from") == obj1.object_id
    assert pop.size() == 3

    # Force obj2 into low utility and idle
    obj2.idle_steps = 10
    obj2.actions_taken = 0
    obj2.prediction_errors = [1.0, 1.0, 1.0]

    retired = pop.cull_low_utility(threshold=0.25)
    assert obj2.object_id in retired
    assert not obj2.is_alive
    assert pop.size() == 2


def test_global_resource_pool_bidding(runtime):
    """P5.3: Test compute budget allocation based on EVR * Utility * Urgency."""
    pool = GlobalResourcePool(total_daily_tokens=300)

    bid_high = ResourceBid(object_id="obj_critical", reasoning_task="Fatal anomaly", evr=0.9, utility=0.9, urgency=1.0, tokens_requested=150)
    bid_med = ResourceBid(object_id="obj_routine", reasoning_task="Routine check", evr=0.5, utility=0.5, urgency=0.5, tokens_requested=100)
    bid_low = ResourceBid(object_id="obj_idle", reasoning_task="Background summarize", evr=0.1, utility=0.1, urgency=0.1, tokens_requested=100)

    allocations = pool.submit_bids_and_allocate([bid_low, bid_high, bid_med])
    assert allocations["obj_critical"] is True
    assert allocations["obj_routine"] is True
    assert allocations["obj_idle"] is False  # Exhausted 250 of 300 tokens

    stats = pool.stats()
    assert stats["remaining"] == 50
    assert stats["allocated_by_object"]["obj_critical"] == 150


def test_utility_priority_scheduler(runtime):
    """P5.5: Test priority execution queue ordered by utility * urgency."""
    store, registry, engine = runtime
    scheduler = UtilityPriorityScheduler()

    high_obj = AGYLivingObject.create(store, registry, engine, name="HighPri")
    high_obj.actions_taken = 10

    low_obj = AGYLivingObject.create(store, registry, engine, name="LowPri")
    low_obj.idle_steps = 5

    execution_order = []
    scheduler.schedule(low_obj, lambda: execution_order.append("low"), urgency=0.1)
    scheduler.schedule(high_obj, lambda: execution_order.append("high"), urgency=1.0)

    scheduler.run_all()
    assert execution_order == ["high", "low"]
