"""Durable local state and memome access for the API.

SQLite is the default for local development. A PostgreSQL URL is accepted as a
deployment contract and fails loudly when the optional psycopg driver is not
installed. Redis is used as a shared cache/event fan-out when configured; the
SQLite store remains the durable source of truth for the local Compose path.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OrganismRecord:
    organism_id: str
    species: str
    generation: int
    fitness: float
    mutation_rate: float
    status: str
    created_at: str
    metadata: dict[str, Any]


class StateStore:
    """Thread-safe SQLite state store with a small, stable repository API."""

    def __init__(self, database_url: str = "sqlite:///./state/living_objects.sqlite3") -> None:
        self.database_url = database_url
        self._lock = threading.RLock()
        if database_url.startswith("sqlite:///"):
            self._connection = sqlite3.connect(
                database_url.removeprefix("sqlite:///"), check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            self._backend = "sqlite"
            self._initialize_sqlite()
        elif database_url.startswith(("postgresql://", "postgres://")):
            try:
                import psycopg  # type: ignore
            except ImportError as exc:  # pragma: no cover - deployment-only path
                raise RuntimeError(
                    "PostgreSQL DATABASE_URL requires the optional 'psycopg[binary]' dependency"
                ) from exc
            self._connection = psycopg.connect(database_url, autocommit=True)
            self._backend = "postgresql"
            self._initialize_postgresql()
        else:
            raise ValueError("DATABASE_URL must be sqlite:///... or postgresql://...")

    def _initialize_sqlite(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS organisms (
                    organism_id TEXT PRIMARY KEY,
                    species TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    fitness REAL NOT NULL,
                    mutation_rate REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memes (
                    meme_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    descriptor TEXT NOT NULL,
                    effectiveness REAL NOT NULL,
                    author_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evolution_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _initialize_postgresql(self) -> None:  # pragma: no cover - deployment-only path
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS organisms (
                    organism_id TEXT PRIMARY KEY, species TEXT NOT NULL,
                    generation INTEGER NOT NULL, fitness DOUBLE PRECISION NOT NULL,
                    mutation_rate DOUBLE PRECISION NOT NULL, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, metadata JSONB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memes (
                    meme_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    descriptor TEXT NOT NULL, effectiveness DOUBLE PRECISION NOT NULL,
                    author_id TEXT NOT NULL, generation INTEGER NOT NULL,
                    created_at TEXT NOT NULL, metadata JSONB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evolution_events (
                    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL,
                    generation INTEGER NOT NULL, payload JSONB NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def close(self) -> None:
        self._connection.close()

    def upsert_organism(self, record: OrganismRecord) -> OrganismRecord:
        data = asdict(record)
        encoded = json.dumps(record.metadata)
        with self._lock:
            if self._backend == "sqlite":
                with self._connection:
                    self._connection.execute(
                        """
                        INSERT INTO organisms
                        (organism_id, species, generation, fitness, mutation_rate, status, created_at, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(organism_id) DO UPDATE SET
                          species=excluded.species, generation=excluded.generation,
                          fitness=excluded.fitness, mutation_rate=excluded.mutation_rate,
                          status=excluded.status, metadata=excluded.metadata
                        """,
                        (
                            record.organism_id,
                            record.species,
                            record.generation,
                            record.fitness,
                            record.mutation_rate,
                            record.status,
                            record.created_at,
                            encoded,
                        ),
                    )
            else:  # pragma: no cover - deployment-only path
                with self._connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO organisms VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (organism_id) DO UPDATE SET
                        species=EXCLUDED.species, generation=EXCLUDED.generation,
                        fitness=EXCLUDED.fitness, mutation_rate=EXCLUDED.mutation_rate,
                        status=EXCLUDED.status, metadata=EXCLUDED.metadata
                        """,
                        (
                            record.organism_id,
                            record.species,
                            record.generation,
                            record.fitness,
                            record.mutation_rate,
                            record.status,
                            record.created_at,
                            json.dumps(record.metadata),
                        ),
                    )
        return record

    def get_organism(self, organism_id: str) -> Optional[OrganismRecord]:
        with self._lock:
            if self._backend == "sqlite":
                row = self._connection.execute(
                    "SELECT * FROM organisms WHERE organism_id = ?", (organism_id,)
                ).fetchone()
                if row is None:
                    return None
                return OrganismRecord(**{**dict(row), "metadata": json.loads(row["metadata"])})
            with self._connection.cursor() as cursor:  # pragma: no cover
                cursor.execute("SELECT * FROM organisms WHERE organism_id = %s", (organism_id,))
                row = cursor.fetchone()
                if row is None:
                    return None
                return OrganismRecord(*row[:-1], row[-1])

    def list_organisms(self, limit: int = 100, offset: int = 0) -> list[OrganismRecord]:
        limit = max(1, min(limit, 10_000))
        with self._lock:
            if self._backend == "sqlite":
                rows = self._connection.execute(
                    "SELECT * FROM organisms ORDER BY generation DESC, created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
                return [OrganismRecord(**{**dict(row), "metadata": json.loads(row["metadata"])}) for row in rows]
            with self._connection.cursor() as cursor:  # pragma: no cover
                cursor.execute(
                    "SELECT * FROM organisms ORDER BY generation DESC, created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset),
                )
                return [OrganismRecord(*row[:-1], row[-1]) for row in cursor.fetchall()]

    def delete_organism(self, organism_id: str) -> bool:
        with self._lock:
            if self._backend == "sqlite":
                with self._connection:
                    cursor = self._connection.execute(
                        "DELETE FROM organisms WHERE organism_id = ?", (organism_id,)
                    )
                return cursor.rowcount > 0
            with self._connection.cursor() as cursor:  # pragma: no cover
                cursor.execute("DELETE FROM organisms WHERE organism_id = %s", (organism_id,))
                return cursor.rowcount > 0

    def add_meme(
        self,
        name: str,
        descriptor: str,
        effectiveness: float,
        author_id: str,
        generation: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        meme = {
            "meme_id": str(uuid.uuid4()),
            "name": name,
            "descriptor": descriptor,
            "effectiveness": float(effectiveness),
            "author_id": author_id,
            "generation": generation,
            "created_at": utc_now(),
            "metadata": metadata or {},
        }
        with self._lock:
            if self._backend == "sqlite":
                with self._connection:
                    self._connection.execute(
                        "INSERT INTO memes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            meme["meme_id"],
                            meme["name"],
                            meme["descriptor"],
                            meme["effectiveness"],
                            meme["author_id"],
                            meme["generation"],
                            meme["created_at"],
                            json.dumps(meme["metadata"]),
                        ),
                    )
            else:  # pragma: no cover
                with self._connection.cursor() as cursor:
                    cursor.execute("INSERT INTO memes VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (*meme.values(),))
        return meme

    def query_memes(self, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 10_000))
        with self._lock:
            if self._backend == "sqlite":
                pattern = f"%{query}%"
                rows = self._connection.execute(
                    """
                    SELECT * FROM memes
                    WHERE name LIKE ? OR descriptor LIKE ?
                    ORDER BY effectiveness DESC, created_at DESC LIMIT ?
                    """,
                    (pattern, pattern, limit),
                ).fetchall()
                result = []
                for row in rows:
                    item = dict(row)
                    item["metadata"] = json.loads(item["metadata"])
                    result.append(item)
                return result
            with self._connection.cursor() as cursor:  # pragma: no cover
                pattern = f"%{query}%"
                cursor.execute(
                    "SELECT * FROM memes WHERE name ILIKE %s OR descriptor ILIKE %s ORDER BY effectiveness DESC LIMIT %s",
                    (pattern, pattern, limit),
                )
                return [dict(zip(("meme_id", "name", "descriptor", "effectiveness", "author_id", "generation", "created_at", "metadata"), row)) for row in cursor.fetchall()]

    def record_event(self, event_type: str, generation: int, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "generation": generation,
            "payload": payload,
            "created_at": utc_now(),
        }
        with self._lock:
            if self._backend == "sqlite":
                with self._connection:
                    self._connection.execute(
                        "INSERT INTO evolution_events VALUES (?, ?, ?, ?, ?)",
                        (event["event_id"], event_type, generation, json.dumps(payload), event["created_at"]),
                    )
            else:  # pragma: no cover
                with self._connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO evolution_events VALUES (%s,%s,%s,%s,%s)",
                        (event["event_id"], event_type, generation, json.dumps(payload), event["created_at"]),
                    )
        return event


class RedisCache:
    """Optional Redis cache that never prevents local tests from running."""

    def __init__(self, redis_url: str = "") -> None:
        self.client = None
        if redis_url:
            try:
                import redis  # type: ignore

                self.client = redis.Redis.from_url(redis_url, decode_responses=True)
                self.client.ping()
            except Exception:
                self.client = None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def cache_summary(self, summary: dict[str, Any]) -> None:
        if self.client is not None:
            self.client.set("living_objects:memome_summary", json.dumps(summary), ex=60)
