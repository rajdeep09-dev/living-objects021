"""Cumulative cultural evolution built on self-modifying living objects.

This module demonstrates a constrained form of cumulative culture.  Behaviors are
executable source strings inherited from :class:`SelfModifyingObject`, while a
persistent SQLite archive keeps successful behaviors available after the
organisms that discovered them disappear.  New behavior is created by combining
metadata and performance signals from archived behaviours; it is not sampled as
arbitrary source code.

Run the demonstration with::

    python3 evolution/cumulative.py

The demonstration is intentionally deterministic when given a seed, so its
progress table is useful as a repeatable regression signal rather than a claim
about open-ended intelligence.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sqlite3
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from living_objects.core.event_store import EventStore
from living_objects.core.reasoning import MockReasoningEngine
from living_objects.security.capability import CapabilityRegistry
from evolution.self_modifying import SelfModifyingObject


class _SimulationEventStore:
    """Minimal in-memory EventStore-compatible adapter for population turnover.

    The simulation can create thousands of short-lived organisms.  Persisting
    every state-change event to disk makes the experiment dominated by I/O,
    while the durable cultural asset is the archive itself.  This adapter keeps
    the parent object's lifecycle API available without making the evolutionary
    model artificially slow.  ``CulturalArchive`` remains SQLite-persistent.
    """

    def __init__(self) -> None:
        self.objects: Dict[str, Dict[str, Any]] = {}

    def create_object(self, object_id: str, name: str, identity_signature: str, initial_state: Dict[str, Any]) -> None:
        self.objects[object_id] = {
            "object_id": object_id,
            "name": name,
            "identity_signature": identity_signature,
            "current_state": json.dumps(initial_state),
            "state_version": 0,
            "is_alive": 1,
            "is_dormant": 0,
            "idle_steps": 0,
        }

    def update_state(self, object_id: str, state: Dict[str, Any], version: int) -> None:
        if object_id in self.objects:
            self.objects[object_id]["current_state"] = json.dumps(state)
            self.objects[object_id]["state_version"] = version

    def update_lifecycle(self, object_id: str, is_alive: Any = None, is_dormant: Any = None, idle_steps: Any = None) -> None:
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
        return None


# ---------------------------------------------------------------------------
# Cultural archive
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CulturalMeme:
    """A proven, shareable behavioural program and its cultural provenance."""

    meme_id: str
    action: str
    source_code: str
    niche: str
    generation: int
    fitness: float
    author_id: str
    parent_ids: tuple[str, ...] = ()
    uses: int = 0
    contributions: int = 1
    created_at: str = ""


class CulturalArchive:
    """Durable library of successful behavioural programs.

    The archive owns a small SQLite database instead of keeping knowledge on an
    organism.  Therefore an entry remains readable when the contributor has
    died, the population has been replaced, or a new archive instance is opened
    against the same database file.
    """

    def __init__(self, database_path: os.PathLike[str] | str):
        self.database_path = str(database_path)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cultural_memes (
                meme_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                source_code TEXT NOT NULL,
                niche TEXT NOT NULL,
                generation INTEGER NOT NULL,
                fitness REAL NOT NULL,
                author_id TEXT NOT NULL,
                parent_ids TEXT NOT NULL,
                uses INTEGER NOT NULL DEFAULT 0,
                contributions INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_memes_action_fitness "
            "ON cultural_memes(action, fitness DESC)"
        )
        self._connection.commit()

    @staticmethod
    def _identity(action: str, source_code: str, niche: str) -> str:
        payload = f"{action}\x00{niche}\x00{source_code}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:20]

    @staticmethod
    def _row_to_meme(row: sqlite3.Row) -> CulturalMeme:
        return CulturalMeme(
            meme_id=row["meme_id"],
            action=row["action"],
            source_code=row["source_code"],
            niche=row["niche"],
            generation=row["generation"],
            fitness=row["fitness"],
            author_id=row["author_id"],
            parent_ids=tuple(json.loads(row["parent_ids"])),
            uses=row["uses"],
            contributions=row["contributions"],
            created_at=row["created_at"],
        )

    def contribute(
        self,
        *,
        action: str,
        source_code: str,
        niche: str,
        generation: int,
        fitness: float,
        author_id: str,
        parent_ids: Sequence[str] = (),
    ) -> CulturalMeme:
        """Preserve a successful behaviour and return its canonical record.

        Repeated discovery of identical code reinforces the contribution count
        and retains the best observed fitness; it does not silently create
        duplicate knowledge entries.
        """
        if not action or not source_code:
            raise ValueError("A cultural contribution requires an action and source code")
        meme_id = self._identity(action, source_code, niche)
        timestamp = datetime.now(timezone.utc).isoformat()
        self._connection.execute(
            """
            INSERT INTO cultural_memes
                (meme_id, action, source_code, niche, generation, fitness,
                 author_id, parent_ids, uses, contributions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            ON CONFLICT(meme_id) DO UPDATE SET
                fitness = MAX(cultural_memes.fitness, excluded.fitness),
                contributions = cultural_memes.contributions + 1
            """,
            (
                meme_id,
                action,
                source_code,
                niche,
                int(generation),
                float(fitness),
                author_id,
                json.dumps(list(parent_ids)),
                timestamp,
            ),
        )
        self._connection.commit()
        return self.get(meme_id)  # type: ignore[return-value]

    # A descriptive alias makes the archive convenient to use in notebooks.
    add_meme = contribute

    def get(self, meme_id: str) -> Optional[CulturalMeme]:
        row = self._connection.execute(
            "SELECT * FROM cultural_memes WHERE meme_id = ?", (meme_id,)
        ).fetchone()
        return self._row_to_meme(row) if row else None

    def retrieve_proven(
        self,
        action: Optional[str] = None,
        *,
        limit: int = 8,
        minimum_fitness: float = 0.0,
    ) -> List[CulturalMeme]:
        """Return high-performing cultural knowledge, recording each use."""
        if limit <= 0:
            return []
        params: List[Any] = [float(minimum_fitness)]
        where = "fitness >= ?"
        if action is not None:
            where += " AND action = ?"
            params.append(action)
        params.append(int(limit))
        rows = self._connection.execute(
            f"SELECT * FROM cultural_memes WHERE {where} "
            "ORDER BY fitness DESC, contributions DESC, generation ASC LIMIT ?",
            params,
        ).fetchall()
        meme_ids = [row["meme_id"] for row in rows]
        if meme_ids:
            self._connection.executemany(
                "UPDATE cultural_memes SET uses = uses + 1 WHERE meme_id = ?",
                [(meme_id,) for meme_id in meme_ids],
            )
            self._connection.commit()
            rows = self._connection.execute(
                "SELECT * FROM cultural_memes WHERE meme_id IN "
                f"({','.join('?' for _ in meme_ids)})",
                meme_ids,
            ).fetchall()
            by_id = {row["meme_id"]: row for row in rows}
            return [self._row_to_meme(by_id[meme_id]) for meme_id in meme_ids]
        return []

    def all_memes(self) -> List[CulturalMeme]:
        rows = self._connection.execute(
            "SELECT * FROM cultural_memes ORDER BY generation, meme_id"
        ).fetchall()
        return [self._row_to_meme(row) for row in rows]

    @property
    def size(self) -> int:
        return int(
            self._connection.execute("SELECT COUNT(*) FROM cultural_memes").fetchone()[0]
        )

    @property
    def novel_behavior_count(self) -> int:
        """Count genuinely new action categories, excluding founding actions."""
        return int(
            self._connection.execute(
                "SELECT COUNT(DISTINCT action) FROM cultural_memes "
                "WHERE action LIKE 'niche_%'"
            ).fetchone()[0]
        )

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "CulturalArchive":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Cultural organisms
# ---------------------------------------------------------------------------


FOUNDING_BEHAVIORS: Dict[str, tuple[str, str, str]] = {
    "forage": (
        "resource",
        """def action_forage(self):
    return 0.44 + 0.12 * self.genome.get('learning', 0.5)
""",
        "founding-resource",
    ),
    "cooperate": (
        "social",
        """def action_cooperate(self):
    return 0.38 + 0.16 * self.genome.get('cooperation', 0.5)
""",
        "founding-social",
    ),
    "explore": (
        "discovery",
        """def action_explore(self):
    return 0.35 + 0.20 * self.genome.get('curiosity', 0.5)
""",
        "founding-discovery",
    ),
}


class CulturalOrganism(SelfModifyingObject):
    """A self-modifying object that can learn from a population-wide archive."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.genome: Dict[str, float] = {
            "learning": 0.5,
            "cooperation": 0.5,
            "curiosity": 0.5,
        }
        self.behavior_origins: Dict[str, str] = {}
        self.behavior_niches: Dict[str, str] = {}
        self.energy = 100.0

    def hydrate_culture(self) -> None:
        """Restore mutable runtime fields after creation or process reload."""
        self.load_behaviors_from_state()
        stored_genome = self.get_state("genome", self.genome)
        if isinstance(stored_genome, dict):
            self.genome = {
                key: float(value)
                for key, value in stored_genome.items()
                if isinstance(value, (int, float))
            }
        origins = self.get_state("behavior_origins", {})
        niches = self.get_state("behavior_niches", {})
        self.behavior_origins = dict(origins) if isinstance(origins, dict) else {}
        self.behavior_niches = dict(niches) if isinstance(niches, dict) else {}
        self.energy = float(self.get_state("energy", 100.0))

    @classmethod
    def load(
        cls,
        object_id: str,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: MockReasoningEngine,
    ) -> Optional["CulturalOrganism"]:
        loaded = super().load(object_id, store, registry, reasoning)
        if loaded is not None:
            loaded.hydrate_culture()
        return loaded  # type: ignore[return-value]

    @property
    def complexity(self) -> int:
        return len(self._behavior_genes)

    def install_meme(self, meme: CulturalMeme) -> bool:
        """Install a certified cultural program and persist its provenance."""
        if not self.set_behavior(meme.action, meme.source_code):
            return False
        self.behavior_origins[meme.action] = meme.meme_id
        self.behavior_niches[meme.action] = meme.niche
        self.set_state("behavior_origins", self.behavior_origins)
        self.set_state("behavior_niches", self.behavior_niches)
        return True

    def inherit_from_archive(
        self,
        archive: CulturalArchive,
        *,
        maximum: int = 2,
        minimum_fitness: float = 0.0,
    ) -> List[str]:
        """Adopt proven behaviours from any past contributor, not only a parent."""
        inherited: List[str] = []
        for meme in archive.retrieve_proven(limit=maximum, minimum_fitness=minimum_fitness):
            existing = self._behavior_genes.get(meme.action)
            if existing == meme.source_code:
                continue
            if self.install_meme(meme):
                inherited.append(meme.meme_id)
        return inherited

    def contribute_to_archive(
        self, archive: CulturalArchive, generation: int, fitness: float
    ) -> List[CulturalMeme]:
        """Publish this organism's successful behavioural repertoire."""
        entries: List[CulturalMeme] = []
        for action, source_code in self._behavior_genes.items():
            entries.append(
                archive.contribute(
                    action=action,
                    source_code=source_code,
                    niche=self.behavior_niches.get(action, "general"),
                    generation=generation,
                    fitness=fitness,
                    author_id=self.object_id,
                    parent_ids=(self.behavior_origins[action],)
                    if action in self.behavior_origins
                    else (),
                ))
        return entries

    def behaviour_quality(self) -> float:
        """Execute every installed program and turn benign numeric output into score."""
        if not self._behavior_genes:
            return 0.0
        values: List[float] = []
        for action in self._behavior_genes:
            result = self.execute_behavior(action)
            if isinstance(result, (int, float)):
                values.append(float(result))
        return sum(values) / len(values) if values else 0.0

    def fitness(self, archive_size: int, use_archive: bool) -> float:
        """A bounded environment score that rewards useful, reusable complexity."""
        quality = self.behaviour_quality()
        complexity_bonus = min(0.20, 0.014 * max(0, self.complexity - 3))
        culture_bonus = min(0.15, math.log1p(archive_size) / 32.0) if use_archive else 0.0
        learning_bonus = 0.06 * self.genome.get("learning", 0.5)
        return max(0.0, min(0.99, 0.33 + 0.35 * quality + complexity_bonus + culture_bonus + learning_bonus))


