"""Multi-objective novelty preservation for long-lived local populations."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ObjectiveVector:
    task_fitness: float
    behavioral_novelty: float
    code_brevity: float
    cultural_influence: float
    longevity: float

    def values(self) -> tuple[float, ...]:
        return (
            self.task_fitness,
            self.behavioral_novelty,
            self.code_brevity,
            self.cultural_influence,
            self.longevity,
        )


class ParetoArchive:
    """Keeps non-dominated organisms and a seeded diversity sample of the rest."""

    objectives = (
        "task_fitness",
        "behavioral_novelty",
        "code_brevity",
        "cultural_influence",
        "longevity",
    )

    def score(self, organism: Any) -> ObjectiveVector:
        genome = getattr(organism, "genome", None)
        strategies = list(getattr(organism, "learned_strategies", {}).values())
        code_lengths = [len(str(getattr(item, "source_code", ""))) for item in strategies]
        descriptors = set(getattr(organism, "behavior_descriptors", {}).values())
        ancestors = list(getattr(organism, "ancestor_ids", []))
        return ObjectiveVector(
            task_fitness=float(getattr(genome, "fitness", getattr(organism, "fitness", 0.0))),
            behavioral_novelty=min(1.0, len(descriptors) / 12.0),
            code_brevity=min(1.0, 100.0 / max(100.0, min(code_lengths, default=1000))),
            cultural_influence=min(1.0, float(getattr(organism, "cultural_adoptions", 0)) / 20.0),
            longevity=min(1.0, len(ancestors) / 100.0),
        )

    def dominated_by(self, left: Any, right: Any) -> bool:
        left_scores = self.score(left).values()
        right_scores = self.score(right).values()
        return all(b >= a for a, b in zip(left_scores, right_scores)) and any(
            b > a for a, b in zip(left_scores, right_scores)
        )

    def pareto_front(self, population: Iterable[Any]) -> list[Any]:
        members = list(population)
        return [
            organism
            for organism in members
            if not any(other is not organism and self.dominated_by(organism, other) for other in members)
        ]

    def cull(self, population: Iterable[Any], max_size: int, rng: random.Random | None = None) -> list[Any]:
        if max_size < 1:
            raise ValueError("max_size must be positive")
        members = list(population)
        front = self.pareto_front(members)
        if len(front) >= max_size:
            return sorted(front, key=lambda item: self.score(item).values(), reverse=True)[:max_size]
        dominated = [item for item in members if item not in front]
        (rng or random.Random(0)).shuffle(dominated)
        return front + dominated[: max_size - len(front)]


__all__ = ["ObjectiveVector", "ParetoArchive"]
