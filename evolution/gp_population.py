"""Deterministic, bounded population evolution for BEAST v6 GP programs."""
from __future__ import annotations

import copy
import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from evolution.fitness import FitnessEvaluator, FitnessResult
from evolution.gp_engine import ALL_REGISTERED_PRIMITIVES, DEFAULT_PRIMITIVES, GPGenome, GPNode, GPTreeBuilder


@dataclass
class GPOrganism:
    organism_id: str
    genome: GPGenome
    fitness_result: FitnessResult | None = None
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    age: int = 0
    cultural_strategies: int = 0

    @property
    def fitness(self) -> float:
        return self.fitness_result.score if self.fitness_result else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "organism_id": self.organism_id, "generation": self.generation,
            "fitness": self.fitness, "program_size": self.genome.complexity(),
            "program_depth": self.genome.depth(), "source_code": self.genome.to_python(f"evolved_gen{self.generation}"),
            "parents": self.parent_ids, "age": self.age,
            "cultural_strategies": self.cultural_strategies, "genome": self.genome.to_dict(),
            "fitness_result": asdict(self.fitness_result) if self.fitness_result else None,
        }


@dataclass(frozen=True)
class GenerationStats:
    generation: int
    best_fitness: float
    average_fitness: float
    median_fitness: float
    best_program_size: int
    population_size: int


@dataclass(frozen=True)
class RunSummary:
    generations: int
    best_fitness: float
    champion_id: str
    target_reached: bool


