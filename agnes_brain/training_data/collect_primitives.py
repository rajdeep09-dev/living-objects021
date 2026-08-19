"""Create source-labelled primitive suggestion examples from the local registry.

The collector imports declared primitive metadata only. It does not execute the
primitive functions, call a language model, or infer a fitness value.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evolution.gp_engine import ALL_REGISTERED_PRIMITIVES, LIST, STRING, Primitive
from evolution.primitive_registry import primitive_approval
from living_objects.beast_brain.collectors import write_jsonl_new


DEFAULT_DESTINATION = Path(__file__).resolve().parent / "primitives" / "from_codebase.jsonl"


def _task_family(primitive: Primitive) -> tuple[str, str]:
    """Return the intentionally simple, auditable description/rationale pair."""

    types = set(primitive.arg_types) | {primitive.return_type}
    signature = f"{primitive.name}({', '.join(primitive.arg_types)}) -> {primitive.return_type}"
    if STRING in types:
        return f"Pure bounded text operation: {signature}.", "useful for text extraction tasks"
    if LIST in types:
        return f"Pure list operation: {signature}.", "useful for list tasks"
    return f"Pure numeric or boolean operation: {signature}.", "useful for numeric computation"


def build_examples() -> tuple[dict[str, Any], ...]:
    """Return one non-executing instruction record for every registered primitive."""

    all_primitives = tuple(ALL_REGISTERED_PRIMITIVES)
    all_names = tuple(primitive.name for primitive in all_primitives)
    if len(set(all_names)) != len(all_names):
        raise ValueError("registered primitive names must be unique")
    examples: list[dict[str, Any]] = []
    for primitive in all_primitives:
        approval = primitive_approval(primitive.name)
        description, rationale = _task_family(primitive)
        record: dict[str, Any] = {
            "task": "general",
            "existing_primitives": [name for name in all_names if name != primitive.name],
            "suggested": {
                "name": primitive.name,
                "description": description,
                "input_types": list(primitive.arg_types),
                "output_type": primitive.return_type,
                "rationale": rationale,
            },
            "source": {
                "kind": "local_primitive_registry",
                "approval_tier": approval.tier,
                "approved_profiles": sorted(approval.approved_profiles),
                "has_side_effects": approval.has_side_effects,
                "requires_network": approval.requires_network,
                "requires_filesystem": approval.requires_filesystem,
            },
        }
        examples.append(record)
    return tuple(examples)


def collect(destination: str | Path = DEFAULT_DESTINATION) -> Path:
    """Write the complete local primitive corpus exactly once."""

    return write_jsonl_new(build_examples_with_ids(), destination)


def build_examples_with_ids() -> tuple[dict[str, Any], ...]:
    """Add content-derived IDs through the shared local collector contract."""

    from living_objects.beast_brain.collectors import _record_id

    records: list[dict[str, Any]] = []
    for example in build_examples():
        record = {"schema_version": "agnes-brain-primitive-example-v1", **example}
        record["record_id"] = _record_id(record)
        records.append(record)
    return tuple(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect local AGNES-BRAIN primitive examples.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    output = collect(args.output)
    print(f"Wrote {len(build_examples())} local primitive examples to {output}")


if __name__ == "__main__":
    main()
