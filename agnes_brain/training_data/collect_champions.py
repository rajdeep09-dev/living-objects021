"""Collect source-audited champions from persisted local report artifacts.

This collector never executes exported source. It accepts only artifacts that
record interpreter-only, zero-network, zero-LLM execution and leaves every
explanation as the explicit placeholder ``FILL`` for later manual review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from living_objects.beast_brain.collectors import _record_id, write_jsonl_new
from living_objects.beast_brain.provenance import ArtifactMeasurement, ProvenanceError, SourceKind, SourceReference


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_ROOT = REPOSITORY_ROOT / "reports"
DEFAULT_DESTINATION = Path(__file__).resolve().parent / "explanations" / "from_champions.jsonl"


def _mapping_at(payload: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping) or not isinstance(current.get(key), Mapping):
            return None
        current = current[key]
    return current


def _candidate(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], tuple[str, ...], Mapping[str, Any], str] | None:
    """Return champion, field prefix, boundary, and task across supported local schemas."""

    result_champion = _mapping_at(payload, "result", "champion")
    result_boundary = _mapping_at(payload, "result", "execution_boundary")
    configuration = _mapping_at(payload, "configuration")
    if result_champion and result_boundary and configuration and isinstance(configuration.get("task"), str):
        return result_champion, ("result", "champion"), result_boundary, configuration["task"]

    final = _mapping_at(payload, "final")
    direct_boundary = _mapping_at(payload, "execution_boundary")
    if final and direct_boundary and configuration and isinstance(configuration.get("name"), str):
        return final, ("final",), direct_boundary, configuration["name"]

    direct_champion = _mapping_at(payload, "champion")
    if direct_champion and direct_boundary and isinstance(payload.get("task"), str):
        return direct_champion, ("champion",), direct_boundary, payload["task"]
    return None


def _is_local_interpreter_boundary(boundary: Mapping[str, Any]) -> bool:
    return (
        boundary.get("network_calls") == 0
        and boundary.get("llm_calls") == 0
        and boundary.get("generated_source_executed") is False
    )


def _fitness_field(champion: Mapping[str, Any], prefix: tuple[str, ...]) -> tuple[str, ...] | None:
    if isinstance(champion.get("training_fitness"), (int, float)):
        return (*prefix, "training_fitness")
    if isinstance(champion.get("fitness"), (int, float)):
        return (*prefix, "fitness")
    return None


def normalize_artifact(artifact_path: str | Path) -> dict[str, Any] | None:
    """Normalize a single supported artifact, or return ``None`` when not admissible.

    A ``None`` result means the file is unrelated, lacks an audited champion, or
    fails the local-execution boundary. It is intentionally excluded rather than
    represented as a training example with invented provenance.
    """

    path = Path(artifact_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    candidate = _candidate(payload)
    if candidate is None:
        return None
    champion, prefix, boundary, task = candidate
    source_code = champion.get("source_audit_export")
    field_path = _fitness_field(champion, prefix)
    if not isinstance(source_code, str) or not source_code.strip() or field_path is None:
        return None
    if not _is_local_interpreter_boundary(boundary):
        return None
    try:
        fitness = ArtifactMeasurement.from_artifact(path, field_path)
        source = SourceReference(
            kind=SourceKind.REAL_BEAST_RUN,
            artifact_path=fitness.artifact_path,
            artifact_sha256=fitness.artifact_sha256,
            note="Persisted report artifact collected without executing champion source.",
        )
        source.validate()
    except ProvenanceError:
        return None
    record: dict[str, Any] = {
        "schema_version": "agnes-brain-champion-explanation-v1",
        "task": task,
        "fitness": fitness.to_dict(),
        "source_code": source_code,
        "explanation": "FILL",
        "source": source.to_dict(),
        "execution_boundary": dict(boundary),
    }
    record["record_id"] = _record_id(record)
    return record


def build_examples(reports_root: str | Path = DEFAULT_REPORTS_ROOT) -> tuple[dict[str, Any], ...]:
    """Walk local reports and return unique, admissible source-audit records."""

    root = Path(reports_root)
    if not root.is_dir():
        raise ProvenanceError(f"reports root does not exist: {root}")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for artifact_path in sorted(root.rglob("*.json")):
        record = normalize_artifact(artifact_path)
        if record is not None and record["record_id"] not in seen:
            records.append(record)
            seen.add(record["record_id"])
    return tuple(records)


def collect(destination: str | Path = DEFAULT_DESTINATION, *, reports_root: str | Path = DEFAULT_REPORTS_ROOT) -> Path:
    """Write the local source-audited champion corpus exactly once."""

    return write_jsonl_new(build_examples(reports_root), destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect local source-audited champions.")
    parser.add_argument("--reports-root", type=Path, default=DEFAULT_REPORTS_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    output = collect(args.output, reports_root=args.reports_root)
    print(f"Wrote {len(build_examples(args.reports_root))} local champion records to {output}")


if __name__ == "__main__":
    main()
