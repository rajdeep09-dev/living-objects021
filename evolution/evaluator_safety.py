"""Explicit evaluator approval policy for bounded evolutionary runs.

An evaluator can be deterministic yet still be unsuitable for evolutionary
selection.  This module records that distinction centrally and makes a pending
review fail closed at construction and population-entry boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class EvaluatorNotApprovedError(RuntimeError):
    """Raised when a task evaluator has no approved safety contract."""


@dataclass(frozen=True)
class EvaluatorApproval:
    evaluator_name: str
    approved: bool
    review_id: str
    reason: str


_APPROVALS: dict[str, EvaluatorApproval] = {
    "GameStrategyEvaluator": EvaluatorApproval(
        evaluator_name="GameStrategyEvaluator",
        approved=False,
        review_id="v12-game-strategy-review-pending",
        reason=(
            "GameStrategyEvaluator is disabled pending a task-specific evaluator safety review; "
            "do not rank or evolve organisms with this benchmark."
        ),
    ),
}


def evaluator_approval(evaluator_or_type: Any) -> EvaluatorApproval:
    """Return a fail-closed approval decision for an evaluator class or instance."""
    evaluator_type = evaluator_or_type if isinstance(evaluator_or_type, type) else type(evaluator_or_type)
    name = evaluator_type.__name__
    return _APPROVALS.get(
        name,
        EvaluatorApproval(
            evaluator_name=name,
            approved=True,
            review_id="v12-baseline-evaluator-contract",
            reason="Evaluator is covered by the bounded baseline evaluator contract.",
        ),
    )


def require_evaluator_approval(evaluator_or_type: Any) -> None:
    """Fail closed when an evaluator has an explicit pending or rejected review."""
    decision = evaluator_approval(evaluator_or_type)
    if not decision.approved:
        raise EvaluatorNotApprovedError(f"{decision.reason} Review: {decision.review_id}.")


__all__ = [
    "EvaluatorApproval",
    "EvaluatorNotApprovedError",
    "evaluator_approval",
    "require_evaluator_approval",
]
