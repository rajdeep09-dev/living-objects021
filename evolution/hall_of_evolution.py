"""Append-only SQLite registry for immutable champion snapshots."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HallOfEvolution:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        with self._lock:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS hall_of_evolution (immortalization_id TEXT PRIMARY KEY, generation INTEGER NOT NULL, record TEXT NOT NULL)"
            )
            self._db.commit()

    def immortalize(self, champion: Any, generation: int, task_name: str, fitness: float, epoch_name: str) -> str:
        identifier = f"{task_name}_{int(generation):07d}"
        strategies = {
            str(name): {
                "code": str(getattr(strategy, "source_code", "")),
                "effectiveness": float(getattr(strategy, "effectiveness", 0.0)),
                "generation_created": int(getattr(strategy, "generation", 0)),
            }
            for name, strategy in getattr(champion, "learned_strategies", {}).items()
        }
        genome = getattr(champion, "genome", None)
        record = {
            "immortalization_id": identifier,
            "generation": int(generation),
            "epoch": epoch_name,
            "fitness": float(fitness),
            "genome": genome.to_dict() if hasattr(genome, "to_dict") else {},
            "strategy_count": len(strategies),
            "strategies": strategies,
            "lineage": list(getattr(champion, "ancestor_ids", []))[-10:],
            "immortalized_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._db.execute(
                "INSERT OR IGNORE INTO hall_of_evolution (immortalization_id, generation, record) VALUES (?, ?, ?)",
                (identifier, int(generation), json.dumps(record, sort_keys=True)),
            )
            self._db.commit()
        return identifier

    def query(self, generation: int) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT record FROM hall_of_evolution ORDER BY ABS(generation - ?) ASC LIMIT 1", (int(generation),)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def close(self) -> None:
        with self._lock:
            self._db.close()


__all__ = ["HallOfEvolution"]
