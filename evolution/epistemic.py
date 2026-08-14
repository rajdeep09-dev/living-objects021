"""Calibrated uncertainty and conservative selection for BEAST v4."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GaussianDistribution:
    mean: float = 0.5
    variance: float = 0.25


@dataclass
class EpistemicState:
    fitness_belief: GaussianDistribution = field(default_factory=GaussianDistribution)
    strategy_confidence: dict[str, float] = field(default_factory=dict)
    world_model_accuracy: float = 0.5
    known_unknowns: set[str] = field(default_factory=set)
    unknown_unknowns_estimate: float = 0.5

    def update_belief(self, observation: float, learning_rate: float) -> None:
        rate = max(0.0, min(1.0, float(learning_rate)))
        observed = max(0.0, min(1.0, float(observation)))
        prior = self.fitness_belief
        prior.mean = (1.0 - rate) * prior.mean + rate * observed
        prior.variance = max(1e-9, prior.variance * (1.0 - 0.5 * rate))
        self.world_model_accuracy = max(0.0, min(1.0, 1.0 - abs(prior.mean - observed)))
        self.unknown_unknowns_estimate = max(0.0, min(1.0, self.unknown_unknowns_estimate * (1.0 - 0.25 * rate)))

    def confidence_interval(self, alpha: float = 0.95) -> tuple[float, float]:
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        z = 1.96 if alpha >= 0.95 else (1.645 if alpha >= 0.90 else 1.0)
        spread = z * math.sqrt(max(0.0, self.fitness_belief.variance))
        return max(0.0, self.fitness_belief.mean - spread), min(1.0, self.fitness_belief.mean + spread)

    def exploration_bonus(self) -> float:
        return round(min(0.5, max(0.0, self.fitness_belief.variance) * 2.0 + 0.1 * self.unknown_unknowns_estimate), 6)


class UncertaintyAwareEvolution:
    def __init__(self, grace_generations: int = 3, ci_width_threshold: float = 0.4) -> None:
        self.grace_generations = max(0, int(grace_generations))
        self.ci_width_threshold = max(0.0, float(ci_width_threshold))
        self.protected_until: dict[str, int] = {}

    def should_protect(self, organism: Any) -> bool:
        state = getattr(organism, "epistemic_state", None)
        if state is None:
            return False
        lo, hi = state.confidence_interval()
        protected = (hi - lo) > self.ci_width_threshold
        if protected:
            object_id = str(getattr(organism, "object_id", organism))
            generation = int(getattr(organism, "generation", 0))
            self.protected_until[object_id] = max(self.protected_until.get(object_id, 0), generation + self.grace_generations)
        return protected or int(getattr(organism, "generation", 0)) <= self.protected_until.get(str(getattr(organism, "object_id", organism)), -1)


__all__ = ["EpistemicState", "GaussianDistribution", "UncertaintyAwareEvolution"]
