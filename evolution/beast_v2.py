"""BEAST v2 core primitives.

This module contains the first four v2 research mechanisms:

* :class:`EvolutionConstitution` makes ecosystem rules mutable and heritable.
* :class:`Morphogenome` grows deterministic Python modules from templates.
* :class:`DefenseLayer` and :class:`RedTeamOrganism` model adversarial pressure.
* :class:`GoalSynthesizer` discovers intrinsic goals from observations.

The implementation is deliberately deterministic when given a seed. Generated
Python is validated before execution, but in-process validation is not a
production security boundary; see ``research/beast_v2_security_findings.md``.
"""
from __future__ import annotations

import ast
import hashlib
import math
import random
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional, Sequence


def _bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class EvolutionConstitution:
    """The heritable rulebook of an ecosystem."""

    selection_pressure: float = 0.5
    crossover_strategy: str = "uniform"
    cultural_adoption_rate: float = 0.3
    novelty_weight: float = 0.3
    extinction_threshold: float = 0.1
    generation_overlap: float = 0.5
    mutation_distribution: str = "gaussian"

    CROSSOVER_STRATEGIES = ("uniform", "one_point", "two_point", "blend")
    MUTATION_DISTRIBUTIONS = ("gaussian", "cauchy", "levy", "uniform")

    def __post_init__(self) -> None:
        for field_name in (
            "selection_pressure",
            "cultural_adoption_rate",
            "novelty_weight",
            "extinction_threshold",
            "generation_overlap",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
        if self.crossover_strategy not in self.CROSSOVER_STRATEGIES:
            raise ValueError(f"unsupported crossover strategy: {self.crossover_strategy}")
        if self.mutation_distribution not in self.MUTATION_DISTRIBUTIONS:
            raise ValueError(f"unsupported mutation distribution: {self.mutation_distribution}")

    def mutate(self, rng: random.Random) -> "EvolutionConstitution":
        """Mutate the rulebook itself while keeping every field valid."""

        def shift(value: float, scale: float = 0.08) -> float:
            return _bounded(value + rng.gauss(0.0, scale))

        crossover = self.crossover_strategy
        distribution = self.mutation_distribution
        if rng.random() < 0.22:
            crossover = rng.choice(self.CROSSOVER_STRATEGIES)
        if rng.random() < 0.22:
            distribution = rng.choice(self.MUTATION_DISTRIBUTIONS)
        return EvolutionConstitution(
            selection_pressure=shift(self.selection_pressure),
            crossover_strategy=crossover,
            cultural_adoption_rate=shift(self.cultural_adoption_rate),
            novelty_weight=shift(self.novelty_weight),
            extinction_threshold=shift(self.extinction_threshold, 0.05),
            generation_overlap=shift(self.generation_overlap, 0.06),
            mutation_distribution=distribution,
        )

    def to_code(self) -> str:
        """Render an auditable selection function from this constitution."""
        values = self.to_dict()
        return (
            "def select_score(fitness, novelty, constitution=None):\n"
            f"    selection_pressure = {values['selection_pressure']:.8f}\n"
            f"    novelty_weight = {values['novelty_weight']:.8f}\n"
            f"    extinction_threshold = {values['extinction_threshold']:.8f}\n"
            "    if fitness < extinction_threshold:\n"
            "        return 0.0\n"
            "    return max(0.0, fitness * selection_pressure + novelty * novelty_weight)\n"
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def diff(self, other: "EvolutionConstitution") -> dict[str, Any]:
        """Return only fields that differ from ``other``."""
        left, right = self.to_dict(), other.to_dict()
        return {key: (left[key], right[key]) for key in left if left[key] != right[key]}


@dataclass(frozen=True)
class Morphogenome:
    """A deterministic code-growing genome based on template expansion."""

    templates: tuple[str, ...] = ("identity", "scale", "offset")
    operators: tuple[str, ...] = ("add", "multiply", "compose")
    module_bias: float = 0.5

    def __post_init__(self) -> None:
        if not self.templates or not self.operators:
            raise ValueError("a morphogenome needs at least one template and operator")
        if not 0.0 <= self.module_bias <= 1.0:
            raise ValueError("module_bias must be between 0 and 1")

    @staticmethod
    def _slug(seed: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", seed).strip("_") or "organism"
        if cleaned[0].isdigit():
            cleaned = f"m_{cleaned}"
        return cleaned

    def grow_module(
        self,
        seed: str,
        complexity: int,
        parent_modules: Sequence[str] = (),
    ) -> str:
        """Produce a complete syntactically valid module without an LLM."""
        if complexity < 1:
            raise ValueError("complexity must be positive")
        slug = self._slug(seed)
        function_name = f"solve_{slug}"
        lines = [
            f'"""Morphogenetically grown module for {slug}."""',
            "from __future__ import annotations",
            "",
        ]
        parent_names: list[str] = []
        for parent in parent_modules:
            parent_slug = self._slug(parent)
            parent_names.append(parent_slug)
            lines.append(f"from module_{parent_slug} import solve_{parent_slug}")
        if parent_modules:
            lines.extend(["", ""])
        lines.append(f"def {function_name}(x):")
        lines.append("    value = x")
        for index in range(complexity):
            template = self.templates[index % len(self.templates)]
            if template == "scale":
                lines.append(f"    value = value * {1.0 + (index + 1) / 100:.4f}")
            elif template == "offset":
                lines.append(f"    value = value + {((index % 3) - 1) * 0.25:.2f}")
            else:
                lines.append("    value = value")
        if parent_names:
            args = ", ".join(f"solve_{name}(x)" for name in parent_names)
            lines.append(f"    parent_signal = ({args})")
            lines.append("    if not isinstance(parent_signal, tuple):")
            lines.append("        parent_signal = (parent_signal,)")
            lines.append("    value = value + sum(float(item) for item in parent_signal) / len(parent_signal)")
        lines.append("    return value")
        lines.append("")
        module = "\n".join(lines)
        ast.parse(module)
        return module

    def graft(self, other: "Morphogenome") -> "Morphogenome":
        """Crossover two code-growing genomes into a third template set."""
        templates = tuple(dict.fromkeys(self.templates + other.templates))
        operators = tuple(dict.fromkeys(self.operators + other.operators))
        return Morphogenome(
            templates=templates,
            operators=operators,
            module_bias=(self.module_bias + other.module_bias) / 2.0,
        )

    def mutate(self, rng: random.Random) -> "Morphogenome":
        templates = list(self.templates)
        operators = list(self.operators)
        catalog = ["identity", "scale", "offset", "clamp", "square"]
        if rng.random() < 0.55:
            candidate = rng.choice(catalog)
            if candidate not in templates:
                templates.append(candidate)
        return Morphogenome(tuple(templates), tuple(operators), _bounded(self.module_bias + rng.gauss(0, 0.08)))


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    reason: str
    fingerprint: str = ""
    risk_flags: tuple[str, ...] = ()


class DefenseLayer:
    """A strategy validator and adaptive immune layer."""

    FORBIDDEN_NODES = (
        ast.Import,
        ast.Global,
        ast.Nonlocal,
        ast.Lambda,
    )

    def __init__(self, immune_strength: float = 0.2) -> None:
        self.immune_strength = _bounded(immune_strength)
        self.attack_count = 0
        self.repulsed_count = 0
        self.known_fingerprints: set[str] = set()

    @staticmethod
    def fingerprint(strategy_code: str) -> str:
        normalized = "".join(strategy_code.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def validate_strategy(self, strategy_code: str) -> ValidationResult:
        if not isinstance(strategy_code, str) or not strategy_code.strip():
            return ValidationResult(False, "empty strategy", risk_flags=("empty",))
        try:
            tree = ast.parse(strategy_code)
        except SyntaxError as exc:
            return ValidationResult(False, f"syntax error: {exc.msg}", risk_flags=("syntax",))
        risks: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, self.FORBIDDEN_NODES):
                risks.append(type(node).__name__)
            if isinstance(node, ast.ImportFrom):
                allowed_generated_import = bool(
                    node.module
                    and (
                        node.module == "__future__"
                        or node.module.startswith("module_")
                    )
                )
                if not allowed_generated_import:
                    risks.append(type(node).__name__)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec", "open", "__import__"}:
                    risks.append(node.func.id)
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                risks.append("dunder_attribute")
        fingerprint = self.fingerprint(strategy_code)
        if risks:
            self.attack_count += 1
            return ValidationResult(False, "forbidden operation", fingerprint, tuple(sorted(set(risks))))
        try:
            compile(tree, "<strategy>", "exec")
        except Exception as exc:  # pragma: no cover - compile mirrors ast.parse
            self.attack_count += 1
            return ValidationResult(False, f"compile error: {exc}", fingerprint, ("compile",))
        self.known_fingerprints.add(fingerprint)
        self.repulsed_count += 1 if self.immune_strength >= 0.0 else 0
        return ValidationResult(True, "accepted", fingerprint)

    def observe_attack(self, repulsed: bool) -> None:
        self.attack_count += 1
        if repulsed:
            self.repulsed_count += 1
            self.immune_strength = _bounded(self.immune_strength + 0.04)
        else:
            self.immune_strength = _bounded(self.immune_strength + 0.02)

    def to_dict(self) -> dict[str, Any]:
        return {
            "immune_strength": round(self.immune_strength, 6),
            "attack_count": self.attack_count,
            "repulsed_count": self.repulsed_count,
            "known_fingerprints": sorted(self.known_fingerprints),
        }


@dataclass(frozen=True)
class AttackResult:
    attacker_id: str
    target_id: str
    detected: bool
    damage: float
    stolen_strategy: Optional[str]
    validation: ValidationResult


class RedTeamOrganism:
    """Adversarial organism that probes a target's strategy boundary."""

    def __init__(self, organism_id: str = "red-team", attack_power: float = 0.5) -> None:
        self.organism_id = organism_id
        self.attack_power = _bounded(attack_power)
        self.generation = 0

    def attack(self, target: Any) -> AttackResult:
        defense = getattr(target, "defense", None)
        if defense is None:
            defense = DefenseLayer()
            setattr(target, "defense", defense)
        malformed = "def attack_target(x):\n    return __import__('os').getcwd()"
        validation = defense.validate_strategy(malformed)
        detected = not validation.accepted
        defense.observe_attack(detected)
        stolen = None
        learned = getattr(target, "learned_strategies", {})
        if learned:
            stolen = max(learned.values(), key=lambda item: getattr(item, "effectiveness", 0.0)).name
        if detected:
            damage = self.attack_power * (1.0 - defense.immune_strength)
        else:
            damage = self.attack_power
            if hasattr(target, "fitness"):
                target.fitness = max(0.0, float(target.fitness) - damage)
        return AttackResult(self.organism_id, str(getattr(target, "object_id", "target")), detected, damage, stolen, validation)


@dataclass(frozen=True)
class EnvironmentState:
    """Serializable observation used by intrinsic goal discovery."""

    coordinates: tuple[int, ...] = ()
    features: Mapping[str, float] = field(default_factory=dict)
    outcome: float = 0.0

    def key(self) -> tuple[Any, ...]:
        return (self.coordinates, tuple(sorted((str(k), round(float(v), 6)) for k, v in self.features.items())))


class GoalSynthesizer:
    """Discover goals from surprise, leverage, and unexplored state coverage."""

    def __init__(self, *, goal_parameters: Optional[Mapping[str, float]] = None) -> None:
        self.observations: list[EnvironmentState] = []
        self.visited: set[tuple[Any, ...]] = set()
        self.goal_parameters = {
            "surprise_weight": 0.45,
            "leverage_weight": 0.35,
            "coverage_weight": 0.20,
        }
        if goal_parameters:
            self.goal_parameters.update({key: float(value) for key, value in goal_parameters.items()})

    def observe(self, state: EnvironmentState | Mapping[str, Any]) -> None:
        if not isinstance(state, EnvironmentState):
            state = EnvironmentState(
                coordinates=tuple(state.get("coordinates", ())),
                features=dict(state.get("features", {})),
                outcome=float(state.get("outcome", 0.0)),
            )
        self.observations.append(state)
        self.visited.add(state.key())

    def synthesize_goal(self) -> Callable[[EnvironmentState | Mapping[str, Any]], float]:
        baseline = max(1, len(self.observations))
        observed_outcomes = [item.outcome for item in self.observations]
        mean_outcome = sum(observed_outcomes) / baseline
        variance = sum((item - mean_outcome) ** 2 for item in observed_outcomes) / baseline
        scale = math.sqrt(variance) + 0.1
        weights = dict(self.goal_parameters)

        def intrinsic_goal(state: EnvironmentState | Mapping[str, Any]) -> float:
            current = state if isinstance(state, EnvironmentState) else EnvironmentState(
                coordinates=tuple(state.get("coordinates", ())),
                features=dict(state.get("features", {})),
                outcome=float(state.get("outcome", 0.0)),
            )
            surprise = min(1.0, abs(current.outcome - mean_outcome) / scale)
            leverage = min(1.0, abs(current.outcome) + sum(abs(v) for v in current.features.values()) / 10.0)
            coverage = 1.0 if current.key() not in self.visited else 0.0
            return _bounded(
                weights["surprise_weight"] * surprise
                + weights["leverage_weight"] * leverage
                + weights["coverage_weight"] * coverage
            )

        intrinsic_goal.__name__ = "intrinsic_goal"
        setattr(intrinsic_goal, "parameters", weights)
        setattr(intrinsic_goal, "observed_states", len(self.visited))
        return intrinsic_goal

    def evolve_goal(self, child_synthesizer: "GoalSynthesizer") -> "GoalSynthesizer":
        """Transfer learned goal parameters to a child synthesizer."""
        child_synthesizer.goal_parameters = dict(self.goal_parameters)
        child_synthesizer.observations.extend(self.observations[-10:])
        child_synthesizer.visited.update(self.visited)
        return child_synthesizer

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_parameters": dict(self.goal_parameters),
            "observations": len(self.observations),
            "visited_states": len(self.visited),
        }
