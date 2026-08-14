"""Verified local exchange for v6 GP programs.

This is deliberately not a financial market.  It uses non-transferable research
credits inside one process, performs no network I/O, and only distributes a
freshly deserialised GP genome after tree/source validation plus held-out task
evaluation.  The typed GP interpreter remains the sole execution mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any

from evolution.fitness import FitnessEvaluator, FitnessResult
from evolution.gp_engine import GPGenome
from evolution.program_validation import ProgramValidator, ValidationReport


@dataclass(frozen=True)
class ProgramOffer:
    """An auditable local catalogue entry, priced in research credits only."""

    offer_id: str
    seller_id: str
    genome: dict[str, Any]
    task: str
    held_out: FitnessResult
    held_out_seed: int
    tree_validation: ValidationReport
    source_validation: ValidationReport
    price_credits: int


class VerifiedProgramMarket:
    """Thread-safe catalogue of validated, locally evaluated GP programs.

    Credits cannot be exchanged for money or redeemed externally.  Purchase
    returns an independent ``GPGenome`` copy so buyers cannot mutate a seller's
    listed object.  Callers are responsible for deciding whether to adopt it;
    this class never installs a program into a running organism.
    """

    MAX_PRICE_CREDITS = 10_000
    HELD_OUT_SEED = 9_973

    def __init__(self, validator: ProgramValidator | None = None) -> None:
        self._validator = validator or ProgramValidator()
        self._lock = threading.RLock()
        self._credits: dict[str, int] = {}
        self._offers: dict[str, ProgramOffer] = {}
        self._history: list[dict[str, Any]] = []

    def grant_research_credits(self, participant_id: str, credits: int) -> int:
        """Mint bounded local research credits; no payment interface exists."""
        if not participant_id or credits < 0 or credits > self.MAX_PRICE_CREDITS:
            raise ValueError("credits must be within 0..10000")
        with self._lock:
            self._credits[participant_id] = self._credits.get(participant_id, 0) + credits
            return self._credits[participant_id]

    def balance(self, participant_id: str) -> int:
        with self._lock:
            return self._credits.get(participant_id, 0)

    def list_program(
        self,
        *,
        seller_id: str,
        offer_id: str,
        genome: GPGenome,
        evaluator: FitnessEvaluator,
        task: str,
        price_credits: int,
    ) -> ProgramOffer:
        """Admit only structurally valid programs with measured held-out score."""
        if not seller_id or not offer_id or not task:
            raise ValueError("seller_id, offer_id, and task are required")
        if price_credits < 1 or price_credits > self.MAX_PRICE_CREDITS:
            raise ValueError("price_credits must be within 1..10000")
        tree_validation = self._validator.validate_tree(genome.tree)
        source_validation = self._validator.validate_source(genome.to_python())
        if not tree_validation.valid or not source_validation.valid:
            raise ValueError("program fails validation")
        # This fixed verifier-owned suite is intentionally not caller-supplied.
        # It is disjoint from GPPopulation's generation + TRAIN_SEED_OFFSET train
        # channel for the bounded generation ranges supported by this component.
        held_out = evaluator.batch_evaluate([genome], seed=self.HELD_OUT_SEED)[0]
        if held_out.correctness <= 0.0:
            raise ValueError("program has no demonstrated held-out correctness")
        offer = ProgramOffer(
            offer_id=offer_id,
            seller_id=seller_id,
            genome=genome.to_dict(),
            task=task,
            held_out=held_out,
            held_out_seed=self.HELD_OUT_SEED,
            tree_validation=tree_validation,
            source_validation=source_validation,
            price_credits=price_credits,
        )
        with self._lock:
            if offer_id in self._offers:
                raise ValueError("offer_id is already listed")
            self._offers[offer_id] = offer
            self._credits.setdefault(seller_id, 0)
            self._history.append({"event": "listed", "offer_id": offer_id, "seller_id": seller_id})
        return offer

    def offers(self) -> list[ProgramOffer]:
        with self._lock:
            return list(self._offers.values())

    def acquire(self, *, buyer_id: str, offer_id: str) -> GPGenome:
        """Atomically exchange research credits for a detached program copy."""
        if not buyer_id:
            raise ValueError("buyer_id is required")
        with self._lock:
            offer = self._offers.get(offer_id)
            if offer is None:
                raise KeyError("unknown offer")
            if offer.seller_id == buyer_id:
                raise ValueError("seller cannot acquire its own offer")
            available = self._credits.get(buyer_id, 0)
            if available < offer.price_credits:
                raise ValueError("insufficient research credits")
            self._credits[buyer_id] = available - offer.price_credits
            self._credits[offer.seller_id] = self._credits.get(offer.seller_id, 0) + offer.price_credits
            self._history.append({
                "event": "acquired", "offer_id": offer_id, "buyer_id": buyer_id,
                "seller_id": offer.seller_id, "price_credits": offer.price_credits,
            })
            return GPGenome.from_dict(offer.genome)

    def history(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(event) for event in self._history]


__all__ = ["ProgramOffer", "VerifiedProgramMarket"]
