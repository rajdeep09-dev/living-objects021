"""
AGY Ecology & Economics Module — Phases 2.11, 4, and 5 Completion
==================================================================

Implements:
  - P2.11: Goal-Directed Reasoning & Sub-goal Planning
  - P4.4:  Emergent Specialization & Task Delegation
  - P4.5:  Consensus Engine (Collective Voting & Quorum)
  - P4.6:  Object Spawning (Parent-Child Lineage)
  - P4.7:  Population Manager (Lifecycle & Generational Evolution)
  - P5.3:  Global Resource Pool & EVR Bidding
  - P5.4:  Auto-Retirement & Tombstoning
  - P5.5:  Utility-Based Priority Scheduler
"""
from __future__ import annotations

import heapq
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type

from living_objects import CapabilityRegistry, EventStore
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject,
    ObjectDiscoveryRegistry,
    TieredReasoningEngine,
)


# ===========================================================================
# P2.11: Goal-Directed Reasoning & Planning
# ===========================================================================

@dataclass
class Goal:
    """A proactive objective pursued by a Living Object."""
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    target_metric: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    priority: float = 1.0  # 0.0 to 1.0
    status: str = "active"  # "active", "achieved", "blocked", "abandoned"
    milestones: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update_progress(self, current: float) -> bool:
        """Update current metric value and return True if target is reached."""
        self.current_value = current
        if self.target_value is not None:
            if abs(current - self.target_value) < 0.01 or (
                self.target_value > 0 and current >= self.target_value
            ) or (
                self.target_value <= 0 and current <= self.target_value
            ):
                self.status = "achieved"
                return True
        return False

    def to_dict(self) -> dict:
        return asdict(self)


