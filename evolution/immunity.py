"""Civilization-scale antibody memory for BEAST v4."""

from __future__ import annotations

import hashlib
from typing import Any, TypedDict


class Antibody(TypedDict):
    pattern: str
    defense: str
    effectiveness: float
    discovered_by: str
    discovered_generation: int
    usage_count: int


class CivilizationImmunity:
    def __init__(self, max_antibodies: int = 10_000) -> None:
        self.registry: dict[str, Antibody] = {}
        self.max_antibodies = max(1, int(max_antibodies))
        self.attack_log: list[dict[str, Any]] = []

    def donate_defense(self, organism: Any, attack_pattern: str, defense_strategy: str, effectiveness: float, generation: int | None = None) -> str:
        pattern = str(attack_pattern).strip()
        defense = str(defense_strategy).strip()
        if not pattern or not defense:
            raise ValueError("antibody pattern and defense are required")
        antibody_id = hashlib.sha256(pattern.encode()).hexdigest()[:20]
        candidate: Antibody = {"pattern": pattern, "defense": defense, "effectiveness": max(0.0, min(1.0, float(effectiveness))), "discovered_by": str(getattr(organism, "object_id", organism)), "discovered_generation": int(generation if generation is not None else getattr(organism, "generation", 0)), "usage_count": 0}
        previous = self.registry.get(antibody_id)
        if previous is None or candidate["effectiveness"] >= previous["effectiveness"]:
            self.registry[antibody_id] = candidate
        if len(self.registry) > self.max_antibodies:
            weakest = min(self.registry, key=lambda key: self.registry[key]["effectiveness"])
            self.registry.pop(weakest, None)
        return antibody_id

    def pre_immunize(self, newborn: Any, top_n: int = 5) -> int:
        applied = 0
        for antibody in sorted(self.registry.values(), key=lambda item: (-item["effectiveness"], item["pattern"]))[: max(0, top_n)]:
            learner = getattr(newborn, "learn", None)
            if callable(learner):
                result = learner(f"antibody:{antibody['pattern']}", antibody["defense"])
                accepted = bool(getattr(result, "accepted", result))
            else:
                accepted = False
            if accepted:
                antibody["usage_count"] += 1
                applied += 1
        return applied

    def evolve_antibodies(self) -> int:
        created = 0
        for antibody in list(self.registry.values()):
            if created >= self.max_antibodies - len(self.registry):
                break
            variant_pattern = hashlib.sha256(f"{antibody['pattern']}|predictive".encode()).hexdigest()[:16]
            if variant_pattern in self.registry:
                continue
            self.registry[variant_pattern] = {**antibody, "pattern": variant_pattern, "effectiveness": round(max(0.0, antibody["effectiveness"] * 0.92), 6), "usage_count": 0}
            created += 1
        return created

    def detect_novel_attack(self, attack: Any) -> bool:
        pattern = str(getattr(attack, "fingerprint", getattr(attack, "attack_type", attack)))
        known = any(item["pattern"] == pattern for item in self.registry.values())
        self.attack_log.append({"pattern": pattern, "novel": not known})
        return not known

    def antibodies(self) -> list[Antibody]:
        return sorted((dict(item) for item in self.registry.values()), key=lambda item: (-item["effectiveness"], item["pattern"]))


__all__ = ["Antibody", "CivilizationImmunity"]
