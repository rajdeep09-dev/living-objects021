"""
LivingObjects Autonomous SRE — Test Suite
===========================================
"""
import os, sys, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, CapabilityRegistry, MockReasoningEngine
from prototypes.agy.p1_enhanced.agy_living_object import AGYLivingObject
from autonomous_sre.sre_system import (
    LivingServer, LivingLoadBalancer, LivingIncidentCommander, AutonomousSRE
)


@pytest.fixture
def sre_cluster(tmp_path):
    sre = AutonomousSRE(name="TestCluster")
    # db_path is auto-generated in __init__ via tempfile
    yield sre
    # Cleanup
    if os.path.exists(sre.db_path):
        os.remove(sre.db_path)
    import shutil
    db_dir = os.path.dirname(sre.db_path)
    if os.path.exists(db_dir):
        shutil.rmtree(db_dir, ignore_errors=True)


def test_deploy_cluster(sre_cluster):
    """Verify cluster deployment with 5 servers + LB + commander."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)
    assert len(sre.servers) == 5
    assert sre.commander is not None
    assert sre.lb is not None
    # All servers should be booting/healthy
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
    assert result["telemetry"]["cpu"] == 45.0

    # Anomalous readings
    result = server.record_telemetry(95.0, 90.0, 92.0)
    assert result["status"] == "degraded"
    assert len(result["anomalies"]) > 0
    assert any(a["severity"] in ("high", "critical") for a in result["anomalies"])


def test_server_self_healing(sre_cluster):
    """Verify servers can diagnose and heal themselves."""
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
    assert server.get_state("cpu") == 30.0  # recovered


def test_incident_commander(sre_cluster):
    """Verify commander creates incidents and spawns investigators."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=3)

    # Create incident
    incident = sre.commander.create_incident("critical", "Server-001 unresponsive")
    assert incident["severity"] == "critical"
    assert incident["status"] == "investigating"

    # Spawn investigator
    server_ids = list(sre.servers.keys())
    bot = sre.commander.spawn_investigator("Server-001", "unresponsive")
    assert bot is not None
    assert bot.get_state("symptom") == "unresponsive"


def test_cascading_failure_simulation(sre_cluster):
    """Verify cascading failure and recovery."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)

    # Simulate cascading failure
    import random
    rng = random.Random(99)
    server_ids = list(sre.servers.keys())
    crashed = rng.sample(server_ids, 3)
    for cid in crashed:
        s = sre.servers[cid]
        s.set_state("status", "crashed")
        s.set_state("cpu", 0.0)

    # Run simulation
    results = sre.simulate_tea_time(steps=10)
    assert results is not None


def test_economic_impact(sre_cluster):
    """Verify economic impact calculation."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)
    impact = sre.get_economic_impact()
    assert impact["mttr_improvement"] == "900x faster"  # 45min / 30sec
    assert impact["downtime_savings_per_incident"] > 0
    assert impact["on_call_savings_per_year"] > 0


def test_load_balancer_isolation(sre_cluster):
    """Verify load balancer isolates failing nodes."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=3)

    # Simulate high error rate on one server
    result = sre.lb.detect_failure("server-1", 0.50)  # 50% error rate
    assert result["isolated"] is True

    # Recover the node
    recover_result = sre.lb.recover_node("server-1")
    assert recover_result["recovered"] is True


def test_full_simulation(sre_cluster):
    """Run full demo simulation."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=5)
    results = sre.run_incident_simulation()
    assert results["servers"] == 5
    assert results["auto_resolved"] > 0


def test_persistence_across_restart(sre_cluster):
    """Verify state persists across process restart."""
    sre = sre_cluster
    sre.deploy_cluster(num_servers=2)

    # Create state
    server = list(sre.servers.values())[0]
    server.record_telemetry(95.0, 50.0, 40.0)
    server.apply_fix("restart_process")
    server.save()
    server_id = server.object_id

    # "Restart" - create new SRE, reload
    sre2 = AutonomousSRE(name="Restart")
    sre2.store = EventStore(sre.db_path)
    sre2.registry = sre.registry
    sre2.engine = MockReasoningEngine()
    sre2.servers = {}

    for sid, s in sre.servers.items():
        loaded = LivingServer.load(sid, sre2.store, sre2.registry, sre2.engine)
        if loaded:
            sre2.servers[sid] = loaded

    # Verify state survived
    assert sre2.servers[list(sre.servers.keys())[0]].get_state("status") == "recovering"
