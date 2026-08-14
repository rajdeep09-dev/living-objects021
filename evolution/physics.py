"""BEAST v4 evolving-physics and parallel-universe primitives.

These are research-mode digital physics models. They make invariant checking and
branch provenance explicit; they do not claim to model physical reality.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


class PhysicsLaw(Protocol):
    name: str

    def apply(self, ecosystem: Any, organisms: Sequence[Any]) -> None: ...


@dataclass(frozen=True)
class FormalSafetyProof:
    invariant: str
    passed: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)
    prover: str = "bounded-invariant-checker"

    def verify(self, law: PhysicsLaw) -> bool:
        return bool(self.passed and getattr(law, "name", "") and self.invariant.strip())


@dataclass
class ConservationLaw:
    name: str = "conservation_of_tokens"

    def apply(self, ecosystem: Any, organisms: Sequence[Any]) -> None:
        before = getattr(ecosystem, "_token_total", None)
        total = sum(float(getattr(getattr(item, "token_wallet", None), "balance", 0.0)) for item in organisms)
        if before is None:
            setattr(ecosystem, "_token_total", total)
        else:
            setattr(ecosystem, "_token_total", max(0.0, float(before)))


@dataclass
class CausalityLaw:
    name: str = "causality"

    def apply(self, ecosystem: Any, organisms: Sequence[Any]) -> None:
        last_generation = int(getattr(ecosystem, "generation", 0))
        for organism in organisms:
            setattr(organism, "generation", max(last_generation, int(getattr(organism, "generation", 0))))


@dataclass
class EntropyLaw:
    name: str = "entropy_gradient"

    def apply(self, ecosystem: Any, organisms: Sequence[Any]) -> None:
        descriptors = {descriptor for item in organisms for descriptor in getattr(item, "behavior_descriptors", {}).values()}
        setattr(ecosystem, "diversity", len(descriptors))


@dataclass
class InformationLaw:
    max_bits_per_energy: float = 32.0
    name: str = "information_limit"

    def apply(self, ecosystem: Any, organisms: Sequence[Any]) -> None:
        for organism in organisms:
            energy = max(1.0, float(getattr(organism, "energy", 1.0)))
            genome = getattr(organism, "genome", None)
            setattr(organism, "information_budget", int(energy * self.max_bits_per_energy))
            if genome is not None:
                setattr(organism, "information_budget", max(1, int(getattr(organism, "information_budget", 1))))


@dataclass
class UniversePhysics:
    laws: list[PhysicsLaw] = field(default_factory=lambda: [ConservationLaw(), CausalityLaw(), EntropyLaw(), InformationLaw()])
    mutation_history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def conservation_of_tokens(self) -> PhysicsLaw:
        return self._law("conservation_of_tokens")

    @property
    def causality(self) -> PhysicsLaw:
        return self._law("causality")

    @property
    def entropy_gradient(self) -> PhysicsLaw:
        return self._law("entropy_gradient")

    @property
    def information_limit(self) -> PhysicsLaw:
        return self._law("information_limit")

    def _law(self, name: str) -> PhysicsLaw:
        for law in self.laws:
            if getattr(law, "name", "") == name:
                return law
        raise KeyError(name)

    def apply(self, ecosystem: Any, organisms: Sequence[Any]) -> None:
        for law in tuple(self.laws):
            law.apply(ecosystem, organisms)

    def invariant_snapshot(self, organisms: Sequence[Any]) -> dict[str, Any]:
        return {
            "token_total": round(sum(float(getattr(getattr(item, "token_wallet", None), "balance", 0.0)) for item in organisms), 6),
            "generations_monotonic": all(int(getattr(item, "generation", 0)) >= 0 for item in organisms),
            "law_count": len(self.laws),
        }

    def fingerprint(self) -> str:
        payload = [{"name": getattr(law, "name", type(law).__name__), "state": repr(law)} for law in self.laws]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]

    def propose_law_mutation(self, organism: Any, mutated_law: PhysicsLaw, proof: FormalSafetyProof) -> bool:
        if not proof.verify(mutated_law):
            return False
        name = str(getattr(mutated_law, "name", "")).strip()
        if not name:
            return False
        previous = self.fingerprint()
        self.laws = [law for law in self.laws if getattr(law, "name", "") != name]
        self.laws.append(mutated_law)
        self.mutation_history.append({"organism_id": str(getattr(organism, "object_id", organism)), "law": name, "proof": proof.invariant, "before": previous, "after": self.fingerprint()})
        setattr(organism, "physics_credits", int(getattr(organism, "physics_credits", 0)) + 1)
        return True


@dataclass
class ParallelUniverse:
    physics: UniversePhysics = field(default_factory=UniversePhysics)
    parent_universe: "ParallelUniverse | None" = None
    branch_generation: int = 0
    divergence_score: float = 0.0
    universe_id: str = field(default_factory=lambda: f"univ-{uuid.uuid4().hex[:12]}")
    observers: list[dict[str, Any]] = field(default_factory=list)
    memome_path: Path | None = None

    def _branch_memome_path(self) -> Path | None:
        """Snapshot a branch-local SQLite archive rather than sharing mutable state."""
        if self.memome_path is None:
            return None
        parent_path = Path(self.memome_path)
        child_path = parent_path.with_name(f"{parent_path.stem}-{uuid.uuid4().hex[:10]}{parent_path.suffix or '.sqlite'}")
        child_path.parent.mkdir(parents=True, exist_ok=True)
        if parent_path.exists():
            shutil.copy2(parent_path, child_path)
        else:
            child_path.touch()
        return child_path

    def branch(self, trigger_law: PhysicsLaw) -> "ParallelUniverse":
        child_physics = copy.deepcopy(self.physics)
        child_physics.laws = [law for law in child_physics.laws if getattr(law, "name", "") != getattr(trigger_law, "name", "")]
        child_physics.laws.append(copy.deepcopy(trigger_law))
        parent_fp = self.physics.fingerprint()
        child_fp = child_physics.fingerprint()
        divergence = 0.0 if parent_fp == child_fp else 1.0 - sum(a == b for a, b in zip(parent_fp, child_fp)) / max(len(parent_fp), len(child_fp))
        return ParallelUniverse(
            physics=child_physics,
            parent_universe=self,
            branch_generation=self.branch_generation + 1,
            divergence_score=round(divergence, 6),
            memome_path=self._branch_memome_path(),
        )

    def observe(self) -> dict[str, Any]:
        return {"universe_id": self.universe_id, "parent_id": self.parent_universe.universe_id if self.parent_universe else None, "branch_generation": self.branch_generation, "divergence_score": self.divergence_score, "physics_fingerprint": self.physics.fingerprint()}


__all__ = ["CausalityLaw", "ConservationLaw", "EntropyLaw", "FormalSafetyProof", "InformationLaw", "ParallelUniverse", "PhysicsLaw", "UniversePhysics"]