class GoalDirectedMixin:
    """Mixin adding autonomous goal management and planning to Living Objects."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._goals_dict: Dict[str, Goal] = {}

    def add_goal(
        self,
        description: str,
        target_metric: Optional[str] = None,
        target_value: Optional[float] = None,
        priority: float = 1.0,
        milestones: Optional[List[str]] = None,
    ) -> Goal:
        g = Goal(
            description=description,
            target_metric=target_metric,
            target_value=target_value,
            priority=priority,
            milestones=milestones or [],
        )
        self._goals_dict[g.goal_id] = g
        if hasattr(self, "emit"):
            self.emit("goal_added", g.to_dict())
        return g

    def get_active_goals(self) -> List[Goal]:
        return [g for g in self._goals_dict.values() if g.status == "active"]

    def pursue_goals(self) -> List[dict]:
        """
        Evaluate active goals, generate plan actions via reasoning engine,
        and execute sub-actions to achieve objectives.
        """
        active = self.get_active_goals()
        if not active:
            return []

        actions_taken = []
        for goal in active:
            # Check if target metric is in state
            if goal.target_metric and hasattr(self, "get_state"):
                cur = self.get_state(goal.target_metric)
                if cur is not None and isinstance(cur, (int, float)):
                    if goal.update_progress(float(cur)):
                        if hasattr(self, "emit"):
                            self.emit("goal_achieved", goal.to_dict())
                        actions_taken.append({
                            "goal_id": goal.goal_id,
                            "action": "completed",
                            "metric": goal.target_metric,
                            "value": cur,
                        })
                        continue

            # Reason about next step for this goal
            prompt = (
                f"You are pursuing goal: '{goal.description}'.\n"
                f"Target metric: {goal.target_metric} -> {goal.target_value}. "
                f"Current state: {getattr(self, '_state', {})}.\n"
                f"What is the single best action to advance this goal?"
            )
            if hasattr(self, "_reasoning") and self._reasoning:
                plan = self._reasoning.reason(
                    prompt,
                    {"return_type": "dict"},
                    {"goal": goal.to_dict(), "state": getattr(self, "_state", {})},
                )
                action_desc = plan.get("result", f"Advance milestone for {goal.description}")
            else:
                action_desc = f"Advance milestone for {goal.description}"

            actions_taken.append({
                "goal_id": goal.goal_id,
                "action": action_desc,
                "status": goal.status,
            })
            if hasattr(self, "emit"):
                self.emit("goal_action", {"goal_id": goal.goal_id, "action": action_desc})

        return actions_taken


# ===========================================================================
# P4.4: Emergent Specialization & Delegation
# ===========================================================================

class DelegationEngine:
    """Handles task delegation between specialized Living Objects."""

    @staticmethod
    def delegate(
        source_obj: AGYLivingObject,
        target_type: str,
        task_name: str,
        task_payload: dict,
        registry: CapabilityRegistry,
    ) -> dict:
        """
        Find an active peer matching target_type, verify/grant communication
        capability, transmit the task, and record delegation in memory.
        """
        peers = source_obj.find_peers_by_type(target_type)
        if not peers:
            peers = source_obj.find_peers_by_tag(target_type)
        if not peers:
            return {"success": False, "reason": f"No active peer found for type or tag '{target_type}'"}

        target_id = peers[0]  # Pick best available peer

        # Ensure capability
        if not registry.check(source_obj.object_id, target_id, "delegate"):
            registry.grant(source_obj.object_id, target_id, ["delegate", "communicate"])
            registry.grant(target_id, source_obj.object_id, ["communicate"])

        message = {
            "type": "delegated_task",
            "task_name": task_name,
            "payload": task_payload,
            "from": source_obj.object_id,
        }
        res = source_obj.communicate(target_id, message)

        if res.get("success"):
            source_obj.emit("task_delegated", {
                "to": target_id, "task": task_name, "payload": task_payload
            })
            if source_obj.memory:
                source_obj.memory.record_strategy(
                    f"delegate_{task_name}",
                    f"Delegated {task_name} to {target_type} ({target_id})",
                    success_rate=0.95,
                )
        return {"success": True, "target_id": target_id, "comm_result": res}


# ===========================================================================
# P4.5: Consensus Engine (Collective Decision Making / Quorum)
# ===========================================================================

@dataclass
class ConsensusProposal:
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    initiator_id: str = ""
    topic: str = ""
    options: List[str] = field(default_factory=list)
    quorum: int = 3
    votes: Dict[str, str] = field(default_factory=dict)  # voter_id -> option
    reasons: Dict[str, str] = field(default_factory=dict) # voter_id -> rationale
    status: str = "pending"  # "pending", "resolved", "expired"
    winner: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConsensusEngine:
    """
    Coordinates decentralized voting among Living Objects to reach quorum decisions.
    """
    def __init__(self):
        self._proposals: Dict[str, ConsensusProposal] = {}

    def create_proposal(
        self,
        initiator_id: str,
        topic: str,
        options: List[str],
        quorum: int = 3,
    ) -> ConsensusProposal:
        p = ConsensusProposal(
            initiator_id=initiator_id,
            topic=topic,
            options=options,
            quorum=quorum,
        )
        self._proposals[p.proposal_id] = p
        return p

    def vote(
        self,
        proposal_id: str,
        voter: AGYLivingObject,
        choice: str,
        reasoning: str = "",
    ) -> dict:
        prop = self._proposals.get(proposal_id)
        if not prop:
            return {"success": False, "reason": "Proposal not found"}
        if prop.status != "pending":
            return {"success": False, "reason": f"Proposal already {prop.status}"}
        if choice not in prop.options:
            return {"success": False, "reason": f"Invalid choice '{choice}'. Options: {prop.options}"}

        prop.votes[voter.object_id] = choice
        prop.reasons[voter.object_id] = reasoning

        voter.emit("consensus_voted", {
            "proposal_id": proposal_id, "choice": choice, "topic": prop.topic
        })

        # Check if quorum reached
        if len(prop.votes) >= prop.quorum:
            tally: Dict[str, int] = {}
            for opt in prop.votes.values():
                tally[opt] = tally.get(opt, 0) + 1
            prop.winner = max(tally, key=tally.get)
            prop.status = "resolved"

            voter.emit("consensus_reached", {
                "proposal_id": proposal_id, "winner": prop.winner, "tally": tally
            })
            return {"success": True, "quorum_reached": True, "winner": prop.winner, "tally": tally}

        return {"success": True, "quorum_reached": False, "current_votes": len(prop.votes)}

    def get_proposal(self, proposal_id: str) -> Optional[ConsensusProposal]:
        return self._proposals.get(proposal_id)


# ===========================================================================
# P4.6: Object Spawning (Parent-Child Lineage)
# ===========================================================================

class ObjectSpawner:
    """Handles recursive spawning of child living objects from parent objects."""

    @staticmethod
    def spawn(
        parent: AGYLivingObject,
        child_cls: Type[AGYLivingObject],
        child_name: str,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: TieredReasoningEngine,
        initial_state: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        goals: Optional[List[str]] = None,
    ) -> AGYLivingObject:
        init = dict(initial_state or {})
        init["_parent_id"] = parent.object_id
        init["_lineage"] = getattr(parent, "_lineage", []) + [parent.object_id]

        child = child_cls.create(
            store=store,
            registry=registry,
            reasoning=reasoning,
            name=child_name,
            initial_state=init,
            tags=tags,
            goals=goals,
        )

        # Grant parent-child capabilities
        registry.grant(parent.object_id, child.object_id, ["control", "delegate", "communicate", "read"])
        registry.grant(child.object_id, parent.object_id, ["report", "communicate"])

        parent.emit("child_spawned", {
            "child_id": child.object_id, "child_name": child_name, "child_type": child_cls.__name__
        })
        child.emit("spawned_by_parent", {
            "parent_id": parent.object_id, "parent_name": parent.name
        })

        return child


# ===========================================================================
# P4.7: Population Manager (Lifecycle & Generational Evolution)
# ===========================================================================

class PopulationManager:
    """
    Coordinates a collection of living objects, tracking lineage,
    generational fitness, cloning with adaptation, and population health.
    """
    def __init__(self, store: EventStore, registry: CapabilityRegistry, reasoning: TieredReasoningEngine):
        self.store = store
        self.registry = registry
        self.reasoning = reasoning
        self._members: Dict[str, AGYLivingObject] = {}
        self.generation: int = 1

    def add_member(self, obj: AGYLivingObject) -> None:
        self._members[obj.object_id] = obj

    def get_member(self, object_id: str) -> Optional[AGYLivingObject]:
        return self._members.get(object_id)

    def active_members(self) -> List[AGYLivingObject]:
        return [o for o in self._members.values() if o.is_alive]

    def size(self) -> int:
        return len(self.active_members())

    def tick_all(self) -> dict:
        """Advance time step for all active objects in population."""
        stats = {"ticked": 0, "dormant": 0, "active": 0, "avg_utility": 0.0}
        utilities = []
        for obj in self.active_members():
            obj.tick()
            stats["ticked"] += 1
            if obj.is_dormant:
                stats["dormant"] += 1
            else:
                stats["active"] += 1
            utilities.append(obj.get_utility())

        if utilities:
            stats["avg_utility"] = round(sum(utilities) / len(utilities), 3)
        return stats

    def clone_with_mutation(
        self,
        source_id: str,
        new_name: str,
        state_mutations: Optional[dict] = None,
    ) -> Optional[AGYLivingObject]:
        """Clone an existing high-utility object with inherited memories and mutated parameters."""
        source = self._members.get(source_id)
        if not source:
            return None

        cls = source.__class__
        new_state = dict(source.state)
        if state_mutations:
            new_state.update(state_mutations)
        new_state["_cloned_from"] = source_id
        new_state["_generation"] = self.generation + 1

        clone = cls.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.reasoning,
            name=new_name,
            initial_state=new_state,
            tags=list(getattr(source, "_tags", [])),
            goals=list(getattr(source, "_goals", [])),
        )

        # Inherit strategies from source
        if source.memory and clone.memory:
            for strat in source.memory.recall_strategies():
                try:
                    c = json.loads(strat["content"]) if isinstance(strat["content"], str) else strat["content"]
                    clone.memory.record_strategy(
                        c.get("strategy_name", "inherited"),
                        c.get("description", ""),
                        success_rate=c.get("success_rate", 0.9),
                    )
                except Exception:
                    pass

        self.add_member(clone)
        return clone

    def cull_low_utility(self, threshold: float = 0.15) -> List[str]:
        """P5.4: Automatically retire objects that have fallen below utility threshold."""
        retired = []
        for obj in list(self.active_members()):
            if obj.get_utility() < threshold and obj.idle_steps >= 5:
                obj.retire()
                retired.append(obj.object_id)
        return retired


# ===========================================================================
# P5.3: Global Resource Pool & EVR Bidding
# ===========================================================================

@dataclass
class ResourceBid:
    object_id: str
    reasoning_task: str
    evr: float
    utility: float
    urgency: float
    tokens_requested: int = 100

    @property
    def score(self) -> float:
        """Expected ROI score = EVR * Utility * Urgency."""
        return max(0.001, self.evr * self.utility * self.urgency)


class GlobalResourcePool:
    """
    Manages a shared compute budget across a population of Living Objects.
    Uses EVR-based bidding to allocate reasoning quota to the highest-ROI tasks.
    """
    def __init__(self, total_daily_tokens: int = 10000):
        self.total_daily_tokens = total_daily_tokens
        self.tokens_remaining = total_daily_tokens
        self._allocations: Dict[str, int] = {}
        self._bid_history: List[dict] = []

    def submit_bids_and_allocate(self, bids: List[ResourceBid]) -> Dict[str, bool]:
        """
        Rank bids by ROI score and allocate compute tokens until pool is exhausted.
        Returns map of object_id -> granted (True/False).
        """
        # Sort bids by score descending
        sorted_bids = sorted(bids, key=lambda b: b.score, reverse=True)
        results = {}

        for bid in sorted_bids:
            if self.tokens_remaining >= bid.tokens_requested:
                self.tokens_remaining -= bid.tokens_requested
                self._allocations[bid.object_id] = self._allocations.get(bid.object_id, 0) + bid.tokens_requested
                results[bid.object_id] = True
                self._bid_history.append({"object_id": bid.object_id, "score": bid.score, "granted": True})
            else:
                results[bid.object_id] = False
                self._bid_history.append({"object_id": bid.object_id, "score": bid.score, "granted": False})

        return results

    def reset_daily_pool(self) -> None:
        self.tokens_remaining = self.total_daily_tokens

    def stats(self) -> dict:
        return {
            "total_pool": self.total_daily_tokens,
            "remaining": self.tokens_remaining,
            "utilization_pct": round((1 - self.tokens_remaining / self.total_daily_tokens) * 100, 1),
            "allocated_by_object": dict(self._allocations),
        }


# ===========================================================================
# P5.5: Utility-Based Priority Scheduler
# ===========================================================================

class UtilityPriorityScheduler:
    """
    Priority queue scheduling object reasoning tasks by priority = urgency * utility.
    """
    def __init__(self):
        self._queue: List[Tuple[float, int, Callable]] = []  # (-priority, counter, task)
        self._counter = 0

    def schedule(self, obj: AGYLivingObject, task: Callable, urgency: float = 1.0) -> None:
        priority = obj.get_utility() * urgency
        # Max-heap using negative priority
        heapq.heappush(self._queue, (-priority, self._counter, task))
        self._counter += 1

    def run_next(self) -> Optional[Any]:
        if not self._queue:
            return None
        _, _, task = heapq.heappop(self._queue)
        return task()

    def run_all(self) -> List[Any]:
        results = []
        while self._queue:
            results.append(self.run_next())
        return results

    def pending_count(self) -> int:
        return len(self._queue)
