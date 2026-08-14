"""Minimum-description-length proxy for reproducible local scoring."""
from __future__ import annotations

import zlib


class MDLFitness:
    def __call__(self, strategy_code: str, correctness: float) -> float:
        if correctness <= 0.0:
            return 0.0
        compressed_length = len(zlib.compress(strategy_code.encode("utf-8"), level=9))
        brevity_bonus = 500.0 / max(100.0, float(compressed_length))
        return round(max(0.0, min(2.0, float(correctness) * min(2.0, brevity_bonus))), 6)


__all__ = ["MDLFitness"]
