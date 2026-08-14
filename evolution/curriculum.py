"""Bounded curriculum policy driven by measured population fitness."""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class TaskConfig:
    name: str
    difficulty: int
    parameters: dict[str, float]


class CurriculumSchedule:
    def __init__(
        self,
        levels: list[TaskConfig],
        *,
        promotion_threshold: float = 0.85,
        demotion_threshold: float = 0.30,
        current_level: int = 0,
    ) -> None:
        if not levels:
            raise ValueError("curriculum needs at least one level")
        if not 0.0 <= demotion_threshold < promotion_threshold <= 1.0:
            raise ValueError("invalid promotion or demotion thresholds")
        self.levels = list(levels)
        self.promotion_threshold = float(promotion_threshold)
        self.demotion_threshold = float(demotion_threshold)
        self.current_level = max(0, min(int(current_level), len(self.levels) - 1))

    @property
    def current(self) -> TaskConfig:
        return self.levels[self.current_level]

    def step(self, average_fitness: float) -> TaskConfig | None:
        if average_fitness >= self.promotion_threshold and self.current_level < len(self.levels) - 1:
            self.current_level += 1
            return self.current
        if average_fitness <= self.demotion_threshold and self.current_level > 0:
            self.current_level -= 1
            return self.current
        return None

    def evolve_schedule(self, rng: random.Random) -> "CurriculumSchedule":
        promotion = max(0.50, min(0.99, self.promotion_threshold + rng.gauss(0.0, 0.05)))
        demotion = max(0.10, min(promotion - 0.05, self.demotion_threshold + rng.gauss(0.0, 0.03)))
        return CurriculumSchedule(
            self.levels,
            promotion_threshold=promotion,
            demotion_threshold=demotion,
            current_level=self.current_level,
        )


__all__ = ["CurriculumSchedule", "TaskConfig"]
