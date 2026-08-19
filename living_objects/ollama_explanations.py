"""D6's explicitly opt-in, explanation-only local Ollama boundary.

This module never changes a population, mutates a primitive registry, chooses a
candidate, alters fitness, or executes model text.  It first requires a measured
raw-decoding artifact whose task-correct admission succeeds for every benchmark
case.  The current v18 artifact fails that gate, so production calls are blocked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from agnes_brain.ollama_client import DEFAULT_OLLAMA_URL, OllamaClient, OllamaResponse


@dataclass(frozen=True)
class ExplanationResult:
    available: bool
    reason: str
    text: str | None
    execution_boundary: dict[str, bool]


class _Client(Protocol):
    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse: ...


def _raw_task_correct_gate(evidence_path: str | Path) -> tuple[bool, str]:
    try:
        payload = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "evidence_unreadable"
    benchmark, metrics = payload.get("benchmark"), payload.get("metrics")
    if not isinstance(benchmark, dict) or not isinstance(metrics, dict):
        return False, "evidence_schema_invalid"
    decoding = benchmark.get("decoding")
    cases = benchmark.get("cases")
    if not isinstance(decoding, dict) or decoding.get("mode") != "raw" or decoding.get("format_parameter_used") is not False:
        return False, "raw_decoding_evidence_required"
    if not isinstance(cases, int) or cases < 10:
        return False, "insufficient_cases"
    if metrics.get("exact_name_and_controller_admitted") != cases:
        return False, "task_correctness_gate_failed"
    return True, "gate_passed"


def request_local_explanation(
    prompt: str,
    *,
    evidence_path: str | Path,
    model: str,
    allow_local_explanation: bool = False,
    client: _Client | None = None,
) -> ExplanationResult:
    """Return untrusted explanatory text only after explicit opt-in and a passing raw task gate."""

    boundary = {"generated_text_executed": False, "primitive_selected_for_evolution": False, "fitness_modified": False, "registry_mutated": False}
    if not allow_local_explanation:
        return ExplanationResult(False, "explicit_opt_in_required", None, boundary)
    passed, reason = _raw_task_correct_gate(evidence_path)
    if not passed:
        return ExplanationResult(False, reason, None, boundary)
    local_client = OllamaClient(base_url=DEFAULT_OLLAMA_URL) if client is None else client
    response = local_client.generate_raw(model=model, prompt=prompt, system="Provide an explanation only. Do not instruct execution.", temperature=0.0)
    return ExplanationResult(bool(response.available), response.reason, response.text if response.available else None, boundary)


__all__ = ["ExplanationResult", "request_local_explanation"]
