"""Safe local dataset collection for BEAST-BRAIN research.

Collectors in this module read repository-local declarative metadata and
persisted run artifacts. They never execute champion source, evaluate a
population, invoke a model, make a request, or create a background process.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from evolution.evaluator_safety import require_evaluator_approval
from evolution.fitness import FitnessEvaluator
from evolution.primitive_registry import approved_primitives, primitive_approval

from .provenance import ArtifactMeasurement, ProvenanceError, SourceKind, SourceReference


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _record_id(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _json_value(value: Any, field_name: str) -> Any:
    """Convert only JSON-compatible deterministic evaluator values to plain data."""

    try:
        return json.loads(json.dumps(value, ensure_ascii=True, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ProvenanceError(f"{field_name} is not JSON-compatible deterministic data") from exc


def collect_primitive_cards(profile_name: str = "default") -> tuple[dict[str, Any], ...]:
    """Serialize primitive metadata already admitted by a declared profile.

    Function bodies are intentionally excluded. A card describes the existing
    typed grammar; it is not permission to execute an additional primitive.
    """

    cards: list[dict[str, Any]] = []
    for primitive in approved_primitives(profile_name):
        approval = primitive_approval(primitive.name)
        if approval.has_side_effects or approval.requires_network or approval.requires_filesystem:
            raise ProvenanceError(f"local collector refuses non-pure primitive {primitive.name!r}")
        card: dict[str, Any] = {
            "schema_version": "beast-brain-primitive-card-v1",
            "source": {"kind": "local_primitive_registry", "profile": profile_name},
            "name": primitive.name,
            "arity": primitive.arity,
            "input_types": list(primitive.arg_types),
            "output_type": primitive.return_type,
            "tier": approval.tier,
            "execution_environment": approval.execution_environment,
            "approved_profiles": sorted(approval.approved_profiles),
        }
        card["record_id"] = _record_id(card)
        cards.append(card)
    return tuple(cards)


def collect_evaluator_case_cards(
    evaluator: FitnessEvaluator,
    *,
    seed: int,
    case_count: int,
) -> tuple[dict[str, Any], ...]:
    """Serialize deterministic, evaluator-owned cases without evaluating programs."""

    require_evaluator_approval(evaluator)
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ProvenanceError("seed must be a non-negative integer")
    if not isinstance(case_count, int) or isinstance(case_count, bool) or case_count < 1:
        raise ProvenanceError("case_count must be a positive integer")
    cases = evaluator.generate_test_cases(seed=seed, n=case_count)
    if len(cases) > case_count:
        raise ProvenanceError("evaluator generated more cases than requested")
    cards: list[dict[str, Any]] = []
    for index, (input_value, expected_output) in enumerate(cases):
        card: dict[str, Any] = {
            "schema_version": "beast-brain-evaluator-case-v1",
            "source": {
                "kind": "local_deterministic_evaluator",
                "evaluator": type(evaluator).__name__,
                "seed": seed,
                "case_index": index,
            },
            "input": _json_value(input_value, "evaluator input"),
            "expected_output": _json_value(expected_output, "evaluator expected_output"),
        }
        card["record_id"] = _record_id(card)
        cards.append(card)
    return tuple(cards)


def _load_artifact(path: str | Path) -> tuple[Path, Mapping[str, Any]]:
    artifact_path = Path(path)
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"cannot read local JSON artifact: {artifact_path}") from exc
    if not isinstance(payload, Mapping):
        raise ProvenanceError("artifact root must be a JSON object")
    return artifact_path, payload


def _mapping_at(payload: Mapping[str, Any], *keys: str) -> Mapping[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping) or not isinstance(current.get(key), Mapping):
            raise ProvenanceError(f"artifact is missing object at {'.'.join(keys)!r}")
        current = current[key]
    return current


def _require_local_execution_boundary(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = _mapping_at(payload, "result", "execution_boundary")
    if boundary.get("network_calls") != 0 or boundary.get("llm_calls") != 0:
        raise ProvenanceError("collector accepts only artifacts that record zero network and LLM calls")
    if boundary.get("generated_source_executed") is not False:
        raise ProvenanceError("collector accepts only interpreter-only artifact evidence")
    return boundary


def collect_champion_card(artifact_path: str | Path) -> dict[str, Any]:
    """Normalize one existing zero-network local champion artifact.

    The card exposes two independently named measured scores rather than
    mislabelling training and fresh-held-out metrics as a time-series action.
    """

    path, payload = _load_artifact(artifact_path)
    boundary = _require_local_execution_boundary(payload)
    configuration = _mapping_at(payload, "configuration")
    champion = _mapping_at(payload, "result", "champion")
    training = ArtifactMeasurement.from_artifact(path, ("result", "champion", "training_fitness"))
    fresh = ArtifactMeasurement.from_artifact(path, ("result", "champion", "fresh", "correctness"))
    source = SourceReference(
        kind=SourceKind.REAL_BEAST_RUN,
        artifact_path=training.artifact_path,
        artifact_sha256=training.artifact_sha256,
        note="Local persisted champion artifact; no source execution occurred during collection.",
    )
    source.validate()
    task = configuration.get("task")
    seed = configuration.get("seed")
    if not isinstance(task, str) or not task:
        raise ProvenanceError("artifact configuration.task must be a non-empty string")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ProvenanceError("artifact configuration.seed must be a non-negative integer")
    primitives = champion.get("tree", {}).get("primitives_used") if isinstance(champion.get("tree"), Mapping) else None
    if not isinstance(primitives, list) or any(not isinstance(name, str) or not name for name in primitives):
        raise ProvenanceError("artifact champion tree must list primitive names")
    card: dict[str, Any] = {
        "schema_version": "beast-brain-champion-card-v1",
        "source": source.to_dict(),
        "task": task,
        "seed": seed,
        "generation": champion.get("generation"),
        "tree_sha256": champion.get("tree_sha256"),
        "primitives_used": primitives,
        "source_audit_export": champion.get("source_audit_export"),
        "measured_scores": {
            "training_fitness": training.to_dict(),
            "fresh_correctness": fresh.to_dict(),
        },
        "execution_boundary": dict(boundary),
    }
    card["record_id"] = _record_id(card)
    return card


def write_jsonl_new(records: Iterable[Mapping[str, Any]], destination: str | Path) -> Path:
    """Persist a local dataset once, with canonical JSON and no overwrite path."""

    materialized = tuple(records)
    if not materialized:
        raise ProvenanceError("refuse to create an empty dataset")
    identifiers: set[str] = set()
    lines: list[bytes] = []
    for record in materialized:
        if not isinstance(record, Mapping):
            raise ProvenanceError("dataset records must be JSON objects")
        identifier = record.get("record_id")
        if not isinstance(identifier, str) or len(identifier) != 64:
            raise ProvenanceError("dataset record must have a 64-character record_id")
        expected_identifier = _record_id({key: value for key, value in record.items() if key != "record_id"})
        if identifier != expected_identifier:
            raise ProvenanceError("dataset record_id does not match canonical record content")
        if identifier in identifiers:
            raise ProvenanceError("dataset contains duplicate record_id values")
        identifiers.add(identifier)
        lines.append(_canonical_json(record) + b"\n")
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ProvenanceError(f"dataset already exists: {target}") from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.writelines(lines)
    return target
