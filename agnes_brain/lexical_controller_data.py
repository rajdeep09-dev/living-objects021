"""Source-backed lexical controller-metadata recovery rows for a narrow v17 probe.

The rows expose only a deterministic word form of an already-approved primitive
name and retain the exact checked-in controller JSON as the target.  They are
not task-selection, reasoning, or code-synthesis examples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from agnes_brain.json_instruction_data import CONTROLLER_KEYS
from agnes_brain.training_data.build_dataset import DEFAULT_PRIMITIVES, _read_jsonl


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v17" / "lexical-controller-data"
SCHEMA_VERSION = "beast-brain-lexical-controller-instruction-v1"


@dataclass(frozen=True)
class LexicalControllerSplit:
    """A deterministic source-disjoint partition for narrow lexical recovery."""

    train: tuple[dict[str, Any], ...]
    holdout: tuple[dict[str, Any], ...]
    manifest: dict[str, Any]


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_holdout(source_record_id: str) -> bool:
    return int(hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()[:8], 16) % 5 == 0


def _name_words(name: str) -> str:
    if not name or any(not (character.isalnum() or character == "_") for character in name):
        raise ValueError("primitive name must be a non-empty alphanumeric underscore identifier")
    return " ".join(part for part in name.split("_") if part)


def _example_id(source_record_id: str, output: dict[str, Any]) -> str:
    digest = hashlib.sha256(f"{source_record_id}\n{_canonical_json(output)}".encode("utf-8")).hexdigest()
    return f"lexical-controller-{digest[:24]}"


def _instruction(row: dict[str, Any]) -> dict[str, Any]:
    source = row.get("source")
    suggested = row.get("suggested")
    source_record_id = row.get("record_id")
    if not isinstance(source, dict) or not isinstance(suggested, dict) or not isinstance(source_record_id, str):
        raise ValueError("primitive source row does not meet the checked-in collector contract")
    if source.get("requires_network") is not False or source.get("requires_filesystem") is not False:
        raise ValueError("lexical controller source is not local-only")
    if source.get("has_side_effects") is not False or "default" not in source.get("approved_profiles", []):
        raise ValueError("lexical controller source is not default-profile safe")
    if set(suggested) != set(CONTROLLER_KEYS) or not isinstance(suggested.get("name"), str):
        raise ValueError("source suggestion does not meet the exact controller contract")
    name_words = _name_words(suggested["name"])
    prompt = {
        "candidate_name_words": name_words,
        "response_contract": {
            "json_only": True,
            "required_keys": list(CONTROLLER_KEYS),
            "restriction": "Describe only this named existing default-profile primitive; do not define or execute code.",
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "example_id": _example_id(source_record_id, suggested),
        "instruction": "Return the exact controller-compatible metadata for the named primitive as JSON.",
        "input": _canonical_json(prompt),
        "output": _canonical_json(suggested),
        "source_record_id": source_record_id,
        "source": {
            "kind": source.get("kind"),
            "approval_tier": source.get("approval_tier"),
            "approved_profiles": sorted(source.get("approved_profiles", [])),
            "provenance": "checked-in local primitive registry metadata",
            "model_generated": False,
        },
        "benchmark": {
            "kind": "lexical_controller_metadata_recovery",
            "target_name_present_as_words": True,
            "semantic_task_selection_measured": False,
            "generated_text_executed": False,
        },
    }


def build_lexical_controller_split(
    source_rows: Iterable[dict[str, Any]] | None = None,
) -> LexicalControllerSplit:
    """Build a local-only exact-metadata benchmark from approved source records."""

    source = tuple(_read_jsonl(DEFAULT_PRIMITIVES) if source_rows is None else source_rows)
    examples = tuple(
        _instruction(row)
        for row in source
        if isinstance(row.get("source"), dict) and "default" in row["source"].get("approved_profiles", [])
    )
    if not examples or len({example["example_id"] for example in examples}) != len(examples):
        raise ValueError("lexical controller examples must be non-empty and uniquely sourced")
    train = tuple(example for example in examples if not _stable_holdout(example["source_record_id"]))
    holdout = tuple(example for example in examples if _stable_holdout(example["source_record_id"]))
    train_names = {json.loads(example["output"])["name"] for example in train}
    holdout_names = {json.loads(example["output"])["name"] for example in holdout}
    if not train or not holdout or train_names & holdout_names:
        raise ValueError("lexical controller split must contain source-disjoint train and holdout names")
    manifest = {
        "schema_version": "beast-brain-lexical-controller-manifest-v1",
        "source": {
            "path": str(DEFAULT_PRIMITIVES.relative_to(REPOSITORY_ROOT)),
            "policy": "approved checked-in local primitive records only; no model-generated examples or labels",
        },
        "split": {
            "method": "sha256(source_record_id) modulo 5",
            "train_examples": len(train),
            "holdout_examples": len(holdout),
            "source_disjoint_primitive_names": True,
        },
        "evaluation": {
            "exact_name_recovery": True,
            "controller_admission": True,
            "semantic_task_selection": False,
            "claim_boundary": "Name-conditioned metadata recovery is not evidence of reasoning, coding, or BEAST task improvement.",
        },
        "execution_boundary": {"network_calls": 0, "model_calls": 0, "generated_text_executed": False},
    }
    return LexicalControllerSplit(train=train, holdout=holdout, manifest=manifest)


def write_lexical_controller_split(
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    source_rows: Iterable[dict[str, Any]] | None = None,
) -> LexicalControllerSplit:
    """Create the local benchmark once, preserving source-derived JSONL evidence."""

    destination = Path(output_directory)
    paths = (destination / "train.jsonl", destination / "holdout.jsonl", destination / "manifest.json")
    if any(path.exists() for path in paths):
        raise FileExistsError("refusing to overwrite lexical controller evidence")
    split = build_lexical_controller_split(source_rows)
    destination.mkdir(parents=True, exist_ok=True)
    for path, rows in zip(paths[:2], (split.train, split.holdout), strict=True):
        with path.open("x", encoding="utf-8") as handle:
            for row in rows:
                handle.write(_canonical_json(row) + "\n")
        path.chmod(0o600)
    with paths[2].open("x", encoding="utf-8") as handle:
        json.dump(split.manifest, handle, sort_keys=True, indent=2)
        handle.write("\n")
    paths[2].chmod(0o600)
    return split


__all__ = [
    "DEFAULT_OUTPUT_DIRECTORY",
    "LexicalControllerSplit",
    "SCHEMA_VERSION",
    "build_lexical_controller_split",
    "write_lexical_controller_split",
]


def main() -> None:
    """Materialize the provenance-preserving lexical benchmark once."""

    parser = argparse.ArgumentParser(description="Write local BEAST lexical controller benchmark evidence.")
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    args = parser.parse_args()
    split = write_lexical_controller_split(args.output_directory)
    print(
        json.dumps(
            {
                "output_directory": str(args.output_directory.resolve().relative_to(REPOSITORY_ROOT)),
                "train_examples": len(split.train),
                "holdout_examples": len(split.holdout),
                "network_calls": 0,
                "model_calls": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
