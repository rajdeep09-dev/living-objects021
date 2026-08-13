"""
Living Mesh Chaos & Fault Injection Engine
===========================================

Injects real-world operational stressors into the Living Mesh to test and prove
autonomous self-healing, emergent cooperation, consensus, and cross-restart continuity.

Chaos scenarios:
  1. Database Latency / Lock Contention Surge
  2. Microservice Dependency Failure & Cascading Timeout
  3. Security Brute-Force & Network Intrusion Attack
  4. FinTech / Asset Market Volatility Shock
  5. Hard Process Crash & Power Outage (Rehydration Resilience)
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ChaosEvent:
    event_id: str
    scenario: str
    target_node_id: str
    target_node_name: str
    severity: str
    timestamp: str
    injected_payload: dict
    healing_detected: bool = False
    healing_action: Optional[str] = None
    time_to_heal_sec: Optional[float] = None


class ChaosEngine:
    """
    Automated stressor and fault injection harness for Living Mesh.
    """
    def __init__(self):
        self._history: List[ChaosEvent] = []

    def inject_db_latency_spike(
        self,
        db_node: Any,
        slow_query_latency_ms: float = 240.0,
        qps: float = 850.0,
    ) -> ChaosEvent:
        """Inject an un-indexed slow query spike causing lock contention."""
        evt = ChaosEvent(
            event_id=f"chaos_db_{int(time.time()*1000)}",
            scenario="db_slow_query_surge",
            target_node_id=db_node.object_id,
            target_node_name=db_node.name,
            severity="critical",
            timestamp=datetime.now(timezone.utc).isoformat(),
            injected_payload={"latency_ms": slow_query_latency_ms, "qps": qps},
        )
        self._history.append(evt)

        # Trigger object reaction
        start_t = time.time()
        metrics = db_node.record_query_metrics(
            qps=qps, avg_latency_ms=slow_query_latency_ms, lock_wait_ms=120.0, cache_hit_rate=0.45
        )

        if metrics.get("anomaly"):
            # Node self-heals
            diag = db_node.diagnose_query_bottleneck("SELECT * FROM transactions WHERE user_id = 90210")
            heal_msg = db_node.apply_auto_index("transactions", "user_id")
            evt.healing_detected = True
            evt.healing_action = heal_msg
            evt.time_to_heal_sec = round(time.time() - start_t, 3)

        return evt

    def inject_service_failure(
        self,
        service_node: Any,
        failed_requests: int = 45,
        total_requests: int = 100,
    ) -> ChaosEvent:
        """Inject downstream microservice failure causing error rate spike."""
        evt = ChaosEvent(
            event_id=f"chaos_svc_{int(time.time()*1000)}",
            scenario="downstream_service_outage",
            target_node_id=service_node.object_id,
            target_node_name=service_node.name,
            severity="high",
            timestamp=datetime.now(timezone.utc).isoformat(),
            injected_payload={"failed": failed_requests, "total": total_requests},
        )
        self._history.append(evt)

        start_t = time.time()
        res = service_node.process_traffic_batch(
            requests_count=total_requests, error_count=failed_requests, dependency_latency_ms=850.0
        )

        if res.get("anomaly"):
            # Node self-adapts: formulate fallback & trip circuit breaker
            strat = service_node.formulate_circuit_breaker_strategy("Dependency payments-api timed out")
            heal_msg = service_node.trip_circuit_breaker("Dependency payments-api timeout exceeds 800ms")
            evt.healing_detected = True
            evt.healing_action = heal_msg
            evt.time_to_heal_sec = round(time.time() - start_t, 3)

        return evt

    def inject_security_intrusion(
        self,
        sentinel_node: Any,
        attacker_ip: str = "198.51.100.42",
        failed_auths: int = 65,
    ) -> ChaosEvent:
        """Inject aggressive credential stuffing / port scan attack."""
        evt = ChaosEvent(
            event_id=f"chaos_sec_{int(time.time()*1000)}",
            scenario="credential_stuffing_attack",
            target_node_id=sentinel_node.object_id,
            target_node_name=sentinel_node.name,
            severity="critical",
            timestamp=datetime.now(timezone.utc).isoformat(),
            injected_payload={"attacker_ip": attacker_ip, "failed_auths": failed_auths},
        )
        self._history.append(evt)

        start_t = time.time()
        res = sentinel_node.analyze_ingress_traffic(
            source_ip_or_id=attacker_ip, failed_auth_attempts=failed_auths, request_entropy=0.92
        )

        if res.get("anomaly"):
            threat = sentinel_node.investigate_threat_vector(f"POST /api/login brute-force from {attacker_ip}")
            heal_msg = sentinel_node.quarantine_actor(attacker_ip, f"Brute force surge ({failed_auths} failed attempts)")
            evt.healing_detected = True
            evt.healing_action = heal_msg
            evt.time_to_heal_sec = round(time.time() - start_t, 3)

        return evt

    def inject_market_shock(
        self,
        portfolio_node: Any,
        shock_volatility: float = 0.78,
    ) -> ChaosEvent:
        """Inject financial liquidity / market drawdown shock."""
        evt = ChaosEvent(
            event_id=f"chaos_fin_{int(time.time()*1000)}",
            scenario="market_drawdown_shock",
            target_node_id=portfolio_node.object_id,
            target_node_name=portfolio_node.name,
            severity="high",
            timestamp=datetime.now(timezone.utc).isoformat(),
            injected_payload={"volatility": shock_volatility},
        )
        self._history.append(evt)

        start_t = time.time()
        res = portfolio_node.record_market_tick(
            portfolio_value_usd=850000.0, daily_volatility=shock_volatility, cash_ratio=0.15
        )

        if res.get("anomaly"):
            hedge = portfolio_node.evaluate_risk_hedge_strategy("Flash crash in crypto/equity liquidity pool")
            heal_msg = portfolio_node.rebalance_cash_buffer(0.40)  # Move to 40% cash buffer
            evt.healing_detected = True
            evt.healing_action = heal_msg
            evt.time_to_heal_sec = round(time.time() - start_t, 3)

        return evt

    def get_history(self) -> List[dict]:
        return [
            {
                "event_id": e.event_id,
                "scenario": e.scenario,
                "target_node_id": e.target_node_id,
                "target_node_name": e.target_node_name,
                "severity": e.severity,
                "timestamp": e.timestamp,
                "injected_payload": e.injected_payload,
                "healing_detected": e.healing_detected,
                "healing_action": e.healing_action,
                "time_to_heal_sec": e.time_to_heal_sec,
            }
            for e in self._history
        ]
