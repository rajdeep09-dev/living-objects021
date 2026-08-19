"""D2's resumable, provenance-labelled local teacher-data collection.

Only responses that are both controller-admitted and exact matches for a
source-backed held-out metadata case are retained.  Invalid, mismatched, or
unavailable responses are counted but never converted into training rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Literal, Protocol

from agnes_brain.controller import resolve_guidance
from agnes_brain.ollama_client import DEFAULT_OLLAMA_URL, OllamaClient, OllamaResponse
from agnes_brain.ollama_controller_benchmark import CONTROLLER_JSON_SCHEMA, DEFAULT_MODEL, SYSTEM_PROMPT, ControllerBenchmarkCase, build_controller_cases
from living_objects.beast_brain.provenance import SourceKind, SourceReference


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v19" / "d2-teacher-data"


class _Client(Protocol):
    def availability(self, model: str) -> Any: ...

    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse: ...

    def generate_json_schema(self, *, model: str, prompt: str, json_schema: dict[str, Any], system: str | None = None, temperature: float = 0.0) -> OllamaResponse: ...


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        record_id = payload.get("record_id")
        if not isinstance(record_id, str):
            raise ValueError("existing teacher-data row lacks record_id")
        ids.add(record_id)
    return ids


def collect_teacher_data(
    *,
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    model: str = DEFAULT_MODEL,
    client: _Client | None = None,
    cases: Iterable[ControllerBenchmarkCase] | None = None,
    decoder_mode: Literal["raw", "ollama_json_schema"] = "raw",
    resume: bool = False,
) -> dict[str, Any]:
    """Collect accepted local teacher rows once, with an opt-in append-only resume path."""

    if decoder_mode not in {"raw", "ollama_json_schema"}:
        raise ValueError("decoder_mode must be 'raw' or 'ollama_json_schema'")
    destination = Path(output_directory)
    rows_path, artifact_path = destination / "teacher_data.jsonl", destination / "run.json"
    if artifact_path.exists():
        raise FileExistsError(f"refusing to overwrite completed D2 evidence: {artifact_path}")
    if rows_path.exists() and not resume:
        raise FileExistsError("teacher-data rows exist; use resume=True only after an interrupted collection")
    selected_cases = tuple(build_controller_cases() if cases is None else cases)
    seen = _existing_ids(rows_path)
    if not destination.exists():
        destination.mkdir(parents=True, exist_ok=False)
    local_client = OllamaClient(base_url=DEFAULT_OLLAMA_URL) if client is None else client
    availability = local_client.availability(model)
    counts = {"attempted": 0, "response_available": 0, "controller_admitted": 0, "exact_name_and_admitted": 0, "retained_rows": len(seen)}
    with rows_path.open("a", encoding="utf-8") as handle:
        if availability.available:
            for case in selected_cases:
                record_seed = f"{case.example_id}:{model}:{decoder_mode}"
                record_id = hashlib.sha256(record_seed.encode("utf-8")).hexdigest()
                if record_id in seen:
                    continue
                counts["attempted"] += 1
                response = local_client.generate_raw(model=model, prompt=case.prompt, system=SYSTEM_PROMPT, temperature=0.0) if decoder_mode == "raw" else local_client.generate_json_schema(model=model, prompt=case.prompt, json_schema=CONTROLLER_JSON_SCHEMA, system=SYSTEM_PROMPT, temperature=0.0)
                if not response.available or response.text is None:
                    continue
                counts["response_available"] += 1
                decision = resolve_guidance(response.text, profile_name="default")
                admitted = decision.accepted
                exact = admitted and decision.primitive_name == case.expected_name
                counts["controller_admitted"] += int(admitted)
                counts["exact_name_and_admitted"] += int(exact)
                if not exact:
                    continue
                source = SourceReference(kind=SourceKind.TEACHER_GENERATED, teacher_model=model, teacher_version="ollama-local-api", prompt_template_id="d2-controller-metadata-v1", note="Local unexecuted response matched source-backed expected primitive.")
                row = {
                    "schema_version": "beast-brain-d2-teacher-row-v1",
                    "record_id": record_id,
                    "source_record_id": case.source_record_id,
                    "example_id": case.example_id,
                    "input": case.prompt,
                    "output": response.text,
                    "source": source.to_dict(),
                    "decoder": {"mode": decoder_mode, "format_parameter_used": decoder_mode == "ollama_json_schema", "temperature": 0.0},
                    "response_sha256": response.raw_sha256,
                    "execution_boundary": {"generated_text_executed": False, "primitive_selected_for_evolution": False, "network_calls": 0},
                }
                handle.write(_canonical(row) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                seen.add(record_id)
                counts["retained_rows"] += 1
    artifact = {
        "schema_version": "beast-brain-d2-teacher-data-run-v1",
        "status": "completed" if availability.available else "blocked_model_unavailable",
        "model": {"identifier": model, "available": bool(availability.available), "reason": str(availability.reason)},
        "decoder": {"mode": decoder_mode, "format_parameter_used": decoder_mode == "ollama_json_schema"},
        "source": "ten deterministic v15 held-out primitive metadata cases; answer names remain redacted from prompts",
        "counts": counts,
        "teacher_data_sha256": hashlib.sha256(rows_path.read_bytes()).hexdigest(),
        "execution_boundary": {"generated_text_executed": False, "primitive_selected_for_evolution": False, "model_downloaded_by_collector": False},
        "claim_boundary": "Retained rows are local teacher-generated supervised text, not measured fitness, reasoning, or general code capability evidence.",
    }
    artifact_path.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    artifact_path.chmod(0o600)
    rows_path.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect D2 local teacher rows only when controller- and task-correct.")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--decoder-mode", choices=("raw", "ollama_json_schema"), default="raw")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(json.dumps(collect_teacher_data(output_directory=args.output_directory, model=args.model, decoder_mode=args.decoder_mode, resume=args.resume), sort_keys=True))


if __name__ == "__main__":
    main()
