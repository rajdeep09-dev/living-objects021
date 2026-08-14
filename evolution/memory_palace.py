"""Spatial organization of memetic knowledge for BEAST v4."""

from __future__ import annotations

import ast
import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np

from evolution.lamarckian import Strategy


@dataclass
class MemoryRoom:
    name: str
    center_strategy_id: str
    radius: float = 1.25
    members: list[str] = field(default_factory=list)


class MemoryPalace:
    def __init__(self, dimension: int = 32, room_radius: float = 1.25) -> None:
        self.dimension = max(4, int(dimension))
        self.room_radius = max(0.01, float(room_radius))
        self._entries: dict[str, tuple[Strategy, np.ndarray]] = {}
        self.rooms: dict[str, MemoryRoom] = {}

    def embed(self, strategy: Strategy) -> np.ndarray:
        try:
            tree = ast.dump(ast.parse(strategy.source_code), annotate_fields=True, include_attributes=False)
        except SyntaxError:
            tree = strategy.source_code
        payload = f"{strategy.name}\0{strategy.descriptor}\0{tree}".encode("utf-8")
        digest = hashlib.sha512(payload).digest()
        values = [((digest[index % len(digest)] / 255.0) * 2.0 - 1.0) for index in range(self.dimension)]
        vector = np.asarray(values, dtype=float)
        norm = float(np.linalg.norm(vector))
        return vector / norm if norm else vector

    def add(self, strategy: Strategy) -> np.ndarray:
        vector = self.embed(strategy)
        self._entries[strategy.strategy_id] = (strategy, vector)
        self._refresh_rooms()
        return vector

    register = add

    def nearest_neighbors(self, query_strategy: Strategy, k: int = 5) -> list[tuple[Strategy, float]]:
        if query_strategy.strategy_id not in self._entries:
            query = self.embed(query_strategy)
        else:
            query = self._entries[query_strategy.strategy_id][1]
        ranked = []
        for strategy, vector in self._entries.values():
            if strategy.strategy_id == query_strategy.strategy_id:
                continue
            ranked.append((strategy, round(float(np.linalg.norm(query - vector)), 6)))
        return sorted(ranked, key=lambda item: (item[1], item[0].strategy_id))[: max(0, int(k))]

    def navigate(self, organism: Any, direction: np.ndarray, steps: int = 3) -> list[Strategy]:
        if not self._entries or steps <= 0:
            return []
        direction = np.asarray(direction, dtype=float).reshape(-1)
        if direction.size != self.dimension:
            raise ValueError(f"direction must have dimension {self.dimension}")
        norm = float(np.linalg.norm(direction))
        if norm == 0.0:
            raise ValueError("direction cannot be zero")
        direction = direction / norm
        learned = list(getattr(organism, "learned_strategies", {}).values())
        cursor = self.embed(learned[0]) if learned else np.zeros(self.dimension)
        result: list[Strategy] = []
        for step in range(1, steps + 1):
            target = cursor + direction * step * 0.35
            candidate = min(self._entries.values(), key=lambda item: float(np.linalg.norm(item[1] - target)))[0]
            if not result or result[-1].strategy_id != candidate.strategy_id:
                result.append(candidate)
        return result

    def create_room(self, name: str, center: Strategy) -> MemoryRoom:
        if center.strategy_id not in self._entries:
            self.add(center)
        room = MemoryRoom(name, center.strategy_id, self.room_radius)
        self.rooms[name] = room
        self._refresh_rooms()
        return room

    def _refresh_rooms(self) -> None:
        for room in self.rooms.values():
            _, center = self._entries.get(room.center_strategy_id, (None, None))
            if center is None:
                room.members = []
                continue
            room.members = [strategy.strategy_id for strategy, vector in self._entries.values() if float(np.linalg.norm(vector - center)) <= room.radius]

    def cluster_count(self, radius: float = 0.85) -> int:
        if not self._entries:
            return 0
        if self.rooms:
            return len(self.rooms)
        remaining = set(self._entries)
        clusters = 0
        while remaining:
            seed_id = remaining.pop()
            _, seed = self._entries[seed_id]
            for strategy_id, (_, vector) in self._entries.items():
                if strategy_id in remaining and float(np.linalg.norm(seed - vector)) <= radius:
                    remaining.remove(strategy_id)
            clusters += 1
        return clusters

    def snapshot(self) -> dict[str, Any]:
        return {"dimension": self.dimension, "strategies": len(self._entries), "rooms": len(self.rooms), "clusters": self.cluster_count()}


__all__ = ["MemoryPalace", "MemoryRoom"]
