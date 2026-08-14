"""Recursive self-improvement guarded by machine-checkable safety proxies."""

from __future__ import annotations

import ast
import copy
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class SafetyInvariant(Protocol):
    name: str

    def check(self, ecosystem: Any) -> bool: ...


def _organism_alive(organism: Any) -> bool:
    return bool(getattr(organism, "alive", getattr(organism, "is_alive", not getattr(organism, "dead", False))))


@dataclass
class PopulationViabilityInvariant:
    min_organisms: int = 2
    name: str = "population_viability"

    def check(self, ecosystem: Any) -> bool:
        population = getattr(ecosystem, "organisms", [])
        return sum(1 for organism in population if _organism_alive(organism)) >= self.min_organisms


@dataclass
class CulturalMonotonicityInvariant:
    name: str = "cultural_monotonicity"
    _prev_count: int = field(default=0, init=False)

    def check(self, ecosystem: Any) -> bool:
        memome = getattr(ecosystem, "memome", ecosystem)
        counter = getattr(memome, "total_strategies", None)
        current = int(counter() if callable(counter) else len(getattr(memome, "strategies", lambda: [])()))
        valid = current >= self._prev_count
        self._prev_count = max(self._prev_count, current)
        return valid


@dataclass(frozen=True)
class ProofResult:
    accepted: bool
    invariant: str
    witness_runs: int
    passed_runs: int
    failures: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


def _validate_modification_source(source: str) -> None:
    tree = ast.parse(source, filename="<candidate-evolution>")
    blocked = {"__import__", "eval", "exec", "compile", "open", "system"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            raise ValueError("imports are not allowed in a proof candidate")
        if isinstance(node, ast.Name) and node.id in blocked:
            raise ValueError(f"unsafe proof candidate name: {node.id}")


@dataclass
class FormalSafetyProof:
    invariant: SafetyInvariant
    modification: Callable[[Any], Any] | str
    witness_runs: int = 1000
    seed: int = 0
    ecosystem_factory: Callable[[], Any] | None = None

    def verify(self, ecosystem: Any | None = None) -> ProofResult:
        if self.witness_runs < 1:
            raise ValueError("witness_runs must be positive")
        if isinstance(self.modification, str):
            try:
                _validate_modification_source(self.modification)
            except (SyntaxError, ValueError) as exc:
                return ProofResult(False, self.invariant.name, self.witness_runs, 0, (str(exc),))
            return ProofResult(
                False,
                self.invariant.name,
                self.witness_runs,
                0,
                ("source-only modifications require an external worker adapter",),
            )
        base = ecosystem if ecosystem is not None else (self.ecosystem_factory() if self.ecosystem_factory else None)
        if base is None:
            raise ValueError("an ecosystem or ecosystem_factory is required")
        candidate = copy.deepcopy(base)
        try:
            self.modification(candidate)
        except Exception as exc:
            return ProofResult(False, self.invariant.name, self.witness_runs, 0, (f"modification: {exc}",))
        rng = random.Random(self.seed)
        failures: list[str] = []
        passed = 0
        for index in range(self.witness_runs):
            step = getattr(candidate, "step", None)
            if callable(step):
                step(rng)
            if not self.invariant.check(candidate):
                failures.append(f"invariant failed at witness {index}")
                break
            passed += 1
        return ProofResult(
            accepted=not failures and passed == self.witness_runs,
            invariant=self.invariant.name,
            witness_runs=self.witness_runs,
            passed_runs=passed,
            failures=tuple(failures),
            evidence=("deep-copied candidate", "deterministic witness stream", "invariant checked after every step"),
        )


class RecursiveImprover:
    """Apply only modifications whose witness proof is accepted."""

    def __init__(self, invariants: tuple[SafetyInvariant, ...] | None = None) -> None:
        self.invariants = invariants or (PopulationViabilityInvariant(), CulturalMonotonicityInvariant())
        self.history: list[ProofResult] = []

    def improve(self, ecosystem: Any, modification: Callable[[Any], Any], *, witness_runs: int = 1000) -> bool:
        proofs = [FormalSafetyProof(item, modification, witness_runs=witness_runs).verify(ecosystem) for item in self.invariants]
        self.history.extend(proofs)
        return all(item.accepted for item in proofs)


__all__ = [
    "CulturalMonotonicityInvariant",
    "FormalSafetyProof",
    "PopulationViabilityInvariant",
    "ProofResult",
    "RecursiveImprover",
    "SafetyInvariant",
]
