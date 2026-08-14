"""Bounded cross-pollination among local task ecosystems."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PollinationReport:
    generation: int
    donations: Mapping[str, int]


class MultiSpeciesEngine:
    def __init__(self, ecosystems: Mapping[str, Any], pollination_interval: int = 1_000) -> None:
        if len(ecosystems) < 2:
            raise ValueError("multi-species evolution requires at least two ecosystems")
        self.ecosystems = dict(ecosystems)
        self.pollination_interval = max(1, int(pollination_interval))

    def pollinate(self, generation: int) -> PollinationReport:
        if generation % self.pollination_interval:
            return PollinationReport(generation, {})
        donations: dict[str, int] = {}
        for source_name, source in self.ecosystems.items():
            champion = source.get_champion()
            strategies = list(getattr(champion, "learned_strategies", {}).values())
            best = max(strategies, key=lambda item: float(getattr(item, "effectiveness", 0.0)), default=None)
            if best is None:
                continue
            for target_name, target in self.ecosystems.items():
                if target_name == source_name or not getattr(target, "population", None):
                    continue
                recipient = target.population[0]
                name = f"foreign_{source_name}_{getattr(best, 'name', 'strategy')}"
                accepted = recipient.learn(
                    name,
                    str(getattr(best, "source_code", "")),
                    performance=max(0.0, min(1.0, float(getattr(best, "effectiveness", 0.0)) * 0.9)),
                )
                donations[f"{source_name}->{target_name}"] = int(bool(accepted))
        return PollinationReport(generation, donations)


__all__ = ["MultiSpeciesEngine", "PollinationReport"]
