"""Central primitive approval metadata for bounded GP profiles.

The registry records what is executable today. It does not itself create an OS
sandbox, grant network access, or certify a primitive as contamination-free for
a particular evaluator; those remain separate contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from evolution.gp_engine import (
    ALL_REGISTERED_PRIMITIVES,
    ARITHMETIC_PRIMITIVES,
    BOOLEAN_PRIMITIVES,
    DEFAULT_PRIMITIVES,
    Primitive,
)


class PrimitiveApprovalError(ValueError):
    """Raised when a population requests primitives outside its declared profile."""


@dataclass(frozen=True)
class PrimitiveProfile:
    name: str
    allowed_names: frozenset[str]
    purpose: str


@dataclass(frozen=True)
class PrimitiveApproval:
    """Reviewable safety metadata for one interpreter primitive."""

    name: str
    input_types: tuple[str, ...]
    output_type: str
    tier: int
    has_side_effects: bool
    requires_network: bool
    requires_filesystem: bool
    execution_environment: str
    approved_on: str
    approved_profiles: frozenset[str]


_REGISTERED_BY_NAME = {primitive.name: primitive for primitive in ALL_REGISTERED_PRIMITIVES}
_TIER_ONE_NAMES = frozenset(primitive.name for primitive in ARITHMETIC_PRIMITIVES + BOOLEAN_PRIMITIVES)
_DEFAULT_NAMES = frozenset(primitive.name for primitive in DEFAULT_PRIMITIVES)

PRIMITIVE_PROFILES: dict[str, PrimitiveProfile] = {
    "default": PrimitiveProfile(
        name="default",
        allowed_names=_DEFAULT_NAMES,
        purpose="New generic runs using the clean, bounded default grammar.",
    ),
    "legacy-artifact": PrimitiveProfile(
        name="legacy-artifact",
        allowed_names=frozenset(_REGISTERED_BY_NAME),
        purpose="Explicit compatibility profile for historic serialized artifacts and convenience tests.",
    ),
    "task-specific": PrimitiveProfile(
        name="task-specific",
        allowed_names=frozenset(_REGISTERED_BY_NAME),
        purpose="Explicit reviewed task grammar; semantic contamination review remains evaluator-specific.",
    ),
}


def _approval_for(primitive: Primitive) -> PrimitiveApproval:
    default_enabled = primitive.name in _DEFAULT_NAMES
    return PrimitiveApproval(
        name=primitive.name,
        input_types=primitive.arg_types,
        output_type=primitive.return_type,
        tier=1 if primitive.name in _TIER_ONE_NAMES else 2,
        has_side_effects=False,
        requires_network=False,
        requires_filesystem=False,
        execution_environment="main-process-pure",
        approved_on="2026-08-18",
        approved_profiles=frozenset(
            {"default", "legacy-artifact", "task-specific"}
            if default_enabled else {"legacy-artifact", "task-specific"}
        ),
    )


PRIMITIVE_APPROVALS: dict[str, PrimitiveApproval] = {
    primitive.name: _approval_for(primitive) for primitive in ALL_REGISTERED_PRIMITIVES
}


def primitive_approval(name: str) -> PrimitiveApproval:
    try:
        return PRIMITIVE_APPROVALS[name]
    except KeyError as exc:
        raise PrimitiveApprovalError(f"unregistered primitive is not approved: {name}") from exc


def approved_primitives(profile_name: str = "default") -> tuple[Primitive, ...]:
    """Return the registered primitives admitted by a declared profile."""
    try:
        profile = PRIMITIVE_PROFILES[profile_name]
    except KeyError as exc:
        raise PrimitiveApprovalError(f"unknown primitive profile: {profile_name}") from exc
    return tuple(primitive for primitive in ALL_REGISTERED_PRIMITIVES if primitive.name in profile.allowed_names)


def require_approved_primitives(primitives: Iterable[Primitive], profile_name: str = "default") -> tuple[Primitive, ...]:
    """Validate a primitive tuple against explicit approval metadata and profile."""
    requested = tuple(primitives)
    try:
        profile = PRIMITIVE_PROFILES[profile_name]
    except KeyError as exc:
        raise PrimitiveApprovalError(f"unknown primitive profile: {profile_name}") from exc
    unknown = [primitive.name for primitive in requested if primitive.name not in PRIMITIVE_APPROVALS]
    forbidden = [primitive.name for primitive in requested if primitive.name not in profile.allowed_names]
    profile_mismatch = [
        primitive.name for primitive in requested
        if primitive.name in PRIMITIVE_APPROVALS
        and profile_name not in PRIMITIVE_APPROVALS[primitive.name].approved_profiles
    ]
    duplicates = sorted({primitive.name for primitive in requested if sum(item.name == primitive.name for item in requested) > 1})
    if unknown:
        raise PrimitiveApprovalError(f"unregistered primitives are not approved: {', '.join(sorted(set(unknown)))}")
    if forbidden or profile_mismatch:
        names = sorted(set(forbidden + profile_mismatch))
        raise PrimitiveApprovalError(f"primitive profile '{profile_name}' does not approve: {', '.join(names)}")
    if duplicates:
        raise PrimitiveApprovalError(f"primitive profile contains duplicate names: {', '.join(duplicates)}")
    return requested


__all__ = [
    "PrimitiveApproval",
    "PrimitiveApprovalError",
    "PrimitiveProfile",
    "PRIMITIVE_APPROVALS",
    "PRIMITIVE_PROFILES",
    "approved_primitives",
    "primitive_approval",
    "require_approved_primitives",
]
