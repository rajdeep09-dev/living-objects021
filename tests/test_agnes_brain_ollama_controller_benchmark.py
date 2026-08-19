from __future__ import annotations

import json

from agnes_brain.controller import resolve_guidance
from agnes_brain.ollama_client import OllamaAvailability, OllamaResponse
from agnes_brain.ollama_controller_benchmark import _response_validity, build_controller_cases, evaluate_raw_controller_baseline


class _StubClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.prompts: list[str] = []

    def availability(self, model: str) -> OllamaAvailability:
        return OllamaAvailability(True, "available", model, (model,))

    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse:
        self.prompts.append(prompt)
        raw = self.response_text.encode("utf-8")
        return OllamaResponse(True, "ok", model, self.response_text, "a" * 64, len(raw), len(prompt.encode("utf-8")), 0.01)

    def generate_json_schema(self, *, model: str, prompt: str, json_schema: dict, system: str | None = None, temperature: float = 0.0) -> OllamaResponse:
        assert json_schema["type"] == "object"
        return self.generate_raw(model=model, prompt=prompt, system=system, temperature=temperature)


def test_controller_cases_are_source_disjoint_and_hide_expected_name_from_prompt() -> None:
    cases = build_controller_cases()

    assert len(cases) == 10
    assert len({case.source_record_id for case in cases}) == 10
    assert all(case.expected_name not in case.prompt for case in cases)


def test_raw_json_validity_is_recorded_separately_from_the_controller_contract() -> None:
    raw_json_valid, required_valid, payload = _response_validity("{}")

    assert raw_json_valid is True
    assert required_valid is False
    assert payload == {}


def test_baseline_persists_digests_and_never_executes_stub_output(tmp_path) -> None:
    first_case = build_controller_cases(limit=1)[0]
    prompt_payload = json.loads(first_case.prompt)
    target = {
        "name": first_case.expected_name,
        "description": prompt_payload["approved_metadata"]["description"],
        "input_types": prompt_payload["approved_metadata"]["input_types"],
        "output_type": prompt_payload["approved_metadata"]["output_type"],
        "rationale": "metadata-matched existing primitive",
    }
    assert resolve_guidance(json.dumps(target)).accepted is True
    client = _StubClient(json.dumps(target))

    artifact = evaluate_raw_controller_baseline(output_directory=tmp_path, model="stub", client=client, limit=1)

    assert artifact["status"] == "completed"
    assert artifact["metrics"] == {
        "raw_json_valid": 1,
        "required_contract_valid": 1,
        "exact_name": 1,
        "controller_admitted": 1,
        "exact_name_and_controller_admitted": 1,
    }
    assert artifact["records"][0]["response"]["persisted_raw_text"] is False
    assert artifact["execution_boundary"]["generated_text_executed"] is False
    assert (tmp_path / "run.json").exists()


def test_json_schema_diagnostic_is_labelled_separately_from_raw_decoding(tmp_path) -> None:
    client = _StubClient("{}")

    artifact = evaluate_raw_controller_baseline(
        output_directory=tmp_path,
        model="stub",
        client=client,
        limit=1,
        decoder_mode="ollama_json_schema",
    )

    assert artifact["benchmark"]["decoding"]["mode"] == "ollama_json_schema"
    assert artifact["benchmark"]["decoding"]["format_parameter_used"] is True
    assert artifact["metrics"]["raw_json_valid"] == 1
    assert artifact["metrics"]["required_contract_valid"] == 0
    assert artifact["metrics"]["exact_name_and_controller_admitted"] == 0