class GPPopulation:
    """Tournament-selected GP organisms with immutable parent isolation.

    The population never executes generated source. Fitness calls the bounded
    interpreter in :mod:`evolution.gp_engine`, and the hall keeps at most 100
    frozen champions to prevent high-generation memory growth.
    """

    HALL_OF_FAME_MAX = 100
    BLOAT_MAX_NODES = 64
    TRAIN_SEED_OFFSET = 17

    def __init__(self, evaluator: FitnessEvaluator, primitives=None, terminals=None, population_size: int = 50, seed: int = 42, tournament_size: int = 5, crossover_rate: float = 0.8, mutation_rate: float = 0.15, elitism_count: int = 3, max_depth: int = 7, bloat_penalty: float = 0.001) -> None:
        if not 2 <= population_size <= 512:
            raise ValueError("population_size must be in 2..512")
        self.evaluator = evaluator
        self.rng = random.Random(seed)
        self.population_size = population_size
        self.tournament_size = max(2, min(tournament_size, population_size))
        self.crossover_rate = max(0.0, min(1.0, crossover_rate))
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.elitism_count = max(1, min(elitism_count, population_size - 1))
        self.max_depth = max(1, min(max_depth, GPTreeBuilder.MAX_DEPTH))
        self.bloat_penalty = max(0.0, bloat_penalty)
        self.builder = GPTreeBuilder(primitives or DEFAULT_PRIMITIVES, terminals or evaluator.terminals, self.rng)
        self.generation = 0
        self.population: list[GPOrganism] = []
        self.hall_of_fame: list[GPOrganism] = []
        self.history: list[GenerationStats] = []

    def initialize(self) -> None:
        self.population = []
        for index in range(self.population_size):
            depth = 2 + (index % max(1, self.max_depth - 1))
            tree = self.builder.random_tree(depth, "full" if index % 2 == 0 else "grow", self.evaluator.output_type)
            self.population.append(GPOrganism(organism_id=self._new_id(), genome=GPGenome(tree=tree), generation=0))
        self._apply_bloat_brake()
        self._evaluate_current()

    def set_primitive_profile(self, primitives) -> None:
        """Apply a declared curriculum profile to future variation operations.

        Existing organisms remain immutable historical programs. The shared RNG
        is retained, so a profile transition does not reseed or otherwise hide
        deterministic population state.
        """
        primitive_tuple = tuple(primitives)
        if not primitive_tuple:
            raise ValueError("a primitive profile must contain at least one primitive")
        self.builder = GPTreeBuilder(primitive_tuple, self.evaluator.terminals, self.rng)

    def step(self) -> GenerationStats:
        if not self.population:
            self.initialize()
        ranked = sorted(self.population, key=self._selection_score, reverse=True)
        next_population = [self._clone_elite(organism) for organism in ranked[:self.elitism_count]]
        while len(next_population) < self.population_size:
            left = self._tournament_select()
            right = self._tournament_select()
            tree = left.genome.tree.copy()
            parents = [left.organism_id]
            if self.rng.random() < self.crossover_rate:
                tree, _ = self.builder.subtree_crossover(tree, right.genome.tree)
                parents.append(right.organism_id)
            if self.rng.random() < self.mutation_rate:
                tree = self.builder.point_mutate(tree)
            if self.rng.random() < self.mutation_rate * 0.25:
                tree = self.builder.hoist_mutate(tree)
            if self.rng.random() < self.mutation_rate * 0.25:
                tree = self.builder.expand_mutate(tree)
            next_population.append(GPOrganism(
                organism_id=self._new_id(), generation=self.generation + 1, parent_ids=parents,
                genome=GPGenome(tree=tree, generation_created=self.generation + 1, parent_ids=parents),
            ))
        self.generation += 1
        self.population = next_population
        self._apply_bloat_brake()
        self._evaluate_current()
        return self.history[-1]

    def run(self, generations: int, target_fitness: float | None = None, checkpoint_every: int = 0, checkpoint: Callable[["GPPopulation"], None] | None = None) -> RunSummary:
        if generations < 0:
            raise ValueError("generations must be non-negative")
        if not self.population:
            self.initialize()
        for _ in range(generations):
            stats = self.step()
            if checkpoint and checkpoint_every and self.generation % checkpoint_every == 0:
                checkpoint(self)
            if target_fitness is not None and stats.best_fitness >= target_fitness:
                break
        champion = self.champion
        return RunSummary(generations=self.generation, best_fitness=champion.fitness, champion_id=champion.organism_id, target_reached=target_fitness is not None and champion.fitness >= target_fitness)

    @property
    def champion(self) -> GPOrganism:
        if not self.population:
            raise RuntimeError("population is not initialized")
        return max(self.population, key=lambda organism: organism.fitness)

    def save_checkpoint(self, path: str | Path) -> None:
        """Write a bounded, JSON-only checkpoint; no pickled code or callables."""
        Path(path).write_text(json.dumps(self.checkpoint_payload(), sort_keys=True), encoding="utf-8")

    def checkpoint_payload(self) -> dict[str, Any]:
        """Return a JSON-compatible bounded snapshot for an atomic caller-owned write."""
        return {
            "version": 2,
            "configuration": {
                "population_size": self.population_size, "tournament_size": self.tournament_size,
                "crossover_rate": self.crossover_rate, "mutation_rate": self.mutation_rate,
                "elitism_count": self.elitism_count, "max_depth": self.max_depth,
                "bloat_penalty": self.bloat_penalty,
            },
            "rng_state": _json_safe_state(self.rng.getstate()),
            "primitive_profile": [primitive.name for primitive in self.builder.primitives],
            "generation": self.generation, "population": [organism.to_dict() for organism in self.population],
            "history": [stat.__dict__ for stat in self.history[-1000:]],
            "hall_of_fame": [organism.to_dict() for organism in self.hall_of_fame],
        }

    @classmethod
    def from_checkpoint_payload(cls, evaluator: FitnessEvaluator, payload: Mapping[str, Any], primitives=None, terminals=None) -> "GPPopulation":
        """Restore a JSON checkpoint without deserializing executable code."""
        version = int(payload.get("version", 0))
        if version not in (1, 2):
            raise ValueError("unsupported GP checkpoint version")
        config = dict(payload.get("configuration", {}))
        if primitives is None and version >= 2:
            known = {primitive.name: primitive for primitive in ALL_REGISTERED_PRIMITIVES}
            profile_names = [str(name) for name in payload.get("primitive_profile", [])]
            missing = [name for name in profile_names if name not in known]
            if missing:
                raise ValueError(f"checkpoint primitive profile is unavailable: {', '.join(missing)}")
            primitives = tuple(known[name] for name in profile_names)
        population = cls(evaluator=evaluator, primitives=primitives, terminals=terminals, **config)
        population.generation = int(payload.get("generation", 0))
        population.population = [population._organism_from_payload(item) for item in payload.get("population", [])]
        population.hall_of_fame = [population._organism_from_payload(item) for item in payload.get("hall_of_fame", [])][-population.HALL_OF_FAME_MAX:]
        population.history = [GenerationStats(**item) for item in payload.get("history", [])][-1000:]
        if "rng_state" in payload:
            population.rng.setstate(_restore_tuple_state(payload["rng_state"]))
        if version == 1 and population.population:
            # Legacy v1 checkpoints omitted full fitness-result state. Preserve
            # backward readability, but v1 is not eligible for v8 exact-resume
            # claims because this evaluator refresh is necessarily approximate.
            results = population.evaluator.batch_evaluate(
                [organism.genome for organism in population.population], seed=population._training_seed()
            )
            for organism, result in zip(population.population, results):
                organism.fitness_result = result
                organism.genome.fitness = result.score
                organism.genome.fitness_variance = max(0.0, 1.0 - result.robustness)
        return population

    @classmethod
    def load_checkpoint(cls, evaluator: FitnessEvaluator, path: str | Path, primitives=None, terminals=None) -> "GPPopulation":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_checkpoint_payload(evaluator=evaluator, payload=payload, primitives=primitives, terminals=terminals)

    def _organism_from_payload(self, payload: Mapping[str, Any]) -> GPOrganism:
        fitness_payload = payload.get("fitness_result")
        return GPOrganism(
            organism_id=str(payload["organism_id"]),
            genome=GPGenome.from_dict(payload["genome"], primitives=self.builder.primitives),
            fitness_result=FitnessResult(**fitness_payload) if fitness_payload else None,
            generation=int(payload.get("generation", 0)),
            parent_ids=list(payload.get("parents", [])),
            age=int(payload.get("age", 0)),
            cultural_strategies=int(payload.get("cultural_strategies", 0)),
        )

    def _evaluate_current(self) -> None:
        results = self.evaluator.batch_evaluate(
            [organism.genome for organism in self.population], seed=self._training_seed()
        )
        for organism, result in zip(self.population, results):
            organism.fitness_result = result
            organism.genome.fitness = result.score
            organism.genome.evaluations += result.test_cases_total
            organism.genome.fitness_variance = max(0.0, 1.0 - result.robustness)
        self._update_hall_of_fame(self.champion)
        values = sorted(organism.fitness for organism in self.population)
        self.history.append(GenerationStats(
            generation=self.generation, best_fitness=values[-1], average_fitness=sum(values) / len(values),
            median_fitness=values[len(values) // 2], best_program_size=self.champion.genome.complexity(), population_size=len(values),
        ))

    def _training_seed(self) -> int:
        """Return the single deterministic training suite seed for this generation."""
        return self.generation + self.TRAIN_SEED_OFFSET

    def _apply_bloat_brake(self) -> None:
        """Hoist oversized descendants to their largest typed valid subtree.

        This is a deterministic post-reproduction safety sweep, not a mutation:
        it does not alter parentage, consume RNG state, or add a mutation event.
        Restricting replacement candidates to the original root result type keeps
        the typed interpreter/evaluator contract intact.
        """
        for organism in self.population:
            tree = organism.genome.tree
            if tree.size() <= self.BLOAT_MAX_NODES:
                continue
            same_type_subtrees = [
                node for _, _, node in self.builder._collect_nodes(tree)
                if node.result_type == tree.result_type and node.size() <= self.BLOAT_MAX_NODES
            ]
            if not same_type_subtrees:
                # Some task terminal profiles intentionally omit a terminal for
                # a result type (for example BOOL).  A fully expanded tree can
                # then have no same-type descendant below the size cap. Keep
                # the post-reproduction safety guarantee total with the same
                # deterministic type-correct fallback the interpreter uses for
                # malformed nodes; this consumes no RNG and is not a mutation.
                hoisted = GPNode(terminal_value=tree.fallback(), value_type=tree.result_type)
            else:
                hoisted = max(same_type_subtrees, key=lambda node: node.size()).copy()
            organism.genome.tree = hoisted
            organism.genome.primitives_used = sorted({
                node.primitive.name for _, _, node in self.builder._collect_nodes(hoisted) if node.primitive
            })

    def _selection_score(self, organism: GPOrganism) -> float:
        return organism.fitness - (self.bloat_penalty * organism.genome.complexity())

    def _tournament_select(self) -> GPOrganism:
        contenders = self.rng.sample(self.population, self.tournament_size)
        return max(contenders, key=self._selection_score)

    def _clone_elite(self, organism: GPOrganism) -> GPOrganism:
        genome = copy.deepcopy(organism.genome)
        genome.parent_ids = [organism.organism_id]
        genome.generation_created = self.generation + 1
        return GPOrganism(organism_id=self._new_id(), genome=genome, generation=self.generation + 1, parent_ids=[organism.organism_id], age=organism.age + 1)

    def _update_hall_of_fame(self, candidate: GPOrganism) -> None:
        self.hall_of_fame.append(copy.deepcopy(candidate))
        self.hall_of_fame.sort(key=lambda organism: organism.fitness, reverse=True)
        self.hall_of_fame = self.hall_of_fame[:self.HALL_OF_FAME_MAX]

    def _new_id(self) -> str:
        return f"gp-{self.generation:06d}-{uuid.UUID(int=self.rng.getrandbits(128)).hex[:12]}"


def _json_safe_state(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe_state(item) for item in value]
    return value


def _restore_tuple_state(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_restore_tuple_state(item) for item in value)
    return value
