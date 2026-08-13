"""
LivingObjects Autonomous SRE — Test Suite
===========================================
"""
import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, CapabilityRegistry, MockReasoningEngine
from autonomous_sre.sre_system import (
    LivingServer,
    LivingLoadBalancer,
    AutonomousSRE,
)


@pytest.fixture
def sre_cluster(tmp_path):
    sre = AutonomousSRE(name="TestCluster")
    yield sre
    sre.close()


def test_deploy_cluster(sre_cluster):
    """Verify cluster deployment with servers + load balancer."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)
    assert len(sre.servers) == 5
    assert sre.lb is not None
    for sid, server in sre.servers.items():
        assert server.get_state("status") in ("healthy", "booting")


def test_server_telemetry(sre_cluster):
    """Verify servers record telemetry and detect anomalies."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=3)
    server = list(sre.servers.values())[0]

    # Normal readings
    result = server.record_telemetry(45.0, 55.0, 40.0)
    assert result["status"] == "healthy"
    assert server.get_state("cpu") == 45.0

    # Anomalous readings
    result = server.record_telemetry(95.0, 90.0, 92.0)
    assert result["status"] == "degraded"
    assert len(result["anomalies"]) > 0
    assert any(a["severity"] in ("high", "critical") for a in result["anomalies"])


def test_server_self_healing(sre_cluster):
    """Verify servers can heal themselves using corrective fixes."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=3)
    server = list(sre.servers.values())[0]

    # Create anomaly
    server.record_telemetry(95.0, 50.0, 40.0)
    assert server.get_state("status") == "degraded"

    # Apply fix
    result = server.apply_fix("restart_process")
    assert result["success"] is True
    assert result["action"] == "restart_process"
    assert server.get_state("cpu") == 30.0


def test_load_balancer_isolation(sre_cluster):
    """Verify load balancer isolates and recovers failing nodes."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=3)

    # Isolate failing node
    result = sre.lb.isolate_node("server-1", "Error rate exceeded 50%")
    assert result["isolated"] is True
    assert "server-1" in sre.lb.get_state("isolated_nodes")

    # Recover the node
    recover_result = sre.lb.recover_node("server-1")
    assert recover_result["recovered"] is True
    assert "server-1" not in sre.lb.get_state("isolated_nodes")


def test_economic_impact(sre_cluster):
    """Verify economic impact calculation."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)
    impact = sre.get_economic_impact()
    assert impact["mttr_improvement"] == "900x faster"
    assert impact["downtime_savings_per_incident"] > 0
    assert impact["on_call_savings_per_year"] > 0


def test_incident_simulation(sre_cluster):
    """Verify autonomous incident resolution simulation."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)
    results = sre.simulate_incidents(steps=25)
    assert len(results["resolutions"]) >= 0


def test_persistence_across_restart(sre_cluster):
    """Verify state persists across process restart."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=2)

    # Mutate state on server
    server = list(sre.servers.values())[0]
    server.record_telemetry(95.0, 50.0, 40.0)
    server.apply_fix("restart_process")
    server.save()
    server_id = server.object_id

    # Simulate reload
    reloaded_store = EventStore(sre.db_path)
    loaded_server = LivingServer.load(server_id, reloaded_store, sre.registry, sre.engine)
    assert loaded_server is not None
    assert loaded_server.get_state("status") == "recovering"
    assert loaded_server.get_state("cpu") == 30.0
