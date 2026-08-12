"""
Memory Manager — Hierarchical memory system.

Levels:
  L1: Working Memory (in-object, fast)
  L2: Episodic Memory (retrieved on demand)
  L3: Semantic Memory (consolidated facts)
  L4: Procedural Memory (learned strategies)
  L5: Relational Memory (other objects)
"""

import json
from typing import List, Optional

from living_objects.core.event_store import EventStore


class MemoryManager:
    """Hierarchical memory: episodic, semantic, procedural, relational."""

    def __init__(self, object_id: str, store: EventStore):
        self.object_id = object_id
        self.store = store

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_episode(
        self,
        observation: str,
        action: str,
        result: str,
        outcome: str = "",
        lesson: str = "",
    ) -> str:
        """Record a structured experience episode."""
        content = {
            "observation": observation,
            "action": action,
            "result": result,
            "outcome": outcome,
            "lesson": lesson,
        }
        return self.store.store_memory(
            self.object_id,
            "episodic",
            content,
            confidence=0.9,
            provenance="direct_experience",
        )

    def record_fact(
        self, fact: str, confidence: float = 1.0, source: str = ""
    ) -> str:
        """Record a semantic fact/belief."""
        return self.store.store_memory(
            self.object_id,
            "semantic",
            {"fact": fact, "source": source},
            confidence=confidence,
            provenance=source,
        )

    def record_strategy(
        self, name: str, description: str, success_rate: float = 0.5
    ) -> str:
        """Record a procedural strategy/heuristic."""
        return self.store.store_memory(
            self.object_id,
            "procedural",
            {
                "name": name,
                "description": description,
                "success_rate": success_rate,
            },
            confidence=success_rate,
            provenance="learned",
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def recall_episodes(self, limit: int = 10) -> List[dict]:
        return self.store.get_memories(self.object_id, "episodic", limit)

    def recall_facts(self, limit: int = 20) -> List[dict]:
        return self.store.get_memories(self.object_id, "semantic", limit)

    def recall_strategies(self, limit: int = 10) -> List[dict]:
        return self.store.get_memories(self.object_id, "procedural", limit)

    def recall_all(self, limit: int = 50) -> List[dict]:
        return self.store.get_memories(self.object_id, limit=limit)

    # ------------------------------------------------------------------
    # Summarization
    # ------------------------------------------------------------------

    def summarize_experiences(self) -> str:
        """Generate a summary of recent experiences for reasoning context."""
        episodes = self.recall_episodes(limit=5)
        if not episodes:
            return "No prior experiences recorded."
        lines = []
        for ep in episodes:
            c = json.loads(ep["content"])
            obs = c.get("observation", "")[:60]
            act = c.get("action", "")[:40]
            out = c.get("outcome", "unknown")
            lines.append(f"- {obs}... → {act}... (outcome: {out})")
        return "\n".join(lines)
