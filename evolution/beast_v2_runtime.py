"""Composable BEAST v2 organism runtime."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from evolution.beast_v2 import (
    DefenseLayer,
    EnvironmentState,
    EvolutionConstitution,
    GoalSynthesizer,
    Morphogenome,
    ValidationResult,
)


@dataclass
class BeastOrganism:
    """A lightweight v2 organism suitable for unit tests and orchestrators."""

    organism_id: str
    generation: int = 0
    constitution: EvolutionConstitution = field(default_factory=EvolutionConstitution)
    morphogenome: Morphogenome = field(default_factory=Morphogenome)
    defense: DefenseLayer = field(default_factory=DefenseLayer)
    goal_synthesizer: GoalSynthesizer = field(default_factory=GoalSynthesizer)
    fitness: float = 0.0
    energy: float = 100.0
    alive: bool = True
    parent_ids: tuple[str, ...] = ()
    learned_modules: dict[str, str] = field(default_factory=dict)
    defense_events: list[dict[str, Any]] = field(default_factory=list)

    def learn(self, module_name: str, source_code: str) -> ValidationResult:
        result = self.defense.validate_strategy(source_code)
        if result.accepted:
            self.learned_modules[module_name] = source_code
        return result

    def grow(self, seed: str, complexity: int = 1) -> str:
        source = self.morphogenome.grow_module(seed, complexity, tuple(self.learned_modules))
        result = self.learn(f"module_{self.morphogenome._slug(seed)}", source)
        if not result.accepted:
            raise ValueError(result.reason)
        return source

    def observe(self, state: EnvironmentState | Mapping[str, Any]) -> None:
        self.goal_synthesizer.observe(state)

    def intrinsic_score(self, state: EnvironmentState | Mapping[str, Any]) -> float:
        return self.goal_synthesizer.synthesize_goal()(state)

    def reproduce(self, rng: Optional[random.Random] = None) -> "BeastOrganism":
        if not self.alive:
            raise RuntimeError("dead organisms cannot reproduce")
        rng = rng or random.Random()
        child = BeastOrganism(
            organism_id=f"{self.organism_id}-g{self.generation + 1}",
            generation=self.generation + 1,
            constitution=self.constitution.mutate(rng),
            morphogenome=self.morphogenome.mutate(rng),
            defense=DefenseLayer(self.defense.immune_strength),
            goal_synthesizer=GoalSynthesizer(goal_parameters=self.goal_synthesizer.goal_parameters),
            parent_ids=(self.organism_id,),
        )
        self.goal_synthesizer.evolve_goal(child.goal_synthesizer)
        child.learned_modules.update(self.learned_modules)
        return child

    def record_attack(self, attack: Any) -> None:
        self.defense_events.append(
            {
                "attacker_id": getattr(attack, "attacker_id", "unknown"),
                "detected": bool(getattr(attack, "detected", False)),
                "damage": float(getattr(attack, "damage", 0.0)),
            }
        )

    def die(self) -> None:
        self.alive = False
        self.energy = 0.0

    def to_state(self) -> dict[str, Any]:
        return {
            "organism_id": self.organism_id,
            "generation": self.generation,
            "constitution": self.constitution.to_dict(),
            "morphogenome": {
                "templates": list(self.morphogenome.templates),
                "operators": list(self.morphogenome.operators),
                "module_bias": self.morphogenome.module_bias,
            },
            "defense": self.defense.to_dict(),
            "goals": self.goal_synthesizer.to_dict(),
            "fitness": self.fitness,
            "energy": self.energy,
            "alive": self.alive,
            "parent_ids": list(self.parent_ids),
            "learned_modules": dict(self.learned_modules),
            "defense_events": list(self.defense_events),
        }
