"""Minimal D6 client facade: gated local explanations only.

It intentionally exposes no primitive suggestion, code generation, execution,
or mutation capability.  A caller gets no model request unless the independently
recorded raw task-correctness gate has passed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from living_objects.ollama_explanations import ExplanationResult, _raw_task_correct_gate, request_local_explanation


class AgnesBrainClient:
    """An explicitly opt-in, explanation-only local client with fail-closed availability."""

    def __init__(self, *, evidence_path: str | Path, model: str, client: Any | None = None) -> None:
        self.evidence_path = Path(evidence_path)
        self.model = str(model)
        self._client = client

    def is_available(self) -> bool:
        passed, _ = _raw_task_correct_gate(self.evidence_path)
        return passed

    def explain(self, code: str, task: str, fitness: float) -> ExplanationResult:
        prompt = f"Explain this already-selected GP audit export for task {task!r} with recorded training fitness {fitness:.6f}. Do not propose modifications or execution.\n\n{code}"
        return request_local_explanation(prompt, evidence_path=self.evidence_path, model=self.model, allow_local_explanation=True, client=self._client)


__all__ = ["AgnesBrainClient", "ExplanationResult"]
