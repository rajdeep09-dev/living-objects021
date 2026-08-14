"""Runnable Lamarckian living objects with durable culture and meta-evolution.

The module makes five engineering claims that are deliberately testable:

1. A strategy learned during a parent's lifetime is inherited by its child.
2. ``mutation_rate`` is a mutable genome field and evolves over generations.
3. Learned strategies are persisted in a SQLite memome and survive creator death.
4. Novel behaviour descriptors accumulate, and contribute a bounded novelty signal
   beside changing environmental performance rather than a single fixed objective.
5. Behaviours are source code stored as state and safely replaced at runtime via
   ``SelfModifyingObject`` delegation.

This is an artificial-life experiment, not a claim of biological equivalence or
open-ended general intelligence.  It is deterministic when a seed is supplied,
which makes the stated properties suitable for regression tests.

Run directly:

    python3 evolution/lamarckian.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import sqlite3
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from living_objects.core.reasoning import MockReasoningEngine
from living_objects.security.capability import CapabilityRegistry
from evolution.self_modifying import SelfModifyingObject


# ---------------------------------------------------------------------------
# Small in-memory runtime adapter
# ---------------------------------------------------------------------------


class _SimulationStore:
    """EventStore-shaped in-memory adapter for high-turnover simulations.

    The object lifecycle is kept in memory because hundreds of short-lived
    organisms are created by a run.  The *cultural* asset that must outlive
    organisms is not this runtime state; it is the separately SQLite-persisted
    :class:`Memome` below.
    """

    def __init__(self) -> None:
        self.objects: Dict[str, Dict[str, Any]] = {}
        self.memories: List[Dict[str, Any]] = []

    def create_object(
        self,
        object_id: str,
        name: str,
        identity_signature: str,
        initial_state: Mapping[str, Any],
    ) -> None:
        self.objects[object_id] = {
            "object_id": object_id,
            "name": name,
            "identity_signature": identity_signature,
            "current_state": json.dumps(dict(initial_state)),
            "state_version": 0,
            "is_alive": 1,
            "is_dormant": 0,
            "idle_steps": 0,
        }

    def update_state(self, object_id: str, state: Mapping[str, Any], version: int) -> None:
        if object_id in self.objects:
            self.objects[object_id]["current_state"] = json.dumps(dict(state))
            self.objects[object_id]["state_version"] = version

    def update_lifecycle(
        self,
        object_id: str,
        is_alive: Optional[int] = None,
        is_dormant: Optional[int] = None,
        idle_steps: Optional[int] = None,
    ) -> None:
        row = self.objects.get(object_id)
        if row is None:
            return
        if is_alive is not None:
            row["is_alive"] = is_alive
        if is_dormant is not None:
            row["is_dormant"] = is_dormant
        if idle_steps is not None:
            row["idle_steps"] = idle_steps

    def append_event(self, _: Any) -> None:
        """The simulation retains state but does not persist per-action audit events."""

    def store_memory(
        self,
        object_id: str,
        memory_type: str,
        content: Mapping[str, Any],
        confidence: float = 1.0,
        provenance: str = "",
    ) -> str:
        """Store the fallback episode API required by ``MemoryManager``."""
        memory_id = f"memory-{len(self.memories) + 1}"
        self.memories.append(
            {
                "memory_id": memory_id,
                "object_id": object_id,
                "memory_type": memory_type,
                "content": json.dumps(dict(content)),
                "confidence": confidence,
                "provenance": provenance,
            }
        )
        return memory_id

    def get_memories(
        self,
        object_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        matches = [
            memory
            for memory in self.memories
            if memory["object_id"] == object_id
            and (memory_type is None or memory["memory_type"] == memory_type)
        ]
        return list(reversed(matches[-limit:]))


# ---------------------------------------------------------------------------
# Persistent cultural memory
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Strategy:
    """A learned executable behaviour preserved in the population's memome."""

    strategy_id: str
    name: str
    source_code: str
    descriptor: str
    effectiveness: float
    author_id: str
    generation: int
    parent_ids: tuple[str, ...] = ()
    uses: int = 0
    contributions: int = 1
    created_at: str = ""

    def to_state(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["parent_ids"] = list(self.parent_ids)
        return payload

    @classmethod
    def from_state(cls, payload: Mapping[str, Any]) -> "Strategy":
        return cls(
            strategy_id=str(payload["strategy_id"]),
            name=str(payload["name"]),
            source_code=str(payload["source_code"]),
            descriptor=str(payload["descriptor"]),
            effectiveness=float(payload["effectiveness"]),
            author_id=str(payload["author_id"]),
            generation=int(payload["generation"]),
            parent_ids=tuple(payload.get("parent_ids", [])),
            uses=int(payload.get("uses", 0)),
            contributions=int(payload.get("contributions", 1)),
            created_at=str(payload.get("created_at", "")),
        )


class Memome:
    """SQLite-backed shared cultural memory.

    A memome is independent from the organisms that contribute to it.  Closing
    an organism or marking it dead has no effect on its deposited strategies;
    later populations can retrieve and install those behaviours through normal
    cultural transmission.
    """

    def __init__(self, database_path: os.PathLike[str] | str):
        self.database_path = str(database_path)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_code TEXT NOT NULL,
                descriptor TEXT NOT NULL,
                effectiveness REAL NOT NULL,
                author_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                parent_ids TEXT NOT NULL,
                uses INTEGER NOT NULL DEFAULT 0,
                contributions INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_strategy_quality "
            "ON strategies(effectiveness DESC, generation ASC)"
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_strategy_name ON strategies(name)"
        )
        self._connection.commit()

    @staticmethod
    def _strategy_id(name: str, source_code: str, descriptor: str) -> str:
        raw = f"{name}\x00{descriptor}\x00{source_code}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:20]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Strategy:
        return Strategy(
            strategy_id=row["strategy_id"],
            name=row["name"],
            source_code=row["source_code"],
            descriptor=row["descriptor"],
            effectiveness=float(row["effectiveness"]),
            author_id=row["author_id"],
            generation=int(row["generation"]),
            parent_ids=tuple(json.loads(row["parent_ids"])),
            uses=int(row["uses"]),
            contributions=int(row["contributions"]),
            created_at=row["created_at"],
        )

    def contribute(
        self,
        *,
        name: str,
        source_code: str,
        descriptor: str,
        effectiveness: float,
        author_id: str,
        generation: int,
        parent_ids: Sequence[str] = (),
    ) -> Strategy:
        """Persist a learned strategy and return its canonical cultural record."""
        if not name or not source_code or not descriptor:
            raise ValueError("name, source_code, and descriptor are required")
        strategy_id = self._strategy_id(name, source_code, descriptor)
        created_at = datetime.now(timezone.utc).isoformat()
        self._connection.execute(
            """
            INSERT INTO strategies
                (strategy_id, name, source_code, descriptor, effectiveness,
                 author_id, generation, parent_ids, uses, contributions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            ON CONFLICT(strategy_id) DO UPDATE SET
                effectiveness = MAX(strategies.effectiveness, excluded.effectiveness),
                contributions = strategies.contributions + 1
            """,
            (
                strategy_id,
                name,
                source_code,
                descriptor,
                float(effectiveness),
                author_id,
                int(generation),
                json.dumps(list(parent_ids)),
                created_at,
            ),
        )
        self._connection.commit()
        found = self.get(strategy_id)
        if found is None:  # pragma: no cover - defensive SQLite invariant
            raise RuntimeError("persisted strategy could not be retrieved")
        return found

    # Compatibility with the earlier in-memory prototype's naming.
    def store_strategy(
        self,
        name: str,
        code: str,
        effectiveness: float,
        author_id: str,
        generation: int,
        descriptor: Optional[str] = None,
    ) -> Strategy:
        return self.contribute(
            name=name,
            source_code=code,
            descriptor=descriptor or name,
            effectiveness=effectiveness,
            author_id=author_id,
            generation=generation,
        )

    def get(self, strategy_id: str) -> Optional[Strategy]:
        row = self._connection.execute(
            "SELECT * FROM strategies WHERE strategy_id = ?", (strategy_id,)
        ).fetchone()
        return self._from_row(row) if row is not None else None

    def retrieve_strategy(self, identifier: str) -> Optional[Strategy]:
        """Retrieve by immutable identifier or latest strategy name and count use."""
        row = self._connection.execute(
            """
            SELECT * FROM strategies
            WHERE strategy_id = ? OR name = ?
            ORDER BY CASE WHEN strategy_id = ? THEN 0 ELSE 1 END,
                     effectiveness DESC, generation DESC
            LIMIT 1
            """,
            (identifier, identifier, identifier),
        ).fetchone()
        if row is None:
            return None
        self._connection.execute(
            "UPDATE strategies SET uses = uses + 1 WHERE strategy_id = ?",
            (row["strategy_id"],),
        )
        self._connection.commit()
        refreshed = self.get(row["strategy_id"])
        return refreshed

    def retrieve_proven(
        self,
        *,
        limit: int = 8,
        minimum_effectiveness: float = 0.0,
    ) -> List[Strategy]:
        """Return high-performing cultural knowledge and record its use."""
        if limit <= 0:
            return []
        rows = self._connection.execute(
            """
            SELECT * FROM strategies
            WHERE effectiveness >= ?
            ORDER BY effectiveness DESC, contributions DESC, generation ASC
            LIMIT ?
            """,
            (float(minimum_effectiveness), int(limit)),
        ).fetchall()
        ids = [row["strategy_id"] for row in rows]
        if ids:
            self._connection.executemany(
                "UPDATE strategies SET uses = uses + 1 WHERE strategy_id = ?",
                [(strategy_id,) for strategy_id in ids],
            )
            self._connection.commit()
        return [self.get(strategy_id) for strategy_id in ids if self.get(strategy_id) is not None]  # type: ignore[list-item]

    def all_strategies(self) -> List[Strategy]:
        rows = self._connection.execute(
            "SELECT * FROM strategies ORDER BY generation, strategy_id"
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @property
    def strategy_count(self) -> int:
        return int(self._connection.execute("SELECT COUNT(*) FROM strategies").fetchone()[0])

    @property
    def novelty_count(self) -> int:
        return int(
            self._connection.execute("SELECT COUNT(DISTINCT descriptor) FROM strategies").fetchone()[0]
        )

    def cultural_complexity(self) -> float:
        """A stable culture metric combining repertoire breadth and proven quality."""
        row = self._connection.execute(
            "SELECT AVG(effectiveness) AS average, COUNT(DISTINCT descriptor) AS variety FROM strategies"
        ).fetchone()
        if not row or not row["variety"]:
            return 0.0
        return float(row["average"]) * math.log1p(int(row["variety"]))

    def get_summary(self) -> Dict[str, Any]:
        return {
            "strategies": self.strategy_count,
            "novel_descriptors": self.novelty_count,
            "cultural_complexity": round(self.cultural_complexity(), 4),
            "top_strategies": [strategy.to_state() for strategy in self.retrieve_proven(limit=5)],
        }

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "Memome":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Heritable genome and self-modifying organism
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LamarckianGenome:
    """Heritable parameters, including the rate at which the genome mutates."""

    learning_rate: float = 0.55
    curiosity: float = 0.55
    cooperation: float = 0.50
    cultural_receptivity: float = 0.75
    mutation_rate: float = 0.10
    inheritance_rate: float = 1.00

    def mutate(self, rng: random.Random) -> "LamarckianGenome":
        """Produce a child genome whose mutation rate is itself heritable and mutable."""
        def bounded(value: float, delta: float, low: float = 0.01, high: float = 1.0) -> float:
            return max(low, min(high, value + delta))

        # Mutation rate receives its own mutation. This is the meta-evolution hook.
        next_rate = bounded(
            self.mutation_rate,
            rng.gauss(0.0, self.mutation_rate * 0.22 + 0.008),
            low=0.01,
            high=0.45,
        )
        return LamarckianGenome(
            learning_rate=bounded(self.learning_rate, rng.gauss(0.0, next_rate * 0.22)),
            curiosity=bounded(self.curiosity, rng.gauss(0.0, next_rate * 0.22)),
            cooperation=bounded(self.cooperation, rng.gauss(0.0, next_rate * 0.18)),
            cultural_receptivity=bounded(
                self.cultural_receptivity, rng.gauss(0.0, next_rate * 0.18)
            ),
            mutation_rate=next_rate,
            inheritance_rate=bounded(
                self.inheritance_rate, rng.gauss(0.0, next_rate * 0.05), low=0.75, high=1.0
            ),
        )

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> "LamarckianGenome":
        recognized = {field: values[field] for field in cls.__dataclass_fields__ if field in values}
        return cls(**recognized)


_SAFE_ACTION = re.compile(r"^[a-z][a-z0-9_]*$")


def _strategy_source(action: str, effectiveness: float, generation: int) -> str:
    """Create a narrow, auditable strategy template from learning evidence."""
    if not _SAFE_ACTION.match(action):
        raise ValueError("strategy names must use lowercase letters, digits, and underscores")
    return (
        f"def action_{action}(self):\n"
        f"    # learned at generation {generation}; persisted in the memome\n"
        f"    learned_value = {effectiveness:.6f}\n"
        f"    return min(0.99, learned_value + 0.08 * self.genome.learning_rate)\n"
    )


class LamarckianOrganism(SelfModifyingObject):
    """A self-modifying object that carries learned programs across generations."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.genome = LamarckianGenome()
        self.generation = 0
        self.energy = 100.0
        self.dead = False
        self._memome: Optional[Memome] = None
        self.learned_strategies: Dict[str, Strategy] = {}
        self.behavior_descriptors: Dict[str, str] = {}
        self.parent_ids: tuple[str, ...] = ()

    @classmethod
    def born(
        cls,
        *,
        store: _SimulationStore,
        registry: CapabilityRegistry,
        reasoning: MockReasoningEngine,
        memome: Memome,
        name: str,
        genome: Optional[LamarckianGenome] = None,
        generation: int = 0,
        parent_ids: Sequence[str] = (),
    ) -> "LamarckianOrganism":
        genome = genome or LamarckianGenome()
        organism = cls.create(
            store=store,
            registry=registry,
            reasoning=reasoning,
            name=name,
            initial_state={
                "genome": genome.to_dict(),
                "generation": generation,
                "energy": 100.0,
                "dead": False,
                "parent_ids": list(parent_ids),
                "learned_strategies": {},
                "behavior_descriptors": {},
            },
        )
        organism.genome = genome
        organism.generation = generation
        organism.parent_ids = tuple(parent_ids)
        organism._memome = memome
        return organism

    def hydrate_lamarckian_state(self) -> None:
        """Restore behavior and learned-strategy state after a persisted reload."""
        self.load_behaviors_from_state()
        genome = self.get_state("genome", {})
        if isinstance(genome, Mapping):
            self.genome = LamarckianGenome.from_dict(genome)
        self.generation = int(self.get_state("generation", 0))
        self.energy = float(self.get_state("energy", 100.0))
        self.dead = bool(self.get_state("dead", False))
        self.parent_ids = tuple(self.get_state("parent_ids", []))
        stored = self.get_state("learned_strategies", {})
        if isinstance(stored, Mapping):
            self.learned_strategies = {
                strategy_id: Strategy.from_state(payload)
                for strategy_id, payload in stored.items()
                if isinstance(payload, Mapping)
            }
        descriptors = self.get_state("behavior_descriptors", {})
        self.behavior_descriptors = dict(descriptors) if isinstance(descriptors, Mapping) else {}

    def attach_memome(self, memome: Memome) -> None:
        self._memome = memome

    @property
    def complexity(self) -> int:
        return len(self._behavior_genes)

    def _persist_lamarckian_state(self) -> None:
        self.set_state("genome", self.genome.to_dict())
        self.set_state("generation", self.generation)
        self.set_state("energy", self.energy)
        self.set_state("dead", self.dead)
        self.set_state("parent_ids", list(self.parent_ids))
        self.set_state(
            "learned_strategies",
            {strategy_id: strategy.to_state() for strategy_id, strategy in self.learned_strategies.items()},
        )
        self.set_state("behavior_descriptors", self.behavior_descriptors)

    def learn(
        self,
        strategy_name: str,
        source_code: Optional[str] = None,
        *,
        descriptor: Optional[str] = None,
        effectiveness: float = 0.65,
        parent_ids: Sequence[str] = (),
    ) -> Strategy:
        """Learn, install, and culturally publish a new executable strategy."""
        if self._memome is None:
            raise RuntimeError("A memome must be attached before learning")
        if not _SAFE_ACTION.match(strategy_name):
            raise ValueError("strategy_name must be a safe action identifier")
        source = source_code or _strategy_source(strategy_name, effectiveness, self.generation)
        if not self.set_behavior(strategy_name, source):
            raise ValueError("learned strategy did not compile")
        strategy = self._memome.contribute(
            name=strategy_name,
            source_code=source,
            descriptor=descriptor or strategy_name,
            effectiveness=effectiveness,
            author_id=self.object_id,
            generation=self.generation,
            parent_ids=parent_ids,
        )
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        self._persist_lamarckian_state()
        return strategy

    def install_strategy(self, strategy: Strategy) -> bool:
        """Install a strategy obtained from a parent or a cultural ancestor."""
        if not self.set_behavior(strategy.name, strategy.source_code):
            return False
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        self._persist_lamarckian_state()
        return True

    def adopt_from_memome(self, *, limit: int = 2, minimum_effectiveness: float = 0.50) -> List[str]:
        """Use knowledge contributed by any previous organism, including dead ones."""
        if self._memome is None:
            return []
        adopted: List[str] = []
        for strategy in self._memome.retrieve_proven(
            limit=limit, minimum_effectiveness=minimum_effectiveness
        ):
            if strategy.strategy_id in self.learned_strategies:
                continue
            if self.install_strategy(strategy):
                adopted.append(strategy.strategy_id)
        return adopted

    def reproduce(self, rng: Optional[random.Random] = None) -> "LamarckianOrganism":
        """Create a child inheriting learned lifetime behavior and evolved meta-traits."""
        if self._memome is None or self._store is None or self._registry is None or self._reasoning is None:
            raise RuntimeError("Organism must be attached to a runtime and memome before reproduction")
        rng = rng or random.Random()
        child_genome = self.genome.mutate(rng)
        child = LamarckianOrganism.born(
            store=self._store,  # type: ignore[arg-type]
            registry=self._registry,
            reasoning=self._reasoning,  # type: ignore[arg-type]
            memome=self._memome,
            name=f"{self.name}-g{self.generation + 1}",
            genome=child_genome,
            generation=self.generation + 1,
            parent_ids=(self.object_id,),
        )

        # Hard Lamarckian contract: pass strategies acquired during lifetime.
        for strategy in self.learned_strategies.values():
            if rng.random() <= self.genome.inheritance_rate:
                child.install_strategy(strategy)
        # Cultural transmission is not limited to direct biological ancestry.
        if child.genome.cultural_receptivity >= 0.40:
            child.adopt_from_memome(limit=2)
        child._persist_lamarckian_state()
        return child

    def execute_strategy(self, name: str) -> Any:
        """Execute state-stored program code through the parent's safe delegate."""
        return self.execute_behavior(name)

    def behavior_quality(self) -> float:
        """Measure the current repertoire without allowing broken code to terminate a run."""
        if not self._behavior_genes:
            return 0.0
        values: List[float] = []
        for action in self._behavior_genes:
            result = self.execute_strategy(action)
            if isinstance(result, (int, float)):
                values.append(float(result))
        return sum(values) / len(values) if values else 0.0

    def die(self, cause: str = "lifecycle_complete") -> None:
        """End an organism while preserving its previously published culture."""
        self.dead = True
        self.is_alive = False
        self.set_state("death_cause", cause)
        self._persist_lamarckian_state()
        self.save()


# ---------------------------------------------------------------------------
# Evolutionary system and metrics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenerationMetrics:
    generation: int
    population: int
    average_fitness: float
    cultural_complexity: float
    average_mutation_rate: float
    novelty_count: int
    archive_size: int
    behaviors_per_organism: float

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LamarckianEcosystem:
    """A seeded, testable ecosystem with cultural and meta-evolution signals."""

    def __init__(
        self,
        archive_path: os.PathLike[str] | str | None = None,
        *,
        seed: int = 21,
        population_size: int = 20,
    ) -> None:
        if population_size < 2:
            raise ValueError("population_size must be at least 2")
        self.rng = random.Random(seed)
        self.population_size = population_size
        self.generation = 0
        self.population: List[LamarckianOrganism] = []
        self.history: List[GenerationMetrics] = []
        self._seen_descriptors: set[str] = set()
        self._temporary_directory: Optional[tempfile.TemporaryDirectory[str]] = None
        if archive_path is None:
            self._temporary_directory = tempfile.TemporaryDirectory(prefix="lamarckian-memome-")
            archive_path = Path(self._temporary_directory.name) / "memome.sqlite"
        else:
            path = Path(archive_path)
            path.parent.mkdir(parents=True, exist_ok=True)
        self.memome = Memome(archive_path)
        self.store = _SimulationStore()
        self.registry = CapabilityRegistry()
        self.reasoning = MockReasoningEngine()

    def close(self) -> None:
        self.memome.close()
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None

    def __enter__(self) -> "LamarckianEcosystem":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _founder_genome(self, index: int) -> LamarckianGenome:
        # A narrow but non-uniform initial distribution makes meta-evolution observable.
        return LamarckianGenome(
            learning_rate=0.46 + 0.015 * (index % 5),
            curiosity=0.45 + 0.020 * (index % 4),
            cooperation=0.45 + 0.010 * (index % 6),
            cultural_receptivity=0.65 + 0.020 * (index % 5),
            mutation_rate=0.075 + 0.010 * (index % 5),
            inheritance_rate=1.0,
        )

    def spawn(
        self,
        name: str,
        genome: Optional[LamarckianGenome] = None,
        generation: Optional[int] = None,
    ) -> LamarckianOrganism:
        organism = LamarckianOrganism.born(
            store=self.store,
            registry=self.registry,
            reasoning=self.reasoning,
            memome=self.memome,
            name=name,
            genome=genome or self._founder_genome(len(self.population)),
            generation=self.generation if generation is None else generation,
        )
        self.population.append(organism)
        return organism

    def spawn_population(self, size: Optional[int] = None) -> List[LamarckianOrganism]:
        if self.population:
            return list(self.population)
        count = self.population_size if size is None else size
        for index in range(count):
            self.spawn(f"founder-{index:02d}", generation=0)
        self._record_metrics()
        return list(self.population)

    def _environment(self) -> Dict[str, float | str]:
        """Changing context prevents any one static score from defining success."""
        modes = ("resource", "social", "navigation", "shelter", "coordination")
        return {
            "mode": modes[self.generation % len(modes)],
            "pressure": 0.35 + 0.45 * ((self.generation * 7) % 11) / 10,
            "complexity": 0.30 + 0.50 * ((self.generation * 3) % 9) / 8,
        }

    def _adaptive_score(
        self,
        organism: LamarckianOrganism,
        environment: Mapping[str, float | str],
    ) -> float:
        """Evaluate dynamic context, usable culture, and bounded novelty together."""
        repertoire = organism.behavior_quality()
        descriptors = set(organism.behavior_descriptors.values())
        unseen = descriptors - self._seen_descriptors
        novelty_bonus = min(0.16, 0.035 * len(unseen))
        culture_bonus = min(0.22, 0.018 * organism.complexity)
        environment_factor = (
            0.04 * organism.genome.learning_rate
            + 0.04 * organism.genome.curiosity
            + 0.03 * float(environment["complexity"])
        )
        mutation_stability = 0.05 * (1.0 - abs(organism.genome.mutation_rate - 0.12) / 0.33)
        return max(
            0.0,
            min(0.99, 0.35 + 0.35 * repertoire + culture_bonus + novelty_bonus + environment_factor + mutation_stability),
        )

    def _innovation_source(self, name: str, generation: int, effectiveness: float) -> str:
        return _strategy_source(name, effectiveness, generation)

    def _learn_from_lifetime(
        self,
        organism: LamarckianOrganism,
        environment: Mapping[str, float | str],
        innovation_index: int,
    ) -> Strategy:
        descriptor = f"{environment['mode']}:path:{self.generation:03d}:{innovation_index}"
        action = f"learned_g{self.generation:03d}_{innovation_index}"
        effectiveness = min(
            0.94,
            0.54
            + 0.0055 * self.generation
            + 0.08 * organism.genome.learning_rate
            + 0.04 * organism.genome.curiosity,
        )
        ancestors = self.memome.retrieve_proven(limit=2, minimum_effectiveness=0.50)
        parent_ids = tuple(strategy.strategy_id for strategy in ancestors)
        return organism.learn(
            action,
            self._innovation_source(action, self.generation, effectiveness),
            descriptor=descriptor,
            effectiveness=effectiveness,
            parent_ids=parent_ids,
        )

    def step(self) -> GenerationMetrics:
        """Advance one generation through learning, cultural sharing, and selection."""
        if not self.population:
            self.spawn_population()
        self.generation += 1
        environment = self._environment()

        # At least two organisms learn each generation.  Learning is lifetime
        # acquisition, then culture makes it available beyond parentage.
        innovators = sorted(self.population, key=lambda item: item.genome.curiosity, reverse=True)[:2]
        for index, organism in enumerate(innovators):
            if organism.complexity < 15:
                self._learn_from_lifetime(organism, environment, index)

        scored = sorted(
            ((self._adaptive_score(organism, environment), organism) for organism in self.population),
            key=lambda item: item[0],
            reverse=True,
        )
        self._seen_descriptors.update(
            descriptor for organism in self.population for descriptor in organism.behavior_descriptors.values()
        )

        elite_count = max(2, len(scored) // 3)
        elites = [organism for _, organism in scored[:elite_count]]
        next_population: List[LamarckianOrganism] = []
        for index in range(self.population_size):
            parent = elites[index % len(elites)]
            child = parent.reproduce(self.rng)
            child.generation = self.generation
            child.set_state("generation", self.generation)
            next_population.append(child)
        for organism in self.population:
            organism.die("replaced_after_reproduction")
        self.population = next_population
        return self._record_metrics(environment)

    def _record_metrics(self, environment: Optional[Mapping[str, float | str]] = None) -> GenerationMetrics:
        if not self.population:
            raise RuntimeError("cannot record an empty population")
        environment = environment or {"mode": "resource", "pressure": 0.5, "complexity": 0.5}
        scores = [self._adaptive_score(organism, environment) for organism in self.population]
        metric = GenerationMetrics(
            generation=self.generation,
            population=len(self.population),
            average_fitness=sum(scores) / len(scores),
            cultural_complexity=self.memome.cultural_complexity(),
            average_mutation_rate=(
                sum(organism.genome.mutation_rate for organism in self.population) / len(self.population)
            ),
            novelty_count=self.memome.novelty_count,
            archive_size=self.memome.strategy_count,
            behaviors_per_organism=(sum(organism.complexity for organism in self.population) / len(self.population)),
        )
        self.history.append(metric)
        return metric

    def get_statistics(self) -> Dict[str, Any]:
        metric = self.history[-1] if self.history else self._record_metrics()
        return metric.as_dict() | {"memome_summary": self.memome.get_summary()}

    def get_champion(self) -> Optional[LamarckianOrganism]:
        if not self.population:
            return None
        environment = self._environment()
        return max(self.population, key=lambda organism: self._adaptive_score(organism, environment))

    def run_evolution(
        self,
        generations: int = 50,
        population_size: Optional[int] = None,
        *,
        report: bool = True,
    ) -> Dict[str, Any]:
        """Run the requested proof demonstration and return its complete history."""
        if generations < 0:
            raise ValueError("generations must not be negative")
        if population_size is not None:
            if self.population:
                raise ValueError("population size cannot change after initialization")
            if population_size < 2:
                raise ValueError("population_size must be at least 2")
            self.population_size = population_size
        self.spawn_population()
        for _ in range(generations):
            self.step()
        if report:
            self.print_progress()
        return {
            "history": [metric.as_dict() for metric in self.history],
            "final_stats": self.get_statistics(),
            "champion": self.get_champion(),
            "memome_summary": self.memome.get_summary(),
        }

    def print_progress(self) -> None:
        """Print the 50-generation proof table requested by the task."""
        print("Gen | Pop | Avg Fitness | Culture | Avg Mutation Rate | Novelties | Archive | Behaviors/Org")
        print("----+-----+-------------+---------+-------------------+-----------+---------+--------------")
        milestones = {0, 10, 20, 30, 40, 50}
        for metric in self.history:
            if metric.generation in milestones:
                print(
                    f"{metric.generation:>3} | {metric.population:>3} | {metric.average_fitness:>11.3f} |"
                    f" {metric.cultural_complexity:>7.3f} | {metric.average_mutation_rate:>17.4f} |"
                    f" {metric.novelty_count:>9} | {metric.archive_size:>7} | {metric.behaviors_per_organism:>12.1f}"
                )


def run_lamarckian_demo() -> None:
    """Run a 50-generation, reproducible proof demonstration."""
    print("\nLAMARCKIAN LIVING OBJECTS — 50-GENERATION PROOF RUN\n")
    with LamarckianEcosystem(seed=21, population_size=20) as ecosystem:
        results = ecosystem.run_evolution(generations=50, report=True)
        initial = results["history"][0]
        final = results["history"][-1]
        print("\nVerified run deltas")
        print(f"  Fitness: {initial['average_fitness']:.3f} -> {final['average_fitness']:.3f}")
        print(f"  Culture: {initial['cultural_complexity']:.3f} -> {final['cultural_complexity']:.3f}")
        print(f"  Mutation rate: {initial['average_mutation_rate']:.4f} -> {final['average_mutation_rate']:.4f}")
        print(f"  Novel descriptors: {initial['novelty_count']} -> {final['novelty_count']}")


if __name__ == "__main__":
    run_lamarckian_demo()
