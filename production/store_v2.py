"""Durable v2 strategy store for the platform control plane."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class StrategyRecord:
    strategy_id: str
    name: str
    source_code: str
    descriptor: str
    effectiveness: float
    author_id: str
    generation: int
    parent_ids: tuple[str, ...] = ()
    node_id: str = "local"
    adoption_count: int = 0
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "source_code": self.source_code,
            "descriptor": self.descriptor,
            "effectiveness": self.effectiveness,
            "author_id": self.author_id,
            "generation": self.generation,
            "parent_ids": list(self.parent_ids),
            "node_id": self.node_id,
            "adoption_count": self.adoption_count,
            "created_at": self.created_at,
        }


class V2Store:
    """SQLite-backed local replica with fitness-weighted merge semantics."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.database_path = str(database_path)
        if self.database_path not in {":memory:", ""}:
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS v2_strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_code TEXT NOT NULL,
                descriptor TEXT NOT NULL,
                effectiveness REAL NOT NULL,
                author_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                parent_ids TEXT NOT NULL,
                node_id TEXT NOT NULL,
                adoption_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    @staticmethod
    def strategy_id(name: str, source_code: str, descriptor: str) -> str:
        raw = f"{name}\x00{descriptor}\x00{source_code}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:20]

    def _from_row(self, row: sqlite3.Row) -> StrategyRecord:
        return StrategyRecord(
            strategy_id=row["strategy_id"],
            name=row["name"],
            source_code=row["source_code"],
            descriptor=row["descriptor"],
            effectiveness=float(row["effectiveness"]),
            author_id=row["author_id"],
            generation=int(row["generation"]),
            parent_ids=tuple(json.loads(row["parent_ids"])),
            node_id=row["node_id"],
            adoption_count=int(row["adoption_count"]),
            created_at=row["created_at"],
        )

    def publish(self, record: StrategyRecord) -> StrategyRecord:
        current = self.get(record.strategy_id)
        if current is not None and current.effectiveness > record.effectiveness:
            return current
        self.connection.execute(
            """
            INSERT INTO v2_strategies
            (strategy_id, name, source_code, descriptor, effectiveness, author_id,
             generation, parent_ids, node_id, adoption_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(strategy_id) DO UPDATE SET
              effectiveness=excluded.effectiveness,
              adoption_count=MAX(v2_strategies.adoption_count, excluded.adoption_count),
              node_id=excluded.node_id
            """,
            (
                record.strategy_id,
                record.name,
                record.source_code,
                record.descriptor,
                record.effectiveness,
                record.author_id,
                record.generation,
                json.dumps(list(record.parent_ids)),
                record.node_id,
                record.adoption_count,
                record.created_at or _utc_now(),
            ),
        )
        self.connection.commit()
        return self.get(record.strategy_id) or record

    def publish_fields(
        self,
        *,
        name: str,
        source_code: str,
        descriptor: str,
        effectiveness: float,
        author_id: str,
        generation: int,
        parent_ids: Iterable[str] = (),
        node_id: str = "local",
    ) -> StrategyRecord:
        return self.publish(
            StrategyRecord(
                strategy_id=self.strategy_id(name, source_code, descriptor),
                name=name,
                source_code=source_code,
                descriptor=descriptor,
                effectiveness=effectiveness,
                author_id=author_id,
                generation=generation,
                parent_ids=tuple(parent_ids),
                node_id=node_id,
                created_at=_utc_now(),
            )
        )

    def get(self, strategy_id: str) -> Optional[StrategyRecord]:
        row = self.connection.execute(
            "SELECT * FROM v2_strategies WHERE strategy_id = ?", (strategy_id,)
        ).fetchone()
        return self._from_row(row) if row else None

    def query(self, text: str = "", limit: int = 100) -> list[StrategyRecord]:
        pattern = f"%{text}%"
        rows = self.connection.execute(
            """
            SELECT * FROM v2_strategies
            WHERE name LIKE ? OR descriptor LIKE ?
            ORDER BY effectiveness DESC, generation ASC
            LIMIT ?
            """,
            (pattern, pattern, limit),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def influence_score(self, strategy_name: str) -> float:
        rows = self.connection.execute(
            "SELECT COUNT(DISTINCT node_id) AS nodes FROM v2_strategies WHERE name = ?",
            (strategy_name,),
        ).fetchone()
        nodes = int(rows["nodes"] if rows else 0)
        return 1.0 if nodes else 0.0

    def lineage(self) -> list[dict[str, str]]:
        edges: list[dict[str, str]] = []
        for record in self.query(limit=10_000):
            edges.extend({"parent": parent, "child": record.strategy_id} for parent in record.parent_ids)
        return edges

    def close(self) -> None:
        self.connection.close()
