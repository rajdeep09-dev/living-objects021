"""
Living Mesh Core Coordinator
============================

The unified runtime tying together thinking objects into an autonomous,
self-governing, self-healing mesh.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Type

from living_objects import CapabilityRegistry, EventStore
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    ObjectDiscoveryRegistry,
    TieredReasoningEngine,
)
from prototypes.agy.p1_enhanced.agy_ecology_economics import (
    ConsensusEngine,
    ConsensusProposal,
    DelegationEngine,
    GlobalResourcePool,
    PopulationManager,
    UtilityPriorityScheduler,
)
from living_mesh.chaos import ChaosEngine, ChaosEvent
from living_mesh.nodes import (
    AutoHealerBot,
    IncidentInvestigatorBot,
    LivingCommander,
    LivingDatabase,
    LivingPortfolio,
    LivingSentinel,
    LivingService,
)


class LivingMesh:
    """
    Autonomous Living Mesh Coordinator.
    """
    def __init__(self, db_path: str = "living_mesh.db"):
        self.db_path = db_path
        self.store = EventStore(db_path)
        self.registry = CapabilityRegistry()
        self.engine = TieredReasoningEngine()
        self.consensus = ConsensusEngine()
        self.resource_pool = GlobalResourcePool(total_daily_tokens=10000)
        self.scheduler = UtilityPriorityScheduler()
        self.pop_manager = PopulationManager(self.store, self.registry, self.engine)
        self.chaos = ChaosEngine()
        self._cognitive_events: List[dict] = []
        self._step_count: int = 0

        # Named node accessors
        self.db_node: Optional[LivingDatabase] = None
        self.api_gateway: Optional[LivingService] = None
        self.sentinel: Optional[LivingSentinel] = None
        self.portfolio: Optional[LivingPortfolio] = None
        self.commander: Optional[LivingCommander] = None

    def bootstrap(self) -> None:
        """Initialize standard Living Mesh nodes and establish mutual trust capabilities."""
        ObjectDiscoveryRegistry.clear()

        # 1. Living Database
        self.db_node = LivingDatabase.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.engine,
            name="CoreDB_Cluster",
            initial_state={
                "qps": 120.0,
                "avg_latency_ms": 12.5,
                "target_latency_ms": 15.0,
                "buffer_pool_mb": 512,
                "cache_hit_rate": 0.96,
                "synthetic_indexes": [],
            },
            tags=["database", "storage", "core"],
            goals=["zero_deadlocks", "maintain_sub_15ms_latency"],
        )
        self.pop_manager.add_member(self.db_node)

        # 2. Living API Gateway Microservice
        self.api_gateway = LivingService.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.engine,
            name="APIGateway_Service",
            initial_state={
                "requests_processed": 0,
                "error_rate": 0.001,
                "target_error_rate": 0.01,
                "circuit_breaker_open": False,
                "dependency_latency_ms": 15.0,
            },
            tags=["microservice", "gateway", "network"],
            goals=["maximize_uptime", "zero_cascading_failures"],
        )
        self.pop_manager.add_member(self.api_gateway)

        # 3. Living Security Sentinel
        self.sentinel = LivingSentinel.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.engine,
            name="SecSentinel_ZeroTrust",
            initial_state={
                "total_inspections": 0,
                "failed_auth_attempts": 0,
                "request_entropy": 0.35,
                "quarantined_sources": [],
            },
            tags=["security", "sentinel", "firewall"],
            goals=["prevent_unauthorized_access", "zero_compromises"],
        )
        self.pop_manager.add_member(self.sentinel)

        # 4. Living Treasury Portfolio
        self.portfolio = LivingPortfolio.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.engine,
            name="TreasuryLedger",
            initial_state={
                "portfolio_value_usd": 1250000.0,
                "daily_volatility": 0.12,
                "target_volatility": 0.15,
                "cash_ratio": 0.25,
            },
            tags=["finance", "treasury", "risk"],
            goals=["preserve_capital", "optimize_liquidity"],
        )
        self.pop_manager.add_member(self.portfolio)

        # 5. Living Incident Commander
        self.commander = LivingCommander.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.engine,
            name="MeshCommander",
            initial_state={
                "status": "ready",
                "active_incidents": 0,
                "investigations_completed": 0,
            },
            tags=["coordinator", "commander", "orchestrator"],
            goals=["maintain_mesh_equilibrium", "rapid_self_healing"],
        )
        self.pop_manager.add_member(self.commander)

        # Grant baseline mesh capabilities
        all_nodes = [self.db_node, self.api_gateway, self.sentinel, self.portfolio, self.commander]
        for src in all_nodes:
            for dst in all_nodes:
                if src.object_id != dst.object_id:
                    self.registry.grant(src.object_id, dst.object_id, ["communicate", "delegate"])

        self.log_event("mesh_bootstrapped", "All 5 core Living Nodes online and interconnected.")

    def log_event(self, event_type: str, message: str, metadata: Optional[dict] = None) -> None:
        evt = {
            "id": f"evt_{int(time.time()*1000)}_{len(self._cognitive_events)}",
            "timestamp": time.strftime("%H:%M:%S"),
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }
        self._cognitive_events.append(evt)
        if len(self._cognitive_events) > 200:
            self._cognitive_events.pop(0)

    def tick(self) -> dict:
        """Advance one global step in the Living Mesh."""
        self._step_count += 1
        stats = self.pop_manager.tick_all()
        return stats

    def get_snapshot(self) -> dict:
        """Generate full state snapshot for web visualizer and CLI."""
        nodes_data = []
        for obj in self.pop_manager.active_members():
            nodes_data.append({
                "id": obj.object_id,
                "name": obj.name,
                "type": obj.__class__.__name__,
                "state": dict(obj.state),
                "is_alive": obj.is_alive,
                "is_dormant": obj.is_dormant,
                "idle_steps": obj.idle_steps,
                "utility": obj.get_utility(),
                "budget_left": getattr(obj, "daily_budget", 1.0),
                "anomalies_count": len(getattr(obj, "_anomaly_history", [])),
                "recent_anomaly": (
                    getattr(obj, "_anomaly_history", [])[-1].to_dict()
                    if getattr(obj, "_anomaly_history", []) else None
                ),
                "tags": getattr(obj, "_tags", []),
                "goals": [g.to_dict() for g in getattr(obj, "get_active_goals", lambda: [])()],
                "memories_count": (
                    len(obj.memory.recall_episodes()) + len(obj.memory.recall_strategies())
                    if obj.memory else 0
                ),
            })

        return {
            "step": self._step_count,
            "population_size": len(nodes_data),
            "resource_pool": self.resource_pool.stats(),
            "nodes": nodes_data,
            "chaos_history": self.chaos.get_history(),
            "recent_events": list(reversed(self._cognitive_events[-20:])),
            "engine_stats": self.engine.stats(),
        }

    def save_all(self) -> None:
        """Persist every object in the mesh to SQLite."""
        for obj in self.pop_manager.active_members():
            obj.save()
        self.log_event("mesh_saved", "All living nodes persisted to SQLite event store.")

    def crash_and_rehydrate(self) -> dict:
        """
        Simulate an abrupt process crash / reboot and rehydrate
        the entire mesh from SQLite.
        """
        self.save_all()
        saved_ids = {obj.name: obj.object_id for obj in self.pop_manager.active_members()}

        # Reset in-memory state
        self.pop_manager = PopulationManager(self.store, self.registry, self.engine)
        ObjectDiscoveryRegistry.clear()

        # Rehydrate all objects from EventStore
        for name, oid in saved_ids.items():
            if "DB" in name:
                self.db_node = LivingDatabase.load(oid, self.store, self.registry, self.engine)
                if self.db_node: self.pop_manager.add_member(self.db_node)
            elif "Gateway" in name:
                self.api_gateway = LivingService.load(oid, self.store, self.registry, self.engine)
                if self.api_gateway: self.pop_manager.add_member(self.api_gateway)
            elif "Sentinel" in name:
                self.sentinel = LivingSentinel.load(oid, self.store, self.registry, self.engine)
                if self.sentinel: self.pop_manager.add_member(self.sentinel)
            elif "Treasury" in name:
                self.portfolio = LivingPortfolio.load(oid, self.store, self.registry, self.engine)
                if self.portfolio: self.pop_manager.add_member(self.portfolio)
            elif "Commander" in name:
                self.commander = LivingCommander.load(oid, self.store, self.registry, self.engine)
                if self.commander: self.pop_manager.add_member(self.commander)
            elif "Investigator" in name:
                bot = IncidentInvestigatorBot.load(oid, self.store, self.registry, self.engine)
                if bot: self.pop_manager.add_member(bot)
            elif "Healer" in name:
                bot = AutoHealerBot.load(oid, self.store, self.registry, self.engine)
                if bot: self.pop_manager.add_member(bot)

        self.log_event("mesh_rehydrated", f"Mesh revived after crash. {self.pop_manager.size()} nodes rehydrated.")
        return {"rehydrated_count": self.pop_manager.size()}
