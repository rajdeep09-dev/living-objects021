"""Measured cultural-epoch detection using Jensen-Shannon divergence."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Epoch:
    start_generation: int
    dominant_strategy_type: str
    divergence_score: float
    name: str


class EpochDetector:
    CHANGE_THRESHOLD = 0.40
    _PREFIXES = ("Primordial", "Awakening", "Classical", "Enlightenment", "Industrial", "Digital", "Quantum", "Transcendent")

    @staticmethod
    def _normalize(values: Sequence[float]) -> list[float]:
        clipped = [max(0.0, float(value)) for value in values]
        total = sum(clipped)
        return [value / total for value in clipped] if total else [1.0 / max(1, len(clipped))] * len(clipped)

    def js_divergence(self, current: Sequence[float], previous: Sequence[float]) -> float:
        length = max(len(current), len(previous))
        if length == 0:
            return 0.0
        left = self._normalize(list(current) + [0.0] * (length - len(current)))
        right = self._normalize(list(previous) + [0.0] * (length - len(previous)))
        middle = [(a + b) / 2.0 for a, b in zip(left, right)]
        def kl(source: list[float], target: list[float]) -> float:
            return sum(value * math.log2(value / reference) for value, reference in zip(source, target) if value and reference)
        return round((kl(left, middle) + kl(right, middle)) / 2.0, 6)

    def check_epoch_boundary(self, generation: int, current: Sequence[float], previous: Sequence[float]) -> Epoch | None:
        divergence = self.js_divergence(current, previous)
        if divergence <= self.CHANGE_THRESHOLD:
            return None
        dominant = max(range(len(current)), key=lambda index: current[index]) if current else 0
        prefix = self._PREFIXES[(generation // 12_500) % len(self._PREFIXES)]
        return Epoch(generation, f"strategy_cluster_{dominant}", divergence, f"{prefix} Era (Gen {generation:,})")


__all__ = ["Epoch", "EpochDetector"]
