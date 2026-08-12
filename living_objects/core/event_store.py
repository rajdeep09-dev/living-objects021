"""
Event Store — SQLite-backed event sourcing with snapshot support.

Every state change, memory update, relationship change, and action is an event.
Current state = fold(all events). Snapshots for fast recovery.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Any, Optional, Dict, List
from datetime import datetime, timezone
from contextlib import contextmanager


@dataclass(frozen=True)
class Event:
    """An immutable event in the audit trail."""
    event_id: str
    object_id: str
    timestamp: str
    event_type: str
    payload: dict
    parent_event_id: Optional[str] = None


class EventStore:
    """SQLite-backed event sourcing with snapshot support."""

    def __init__(self, db_path: str = "living_objects.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS objects (
                    object_id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TEXT,
                    identity_signature TEXT,
                    current_state TEXT,
                    state_version INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    object_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    parent_event_id TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(object_id)
                );

                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    object_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    provenance TEXT,
                    FOREIGN KEY (object_id) REFERENCES objects(object_id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_object
                    ON events(object_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_memories_object
                    ON memories(object_id, memory_type);
            """)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Object lifecycle
    # ------------------------------------------------------------------

    def create_object(
        self,
        object_id: str,
        name: str,
        identity_signature: str,
        initial_state: dict,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO objects
                   (object_id, name, created_at, identity_signature, current_state, state_version)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    object_id,
                    name,
                    datetime.now(timezone.utc).isoformat(),
                    identity_signature,
                    json.dumps(initial_state),
                    0,
                ),
            )

    def get_object(self, object_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM objects WHERE object_id = ?", (object_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_state(self, object_id: str, state: dict, version: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE objects SET current_state = ?, state_version = ? WHERE object_id = ?",
                (json.dumps(state), version, object_id),
            )

    def delete_object(self, object_id: str) -> None:
        """Hard delete — for testing only."""
        with self._connect() as conn:
            conn.execute("DELETE FROM memories WHERE object_id = ?", (object_id,))
            conn.execute("DELETE FROM events WHERE object_id = ?", (object_id,))
            conn.execute("DELETE FROM objects WHERE object_id = ?", (object_id,))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def append_event(self, event: Event) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO events
                   (event_id, object_id, timestamp, event_type, payload, parent_event_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id,
                    event.object_id,
                    event.timestamp,
                    event.event_type,
                    json.dumps(event.payload),
                    event.parent_event_id,
                ),
            )

    def get_events(
        self, object_id: str, event_type: Optional[str] = None
    ) -> List[Event]:
        with self._connect() as conn:
            if event_type:
                rows = conn.execute(
                    """SELECT * FROM events
                       WHERE object_id = ? AND event_type = ?
                       ORDER BY timestamp""",
                    (object_id, event_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM events
                       WHERE object_id = ?
                       ORDER BY timestamp""",
                    (object_id,),
                ).fetchall()
            return [Event(**dict(r)) for r in rows]

    def get_event_count(self, object_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM events WHERE object_id = ?",
                (object_id,),
            ).fetchone()
            return row["count"] if row else 0

    # ------------------------------------------------------------------
    # Memories
    # ------------------------------------------------------------------

    def store_memory(
        self,
        object_id: str,
        memory_type: str,
        content: dict,
        confidence: float = 1.0,
        provenance: str = "",
    ) -> str:
        memory_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO memories
                   (memory_id, object_id, timestamp, memory_type, content, confidence, provenance)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory_id,
                    object_id,
                    datetime.now(timezone.utc).isoformat(),
                    memory_type,
                    json.dumps(content),
                    confidence,
                    provenance,
                ),
            )
        return memory_id

    def get_memories(
        self,
        object_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        with self._connect() as conn:
            if memory_type:
                rows = conn.execute(
                    """SELECT * FROM memories
                       WHERE object_id = ? AND memory_type = ?
                       ORDER BY timestamp DESC LIMIT ?""",
                    (object_id, memory_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM memories
                       WHERE object_id = ?
                       ORDER BY timestamp DESC LIMIT ?""",
                    (object_id, limit),
                ).fetchall()
            return [dict(r) for r in rows]
