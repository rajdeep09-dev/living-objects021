"""Candidate-only repair search for bounded v6 GP programs.

This module proposes and ranks AST changes using the typed interpreter.  It
never writes files, calls external services, runs exported source, or applies a
candidate to a live organism.  A caller must separately review and adopt a
returned proposal after its own policy checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from evolution.fitness import FitnessEvaluator, FitnessResult
from evolution.gp_engine import GPGenome, GPTreeBuilder
from evolution.program_validation import ProgramValidator, ValidationReport


@dataclass(frozen=True)
class RepairProposal:
    baseline: FitnessResult
    candidate: GPGenome
    candidate_result: FitnessResult
    validation: ValidationReport
    accepted_for_review: bool
    reason: str


class EvolutionaryRepair:
    """Generate finite GP AST variants and return only measurable improvements."""

    def __init__(self, builder: GPTreeBuilder, validator: ProgramValidator | None = None) -> None:
        self._builder = builder
        self._validator = validator or ProgramValidator()

    def variants(self, baseline: GPGenome, count: int = 8) -> list[GPGenome]:
        """Create a bounded set of tree-only variants; source is never executed."""
        if count < 1 or count > 64:
            raise ValueError("count must be within 1..64")
        transforms = (self._builder.point_mutate, self._builder.hoist_mutate, self._builder.expand_mutate)
        result: list[GPGenome] = []
        for index in range(count):
            tree = transforms[index % len(transforms)](baseline.tree)
            result.append(GPGenome(
                tree=tree,
                generation_created=baseline.generation_created + 1,
                parent_ids=[f"repair:{id(baseline)}"],
            ))
        return result

    def propose(
        self,
        baseline: GPGenome,
        evaluator: FitnessEvaluator,
        candidates: Iterable[GPGenome] | None = None,
    ) -> RepairProposal:
        """Return the best validated improvement for human/policy review only."""
        baseline_result = evaluator.batch_evaluate([baseline], seed=9_973)[0]
        best = baseline
        best_result = baseline_result
        best_validation = self._validator.validate_tree(baseline.tree)
        for candidate in candidates if candidates is not None else self.variants(baseline):
            validation = self._validator.validate_tree(candidate.tree)
            if not validation.valid:
                continue
            result = evaluator.batch_evaluate([candidate], seed=9_973)[0]
            if result.correctness > best_result.correctness or (
                result.correctness == best_result.correctness and candidate.complexity() < best.complexity()
            ):
                best, best_result, best_validation = candidate, result, validation
        improved = best_result.correctness > baseline_result.correctness
        return RepairProposal(
            baseline=baseline_result,
            candidate=best,
            candidate_result=best_result,
            validation=best_validation,
            accepted_for_review=improved and best_validation.valid,
            reason="measured held-out correctness improved" if improved else "no measured held-out improvement",
        )


__all__ = ["EvolutionaryRepair", "RepairProposal"]
