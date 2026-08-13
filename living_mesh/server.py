"""
Living Mesh HTTP Server & Real-Time Mission Control API
========================================================

Zero-dependency standard library HTTP server providing:
  - Static file delivery for Mission Control UI
  - Real-time JSON snapshot API
  - Interactive chaos injection endpoints
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from living_mesh.mesh import LivingMesh

PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
DB_FILE = os.path.join(os.path.dirname(__file__), "_mesh_live.db")

# Singleton mesh instance for server
_mesh: Optional[LivingMesh] = None


def get_mesh() -> LivingMesh:
    global _mesh
    if _mesh is None:
        _mesh = LivingMesh(db_path=DB_FILE)
        _mesh.bootstrap()
    return _mesh


class LivingMeshHandler(SimpleHTTPRequestHandler):
    """Handles web requests and API endpoints for Living Mesh."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        # Silence default request logging
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/snapshot":
            mesh = get_mesh()
            snapshot = mesh.get_snapshot()
            self._send_json(snapshot)
        elif parsed.path == "/api/tick":
            mesh = get_mesh()
            stats = mesh.tick()
            self._send_json({"status": "ticked", "stats": stats})
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        mesh = get_mesh()

        if parsed.path == "/api/chaos/db":
            evt = mesh.chaos.inject_db_latency_spike(mesh.db_node, slow_query_latency_ms=280.0)
            mesh.log_event("chaos_db_spike", f"Injected 280ms query latency spike. Auto-healed: {evt.healing_detected}", evt.injected_payload)
            self._send_json({"success": True, "event": evt.__dict__})

        elif parsed.path == "/api/chaos/service":
            evt = mesh.chaos.inject_service_failure(mesh.api_gateway, failed_requests=50, total_requests=100)
            mesh.log_event("chaos_service_failure", f"Injected 50% service outage. Circuit breaker: {evt.healing_detected}", evt.injected_payload)
            self._send_json({"success": True, "event": evt.__dict__})

        elif parsed.path == "/api/chaos/security":
            evt = mesh.chaos.inject_security_intrusion(mesh.sentinel, attacker_ip="198.51.100.99", failed_auths=75)
            mesh.log_event("chaos_security_attack", f"Injected brute-force attack from 198.51.100.99. Quarantined: {evt.healing_detected}", evt.injected_payload)
            self._send_json({"success": True, "event": evt.__dict__})

        elif parsed.path == "/api/chaos/market":
            evt = mesh.chaos.inject_market_shock(mesh.portfolio, shock_volatility=0.88)
            mesh.log_event("chaos_market_shock", f"Injected market volatility shock (0.88). Rebalanced: {evt.healing_detected}", evt.injected_payload)
            self._send_json({"success": True, "event": evt.__dict__})

        elif parsed.path == "/api/chaos/crash":
            res = mesh.crash_and_rehydrate()
            self._send_json({"success": True, "rehydrated": res})

        elif parsed.path == "/api/consensus/trigger":
            # Initiate emergency consensus
            prop = mesh.consensus.create_proposal(
                initiator_id=mesh.commander.object_id,
                topic="Approve emergency load-shedding policy",
                options=["APPROVE", "REJECT"],
                quorum=3,
            )
            v1 = mesh.consensus.vote(prop.proposal_id, mesh.commander, "APPROVE", "Preserves system integrity")
            v2 = mesh.consensus.vote(prop.proposal_id, mesh.api_gateway, "APPROVE", "Reduces ingress pressure")
            v3 = mesh.consensus.vote(prop.proposal_id, mesh.db_node, "APPROVE", "Safeguards database locks")
            mesh.log_event("consensus_completed", f"Quorum reached on proposal '{prop.topic}'. Winner: {v3.get('winner')}")
            self._send_json({"success": True, "winner": v3.get("winner"), "proposal_id": prop.proposal_id})

        elif parsed.path == "/api/spawn/investigator":
            bot = mesh.commander.spawn_investigator(
                bot_name=f"ForensicsBot_{int(time.time())%1000}",
                target_node_id=mesh.db_node.object_id,
                symptom="latency_anomaly",
                store=mesh.store,
                registry=mesh.registry,
                reasoning=mesh.engine,
            )
            mesh.pop_manager.add_member(bot)
            mesh.log_event("bot_spawned", f"Commander spawned child worker '{bot.name}' (ID: {bot.object_id[:8]})")
            self._send_json({"success": True, "bot_id": bot.object_id, "bot_name": bot.name})

        else:
            self.send_error(404, "Unknown endpoint")

    def _send_json(self, data: Any):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def start_server(port: int = PORT, background: bool = False):
    mesh = get_mesh()
    server = HTTPServer(("0.0.0.0", port), LivingMeshHandler)
    print(f"🚀 Living Mesh Mission Control running at http://localhost:{port}")
    if background:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server
    else:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Living Mesh server.")
            server.server_close()


if __name__ == "__main__":
    start_server(PORT)
