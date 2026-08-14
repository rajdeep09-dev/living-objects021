"""Bounded, auditable historical reinterpretation for BEAST v4."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RevisionProposal:
    proposal_id: str
    organism_id: str
    ancestor_id: str
    revised_strategy: str
    strategy_name: str
    generations_back: int
    expected_fitness_delta: float
    created_at: float = field(default_factory=time.time)
    status: str = "proposed"


@dataclass(frozen=True)
class RevisionResult:
    proposal_id: str
    applied: bool
    affected_organisms: int = 0
    net_fitness_change: float = 0.0
    paradox: bool = False
    reason: str = ""


class RevisionError(ValueError):
    """Raised when a requested history rewrite exceeds a configured safety budget."""


class TemporalRevisionEngine:
    BUTTERFLY_BUDGET = 10
    MAX_CAUSAL_RECOMPUTATIONS = 100_000

    def __init__(self, organisms: Sequence[Any] | None = None, lineage: Mapping[str, str | None] | None = None, memome: Any = None, butterfly_budget: int | None = None, max_causal_recomputations: int | None = None) -> None:
        self.organisms: dict[str, Any] = {str(getattr(item, "object_id", item)): item for item in (organisms or ())}
        self.lineage: dict[str, str | None] = dict(lineage or {})
        self.memome = memome
        self.butterfly_budget = max(1, int(butterfly_budget or self.BUTTERFLY_BUDGET))
        self.max_causal_recomputations = max(1, int(max_causal_recomputations or self.MAX_CAUSAL_RECOMPUTATIONS))
        self.proposals: dict[str, RevisionProposal] = {}
        self.revision_log: list[dict[str, Any]] = []

    def register(self, organism: Any, parent_id: str | None = None) -> str:
        object_id = str(getattr(organism, "object_id", organism))
        self.organisms[object_id] = organism
        self.lineage[object_id] = parent_id
        return object_id

    def _distance(self, descendant_id: str, ancestor_id: str) -> int | None:
        if descendant_id == ancestor_id:
            return 0
        current = descendant_id
        distance = 0
        seen: set[str] = set()
        while current and current not in seen:
            seen.add(current)
            current = self.lineage.get(current) or ""
            distance += 1
            if current == ancestor_id:
                return distance
        return None

    def propose_revision(self, organism: Any, ancestor_id: str, revised_strategy: str, strategy_name: str) -> RevisionProposal:
        organism_id = str(getattr(organism, "object_id", organism))
        distance = self._distance(organism_id, ancestor_id)
        if distance is None:
            raise ValueError("ancestor is not in the organism's causal chain")
        if distance > self.butterfly_budget:
            raise RevisionError("revision exceeds butterfly budget")
        if not revised_strategy.strip() or not strategy_name.strip():
            raise ValueError("revision requires strategy code and name")
        expected_delta = round(max(0.0, 0.05 + 0.01 * min(distance, 5)), 6)
        proposal = RevisionProposal(f"rev-{uuid.uuid4().hex[:12]}", organism_id, ancestor_id, revised_strategy, strategy_name, distance, expected_delta)
        self.proposals[proposal.proposal_id] = proposal
        return proposal

    def _causal_cone_size(self, proposal: RevisionProposal) -> int:
        """Bound both history depth and worst-case recomputation before mutation."""
        depth = int(proposal.generations_back)
        if depth > self.butterfly_budget:
            raise RevisionError(
                f"revision depth {depth} exceeds butterfly budget {self.butterfly_budget}"
            )
        estimated = depth * len(self.organisms)
        if estimated > self.max_causal_recomputations:
            raise RevisionError(
                f"revision would recompute {estimated} organism-generations; limit is {self.max_causal_recomputations}"
            )
        return estimated

    def revision_paradox_check(self, proposal: RevisionProposal) -> bool:
        if proposal.organism_id == proposal.ancestor_id:
            return True
        if proposal.generations_back < 1 or proposal.generations_back > self.butterfly_budget:
            return True
        if not proposal.revised_strategy.strip() or proposal.status != "proposed":
            return True
        return self._distance(proposal.organism_id, proposal.ancestor_id) != proposal.generations_back

    def _causal_cone(self, ancestor_id: str) -> list[Any]:
        cone = []
        for object_id, organism in self.organisms.items():
            if self._distance(object_id, ancestor_id) is not None:
                cone.append(organism)
        return cone

    def apply_revision(self, proposal: RevisionProposal) -> RevisionResult:
        stored = self.proposals.get(proposal.proposal_id, proposal)
        if self.revision_paradox_check(stored):
            return RevisionResult(stored.proposal_id, False, paradox=True, reason="causal paradox or invalid revision")
        try:
            self._causal_cone_size(stored)
        except RevisionError as error:
            return RevisionResult(stored.proposal_id, False, reason=str(error))
        ancestor = self.organisms.get(stored.ancestor_id)
        if ancestor is None:
            return RevisionResult(stored.proposal_id, False, reason="ancestor is not alive in the registered history")
        install = getattr(ancestor, "install_strategy", None)
        if callable(install) and not install(stored.revised_strategy):
            return RevisionResult(stored.proposal_id, False, reason="ancestor rejected revised strategy")
        setattr(ancestor, "temporal_revisions", getattr(ancestor, "temporal_revisions", []) + [stored.strategy_name])
        cone = self._causal_cone(stored.ancestor_id)
        net = 0.0
        for item in cone:
            old = float(getattr(item, "fitness", 0.0))
            setattr(item, "fitness", min(1.0, old + stored.expected_fitness_delta))
            net += float(getattr(item, "fitness", 0.0)) - old
        self.proposals[stored.proposal_id] = RevisionProposal(**{**stored.__dict__, "status": "applied"})
        self.revision_log.append({"proposal_id": stored.proposal_id, "ancestor_id": stored.ancestor_id, "affected": len(cone), "net_fitness_change": round(net, 6)})
        return RevisionResult(stored.proposal_id, True, len(cone), round(net, 6))


__all__ = ["RevisionError", "RevisionProposal", "RevisionResult", "TemporalRevisionEngine"]
