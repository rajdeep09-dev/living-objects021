"""Computable awareness proxies; these are not claims of sentience."""

from __future__ import annotations

import math
from typing import Any


def _sigmoid_normalize(value: float) -> float:
    """Map a finite raw Phi proxy to [0, 1] with a smooth bounded curve."""
    raw = max(0.0, min(1.0, float(value)))
    if raw <= 0.0:
        return 0.0
    if raw >= 1.0:
        return 1.0
    curve = lambda x: 1.0 / (1.0 + math.exp(-12.0 * (x - 0.5)))
    lo, hi = curve(0.0), curve(1.0)
    return max(0.0, min(1.0, (curve(raw) - lo) / (hi - lo)))


class ConsciousnessMetrics:
    def integrated_information(self, organism: Any) -> float:
        strategies = list(getattr(organism, "learned_strategies", {}).values())
        if len(strategies) < 2:
            return 0.0
        qualities = [max(0.0, min(1.0, float(item.effectiveness))) for item in strategies]
        whole = max(qualities) + min(0.25, 0.05 * (len(qualities) - 1))
        parts = sum(qualities) / len(qualities)
        return round(_sigmoid_normalize(whole - parts), 6)

    def self_model_accuracy(self, organism: Any) -> float:
        predicted = getattr(organism, "predicted_fitness", None)
        actual = float(getattr(organism, "fitness", 0.0))
        if predicted is None:
            quality = float(getattr(organism, "behavior_quality", lambda: actual)())
            predicted = quality if quality else actual
        return round(max(0.0, min(1.0, 1.0 - abs(float(predicted) - actual))), 6)

    def global_workspace_breadth(self, organism: Any) -> float:
        strategies = getattr(organism, "learned_strategies", {})
        descriptors = getattr(organism, "behavior_descriptors", {})
        if not strategies:
            return 0.0
        accessible = sum(1 for key in strategies if key in strategies and key in {getattr(item, "strategy_id", key) for item in strategies.values()})
        return round(accessible / max(1, len(strategies)) * (1.0 if descriptors else 0.75), 6)

    def composite_awareness_score(self, organism: Any) -> float:
        raw = self.integrated_information(organism) * self.self_model_accuracy(organism) * self.global_workspace_breadth(organism)
        return round(max(0.0, min(1.0, raw)), 6)


__all__ = ["ConsciousnessMetrics"]
