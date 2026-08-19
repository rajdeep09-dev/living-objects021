"""Regression coverage for D1–D6 guarded local-distillation components."""

from __future__ import annotations

import json
from dataclasses import replace

from agnes_brain.d1_teacher_baseline import run_d1_teacher_baseline
from agnes_brain.d3_lora_guard import lora_preflight
from agnes_brain.d4_student_evaluator import evaluate_student_responses
from agnes_brain.d5_gguf_handoff import gguf_handoff_preflight
from agnes_brain.ollama_client import OllamaAvailability, OllamaResponse
from agnes_brain.ollama_controller_benchmark import ControllerBenchmarkCase
from agnes_brain.teacher_data import collect_teacher_data
from agnes_brain.distill.generate_from_teacher import DEFAULT_BASE_RECORDS, generate_from_teacher
from living_objects.ollama_explanations import request_local_explanation
from living_objects.sdk import evolve


class FakeClient:
    def __init__(self, text: str, *, available: bool = True) -> None:
        self.text, self.available, self.calls = text, available, 0

    def availability(self, model: str) -> OllamaAvailability:
        return OllamaAvailability(self.available, "available" if self.available else "model_unavailable", model, (model,) if self.available else ())

    def generate_raw(self, **_: object) -> OllamaResponse:
        self.calls += 1
        return OllamaResponse(True, "ok", "test", self.text, "a" * 64, len(self.text), 12, 0.01)

    def generate_json_schema(self, **_: object) -> OllamaResponse:
        return self.generate_raw()


def _case() -> ControllerBenchmarkCase:
    return ControllerBenchmarkCase("case", "source", "add", '{"x":1}')


def _accepted() -> str:
    return json.dumps({"name": "add", "description": "sum", "input_types": ["float", "float"], "output_type": "float", "rationale": "registered"})


def test_d1_records_raw_json_and_snake_case_without_persisting_text(tmp_path):
    report_path = tmp_path / "teacher-baseline-test.txt"
    artifact = run_d1_teacher_baseline(output_directory=tmp_path, text_report_path=report_path, client=FakeClient('{"name":"example_primitive","inputs":["float"],"output":"float"}'))
    assert artifact["metrics"] == {"valid_json": True, "name_present": True, "snake_case_name": True}
    assert "example_primitive" not in (tmp_path / "run.json").read_text(encoding="utf-8")
    assert report_path.read_text(encoding="utf-8").endswith("VALID: example_primitive\n")


def test_d2_retains_only_exact_controller_admitted_rows(tmp_path):
    artifact = collect_teacher_data(output_directory=tmp_path, client=FakeClient(_accepted()), cases=(_case(),))
    assert artifact["counts"]["retained_rows"] == 1
    row = json.loads((tmp_path / "teacher_data.jsonl").read_text(encoding="utf-8"))
    assert row["source"]["kind"] == "teacher_generated"


def test_specified_d2_generator_defaults_to_no_model_calls_and_no_invented_task(tmp_path):
    manifest = generate_from_teacher(base_records_path=DEFAULT_BASE_RECORDS, output_path=tmp_path / "teacher_generated.jsonl", manifest_path=tmp_path / "manifest.json", client=FakeClient("not used"))
    assert manifest["status"] == "dry_run"
    assert manifest["counts"]["source_records"] > 0
    assert manifest["counts"]["requested_variations"] == manifest["counts"]["source_records"] * 5
    assert not (tmp_path / "teacher_generated.jsonl").exists()


def test_d3_and_d5_preflights_fail_closed_for_missing_inputs(tmp_path):
    assert lora_preflight(base_model_directory=tmp_path / "missing", teacher_data_path=tmp_path / "missing.jsonl", adapter_output_directory=tmp_path / "adapter")["status"] == "blocked"
    assert gguf_handoff_preflight(adapter_directory=tmp_path / "adapter", converter_path=tmp_path / "convert.py", validation_artifact=tmp_path / "validation.json")["status"] == "blocked"


def test_d5_rejects_an_evaluation_artifact_without_full_task_correctness(tmp_path):
    adapter, converter, evaluation = tmp_path / "adapter", tmp_path / "convert.py", tmp_path / "evaluation.json"
    adapter.mkdir()
    converter.write_text("# not executed", encoding="utf-8")
    evaluation.write_text(json.dumps({"metrics": {"cases": 10, "exact_name_and_controller_admitted": 0}}), encoding="utf-8")
    report = gguf_handoff_preflight(adapter_directory=adapter, converter_path=converter, validation_artifact=evaluation, user_confirmed_release=True)
    assert "task_correct_evaluation_not_passed" in report["reasons"]


def test_d4_uses_exact_name_and_controller_rubric():
    report = evaluate_student_responses(({"source_record_id": "source", "response": _accepted()},), cases=(_case(),))
    assert report["metrics"]["exact_name_and_controller_admitted"] == 1


def test_d4_empty_submission_is_not_counted_as_valid_json():
    report = evaluate_student_responses((), cases=(_case(),))
    assert report["metrics"]["submitted"] == 0
    assert report["metrics"]["raw_json_valid"] == 0


def test_d4_rejects_a_declared_training_source_overlap():
    try:
        evaluate_student_responses((), cases=(_case(),), training_source_ids=("source",))
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("source overlap must fail closed")


def test_d6_blocks_before_local_call_when_v18_gate_is_not_task_correct(tmp_path):
    evidence = {"benchmark": {"cases": 10, "decoding": {"mode": "raw", "format_parameter_used": False}}, "metrics": {"exact_name_and_controller_admitted": 0}}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    client = FakeClient("not used")
    result = request_local_explanation("why", evidence_path=path, model="local", allow_local_explanation=True, client=client)
    assert result.reason == "task_correctness_gate_failed"
    assert client.calls == 0


def test_d6_optional_sdk_hook_leaves_gp_result_without_explanation_when_gate_fails(tmp_path):
    evidence = {"benchmark": {"cases": 10, "decoding": {"mode": "raw", "format_parameter_used": False}}, "metrics": {"exact_name_and_controller_admitted": 0}}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    result = evolve("manhattan", generations=1, seed=9, population_size=8, artifact_dir=tmp_path, enable_local_explanation=True, explanation_evidence_path=path, explanation_model="local", explanation_client=FakeClient("not used"))
    assert "brain_explanation" not in result.champion
    assert result.execution_boundary["llm_calls"] == 0
