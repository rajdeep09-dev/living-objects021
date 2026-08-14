"""Candidate-only source repair for small, reproducible Python functions.

The implementation is intentionally narrower than autonomous production repair:
it accepts supplied source and an assertion-only test, creates finite AST edits,
tests candidates in ``IsolatedSandbox``, and returns a proposal.  It never opens
or changes repository files, installs a candidate, invokes a network service, or
uses evolved source in the main process.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import Iterable

from evolution.sandbox import IsolatedSandbox, ResourceLimits


@dataclass(frozen=True)
class BugReport:
    bug_id: str
    broken_source: str
    assertion_test: str
    expected_output: str = ""
    task_domain: str = "local_python"


@dataclass(frozen=True)
class FixCandidate:
    source: str
    test_passed: bool
    edit_distance: int
    generation: int
    mutation: str
    assertions_passed: int = 0
    assertions_total: int = 0
    sandbox_stdout: str = ""
    sandbox_stderr: str = ""


class CandidateOnlyBugFixer:
    """Bounded candidate-only AST repair with partial-test survivor selection.

    Every source candidate remains a proposal only and is evaluated exclusively
    in :class:`IsolatedSandbox`. A failed round retains only a small number of
    candidates that satisfy the most individual assertions, allowing a two-step
    repair to be discovered without permission to alter a repository, install
    code, or invoke external services.
    """

    MAX_SOURCE_BYTES = 16_384
    MAX_CANDIDATES = 64
    MAX_ROUNDS = 4
    MAX_SURVIVORS = 4

    def __init__(self, sandbox: IsolatedSandbox | None = None) -> None:
        self._sandbox = sandbox or IsolatedSandbox(ResourceLimits(max_cpu_ms=350, max_memory_mb=32))

    def propose(self, report: BugReport) -> FixCandidate | None:
        self._validate_report(report)
        assertions = self._assertion_sources(report.assertion_test)
        survivors: list[FixCandidate] = [
            FixCandidate(
                source=report.broken_source,
                test_passed=False,
                edit_distance=0,
                generation=0,
                mutation="seed",
                assertions_passed=0,
                assertions_total=len(assertions),
            )
        ]
        evaluated_sources = {report.broken_source}
        budget_remaining = self.MAX_CANDIDATES

        for generation in range(1, self.MAX_ROUNDS + 1):
            round_candidates: list[FixCandidate] = []
            for seed in survivors:
                for mutation, source in self._mutations(seed.source):
                    if budget_remaining <= 0:
                        break
                    if source in evaluated_sources:
                        continue
                    evaluated_sources.add(source)
                    budget_remaining -= 1
                    result = self._sandbox.run(f"{source}\n\n{report.assertion_test}\n", timeout_ms=350)
                    assertions_passed = len(assertions) if result.ok else self._count_passing_assertions(source, assertions)
                    round_candidates.append(FixCandidate(
                        source=source,
                        test_passed=result.ok,
                        edit_distance=self._edit_distance(report.broken_source, source),
                        generation=generation,
                        mutation=mutation if seed.generation == 0 else f"{seed.mutation}->{mutation}",
                        assertions_passed=assertions_passed,
                        assertions_total=len(assertions),
                        sandbox_stdout=result.stdout,
                        sandbox_stderr=result.stderr,
                    ))
                if budget_remaining <= 0:
                    break
            passing = [candidate for candidate in round_candidates if candidate.test_passed]
            if passing:
                return min(passing, key=lambda item: (item.edit_distance, item.mutation))
            if not round_candidates or budget_remaining <= 0:
                break
            survivors = sorted(
                round_candidates,
                key=lambda item: (-item.assertions_passed, item.edit_distance, item.mutation, item.source),
            )[: self.MAX_SURVIVORS]
        return None

    def _validate_report(self, report: BugReport) -> None:
        if not report.bug_id or len(report.broken_source.encode("utf-8")) > self.MAX_SOURCE_BYTES:
            raise ValueError("bug_id is required and source must be at most 16384 bytes")
        if len(report.assertion_test.encode("utf-8")) > self.MAX_SOURCE_BYTES:
            raise ValueError("test must be at most 16384 bytes")
        source_tree = ast.parse(report.broken_source, mode="exec")
        test_tree = ast.parse(report.assertion_test, mode="exec")
        disallowed = (ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith, ast.Global, ast.Nonlocal, ast.ClassDef)
        for tree in (source_tree, test_tree):
            for node in ast.walk(tree):
                if isinstance(node, disallowed):
                    raise ValueError("imports, context managers, globals, and classes are not permitted")
                if isinstance(node, ast.Name) and node.id in {"open", "exec", "eval", "compile", "__import__"}:
                    raise ValueError("unsafe name in repair input")
        if not test_tree.body or not all(isinstance(node, ast.Assert) for node in test_tree.body):
            raise ValueError("test must contain assertions only")

    def _mutations(self, source: str) -> Iterable[tuple[str, str]]:
        tree = ast.parse(source, mode="exec")
        nodes = list(ast.walk(tree))
        operator_swaps: dict[type[ast.operator], type[ast.operator]] = {
            ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult,
        }
        comparisons: dict[type[ast.cmpop], type[ast.cmpop]] = {
            ast.Gt: ast.Lt, ast.Lt: ast.Gt, ast.GtE: ast.LtE, ast.LtE: ast.GtE,
        }
        for index, node in enumerate(nodes):
            if isinstance(node, ast.BinOp) and type(node.op) in operator_swaps:
                clone = copy.deepcopy(tree)
                target = list(ast.walk(clone))[index]
                assert isinstance(target, ast.BinOp)
                target.op = operator_swaps[type(target.op)]()
                yield "swap_operator", self._unparse(clone)
            elif isinstance(node, ast.Compare) and node.ops and type(node.ops[0]) in comparisons:
                clone = copy.deepcopy(tree)
                target = list(ast.walk(clone))[index]
                assert isinstance(target, ast.Compare)
                target.ops[0] = comparisons[type(target.ops[0])]()
                yield "flip_comparator", self._unparse(clone)
            elif isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
                for delta in (-1, 1):
                    clone = copy.deepcopy(tree)
                    target = list(ast.walk(clone))[index]
                    assert isinstance(target, ast.Constant)
                    target.value += delta
                    yield "off_by_one", self._unparse(clone)

    def _count_passing_assertions(self, source: str, assertions: tuple[str, ...]) -> int:
        """Measure assertion-level progress in isolated, independent runs."""
        return sum(
            self._sandbox.run(f"{source}\n\n{assertion}\n", timeout_ms=350).ok
            for assertion in assertions
        )

    @staticmethod
    def _assertion_sources(assertion_test: str) -> tuple[str, ...]:
        """Normalize each pre-validated assertion into an isolated test script."""
        tree = ast.parse(assertion_test, mode="exec")
        return tuple(ast.unparse(node) for node in tree.body)

    @staticmethod
    def _unparse(tree: ast.AST) -> str:
        return ast.unparse(ast.fix_missing_locations(tree))

    @staticmethod
    def _edit_distance(left: str, right: str) -> int:
        return sum(a != b for a, b in zip(left, right)) + abs(len(left) - len(right))


__all__ = ["BugReport", "FixCandidate", "CandidateOnlyBugFixer"]
