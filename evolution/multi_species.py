"""Producer/Consumer/Decomposer ecosystem with symbiotic exchange."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol


class MemeArchive(Protocol):
    def contribute(self, **kwargs: Any) -> Any: ...

    def query(self, text: str = "", limit: int = 100) -> list[dict[str, Any]]: ...


@dataclass
class SpeciesOrganism:
    organism_id: str
    generation: int
    energy: float = 1.0
    fitness: float = 0.0
    alive: bool = True
    adopted_memes: int = 0

    species: ClassVar[str] = "adaptive"

    def step(self, ecosystem: "MultiSpeciesEcosystem") -> None:
        raise NotImplementedError


class Producer(SpeciesOrganism):
    species = "producer"

    def step(self, ecosystem: "MultiSpeciesEcosystem") -> None:
        descriptor = f"producer:{ecosystem.generation}:{self.organism_id}"
        ecosystem.archive.contribute(
            name="producer_meme",
            descriptor=descriptor,
            source_code="def producer_behavior(context): return context.get('signal', 0.5) + 0.1",
            effectiveness=min(1.0, 0.55 + self.energy * 0.2),
            author_id=self.organism_id,
            generation=ecosystem.generation,
        )
        self.energy = min(2.0, self.energy + 0.03)
        self.fitness = min(1.0, self.fitness + 0.02)


class Consumer(SpeciesOrganism):
    species = "consumer"

    def step(self, ecosystem: "MultiSpeciesEcosystem") -> None:
        memes = ecosystem.archive.query("", limit=3)
        self.adopted_memes += len(memes)
        self.energy = min(2.0, self.energy + (0.06 if memes else -0.02))
        self.fitness = min(1.0, self.fitness + 0.015 + min(0.02, len(memes) * 0.004))


class Decomposer(SpeciesOrganism):
    species = "decomposer"

    def step(self, ecosystem: "MultiSpeciesEcosystem") -> None:
        recyclable = ecosystem.archive.query("", limit=1)
        if recyclable:
            ecosystem.recycled_memes += 1
            self.energy = min(2.0, self.energy + 0.05)
        else:
            self.energy = min(2.0, self.energy + 0.01)
        self.fitness = min(1.0, self.fitness + 0.01)


@dataclass(frozen=True)
class EcosystemGeneration:
    generation: int
    producers: int
    consumers: int
    decomposers: int
    alive: int
    average_fitness: float
    recycled_memes: int


class MultiSpeciesEcosystem:
    def __init__(self, archive: MemeArchive, size: int = 90, seed: int = 3) -> None:
        if size < 3:
            raise ValueError("size must be at least 3")
        self.archive = archive
        self.generation = 0
        self.recycled_memes = 0
        self.rng = random.Random(seed)
        third = size // 3
        self.population: list[SpeciesOrganism] = (
            [Producer(f"producer-{i:04d}", 0) for i in range(third)]
            + [Consumer(f"consumer-{i:04d}", 0) for i in range(third)]
            + [Decomposer(f"decomposer-{i:04d}", 0) for i in range(size - third * 2)]
        )

    def step(self) -> EcosystemGeneration:
        self.generation += 1
        for organism in self.population:
            organism.generation = self.generation
            organism.step(self)
        alive = [item for item in self.population if item.alive]
        return EcosystemGeneration(
            generation=self.generation,
            producers=sum(isinstance(item, Producer) for item in alive),
            consumers=sum(isinstance(item, Consumer) for item in alive),
            decomposers=sum(isinstance(item, Decomposer) for item in alive),
            alive=len(alive),
            average_fitness=sum(item.fitness for item in alive) / len(alive),
            recycled_memes=self.recycled_memes,
        )

    def run(self, generations: int = 1) -> list[EcosystemGeneration]:
        return [self.step() for _ in range(generations)]

    def species_counts(self) -> dict[str, int]:
        return {
            "producer": sum(isinstance(item, Producer) for item in self.population if item.alive),
            "consumer": sum(isinstance(item, Consumer) for item in self.population if item.alive),
            "decomposer": sum(isinstance(item, Decomposer) for item in self.population if item.alive),
        }
