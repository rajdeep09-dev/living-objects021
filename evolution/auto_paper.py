"""Deterministic research abstracts generated only from measured metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Abstract:
    generation: int
    title: str
    findings: tuple[str, ...]
    peak_fitness: float
    strategies_count: int


class AutomaticPaperWriter:
    def write_abstract(self, generation: int, previous: Abstract | None, records: Iterable[Any], memome: Any, champion: Any) -> Abstract:
        metrics = list(records)
        latest = metrics[-1] if metrics else None
        fitness = float(getattr(latest, "average_fitness", getattr(latest, "best_fitness", 0.0)))
        archive_size = int(getattr(memome, "total_strategies", lambda: 0)())
        prior_fitness = previous.peak_fitness if previous else 0.0
        prior_archive = previous.strategies_count if previous else 0
        genome = getattr(champion, "genome", None)
        mutation_rate = float(getattr(genome, "mutation_rate", 0.0))
        receptivity = float(getattr(genome, "cultural_receptivity", 0.0))
        return Abstract(
            generation=generation,
            title=f"Cultural Evolution in a Lamarckian Digital Ecosystem: Generations {max(0, generation - 10_000):,}-{generation:,}",
            findings=(
                f"Measured average fitness changed by {fitness - prior_fitness:+.4f} over this interval.",
                f"{archive_size - prior_archive} new cultural strategies were recorded.",
                f"Champion mutation rate: {mutation_rate:.4f}; cultural receptivity: {receptivity:.4f}.",
            ),
            peak_fitness=fitness,
            strategies_count=archive_size,
        )


__all__ = ["Abstract", "AutomaticPaperWriter"]
