"""Create-once raw-output evaluation for an optional local Ollama model.

The ten cases are held-out source records from the existing v15 controller
corpus.  They ask only for a registered primitive name from provided approved
metadata.  This tests JSON generation and metadata-to-controller translation,
not reasoning, program synthesis, or an evolutionary improvement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

from agnes_brain.controller import resolve_guidance
from agnes_brain.json_instruction_data import CONTROLLER_KEYS, build_json_instruction_split
from agnes_brain.ollama_client import DEFAULT_OLLAMA_URL, OllamaAvailability, OllamaClient, OllamaResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "qwen2.5-coder:1.5b"
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v18" / "ollama-raw-controller-baseline"
BENCHMARK_SCHEMA_VERSION = "beast-brain-ollama-controller-baseline-v1"
SYSTEM_PROMPT = "Return only the requested JSON object. Do not execute code, define tools, or make requests."
CONTROLLER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": list(CONTROLLER_KEYS),
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "input_types": {"type": "array", "items": {"type": "string"}},
        "output_type": {"type": "string"},
        "rationale": {"type": "string"},
    },
}


class _LocalModelClient(Protocol):
    def availability(self, model: str) -> OllamaAvailability: ...

    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse: ...

    def generate_json_schema(
        self,
        *,
        model: str,
        prompt: str,
        json_schema: dict[str, Any],
        system: str | None = None,
        temperature: float = 0.0,
    ) -> OllamaResponse: ...


@dataclass(frozen=True)
class ControllerBenchmarkCase:
    """One source-backed, held-out metadata-to-controller translation task."""

    example_id: str
    source_record_id: str
    expected_name: str
    prompt: str


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _redact_expected_name(description: str, expected_name: str) -> str:
    """Remove only the answer token from source-backed metadata before prompting."""

    return re.sub(re.escape(expected_name), "the primitive", description, flags=re.IGNORECASE)


def build_controller_cases(*, limit: int = 10) -> tuple[ControllerBenchmarkCase, ...]:
    """Build a deterministic held-out prompt set without calling a model."""

    if not 1 <= int(limit) <= 10:
        raise ValueError("limit must be in [1, 10]")
    split = build_json_instruction_split()
    cases: list[ControllerBenchmarkCase] = []
    for example in sorted(split.holdout, key=lambda item: str(item["example_id"]))[:limit]:
        source_prompt = json.loads(str(example["input"]))
        target = json.loads(str(example["output"]))
        metadata = {
            "description": _redact_expected_name(str(target["description"]), str(target["name"])),
            "input_types": target["input_types"],
            "output_type": target["output_type"],
        }
        prompt = {
            "instruction": "Return one controller-compatible suggestion for the supplied approved metadata.",
            "allowed_existing_primitives": source_prompt["existing_primitives"],
            "approved_metadata": metadata,
            "response_contract": {
                "json_only": True,
                "required_keys": list(CONTROLLER_KEYS),
                "restriction": "Select an existing default-profile primitive. Do not define or execute code.",
            },
        }
        cases.append(
            ControllerBenchmarkCase(
                example_id=str(example["example_id"]),
                source_record_id=str(example["source_record_id"]),
                expected_name=str(target["name"]),
                prompt=_canonical_json(prompt),
            )
        )
    if len(cases) != limit:
        raise ValueError("the held-out source corpus did not provide the requested number of cases")
    if len({case.source_record_id for case in cases}) != len(cases):
        raise ValueError("benchmark cases must remain source-record disjoint")
    return tuple(cases)


def _response_validity(raw_text: str) -> tuple[bool, bool, dict[str, Any] | None]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return False, False, None
    if not isinstance(payload, dict) or set(payload) != set(CONTROLLER_KEYS):
        return True, False, payload if isinstance(payload, dict) else None
    return True, True, payload


def evaluate_raw_controller_baseline(
    *,
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    model: str = DEFAULT_MODEL,
    client: _LocalModelClient | None = None,
    limit: int = 10,
    decoder_mode: Literal["raw", "ollama_json_schema"] = "raw",
) -> dict[str, Any]:
    """Evaluate raw local completions and persist compact digests once.

    The persisted artifact intentionally excludes raw prompts and raw model text.
    It records only source identifiers, digests, byte sizes, validation outcomes,
    and controller audit metadata.  Model output remains untrusted and unexecuted.
    """

    destination = Path(output_directory)
    artifact_path = destination / "run.json"
    if artifact_path.exists():
        raise FileExistsError(f"refusing to overwrite Ollama baseline evidence: {artifact_path}")
    if decoder_mode not in {"raw", "ollama_json_schema"}:
        raise ValueError("decoder_mode must be 'raw' or 'ollama_json_schema'")
    local_client = OllamaClient(base_url=DEFAULT_OLLAMA_URL) if client is None else client
    availability = local_client.availability(model)
    cases = build_controller_cases(limit=limit)
    artifact: dict[str, Any] = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "status": "completed" if availability.available else "blocked_model_unavailable",
        "model": {"identifier": model, "available": availability.available, "availability_reason": availability.reason},
        "benchmark": {
            "cases": len(cases),
            "source": "v15 checked-in primitive metadata; deterministic held-out source records",
            "source_disjoint_from_v15_training": True,
            "task": "metadata-to-controller translation",
            "decoding": {
                "mode": decoder_mode,
                "format_parameter_used": decoder_mode == "ollama_json_schema",
                "json_schema_sha256": hashlib.sha256(_canonical_json(CONTROLLER_JSON_SCHEMA).encode("utf-8")).hexdigest() if decoder_mode == "ollama_json_schema" else None,
                "temperature": 0.0,
                "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
            },
        },
        "records": [],
        "metrics": {
            "raw_json_valid": 0,
            "required_contract_valid": 0,
            "exact_name": 0,
            "controller_admitted": 0,
            "exact_name_and_controller_admitted": 0,
        },
        "execution_boundary": {
            "local_loopback_http_calls_only": True,
            "model_downloaded_by_evaluator": False,
            "generated_text_executed": False,
            "candidate_program_executed": False,
            "primitive_selected_for_evolution": False,
            "global_registry_mutated": False,
        },
        "claim_boundary": "This measures ten source-backed metadata-to-controller translations. A provider-side JSON Schema diagnostic measures constrained form, not raw decoding or model reasoning. Neither mode is evidence of coding, general language ability, native-model improvement, or frontier-model equivalence.",
    }
    if availability.available:
        for case in cases:
            response = (
                local_client.generate_raw(model=model, prompt=case.prompt, system=SYSTEM_PROMPT, temperature=0.0)
                if decoder_mode == "raw"
                else local_client.generate_json_schema(
                    model=model,
                    prompt=case.prompt,
                    json_schema=CONTROLLER_JSON_SCHEMA,
                    system=SYSTEM_PROMPT,
                    temperature=0.0,
                )
            )
            raw_json_valid, required_valid, payload = _response_validity(response.text) if response.available and response.text is not None else (False, False, None)
            expected_name = payload.get("name") if payload is not None else None
            exact_name = required_valid and expected_name == case.expected_name
            decision = resolve_guidance(response.text, profile_name="default") if response.available and response.text is not None else None
            admitted = bool(decision and decision.accepted)
            exact_name_and_admitted = admitted and exact_name
            artifact["metrics"]["raw_json_valid"] += int(raw_json_valid)
            artifact["metrics"]["required_contract_valid"] += int(required_valid)
            artifact["metrics"]["exact_name"] += int(exact_name)
            artifact["metrics"]["controller_admitted"] += int(admitted)
            artifact["metrics"]["exact_name_and_controller_admitted"] += int(exact_name_and_admitted)
            artifact["records"].append(
                {
                    "example_id": case.example_id,
                    "source_record_id": case.source_record_id,
                    "expected_name_sha256": hashlib.sha256(case.expected_name.encode("utf-8")).hexdigest(),
                    "prompt_sha256": hashlib.sha256(case.prompt.encode("utf-8")).hexdigest(),
                    "response": {
                        "available": response.available,
                        "reason": response.reason,
                        "raw_sha256": response.raw_sha256,
                        "raw_bytes": response.raw_bytes,
                        "request_bytes": response.request_bytes,
                        "elapsed_seconds": response.elapsed_seconds,
                        "persisted_raw_text": False,
                    },
                    "raw_json_valid": raw_json_valid,
                    "required_contract_valid": required_valid,
                    "exact_name": exact_name,
                    "controller_admitted": admitted,
                    "exact_name_and_controller_admitted": exact_name_and_admitted,
                    "controller_decision": decision.audit_record() if decision is not None else None,
                }
            )
    destination.mkdir(parents=True, exist_ok=True)
    with artifact_path.open("x", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    artifact_path.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a raw local Ollama controller baseline without executing model text.")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--decoder-mode", choices=("raw", "ollama_json_schema"), default="raw")
    args = parser.parse_args()
    artifact = evaluate_raw_controller_baseline(output_directory=args.output_directory, model=args.model, decoder_mode=args.decoder_mode)
    print(json.dumps({"status": artifact["status"], "model": args.model, "metrics": artifact["metrics"]}, sort_keys=True))


if __name__ == "__main__":
    main()
