"""Safe repair-pattern evaluation without executing untrusted strategy code."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RepairResult:
    source_code: str
    improved: bool
    score: float
    applied_patterns: tuple[str, ...]


class DebuggerOrganism:
    """Uses whitelisted textual repairs and an injected deterministic verifier."""

    _PATTERNS = {
        "strip_trailing_whitespace": lambda code: "\n".join(line.rstrip() for line in code.splitlines()),
        "normalize_tabs": lambda code: code.replace("\t", "    "),
        "ensure_terminal_newline": lambda code: code.rstrip("\n") + "\n",
    }

    def attempt_repair(
        self,
        broken_source: str,
        baseline_score: float,
        verifier: Callable[[str], float],
    ) -> RepairResult | None:
        current = broken_source
        best_score = float(baseline_score)
        applied: list[str] = []
        for name, repair in self._PATTERNS.items():
            candidate = repair(current)
            score = max(0.0, min(1.0, float(verifier(candidate))))
            if score > best_score:
                current, best_score = candidate, score
                applied.append(name)
        if not applied:
            return None
        return RepairResult(current, True, best_score, tuple(applied))


__all__ = ["DebuggerOrganism", "RepairResult"]
