"""
Living Mesh Interactive Terminal Mission Control
=================================================

Interactive command-line cockpit to inspect, stress-test, and interact with
Living Objects in real time.

Usage:
    python -m living_mesh.cli
"""
from __future__ import annotations

import os
import sys
import time

from living_mesh.mesh import LivingMesh


def print_banner():
    banner = r"""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║   ██╗     ██╗██╗   ██╗██╗███╗   ██╗ ██████╗ ███╗   ███╗███████╗███████╗  ║
  ║   ██║     ██║██║   ██║██║████╗  ██║██╔════╝ ████╗ ████║██╔════╝██╔════╝  ║
  ║   ██║     ██║██║   ██║██║██╔██╗ ██║██║  ███╗██╔████╔██║█████╗  ███████╗  ║
  ║   ██║     ██║╚██╗ ██╔╝██║██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══╝  ╚════██║  ║
  ║   ███████╗██║ ╚████╔╝ ██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║███████╗███████║  ║
  ║   ╚══════╝╚═╝  ╚═══╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚══════╝  ║
  ║             AUTONOMOUS INTELLIGENCE OPERATING SYSTEM                 ║
  ╚═══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def render_dashboard(mesh: LivingMesh):
    snap = mesh.get_snapshot()
    print("\n" + "─" * 75)
    print(f"  Step: {snap['step']}  |  Population: {snap['population_size']} Nodes  |  Pool Tokens: {snap['resource_pool']['remaining']}/{snap['resource_pool']['total_pool']}")
    print("─" * 75)

    print(f"  {'NODE NAME':<24} {'TYPE':<16} {'UTILITY':>8} {'STATUS':<12} {'ANOMALIES'}")
    print("  " + "─" * 71)

    for n in snap["nodes"]:
        status = "DORMANT" if n["is_dormant"] else ("ANOMALY" if (n["recent_anomaly"] and not n["recent_anomaly"]["resolved"]) else "HEALTHY")
        anom_str = f"{n['anomalies_count']} recorded"
        print(f"  {n['name']:<24} {n['type']:<16} {n['utility']:>8.3f} {status:<12} {anom_str}")

    print("\n  RECENT COGNITIVE LOGS:")
    for evt in snap["recent_events"][:4]:
        print(f"    [{evt['timestamp']}] [{evt['event_type'].upper()}] {evt['message']}")
    print("─" * 75)


def run_cli():
    db_file = os.path.join(os.path.dirname(__file__), "_mesh_cli.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    mesh = LivingMesh(db_path=db_file)
    mesh.bootstrap()

    print_banner()
    print("  Initialized Living Mesh with 5 core Thinking Nodes.")

    while True:
        render_dashboard(mesh)
        print("\n  INTERACTIVE COMMANDS:")
        print("    [1] ⚡ Inject Database Latency & Slow Query Surge")
        print("    [2] 🔌 Inject Microservice Dependency Failure")
        print("    [3] 🚨 Inject Security Brute-Force Intrusion")
        print("    [4] 📉 Inject Financial Liquidity Volatility Shock")
        print("    [5] 🗳️ Trigger Emergency Mesh Quorum Vote")
        print("    [6] 🤖 Commander Spawns Forensics Worker Bot")
        print("    [7] 💥 Simulate Sudden Hard Crash & Rehydrate from SQLite")
        print("    [8] ⏩ Step Simulation (Tick All Nodes)")
        print("    [q] Quit")

        try:
            choice = input("\n  Enter command > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            evt = mesh.chaos.inject_db_latency_spike(mesh.db_node)
            mesh.log_event("db_spike", f"Injected 240ms latency. Auto-healed: {evt.healing_detected} ({evt.healing_action})")
        elif choice == "2":
            evt = mesh.chaos.inject_service_failure(mesh.api_gateway)
            mesh.log_event("svc_failure", f"Injected 45% service error. Tripped breaker: {evt.healing_detected}")
        elif choice == "3":
            evt = mesh.chaos.inject_security_intrusion(mesh.sentinel)
            mesh.log_event("sec_intrusion", f"Injected brute force from 198.51.100.42. Quarantined: {evt.healing_detected}")
        elif choice == "4":
            evt = mesh.chaos.inject_market_shock(mesh.portfolio)
            mesh.log_event("market_shock", f"Injected 0.78 market volatility. Rebalanced: {evt.healing_detected}")
        elif choice == "5":
            prop = mesh.consensus.create_proposal(
                initiator_id=mesh.commander.object_id,
                topic="Emergency Mesh Resource Optimization Policy",
                options=["APPROVE", "REJECT"],
                quorum=3,
            )
            v1 = mesh.consensus.vote(prop.proposal_id, mesh.commander, "APPROVE", "Saves system bandwidth")
            v2 = mesh.consensus.vote(prop.proposal_id, mesh.api_gateway, "APPROVE", "Sheds excess traffic")
            v3 = mesh.consensus.vote(prop.proposal_id, mesh.db_node, "APPROVE", "Preserves locks")
            mesh.log_event("consensus", f"Consensus reached on '{prop.topic}'. Winner: {v3.get('winner')}")
        elif choice == "6":
            bot = mesh.commander.spawn_investigator(
                bot_name=f"ForensicsBot_{int(time.time())%1000}",
                target_node_id=mesh.db_node.object_id,
                symptom="latency_anomaly",
                store=mesh.store,
                registry=mesh.registry,
                reasoning=mesh.engine,
            )
            mesh.pop_manager.add_member(bot)
            mesh.log_event("spawned", f"Commander spawned child worker '{bot.name}' (ID: {bot.object_id[:8]})")
        elif choice == "7":
            res = mesh.crash_and_rehydrate()
            print(f"\n  💥 SIMULATED CRASH & REBOOT COMPLETE: {res['rehydrated_count']} Nodes rehydrated from SQLite.")
            time.sleep(1)
        elif choice == "8":
            mesh.tick()
        elif choice == "q":
            print("\n  Exiting Living Mesh. Goodbye!")
            break

    if os.path.exists(db_file):
        os.remove(db_file)


if __name__ == "__main__":
    run_cli()
