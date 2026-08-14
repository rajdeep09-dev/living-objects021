"""Organisms that tune the evolutionary policy itself."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, replace
from typing import Any, Optional, Protocol


class ImprovementArchive(Protocol):
    def contribute(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class EvolutionPolicy:
    mutation_rate: float = 0.1
    inheritance_rate: float = 0.8
    novelty_bonus: float = 0.1

    def bounded(self) -> "EvolutionPolicy":
        return EvolutionPolicy(
            mutation_rate=max(0.01, min(0.5, self.mutation_rate)),
            inheritance_rate=max(0.1, min(1.0, self.inheritance_rate)),
            novelty_bonus=max(0.0, min(1.0, self.novelty_bonus)),
        )


@dataclass(frozen=True)
class EvolutionImprovement:
    generation: int
    organism_id: str
    before: EvolutionPolicy
    after: EvolutionPolicy
    observed_fitness: float
    reason: str
    meme_id: Optional[str] = None


class SelfImprovingOrganism:
    """A policy-bearing organism that records successful policy experiments."""

    def __init__(self, organism_id: str, policy: Optional[EvolutionPolicy] = None, seed: int = 0) -> None:
        self.organism_id = organism_id
        self.policy = (policy or EvolutionPolicy()).bounded()
        self.best_fitness = 0.0
        self.last_fitness = 0.0
        self.generation = 0
        self._rng = random.Random(seed)
        self.improvements: list[EvolutionImprovement] = []

    def improve_evolution(
        self,
        archive: ImprovementArchive,
        observed_fitness: Optional[float] = None,
        generation: Optional[int] = None,
    ) -> EvolutionImprovement:
        """Tune policy parameters and publish the change as an improvement meme."""
        fitness = self.last_fitness if observed_fitness is None else float(observed_fitness)
        generation = self.generation + 1 if generation is None else generation
        before = self.policy
        improving = fitness >= self.best_fitness
        if improving:
            after = EvolutionPolicy(
                mutation_rate=before.mutation_rate * 0.985,
                inheritance_rate=before.inheritance_rate + 0.012,
                novelty_bonus=before.novelty_bonus + 0.008,
            ).bounded()
            reason = "fitness improved or held; preserve learned behavior and widen novelty"
            self.best_fitness = max(self.best_fitness, fitness)
        else:
            after = EvolutionPolicy(
                mutation_rate=before.mutation_rate * 1.04,
                inheritance_rate=before.inheritance_rate - 0.01,
                novelty_bonus=before.novelty_bonus + 0.015,
            ).bounded()
            reason = "fitness regressed; explore a wider policy neighborhood"
        self.policy = after
        self.last_fitness = fitness
        self.generation = generation
        source_code = (
            "def apply_policy(previous, improved):\n"
            "    return improved\n"
        )
        meme_id = archive.contribute(
            name="evolution_improvement",
            descriptor=f"policy:{self.organism_id}:g{generation}",
            source_code=source_code,
            effectiveness=fitness,
            author_id=self.organism_id,
            generation=generation,
        )
        improvement = EvolutionImprovement(generation, self.organism_id, before, after, fitness, reason, str(meme_id))
        self.improvements.append(improvement)
        return improvement


class SelfImprovingEvolution:
    """Small coordinator used to benchmark policy improvement over generations."""

    def __init__(self, size: int = 128, seed: int = 11) -> None:
        self.organisms = [SelfImprovingOrganism(f"policy-{i:04d}", seed=seed + i) for i in range(size)]
        self.rng = random.Random(seed)
        self.history: list[dict[str, float]] = []

    def step(self, archive: ImprovementArchive, generation: int) -> dict[str, float]:
        fitnesses: list[float] = []
        for organism in self.organisms:
            observed = max(0.0, min(1.0, 0.35 + organism.policy.inheritance_rate * 0.35 + organism.policy.novelty_bonus * 0.2 + self.rng.random() * 0.1))
            organism.improve_evolution(archive, observed_fitness=observed, generation=generation)
            fitnesses.append(observed)
        metric = {
            "generation": float(generation),
            "average_fitness": sum(fitnesses) / len(fitnesses),
            "average_mutation_rate": sum(o.policy.mutation_rate for o in self.organisms) / len(self.organisms),
            "improvement_count": float(sum(len(o.improvements) for o in self.organisms)),
        }
        self.history.append(metric)
        return metric

    def run(self, archive: ImprovementArchive, generations: int = 10) -> list[dict[str, float]]:
        return [self.step(archive, generation) for generation in range(1, generations + 1)]

