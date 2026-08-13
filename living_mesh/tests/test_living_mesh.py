"""
Unit and Integration Tests for Living Mesh
===========================================
"""
import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from living_mesh.mesh import LivingMesh
from living_mesh.chaos import ChaosEngine


@pytest.fixture
def mesh_instance(tmp_path):
    db_file = str(tmp_path / "mesh_test.db")
    mesh = LivingMesh(db_path=db_file)
    mesh.bootstrap()
    yield mesh


def test_mesh_bootstrap(mesh_instance):
    """Verify all 5 nodes are created and connected."""
    mesh = mesh_instance
    assert mesh.pop_manager.size() == 5
    assert mesh.db_node is not None
    assert mesh.api_gateway is not None
    assert mesh.sentinel is not None
    assert mesh.portfolio is not None
    assert mesh.commander is not None

    # Check mutual capabilities
    assert mesh.registry.check(mesh.db_node.object_id, mesh.api_gateway.object_id, "communicate")
    assert mesh.registry.check(mesh.commander.object_id, mesh.db_node.object_id, "delegate")


def test_database_self_healing(mesh_instance):
    """Verify LivingDatabase detects latency anomalies and applies auto-indexes."""
    mesh = mesh_instance
    evt = mesh.chaos.inject_db_latency_spike(mesh.db_node, slow_query_latency_ms=250.0)

    assert evt.healing_detected is True
    assert "idx_auto_transactions_user_id" in mesh.db_node.get_state("synthetic_indexes")
    assert mesh.db_node.get_state("avg_latency_ms") < 100.0


def test_service_circuit_breaker(mesh_instance):
    """Verify LivingService trips circuit breaker during dependency outage."""
    mesh = mesh_instance
    evt = mesh.chaos.inject_service_failure(mesh.api_gateway, failed_requests=60, total_requests=100)

    assert evt.healing_detected is True
    assert mesh.api_gateway.get_state("circuit_breaker_open") is True

    # Test circuit breaker reset
    msg = mesh.api_gateway.reset_circuit_breaker()
    assert "CLOSED" in msg
    assert mesh.api_gateway.get_state("circuit_breaker_open") is False


def test_sentinel_quarantine(mesh_instance):
    """Verify LivingSentinel detects attack and isolates rogue actor."""
    mesh = mesh_instance
    evt = mesh.chaos.inject_security_intrusion(mesh.sentinel, attacker_ip="192.0.2.1", failed_auths=80)

    assert evt.healing_detected is True
    assert "192.0.2.1" in mesh.sentinel.get_state("quarantined_sources")


def test_portfolio_rebalancing(mesh_instance):
    """Verify LivingPortfolio rebalances reserves during volatility shock."""
    mesh = mesh_instance
    evt = mesh.chaos.inject_market_shock(mesh.portfolio, shock_volatility=0.85)

    assert evt.healing_detected is True
    assert mesh.portfolio.get_state("cash_ratio") == 0.40


def test_commander_spawning(mesh_instance):
    """Verify LivingCommander spawns child worker bots with lineage."""
    mesh = mesh_instance
    bot = mesh.commander.spawn_investigator(
        bot_name="ForensicWorker_1",
        target_node_id=mesh.db_node.object_id,
        symptom="latency_anomaly",
        store=mesh.store,
        registry=mesh.registry,
        reasoning=mesh.engine,
    )
    mesh.pop_manager.add_member(bot)

    assert bot.get_state("_parent_id") == mesh.commander.object_id
    assert mesh.registry.check(mesh.commander.object_id, bot.object_id, "control")
    assert mesh.pop_manager.size() == 6


def test_mesh_consensus(mesh_instance):
    """Verify decentralized quorum consensus across living objects."""
    mesh = mesh_instance
    prop = mesh.consensus.create_proposal(
        initiator_id=mesh.commander.object_id,
        topic="Shed non-critical telemetry during traffic surge",
        options=["APPROVE", "REJECT"],
        quorum=3,
    )

    v1 = mesh.consensus.vote(prop.proposal_id, mesh.commander, "APPROVE", "Saves CPU")
    v2 = mesh.consensus.vote(prop.proposal_id, mesh.api_gateway, "APPROVE", "Reduces queue")
    v3 = mesh.consensus.vote(prop.proposal_id, mesh.db_node, "APPROVE", "Maintains lock margins")

    assert v3["quorum_reached"] is True
    assert v3["winner"] == "APPROVE"


def test_mesh_crash_and_rehydration(mesh_instance):
    """Verify the entire mesh survives a process crash with full memory fidelity."""
    mesh = mesh_instance

    # Apply some mutations
    mesh.db_node.apply_auto_index("users", "email")
    mesh.sentinel.quarantine_actor("10.0.0.99", "Suspicious port scan")
    mesh.save_all()

    # Trigger crash and rehydration
    res = mesh.crash_and_rehydrate()
    assert res["rehydrated_count"] == 5

    # Check state integrity
    assert "idx_auto_users_email" in mesh.db_node.get_state("synthetic_indexes")
    assert "10.0.0.99" in mesh.sentinel.get_state("quarantined_sources")


def test_mesh_snapshot(mesh_instance):
    """Verify snapshot generation for web UI and CLI."""
    mesh = mesh_instance
    snap = mesh.get_snapshot()

    assert snap["population_size"] == 5
    assert len(snap["nodes"]) == 5
    assert "resource_pool" in snap
    assert "recent_events" in snap
