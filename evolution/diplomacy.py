"""Bilateral, escrowed exchange between independent ecosystems."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from evolution.beast_v2 import EvolutionConstitution
from evolution.beast_v2_culture import FederatedMemome


@dataclass
class Ecosystem:
    ecosystem_id: str
    memome: FederatedMemome
    constitution: EvolutionConstitution = field(default_factory=EvolutionConstitution)
    dsl_vocabulary: set[str] = field(default_factory=set)
    novelty_archive: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ExchangeProposal:
    proposal_id: str
    our_ecosystem_id: str
    their_ecosystem_id: str
    our_offer: tuple[str, ...]
    our_request: tuple[str, ...]
    status: str = "escrowed"


@dataclass(frozen=True)
class ExchangeResult:
    proposal_id: str
    accepted: bool
    transferred_to_ours: tuple[str, ...] = ()
    transferred_to_theirs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class CompatibilityReport:
    score: float
    dsl_overlap: float
    constitutional_similarity: float
    novelty_distance: float


class DiplomacyProtocol:
    def __init__(self) -> None:
        self.proposals: dict[str, ExchangeProposal] = {}
        self._ecosystems: dict[str, Ecosystem] = {}
        self.audit_log: list[dict[str, Any]] = []

    def propose_exchange(self, our_ecosystem: Ecosystem, their_ecosystem: Ecosystem, our_offer: list[str], our_request: list[str]) -> ExchangeProposal:
        if our_ecosystem.ecosystem_id == their_ecosystem.ecosystem_id:
            raise ValueError("an ecosystem cannot negotiate with itself")
        our_names = {item.name for item in our_ecosystem.memome.strategies()}
        if any(item not in our_names for item in our_offer):
            raise ValueError("every offered strategy must exist in the offering ecosystem")
        proposal_id = hashlib.sha256(json.dumps([our_ecosystem.ecosystem_id, their_ecosystem.ecosystem_id, sorted(our_offer), sorted(our_request)]).encode()).hexdigest()[:20]
        proposal = ExchangeProposal(proposal_id, our_ecosystem.ecosystem_id, their_ecosystem.ecosystem_id, tuple(our_offer), tuple(our_request))
        self.proposals[proposal_id] = proposal
        self._ecosystems[our_ecosystem.ecosystem_id] = our_ecosystem
        self._ecosystems[their_ecosystem.ecosystem_id] = their_ecosystem
        self.audit_log.append({"type": "proposal", "proposal_id": proposal_id})
        return proposal

    def accept(self, proposal: ExchangeProposal) -> ExchangeResult:
        stored = self.proposals.get(proposal.proposal_id)
        if stored is None or stored.status != "escrowed":
            return ExchangeResult(proposal.proposal_id, False, reason="proposal is not escrowed")
        ours = self._ecosystems[stored.our_ecosystem_id]
        theirs = self._ecosystems[stored.their_ecosystem_id]
        received_ours: list[str] = []
        received_theirs: list[str] = []
        for name in stored.our_request:
            strategy = theirs.memome.strategies()
            match = next((item for item in strategy if item.name == name), None)
            if match is not None:
                ours.memome.contribute(match)
                received_ours.append(name)
        for name in stored.our_offer:
            strategy = next((item for item in ours.memome.strategies() if item.name == name), None)
            if strategy is not None:
                theirs.memome.contribute(strategy)
                received_theirs.append(name)
        self.proposals[stored.proposal_id] = ExchangeProposal(
            proposal_id=stored.proposal_id,
            our_ecosystem_id=stored.our_ecosystem_id,
            their_ecosystem_id=stored.their_ecosystem_id,
            our_offer=stored.our_offer,
            our_request=stored.our_request,
            status="accepted",
        )
        self.audit_log.append({"type": "accepted", "proposal_id": stored.proposal_id})
        return ExchangeResult(stored.proposal_id, True, tuple(received_ours), tuple(received_theirs))

    def reject(self, proposal: ExchangeProposal, reason: str) -> None:
        stored = self.proposals.get(proposal.proposal_id)
        if stored is not None:
            self.proposals[stored.proposal_id] = ExchangeProposal(
                proposal_id=stored.proposal_id,
                our_ecosystem_id=stored.our_ecosystem_id,
                their_ecosystem_id=stored.their_ecosystem_id,
                our_offer=stored.our_offer,
                our_request=stored.our_request,
                status="rejected",
            )
            self.audit_log.append({"type": "rejected", "proposal_id": stored.proposal_id, "reason": reason})

    def assess_compatibility(self, ecosystem_a: Ecosystem, ecosystem_b: Ecosystem) -> CompatibilityReport:
        union = ecosystem_a.dsl_vocabulary | ecosystem_b.dsl_vocabulary
        overlap = len(ecosystem_a.dsl_vocabulary & ecosystem_b.dsl_vocabulary) / len(union) if union else 1.0
        a = ecosystem_a.constitution.to_dict()
        b = ecosystem_b.constitution.to_dict()
        shared = [key for key in a if key in b and a[key] == b[key]]
        similarity = len(shared) / max(1, len(a))
        union_novelty = ecosystem_a.novelty_archive | ecosystem_b.novelty_archive
        distance = 0.0 if not union_novelty else 1.0 - len(ecosystem_a.novelty_archive & ecosystem_b.novelty_archive) / len(union_novelty)
        score = max(0.0, min(1.0, 0.45 * overlap + 0.35 * similarity + 0.20 * (1.0 - distance)))
        return CompatibilityReport(round(score, 6), round(overlap, 6), round(similarity, 6), round(distance, 6))


__all__ = ["CompatibilityReport", "DiplomacyProtocol", "Ecosystem", "ExchangeProposal", "ExchangeResult"]
