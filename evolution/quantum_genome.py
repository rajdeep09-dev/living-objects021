"""Classical probability-amplitude experiments for uncertain genomes."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict

from evolution.lamarckian import LamarckianGenome


@dataclass
class QuantumGenome:
    amplitudes: Dict[str, complex]
    measurement_history: list[str] = field(default_factory=list)
    _correlation: dict[str, str] | None = field(default=None, repr=False)

    def _normalized_weights(self) -> tuple[list[str], list[float]]:
        states = list(self.amplitudes)
        weights = [abs(self.amplitudes[state]) ** 2 for state in states]
        total = sum(weights)
        if not states or total <= 0:
            raise ValueError("quantum genome must contain a non-zero amplitude")
        return states, [weight / total for weight in weights]

    def measure(self, rng: random.Random) -> LamarckianGenome:
        states, weights = self._normalized_weights()
        if self._correlation and self._correlation.get("state"):
            selected = self._correlation["state"]
        else:
            selected = rng.choices(states, weights=weights, k=1)[0]
            if self._correlation is not None:
                self._correlation["state"] = selected
        self.measurement_history.append(selected)
        values = {
            "learning_rate": 0.55,
            "curiosity": 0.55,
            "cooperation": 0.50,
            "cultural_receptivity": 0.75,
            "mutation_rate": 0.10,
            "inheritance_rate": 1.00,
        }
        if ":" in selected:
            field_name, raw_value = selected.split(":", 1)
            if field_name in values:
                values[field_name] = max(0.0, min(1.0, float(raw_value)))
        elif selected in values:
            values[selected] = max(0.01, min(1.0, self.amplitudes[selected].real))
        elif selected in {"low", "high"}:
            values["mutation_rate"] = 0.05 if selected == "low" else 0.35
        return LamarckianGenome(**values)

    def entangle(self, other: "QuantumGenome") -> tuple["QuantumGenome", "QuantumGenome"]:
        states = list(dict.fromkeys([*self.amplitudes, *other.amplitudes]))
        shared = {"states": "|".join(states), "state": ""}
        left = QuantumGenome(dict(self.amplitudes), _correlation=shared)
        right = QuantumGenome(dict(other.amplitudes), _correlation=shared)
        return left, right

    def interfere(self, other: "QuantumGenome") -> "QuantumGenome":
        states = set(self.amplitudes) | set(other.amplitudes)
        result: dict[str, complex] = {}
        for state in states:
            left = self.amplitudes.get(state, 0j)
            right = other.amplitudes.get(state, 0j)
            result[state] = left + right if state in self.amplitudes and state in other.amplitudes else left or right
        return QuantumGenome(result)


__all__ = ["QuantumGenome"]
