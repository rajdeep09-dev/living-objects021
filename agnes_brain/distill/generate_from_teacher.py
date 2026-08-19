"""Generate source-backed, explicitly unverified D2 teacher rows.

The generator never invents a task label: every prompt carries the checked-in
base record's task and requests five paraphrased controller records for that
same approved primitive.  The default is dry-run; a local model call requires
``--execute`` and is bounded to loopback Ollama through the shared client.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Protocol

from agnes_brain.controller import resolve_guidance
from agnes_brain.json_instruction_data import build_json_instruction_split
from agnes_brain.ollama_client import DEFAULT_OLLAMA_URL, OllamaClient, OllamaResponse
from agnes_brain.ollama_controller_benchmark import DEFAULT_MODEL, SYSTEM_PROMPT
from living_objects.beast_brain.provenance import SourceKind, SourceReference


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_RECORDS = REPOSITORY_ROOT / "agnes_brain" / "training_data" / "primitives" / "from_codebase.jsonl"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "agnes_brain" / "training_data" / "teacher_generated.jsonl"
DEFAULT_MANIFEST = REPOSITORY_ROOT / "reports" / "v19" / "d2-teacher-generation" / "manifest.json"
CONTROLLER_KEYS = ("name", "description", "input_types", "output_type", "rationale")


class _Client(Protocol):
    def availability(self, model: str) -> Any: ...

    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse: ...


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _load_sources(path: Path) -> tuple[tuple[dict[str, Any], str], ...]:
    rows: list[tuple[dict[str, Any], str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        suggested, identifiers = row.get("suggested"), row.get("existing_primitives")
        if not isinstance(suggested, dict) or not isinstance(identifiers, list) or not isinstance(row.get("record_id"), str) or not isinstance(row.get("task"), str):
            raise ValueError(f"invalid approved base record on line {number}")
        if set(suggested) != set(CONTROLLER_KEYS) or any(not isinstance(value, str) for value in suggested.values() if not isinstance(value, list)):
            raise ValueError(f"invalid suggested controller schema on line {number}")
        rows.append((row, hashlib.sha256(line.encode("utf-8")).hexdigest()))
    if not rows:
        raise ValueError("approved base record file is empty")
    return tuple(rows)


def build_variation_prompt(row: dict[str, Any]) -> str:
    """Build a source-only prompt that cannot introduce a new task or primitive name."""

    target = row["suggested"]
    prompt = {
        "instruction": "Return JSON only. Produce exactly five concise paraphrases of the reviewed controller record. Preserve name, input_types, and output_type exactly. Do not define code, select a new primitive, or add a new task.",
        "task": row["task"],
        "approved_reviewed_record": target,
        "existing_approved_primitives": row["existing_primitives"],
        "response_contract": {"top_level_key": "variations", "variation_count": 5, "exact_keys_per_variation": list(CONTROLLER_KEYS)},
    }
    return _canonical(prompt)


def _parse_variations(text: str, *, expected_name: str) -> tuple[dict[str, Any], ...] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    variations = payload.get("variations") if isinstance(payload, dict) else None
    if not isinstance(variations, list) or len(variations) != 5:
        return None
    accepted: list[dict[str, Any]] = []
    for variation in variations:
        if not isinstance(variation, dict) or set(variation) != set(CONTROLLER_KEYS):
            return None
        if variation.get("name") != expected_name or not isinstance(variation.get("description"), str) or not isinstance(variation.get("rationale"), str):
            return None
        if not isinstance(variation.get("input_types"), list) or not all(isinstance(value, str) for value in variation["input_types"]) or not isinstance(variation.get("output_type"), str):
            return None
        decision = resolve_guidance(_canonical(variation), profile_name="default")
        if not decision.accepted or decision.primitive_name != expected_name:
            return None
        accepted.append(variation)
    return tuple(accepted)


def _existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    records: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        identifier = row.get("record_id")
        if not isinstance(identifier, str):
            raise ValueError("existing teacher output contains no record_id")
        records.add(identifier)
    return records


def generate_from_teacher(
    *,
    base_records_path: str | Path = DEFAULT_BASE_RECORDS,
    output_path: str | Path = DEFAULT_OUTPUT,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    model: str = DEFAULT_MODEL,
    execute: bool = False,
    resume: bool = False,
    limit: int | None = None,
    client: _Client | None = None,
) -> dict[str, Any]:
    """Validate sources and optionally append model-generated rows without overwrite or execution."""

    source_path, output, manifest = Path(base_records_path), Path(output_path), Path(manifest_path)
    if manifest.exists():
        raise FileExistsError(f"refusing to overwrite D2 manifest: {manifest}")
    if output.exists() and not resume:
        raise FileExistsError("teacher output already exists; use resume=True only after an interrupted collection")
    sources = _load_sources(source_path)
    # D4 uses the existing deterministic held-out partition.  D2 must never
    # turn those evaluation sources into teacher training rows.
    train_source_ids = {str(example["source_record_id"]) for example in build_json_instruction_split().train}
    sources = tuple(item for item in sources if str(item[0]["record_id"]) in train_source_ids)
    if not sources:
        raise ValueError("no approved D2 training records remain after source-disjoint split")
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        sources = sources[:limit]
    source_file_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    counts = {"source_records": len(sources), "prompts": len(sources), "requested_variations": len(sources) * 5, "responses_available": 0, "schema_valid_responses": 0, "retained_rows": 0}
    availability_reason = "dry_run"
    prior_ids = _existing_ids(output)
    if execute:
        local_client = OllamaClient(base_url=DEFAULT_OLLAMA_URL) if client is None else client
        availability = local_client.availability(model)
        availability_reason = str(availability.reason)
        if availability.available:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("a", encoding="utf-8") as handle:
                for source, digest in sources:
                    prompt = build_variation_prompt(source)
                    response = local_client.generate_raw(model=model, prompt=prompt, system=SYSTEM_PROMPT, temperature=0.0)
                    if not response.available or response.text is None:
                        continue
                    counts["responses_available"] += 1
                    variations = _parse_variations(response.text, expected_name=str(source["suggested"]["name"]))
                    if variations is None:
                        continue
                    counts["schema_valid_responses"] += 1
                    for ordinal, variation in enumerate(variations):
                        identity = hashlib.sha256(f"{source['record_id']}:{digest}:{model}:d2-v1:{ordinal}".encode("utf-8")).hexdigest()
                        if identity in prior_ids:
                            continue
                        provenance = SourceReference(kind=SourceKind.TEACHER_GENERATED, teacher_model=model, teacher_version="ollama-local-api", prompt_template_id="d2-five-variation-v1", note="Unverified local teacher text derived from a digest-identified approved base record.")
                        row = {"schema_version": "beast-brain-teacher-generated-v1", "record_id": identity, "model_generated": True, "unverified_teacher_data": True, "task": source["task"], "source_record_id": source["record_id"], "source_record_sha256": digest, "source_file_sha256": source_file_sha, "input": prompt, "output": variation, "source": provenance.to_dict(), "execution_boundary": {"generated_text_executed": False, "fitness_measured": False, "primitive_selected_for_evolution": False}}
                        handle.write(_canonical(row) + "\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                        prior_ids.add(identity)
                        counts["retained_rows"] += 1
    manifest.parent.mkdir(parents=True, exist_ok=True)
    status = "dry_run" if not execute else ("completed" if availability_reason == "available" else "blocked_model_unavailable")
    payload = {"schema_version": "beast-brain-d2-teacher-generation-manifest-v1", "status": status, "model": {"identifier": model, "availability_reason": availability_reason}, "base_records": {"path": str(source_path), "sha256": source_file_sha}, "output_path": str(output), "split": {"training_source_records_only": True, "method": "existing v15 sha256(source_record_id) modulo 5 split", "heldout_sources_reserved_for_d4": True}, "counts": counts, "execution_boundary": {"loopback_calls_only": bool(execute), "generated_text_executed": False, "fitness_measured": False, "model_downloaded": False, "registry_mutated": False}, "claim_boundary": "Rows, if retained, are unverified model-generated teaching data. They are not measured BEAST experience, approved new primitives, or evidence of reasoning/coding capability."}
    manifest.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest.chmod(0o600)
    if output.exists():
        output.chmod(0o600)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or run the guarded D2 teacher-data generator.")
    parser.add_argument("--base-records-path", type=Path, default=DEFAULT_BASE_RECORDS)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--execute", action="store_true", help="Make bounded local loopback calls; without this flag only a dry-run manifest is written.")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    print(json.dumps(generate_from_teacher(base_records_path=args.base_records_path, output_path=args.output_path, manifest_path=args.manifest_path, model=args.model, execute=args.execute, resume=args.resume, limit=args.limit), sort_keys=True))


if __name__ == "__main__":
    main()
