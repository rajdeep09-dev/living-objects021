"""D4 deterministic source-disjoint evaluator for externally produced student records."""

from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path
from typing import Any, Iterable

from agnes_brain.controller import resolve_guidance
from agnes_brain.json_instruction_data import build_json_instruction_split
from agnes_brain.ollama_controller_benchmark import ControllerBenchmarkCase, build_controller_cases


def evaluate_student_responses(
    responses: Iterable[dict[str, Any]], *, cases: Iterable[ControllerBenchmarkCase] | None = None, teacher_metrics: dict[str, Any] | None = None, training_source_ids: Iterable[str] = ()
) -> dict[str, Any]:
    """Score responses with a fixed exact-name rubric; no model calls or execution occur."""

    expected = {case.source_record_id: case for case in (build_controller_cases() if cases is None else cases)}
    declared_training_ids = {str(identifier) for identifier in training_source_ids}
    if cases is None and not declared_training_ids:
        declared_training_ids = {str(example["source_record_id"]) for example in build_json_instruction_split().train}
    overlap = set(expected) & declared_training_ids
    if overlap:
        raise ValueError("student evaluation cases overlap declared training source identifiers")
    records = list(responses)
    if len({str(row.get("source_record_id")) for row in records}) != len(records):
        raise ValueError("student responses must contain at most one row per source record")
    metrics = {"cases": len(expected), "submitted": 0, "raw_json_valid": 0, "schema_valid": 0, "exact_name": 0, "controller_admitted": 0, "exact_name_and_controller_admitted": 0}
    audit: list[dict[str, Any]] = []
    for source_record_id, case in sorted(expected.items()):
        row = next((item for item in records if item.get("source_record_id") == source_record_id), None)
        text = row.get("response") if isinstance(row, dict) else None
        metrics["submitted"] += int(isinstance(text, str))
        if isinstance(text, str):
            try:
                payload, json_valid = json.loads(text), True
            except json.JSONDecodeError:
                payload, json_valid = None, False
        else:
            payload, json_valid = None, False
        schema_valid = bool(isinstance(payload, dict) and set(payload) == {"name", "description", "input_types", "output_type", "rationale"})
        decision = resolve_guidance(text, profile_name="default") if isinstance(text, str) else None
        exact = bool(schema_valid and payload.get("name") == case.expected_name)
        admitted = bool(decision and decision.accepted)
        exact_admitted = exact and admitted
        metrics["raw_json_valid"] += int(json_valid)
        metrics["schema_valid"] += int(schema_valid)
        metrics["exact_name"] += int(exact)
        metrics["controller_admitted"] += int(admitted)
        metrics["exact_name_and_controller_admitted"] += int(exact_admitted)
        audit.append({"source_record_id": source_record_id, "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text, str) else None, "raw_json_valid": json_valid, "schema_valid": schema_valid, "exact_name": exact, "controller_admitted": admitted, "exact_name_and_controller_admitted": exact_admitted})
    return {"schema_version": "beast-brain-d4-student-evaluation-v1", "metrics": metrics, "teacher_comparison": teacher_metrics or None, "source_disjoint_from_declared_training": True, "records": audit, "execution_boundary": {"model_calls": 0, "generated_text_executed": False, "primitive_selected_for_evolution": False}, "claim_boundary": "Exact source-backed primitive recovery is the sole task-correctness rubric; this score does not measure general reasoning or coding."}


def main() -> None:
    """Evaluate a JSONL response file without invoking or executing a model."""

    parser = argparse.ArgumentParser(description="Run D4 deterministic student evaluation without model calls.")
    parser.add_argument("--responses-jsonl", type=Path, help="Optional JSONL student submissions; omitted means an explicit empty-submission baseline.")
    parser.add_argument("--report-path", type=Path, required=True)
    parser.add_argument("--training-source-ids-json", type=Path)
    args = parser.parse_args()
    if args.report_path.exists():
        raise FileExistsError(f"refusing to overwrite D4 evidence: {args.report_path}")
    rows = tuple(json.loads(line) for line in args.responses_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()) if args.responses_jsonl else ()
    training_ids = tuple(json.loads(args.training_source_ids_json.read_text(encoding="utf-8"))) if args.training_source_ids_json else ()
    report = evaluate_student_responses(rows, training_source_ids=training_ids)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    args.report_path.chmod(0o600)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
