"""Holdout-gated, candidate-only improvement decisions for v6 GP genomes."""
from __future__ import annotations

from dataclasses import dataclass

from evolution.fitness import FitnessEvaluator
from evolution.gp_engine import GPGenome
from evolution.program_validation import ProgramValidator, ValidationReport


@dataclass(frozen=True)
class ImprovementDecision:
    accepted: bool
    reason: str
    baseline_score: float
    candidate_score: float
    validation: ValidationReport


class SafeImprovementGate:
    """Promote only valid AST candidates that improve a deterministic holdout.

    The gate deliberately returns a decision rather than editing source files,
    calling external tools, or executing exported Python.  A caller may choose
    to persist the accepted *typed AST* as a new organism genome.
    """

    def __init__(self, evaluator: FitnessEvaluator, validator: ProgramValidator | None = None,
                 min_improvement: float = 0.01, max_complexity_ratio: float = 1.5) -> None:
        self.evaluator = evaluator
        self.validator = validator or ProgramValidator()
        self.min_improvement = max(0.0, min_improvement)
        self.max_complexity_ratio = max(1.0, max_complexity_ratio)

    def evaluate(self, baseline: GPGenome, candidate: GPGenome, seed: int = 101) -> ImprovementDecision:
        validation = self.validator.validate_tree(candidate.tree)
        if not validation.valid:
            return ImprovementDecision(False, validation.reason, baseline.fitness, candidate.fitness, validation)
        if candidate.complexity() > max(1, baseline.complexity()) * self.max_complexity_ratio:
            return ImprovementDecision(False, "candidate exceeds complexity budget", baseline.fitness, candidate.fitness, validation)
        baseline_result, candidate_result = self.evaluator.batch_evaluate([baseline, candidate], seed=seed)
        improvement = candidate_result.score - baseline_result.score
        if improvement < self.min_improvement:
            return ImprovementDecision(False, "insufficient holdout improvement", baseline_result.score, candidate_result.score, validation)
        return ImprovementDecision(True, "validated holdout improvement", baseline_result.score, candidate_result.score, validation)


__all__ = ["ImprovementDecision", "SafeImprovementGate"]
