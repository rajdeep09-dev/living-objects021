from __future__ import annotations

import pytest

from evolution.bug_fixer import BugReport, CandidateOnlyBugFixer


def test_candidate_only_bug_fixer_returns_small_passing_proposal() -> None:
    report = BugReport(
        bug_id="add-operator",
        broken_source="def add(left, right):\n    return left - right\n",
        assertion_test="assert add(2, 3) == 5",
    )
    candidate = CandidateOnlyBugFixer().propose(report)
    assert candidate is not None
    assert candidate.test_passed is True
    assert candidate.mutation == "swap_operator"
    assert "return left + right" in candidate.source
    assert "return left - right" in report.broken_source


def test_candidate_only_bug_fixer_rejects_unsafe_or_non_assert_test_inputs() -> None:
    fixer = CandidateOnlyBugFixer()
    with pytest.raises(ValueError, match="unsafe"):
        fixer.propose(BugReport("unsafe", "def x():\n return 1", "open('bad', 'w')"))
    with pytest.raises(ValueError, match="assertions only"):
        fixer.propose(BugReport("bad-test", "def x():\n return 1", "print(x())"))
