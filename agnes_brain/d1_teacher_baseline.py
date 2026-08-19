"""D1's immutable raw local-teacher baseline.

The baseline has a single deliberately small contract: request JSON from a
named already-installed local Ollama model, parse it independently, and report
whether the returned ``name`` is snake case.  It neither constrains decoding nor
executes the returned text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Protocol

from agnes_brain.ollama_client import DEFAULT_OLLAMA_URL, OllamaClient, OllamaResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "qwen2.5-coder:1.5b"
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v19" / "d1-teacher-baseline"
DEFAULT_TEXT_REPORT = REPOSITORY_ROOT / "reports" / "v15" / "teacher-baseline-test.txt"
D1_PROMPT = 'Return JSON only: {"name":"example_primitive","inputs":["float"],"output":"float"}'
_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


class _Client(Protocol):
    def availability(self, model: str) -> Any: ...

    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse: ...


def _parse_name(text: str | None) -> tuple[bool, str | None, bool]:
    if text is None:
        return False, None, False
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return False, None, False
    name = payload.get("name") if isinstance(payload, dict) else None
    return True, name if isinstance(name, str) else None, bool(isinstance(name, str) and _SNAKE_CASE.fullmatch(name))


def run_d1_teacher_baseline(
    *, output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY, text_report_path: str | Path = DEFAULT_TEXT_REPORT, model: str = DEFAULT_MODEL, client: _Client | None = None
) -> dict[str, Any]:
    """Create one raw-output baseline artifact, refusing to overwrite evidence."""

    destination = Path(output_directory)
    artifact_path = destination / "run.json"
    text_report = Path(text_report_path)
    if artifact_path.exists():
        raise FileExistsError(f"refusing to overwrite D1 evidence: {artifact_path}")
    if text_report.exists():
        raise FileExistsError(f"refusing to overwrite D1 standalone report: {text_report}")
    local_client = OllamaClient(base_url=DEFAULT_OLLAMA_URL) if client is None else client
    availability = local_client.availability(model)
    artifact: dict[str, Any] = {
        "schema_version": "beast-brain-d1-teacher-baseline-v1",
        "status": "blocked_model_unavailable",
        "model": {"identifier": model, "available": bool(availability.available), "reason": str(availability.reason)},
        "prompt_sha256": hashlib.sha256(D1_PROMPT.encode("utf-8")).hexdigest(),
        "decoder": {"mode": "raw", "temperature": 0.0, "format_parameter_used": False},
        "metrics": {"valid_json": False, "name_present": False, "snake_case_name": False},
        "response": {"available": False, "reason": "model_unavailable", "raw_sha256": None, "raw_bytes": 0, "persisted_raw_text": False},
        "execution_boundary": {"local_loopback_http_calls_only": True, "generated_text_executed": False, "primitive_selected_for_evolution": False},
        "claim_boundary": "This one-prompt raw local API check is not a reasoning, coding, instruction-following, or controller-admission benchmark.",
    }
    if availability.available:
        response = local_client.generate_raw(model=model, prompt=D1_PROMPT, temperature=0.0)
        valid_json, name, snake_case = _parse_name(response.text if response.available else None)
        artifact["status"] = "completed" if response.available else "blocked_completion_unavailable"
        artifact["metrics"] = {"valid_json": valid_json, "name_present": name is not None, "snake_case_name": snake_case}
        artifact["response"] = {"available": response.available, "reason": response.reason, "raw_sha256": response.raw_sha256, "raw_bytes": response.raw_bytes, "persisted_raw_text": False}
        raw_for_report = response.text if response.available and response.text is not None else ""
    else:
        raw_for_report = ""
    destination.mkdir(parents=True, exist_ok=True)
    text_report.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    verdict = f"VALID: {name}" if artifact["metrics"]["valid_json"] and artifact["metrics"]["snake_case_name"] else "INVALID"
    text_report.write_text(raw_for_report + ("\n" if raw_for_report else "") + verdict + "\n", encoding="utf-8")
    artifact_path.chmod(0o600)
    text_report.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Run D1's raw local teacher baseline without executing output.")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--text-report-path", type=Path, default=DEFAULT_TEXT_REPORT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(json.dumps(run_d1_teacher_baseline(output_directory=args.output_directory, text_report_path=args.text_report_path, model=args.model), sort_keys=True))


if __name__ == "__main__":
    main()
