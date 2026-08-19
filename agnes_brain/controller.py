"""Bounded controller adapter between untrusted guidance text and BEAST primitives.

The adapter can *select* an existing registered primitive only after exact schema,
signature, and v12 profile checks. It cannot define a primitive, change global
registries, run generated text, run candidate code, make a request, or start a
worker. The local byte-bigram smoke model is expected to fail this JSON contract
most of the time; rejection is an intended safe outcome.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from evolution.gp_engine import ALL_REGISTERED_PRIMITIVES, Primitive
from evolution.primitive_registry import PrimitiveApprovalError, primitive_approval, require_approved_primitives


MAX_GUIDANCE_BYTES = 2048
MAX_TEXT_FIELD_LENGTH = 280
_PRIMITIVES_BY_NAME = {primitive.name: primitive for primitive in ALL_REGISTERED_PRIMITIVES}


@dataclass(frozen=True)
class GuidanceDecision:
    """A reviewable result for one untrusted guidance response."""

    accepted: bool
    reason: str
    profile_name: str
    raw_sha256: str
    raw_bytes: int
    primitive_name: str | None = None
    primitive: Primitive | None = None
    rationale: str | None = None

    def audit_record(self) -> dict[str, Any]:
        """Return non-executable audit metadata without retaining untrusted raw text."""

        return {
            "schema_version": "beast-brain-guidance-decision-v1",
            "accepted": self.accepted,
            "reason": self.reason,
            "profile_name": self.profile_name,
            "raw_sha256": self.raw_sha256,
            "raw_bytes": self.raw_bytes,
            "primitive_name": self.primitive_name,
            "approval": (
                {
                    "tier": primitive_approval(self.primitive_name).tier,
                    "approved_profiles": sorted(primitive_approval(self.primitive_name).approved_profiles),
                    "requires_network": primitive_approval(self.primitive_name).requires_network,
                    "requires_filesystem": primitive_approval(self.primitive_name).requires_filesystem,
                }
                if self.accepted and self.primitive_name is not None
                else None
            ),
            "execution_boundary": {
                "model_output_executed": False,
                "candidate_program_executed": False,
                "global_registry_mutated": False,
                "network_calls": 0,
            },
        }


def _digest(raw: str) -> tuple[str, int]:
    payload = raw.encode("utf-8", errors="strict")
    return hashlib.sha256(payload).hexdigest(), len(payload)


def resolve_guidance(raw: str, *, profile_name: str = "default") -> GuidanceDecision:
    """Validate a proposed existing primitive without executing any response text.

    Valid JSON must contain exactly the model-contract keys ``name``,
    ``description``, ``input_types``, ``output_type``, and ``rationale``. The
    description is checked only for type/length. Signature and approval facts are
    read exclusively from the already registered primitive metadata.
    """

    if not isinstance(raw, str):
        raise TypeError("guidance response must be text")
    raw_sha256, raw_bytes = _digest(raw)
    if raw_bytes > MAX_GUIDANCE_BYTES:
        return GuidanceDecision(False, "response_too_large", profile_name, raw_sha256, raw_bytes)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return GuidanceDecision(False, "invalid_json", profile_name, raw_sha256, raw_bytes)
    if not isinstance(payload, dict):
        return GuidanceDecision(False, "response_not_object", profile_name, raw_sha256, raw_bytes)
    required = {"name", "description", "input_types", "output_type", "rationale"}
    if set(payload) != required:
        return GuidanceDecision(False, "invalid_schema_keys", profile_name, raw_sha256, raw_bytes)
    name = payload["name"]
    description = payload["description"]
    input_types = payload["input_types"]
    output_type = payload["output_type"]
    rationale = payload["rationale"]
    if not isinstance(name, str) or not isinstance(description, str) or not isinstance(rationale, str):
        return GuidanceDecision(False, "invalid_text_fields", profile_name, raw_sha256, raw_bytes)
    if len(description) > MAX_TEXT_FIELD_LENGTH or len(rationale) > MAX_TEXT_FIELD_LENGTH:
        return GuidanceDecision(False, "text_field_too_large", profile_name, raw_sha256, raw_bytes)
    if not isinstance(input_types, list) or not all(isinstance(item, str) for item in input_types) or not isinstance(output_type, str):
        return GuidanceDecision(False, "invalid_signature_fields", profile_name, raw_sha256, raw_bytes)
    primitive = _PRIMITIVES_BY_NAME.get(name)
    if primitive is None:
        return GuidanceDecision(False, "unregistered_primitive", profile_name, raw_sha256, raw_bytes, primitive_name=name)
    if tuple(input_types) != primitive.arg_types or output_type != primitive.return_type:
        return GuidanceDecision(False, "signature_mismatch", profile_name, raw_sha256, raw_bytes, primitive_name=name)
    try:
        require_approved_primitives((primitive,), profile_name=profile_name)
    except PrimitiveApprovalError:
        return GuidanceDecision(False, "primitive_not_approved_for_profile", profile_name, raw_sha256, raw_bytes, primitive_name=name)
    approval = primitive_approval(name)
    if approval.has_side_effects or approval.requires_network or approval.requires_filesystem:
        return GuidanceDecision(False, "side_effecting_primitive_rejected", profile_name, raw_sha256, raw_bytes, primitive_name=name)
    return GuidanceDecision(
        True,
        "approved_existing_primitive",
        profile_name,
        raw_sha256,
        raw_bytes,
        primitive_name=name,
        primitive=primitive,
        rationale=rationale,
    )


__all__ = ["GuidanceDecision", "MAX_GUIDANCE_BYTES", "resolve_guidance"]