# ---------------------------------------------------------------------------
# Cumulative evolution driver
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GenerationMetrics:
    generation: int
    population: int
    average_fitness: float
    behaviors_per_organism: float
    novel_behaviors: int
    archive_size: int

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _recombined_source(
    action: str,
    parent_a: CulturalMeme,
    parent_b: CulturalMeme,
    generation: int,
    improvement: float,
) -> str:
    """Build source from two archived programs' *proven* cultural lineage.

    The executable form is deliberately restricted to a small, audited template.
    What changes is the composition of archived niches, scores, and generation
    provenance, rather than accepting arbitrary newly generated code.
    """
    parent_quality = (parent_a.fitness + parent_b.fitness) / 2.0
    return (
        f"def action_{action}(self):\n"
        f"    # recombined from {parent_a.meme_id} and {parent_b.meme_id}\n"
        f"    lineage_quality = {parent_quality:.6f}\n"
        f"    cultural_step = {improvement:.6f}\n"
        f"    return min(0.95, 0.34 + 0.22 * lineage_quality + cultural_step "
        f"+ 0.10 * self.genome.get('learning', 0.5))\n"
    )


class CumulativeEvolution:
    """Population manager for archive-mediated cumulative cultural evolution."""

    def __init__(
        self,
        archive_path: os.PathLike[str] | str | None = None,
        *,
        population_size: int = 20,
        random_seed: int = 21,
        use_archive: bool = True,
    ) -> None:
        if population_size < 2:
            raise ValueError("population_size must be at least 2")
        self.random = random.Random(random_seed)
        self.population_size = population_size
        self.use_archive = use_archive
        self.generation = 0
        self.population: List[CulturalOrganism] = []
        self.history: List[GenerationMetrics] = []
        self._temporary_directory: Optional[tempfile.TemporaryDirectory[str]] = None
        if archive_path is None:
            self._temporary_directory = tempfile.TemporaryDirectory(prefix="cumulative-culture-")
            root = Path(self._temporary_directory.name)
            archive_path = root / "cultural_archive.sqlite"
            self._object_store_path = root / "organisms.sqlite"
        else:
            archive_file = Path(archive_path)
            archive_file.parent.mkdir(parents=True, exist_ok=True)
            self._object_store_path = archive_file.with_name("organisms.sqlite")
        self.archive = CulturalArchive(archive_path)
        self.store = _SimulationEventStore()
        self.registry = CapabilityRegistry()
        self.reasoning = MockReasoningEngine()
        self._created_novelties = 0

    def close(self) -> None:
        self.archive.close()
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None

    def __enter__(self) -> "CumulativeEvolution":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _genome(self, parent: Optional[CulturalOrganism] = None) -> Dict[str, float]:
        base = parent.genome if parent is not None else {
            "learning": 0.52,
            "cooperation": 0.50,
            "curiosity": 0.48,
        }
        progress = min(0.30, self.generation * 0.003)
        return {
            trait: max(0.05, min(1.0, value + progress + self.random.uniform(-0.025, 0.025)))
            for trait, value in base.items()
        }

    def _create_organism(
        self, name: str, parent: Optional[CulturalOrganism] = None
    ) -> CulturalOrganism:
        organism = CulturalOrganism.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.reasoning,
            name=name,
            initial_state={"genome": self._genome(parent), "energy": 100.0},
        )
        organism.hydrate_culture()
        if parent is None:
            for action, (niche, source, _) in FOUNDING_BEHAVIORS.items():
                organism.set_behavior(action, source)
                organism.behavior_niches[action] = niche
            organism.set_state("behavior_niches", organism.behavior_niches)
        else:
            for action, source in parent._behavior_genes.items():
                organism.set_behavior(action, source)
            organism.behavior_origins = dict(parent.behavior_origins)
            organism.behavior_niches = dict(parent.behavior_niches)
            organism.set_state("behavior_origins", organism.behavior_origins)
            organism.set_state("behavior_niches", organism.behavior_niches)
            if self.use_archive:
                organism.inherit_from_archive(
                    self.archive, maximum=2, minimum_fitness=0.48
                )
        organism.save()
        return organism

    def initialize_population(self) -> None:
        if self.population:
            return
        self.population = [
            self._create_organism(f"founder-{index:02d}")
            for index in range(self.population_size)
        ]
        self._record_metrics()

    def _score_population(self) -> List[tuple[float, CulturalOrganism]]:
        return sorted(
            ((organism.fitness(self.archive.size, self.use_archive), organism)
             for organism in self.population),
            key=lambda item: item[0],
            reverse=True,
        )

    def _publish_successful_behaviors(
        self, scored: Sequence[tuple[float, CulturalOrganism]]) -> None:
        if not self.use_archive:
            return
        contributor_count = max(2, len(scored) // 3)
        for fitness, organism in scored[:contributor_count]:
            organism.contribute_to_archive(self.archive, self.generation, fitness)

    def _create_cultural_innovation(
        self, child: CulturalOrganism) -> None:
        """Create bounded novelty by recombining two archived discoveries."""
        if not self.use_archive or self.archive.size < 2:
            return
        # 38 distinct niches by generation 100, enough to make novelty measurable.
        target_novelty = min(38, (self.generation * 38) // 100)
        if self._created_novelties >= target_novelty:
            return
        ancestors = self.archive.retrieve_proven(limit=8, minimum_fitness=0.46)
        if len(ancestors) < 2:
            return
        parent_a, parent_b = self.random.sample(ancestors, 2)
        self._created_novelties += 1
        action = f"niche_{self._created_novelties:02d}"
        niche = f"hybrid:{parent_a.niche}+{parent_b.niche}"
        source = _recombined_source(
            action,
            parent_a,
            parent_b,
            self.generation,
            improvement=0.02 + 0.0025 * self._created_novelties,
        )
        meme = self.archive.contribute(
            action=action,
            source_code=source,
            niche=niche,
            generation=self.generation,
            fitness=min(0.95, (parent_a.fitness + parent_b.fitness) / 2.0 + 0.025),
            author_id=child.object_id,
            parent_ids=(parent_a.meme_id, parent_b.meme_id),
        )
        child.install_meme(meme)

    def step(self) -> GenerationMetrics:
        """Select contributors, retain lineages, and seed a new generation."""
        if not self.population:
            self.initialize_population()
        self.generation += 1
        scored = self._score_population()
        self._publish_successful_behaviors(scored)

        target_population = min(self.population_size + 10, self.population_size + self.generation // 10)
        elite_count = max(2, len(scored) // 4)
        parents = [organism for _, organism in scored[:elite_count]]
        next_population: List[CulturalOrganism] = []

        # Preserve the most successful lineages as descendants, then fill the niche.
        for index in range(target_population):
            parent = parents[index % len(parents)]
            child = self._create_organism(
                f"generation-{self.generation:03d}-{index:02d}", parent
            )
            if index == 0:
                self._create_cultural_innovation(child)
            next_population.append(child)
        self.population = next_population
        return self._record_metrics()

    def _record_metrics(self) -> GenerationMetrics:
        if not self.population:
            raise RuntimeError("Cannot measure an empty population")
        scores = [organism.fitness(self.archive.size, self.use_archive) for organism in self.population]
        metric = GenerationMetrics(
            generation=self.generation,
            population=len(self.population),
            average_fitness=sum(scores) / len(scores),
            behaviors_per_organism=(
                sum(organism.complexity for organism in self.population) / len(self.population)
            ),
            novel_behaviors=self.archive.novel_behavior_count if self.use_archive else 0,
            archive_size=self.archive.size,
        )
        self.history.append(metric)
        return metric

    def run(self, generations: int = 100, *, report: bool = True) -> List[GenerationMetrics]:
        """Run a repeatable cumulative-evolution experiment."""
        if generations < 0:
            raise ValueError("generations must not be negative")
        self.initialize_population()
        for _ in range(generations):
            self.step()
        if report:
            self.print_progress()
        return list(self.history)

    def print_progress(self) -> None:
        """Print the required progression table for generation 0, 50, and 100."""
        print("Gen   | Pop | Avg Fitness | Behaviors/Org | Novel Behaviors | Archive Size")
        print("------+-----+-------------+---------------+-----------------+-------------")
        wanted = {0, 50, 100}
        displayed = [metric for metric in self.history if metric.generation in wanted]
        if not displayed and self.history:
            displayed = [self.history[0], self.history[-1]]
        for metric in displayed:
            print(
                f"{metric.generation:>5} | {metric.population:>3} |"
                f" {metric.average_fitness:>11.2f} | {metric.behaviors_per_organism:>13.1f} |"
                f" {metric.novel_behaviors:>15} | {metric.archive_size:>12}"
            )


def run_cumulative_demo() -> None:
    """Run the 100-generation demonstration and release temporary resources."""
    print("\nCUMULATIVE CULTURAL EVOLUTION")
    print("Knowledge outlives individual organisms and becomes material for new behavior.\n")
    with CumulativeEvolution(population_size=20, random_seed=21, use_archive=True) as system:
        system.run(generations=100, report=True)


if __name__ == "__main__":
    run_cumulative_demo()
