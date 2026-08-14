"""Scalable evolution primitives for 10,000+ software organisms.

The module keeps the hot path compact: fixed-width population state is held in
an mmap file, cultural records are partitioned across SQLite shards, and batch
operations can be evaluated in worker processes. It is deliberately model
agnostic so an external evaluator can be attached without making the runtime
depend on a specific vendor.
"""

from __future__ import annotations

import hashlib
import mmap
import multiprocessing
import os
import random
import sqlite3
import struct
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence


@dataclass(frozen=True)
class ScalableOrganism:
    organism_id: str
    generation: int = 0
    fitness: float = 0.0
    mutation_rate: float = 0.1
    inheritance_rate: float = 0.8
    novelty_bonus: float = 0.1
    species: str = "adaptive"


@dataclass(frozen=True)
class ScalableGeneration:
    generation: int
    organism_count: int
    average_fitness: float
    best_fitness: float
    average_mutation_rate: float
    novelty_count: int
    elapsed_seconds: float


class MMapPopulationState:
    """Fixed-width memory-mapped state for bounded, low-allocation updates."""

    _record = struct.Struct("<ffff")

    def __init__(self, path: os.PathLike[str] | str, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.capacity = capacity
        self._size = self._record.size * capacity
        with self.path.open("a+b") as handle:
            handle.truncate(self._size)
        self._file = self.path.open("r+b")
        self._map = mmap.mmap(self._file.fileno(), self._size)

    def write(self, index: int, organism: ScalableOrganism) -> None:
        if not 0 <= index < self.capacity:
            raise IndexError(index)
        self._map[index * self._record.size : (index + 1) * self._record.size] = self._record.pack(
            organism.fitness,
            organism.mutation_rate,
            organism.inheritance_rate,
            organism.novelty_bonus,
        )

    def read(self, index: int) -> tuple[float, float, float, float]:
        if not 0 <= index < self.capacity:
            raise IndexError(index)
        offset = index * self._record.size
        return self._record.unpack(self._map[offset : offset + self._record.size])

    def flush(self) -> None:
        self._map.flush()

    def close(self) -> None:
        self.flush()
        self._map.close()
        self._file.close()

    def __enter__(self) -> "MMapPopulationState":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class ShardedMemome:
    """SQLite memome partitioned at a configurable capacity per file."""

    def __init__(self, directory: os.PathLike[str] | str, shard_capacity: int = 1_000_000) -> None:
        if shard_capacity < 1:
            raise ValueError("shard_capacity must be positive")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.shard_capacity = shard_capacity
        self._connections: dict[int, sqlite3.Connection] = {}
        self._counts: dict[int, int] = {}
        self._hot_cache: list[dict[str, Any]] = []

    def _path(self, shard: int) -> Path:
        return self.directory / f"memome_{shard:05d}.sqlite3"

    def _connection(self, shard: int) -> sqlite3.Connection:
        if shard not in self._connections:
            connection = sqlite3.connect(self._path(shard))
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memes (
                    meme_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    descriptor TEXT NOT NULL, source_code TEXT NOT NULL,
                    effectiveness REAL NOT NULL, author_id TEXT NOT NULL,
                    generation INTEGER NOT NULL, created_at REAL NOT NULL
                )
                """
            )
            connection.commit()
            self._connections[shard] = connection
            self._counts[shard] = connection.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
        return self._connections[shard]

    def _active_shard(self) -> int:
        shard = max(self._counts, default=0)
        while self._counts.get(shard, 0) >= self.shard_capacity:
            shard += 1
        self._connection(shard)
        return shard

    @property
    def shard_count(self) -> int:
        return max(self._counts.keys(), default=-1) + 1

    @property
    def count(self) -> int:
        return sum(self._counts.values())

    def contribute(
        self,
        name: str,
        descriptor: str,
        source_code: str = "",
        effectiveness: float = 0.0,
        author_id: str = "system",
        generation: int = 0,
        meme_id: Optional[str] = None,
    ) -> str:
        shard = self._active_shard()
        meme_id = meme_id or uuid.uuid4().hex
        connection = self._connection(shard)
        cursor = connection.execute(
            "INSERT OR IGNORE INTO memes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (meme_id, name, descriptor, source_code, effectiveness, author_id, generation, time.time()),
        )
        connection.commit()
        self._counts[shard] = connection.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
        if cursor.rowcount:
            self._hot_cache.append(
                {
                    "meme_id": meme_id,
                    "name": name,
                    "descriptor": descriptor,
                    "source_code": source_code,
                    "effectiveness": effectiveness,
                    "author_id": author_id,
                    "generation": generation,
                }
            )
            self._hot_cache = self._hot_cache[-256:]
        return meme_id

    def query(self, text: str = "", limit: int = 100) -> list[dict[str, Any]]:
        if not text and self._hot_cache:
            return sorted(self._hot_cache, key=lambda item: item["effectiveness"], reverse=True)[:limit]
        pattern = f"%{text}%"
        results: list[dict[str, Any]] = []
        for shard in sorted(self._counts):
            rows = self._connection(shard).execute(
                """SELECT * FROM memes WHERE name LIKE ? OR descriptor LIKE ?
                ORDER BY effectiveness DESC, created_at DESC LIMIT ?""",
                (pattern, pattern, limit),
            ).fetchall()
            results.extend(
                dict(zip(("meme_id", "name", "descriptor", "source_code", "effectiveness", "author_id", "generation", "created_at"), row))
                for row in rows
            )
            if len(results) >= limit:
                break
        return results[:limit]

    def close(self) -> None:
        for connection in self._connections.values():
            connection.close()
        self._connections.clear()

    def __enter__(self) -> "ShardedMemome":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _evolve_batch(batch: Sequence[ScalableOrganism], generation: int, seed: int) -> list[ScalableOrganism]:
    rng = random.Random(seed)
    evolved: list[ScalableOrganism] = []
    for organism in batch:
        exploration = (rng.random() - 0.45) * organism.mutation_rate * 0.25
        inherited = organism.inheritance_rate * min(1.0, organism.fitness + 0.04)
        fitness = max(0.0, min(1.0, organism.fitness + 0.015 + exploration + organism.novelty_bonus * 0.01))
        mutation = max(0.01, min(0.5, organism.mutation_rate + (rng.random() - 0.48) * 0.01))
        novelty = max(0.01, min(1.0, organism.novelty_bonus + (rng.random() - 0.5) * 0.02))
        evolved.append(
            replace(
                organism,
                generation=generation,
                fitness=fitness,
                mutation_rate=mutation,
                inheritance_rate=max(0.1, min(1.0, inherited)),
                novelty_bonus=novelty,
            )
        )
    return evolved


class ScalableEvolution:
    """Population engine for bounded 10,000-organism benchmark runs."""

    def __init__(
        self,
        organism_count: int = 10_000,
        workers: int = 1,
        seed: int = 7,
        state_path: os.PathLike[str] | str = "state/population.mmap",
        memome_dir: os.PathLike[str] | str = "state/memome",
    ) -> None:
        if organism_count < 1:
            raise ValueError("organism_count must be positive")
        self.organism_count = organism_count
        self.workers = max(1, workers)
        self.rng = random.Random(seed)
        self.population = [
            ScalableOrganism(organism_id=f"org-{index:06d}", mutation_rate=0.08 + (index % 11) * 0.003)
            for index in range(organism_count)
        ]
        self.state = MMapPopulationState(state_path, organism_count)
        self.memome = ShardedMemome(memome_dir)
        self.novelty_count = 0
        self._sync_state()

    def _sync_state(self) -> None:
        for index, organism in enumerate(self.population):
            self.state.write(index, organism)

    def batch_reproduce(self, batch_size: int = 1_000) -> Iterator[list[ScalableOrganism]]:
        """Yield reproduction batches without materializing extra populations."""
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        for start in range(0, len(self.population), batch_size):
            batch = self.population[start : start + batch_size]
            yield [
                replace(
                    parent,
                    organism_id=f"{parent.organism_id}-g{parent.generation + 1}",
                    generation=parent.generation + 1,
                )
                for parent in batch
            ]

    def step(self) -> ScalableGeneration:
        started = time.perf_counter()
        generation = max(item.generation for item in self.population) + 1
        batches = list(self.batch_reproduce())
        if self.workers > 1 and len(batches) > 1:
            with ProcessPoolExecutor(max_workers=self.workers) as executor:
                evolved_batches = list(
                    executor.map(
                        _evolve_batch,
                        batches,
                        [generation] * len(batches),
                        [self.rng.randrange(2**31) for _ in batches],
                    )
                )
        else:
            evolved_batches = [
                _evolve_batch(batch, generation, self.rng.randrange(2**31)) for batch in batches
            ]
        self.population = [item for batch in evolved_batches for item in batch]
        self.novelty_count += sum(1 for item in self.population if item.novelty_bonus > 0.12)
        self._sync_state()
        average = sum(item.fitness for item in self.population) / len(self.population)
        return ScalableGeneration(
            generation=generation,
            organism_count=len(self.population),
            average_fitness=average,
            best_fitness=max(item.fitness for item in self.population),
            average_mutation_rate=sum(item.mutation_rate for item in self.population) / len(self.population),
            novelty_count=self.novelty_count,
            elapsed_seconds=time.perf_counter() - started,
        )

    def run(self, generations: int = 1) -> list[ScalableGeneration]:
        if generations < 1:
            raise ValueError("generations must be positive")
        return [self.step() for _ in range(generations)]

    def close(self) -> None:
        self.state.close()
        self.memome.close()

    def __enter__(self) -> "ScalableEvolution":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AgnesEvaluator:
    """Optional adapter for the repository's existing Agnes tiered engine."""

    def __init__(self, engine: Any = None) -> None:
        self.engine = engine
        self.mode = "provided" if engine is not None else "local-fallback"
        if engine is None:
            try:
                from prototypes.agy.p1_enhanced.agnes_reasoning_engine import TieredAgnesEngine

                self.engine = TieredAgnesEngine(fallback=True)
                self.mode = "agnes-with-fallback"
            except Exception:
                self.engine = None

    def score(self, organism: ScalableOrganism, context: Optional[dict[str, Any]] = None) -> float:
        context = context or {}
        if self.engine is None:
            return max(0.0, min(1.0, organism.fitness + organism.novelty_bonus * 0.05))
        try:
            result = self.engine.reason(
                f"Evaluate organism {organism.organism_id} for adaptive fitness.",
                {"return_type": "float", "minimum": 0.0, "maximum": 1.0},
                {"state": organism.__dict__, **context},
            )
            value = result.get("result", result.get("fitness", organism.fitness))
            return max(0.0, min(1.0, float(value)))
        except Exception:
            return max(0.0, min(1.0, organism.fitness + organism.novelty_bonus * 0.05))
