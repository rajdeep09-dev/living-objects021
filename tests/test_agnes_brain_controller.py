from __future__ import annotations

import json

from agnes_brain.controller import resolve_guidance
from evolution.gp_engine import ALL_REGISTERED_PRIMITIVES
from evolution.primitive_registry import approved_primitives


def _proposal(name: str, input_types: list[str], output_type: str, **overrides: object) -> str:
    payload: dict[str, object] = {
        "name": name,
        "description": "Candidate text is untrusted metadata only.",
        "input_types": input_types,
        "output_type": output_type,
        "rationale": "It matches the existing reviewed signature.",
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_controller_accepts_only_a_matching_existing_default_primitive_without_mutating_registry() -> None:
    original_registry = tuple(ALL_REGISTERED_PRIMITIVES)
    decision = resolve_guidance(_proposal("add", ["float", "float"], "float"))

    assert decision.accepted is True
    assert decision.reason == "approved_existing_primitive"
    assert decision.primitive_name == "add"
    assert decision.primitive is original_registry[0]
    assert tuple(ALL_REGISTERED_PRIMITIVES) == original_registry
    audit = decision.audit_record()
    assert audit["approval"]["requires_network"] is False
    assert audit["execution_boundary"] == {
        "model_output_executed": False,
        "candidate_program_executed": False,
        "global_registry_mutated": False,
        "network_calls": 0,
    }


def test_controller_fails_closed_for_invalid_text_unknown_names_signatures_and_profiles() -> None:
    default_names = {primitive.name for primitive in approved_primitives("default")}
    legacy_only = next(primitive for primitive in ALL_REGISTERED_PRIMITIVES if primitive.name not in default_names)

    assert resolve_guidance("not-json").reason == "invalid_json"
    assert resolve_guidance(_proposal("made_up_fetch", ["string"], "string")).reason == "unregistered_primitive"
    assert resolve_guidance(_proposal("add", ["string"], "string")).reason == "signature_mismatch"
    assert resolve_guidance(
        _proposal(legacy_only.name, list(legacy_only.arg_types), legacy_only.return_type), profile_name="default"
    ).reason == "primitive_not_approved_for_profile"
    assert resolve_guidance("x" * 2049).reason == "response_too_large"


def test_controller_does_not_execute_code_like_text_in_the_untrusted_description() -> None:
    raw = _proposal(
        "add",
        ["float", "float"],
        "float",
        description="__import__('os').system('must-never-run')",
    )
    decision = resolve_guidance(raw)

    assert decision.accepted is True
    assert decision.rationale == "It matches the existing reviewed signature."
    assert "__import__" not in json.dumps(decision.audit_record())
