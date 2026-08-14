"""Excavate and safely resurrect strategies from cultural history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from evolution.beast_v2_culture import FederatedMemome
from evolution.lamarckian import Strategy


@dataclass(frozen=True)
class ExtinctStrategy:
    strategy: Strategy
    last_known_generation: int
    reason: str = "creator_or_usage_lost"

    @property
    def name(self) -> str:
        return self.strategy.name


@dataclass(frozen=True)
class ArchaeologyReport:
    excavated: int
    evaluated: int
    resurrected: int
    candidates: tuple[str, ...] = ()
    relevance: dict[str, float] = field(default_factory=dict)


class KnowledgeArchaeologist:
    def __init__(self, relevance_threshold: float = 0.55) -> None:
        self.relevance_threshold = relevance_threshold
        self.resurrection_log: list[dict[str, Any]] = []

    def excavate(self, memome: FederatedMemome, cutoff_generation: int) -> list[ExtinctStrategy]:
        return [
            ExtinctStrategy(strategy, strategy.generation)
            for strategy in memome.strategies()
            if strategy.generation <= cutoff_generation and strategy.uses == 0
        ]

    def evaluate_relevance(self, strategy: ExtinctStrategy, current_ecosystem: Any) -> float:
        descriptors: set[str] = set()
        for organism in getattr(current_ecosystem, "organisms", current_ecosystem if isinstance(current_ecosystem, list) else []):
            descriptors.update(getattr(organism, "behavior_descriptors", {}).values())
        if strategy.strategy.descriptor in descriptors:
            return 1.0
        current_generation = int(getattr(current_ecosystem, "generation", strategy.last_known_generation))
        age = max(0, current_generation - strategy.last_known_generation)
        return max(0.0, min(1.0, strategy.strategy.effectiveness - 0.02 * age + 0.25))

    def resurrect(self, strategy: ExtinctStrategy, target: Any) -> bool:
        installer = getattr(target, "install_strategy", None)
        if not callable(installer) or not installer(strategy.strategy):
            return False
        setattr(target, "resurrected_strategies", getattr(target, "resurrected_strategies", []) + [strategy.name])
        self.resurrection_log.append({"strategy": strategy.name, "target": getattr(target, "object_id", "unknown"), "resurrected": True})
        return True

    def run_archaeology_pass(self, memome: FederatedMemome, population: list[Any]) -> ArchaeologyReport:
        cutoff = max((getattr(organism, "generation", 0) for organism in population), default=0)
        extinct = self.excavate(memome, cutoff)
        relevance: dict[str, float] = {}
        resurrected = 0
        candidates: list[str] = []
        target = population[0] if population else None
        for item in extinct:
            score = self.evaluate_relevance(item, population)
            relevance[item.name] = score
            if score >= self.relevance_threshold and target is not None:
                candidates.append(item.name)
                resurrected += int(self.resurrect(item, target))
        return ArchaeologyReport(len(extinct), len(extinct), resurrected, tuple(candidates), relevance)


__all__ = ["ArchaeologyReport", "ExtinctStrategy", "KnowledgeArchaeologist"]
