"""D5 preflight for an explicit, user-confirmed GGUF handoff; it never converts files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _evaluation_passes(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    metrics = payload.get("metrics")
    return bool(isinstance(metrics, dict) and isinstance(metrics.get("cases"), int) and metrics["cases"] > 0 and metrics.get("exact_name_and_controller_admitted") == metrics["cases"])


def gguf_handoff_preflight(*, adapter_directory: str | Path, converter_path: str | Path, validation_artifact: str | Path, user_confirmed_release: bool = False) -> dict[str, Any]:
    """Check required handoff artifacts without conversion, upload, or release creation."""

    adapter, converter, validation = Path(adapter_directory), Path(converter_path), Path(validation_artifact)
    reasons = [label for label, path, predicate in (
        ("trained_adapter_missing", adapter, Path.is_dir),
        ("converter_missing", converter, Path.is_file),
        ("validation_artifact_missing", validation, Path.is_file),
    ) if not predicate(path)]
    if validation.is_file() and not _evaluation_passes(validation):
        reasons.append("task_correct_evaluation_not_passed")
    if not user_confirmed_release:
        reasons.append("explicit_release_confirmation_missing")
    return {"schema_version": "beast-brain-d5-gguf-handoff-v1", "status": "ready_for_explicit_external_conversion" if not reasons else "blocked", "reasons": reasons, "paths": {"adapter_directory": str(adapter), "converter_path": str(converter), "validation_artifact": str(validation)}, "execution_boundary": {"conversion_started": False, "gguf_created": False, "binary_published": False, "network_calls": 0}, "claim_boundary": "A preflight cannot establish GGUF compatibility, adapter quality, or a release until all inputs and an independently recorded validation exist."}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect D5 GGUF handoff prerequisites without converting or publishing binaries.")
    parser.add_argument("--adapter-directory", type=Path, required=True)
    parser.add_argument("--converter-path", type=Path, required=True)
    parser.add_argument("--validation-artifact", type=Path, required=True)
    parser.add_argument("--confirm-release", action="store_true")
    parser.add_argument("--report-path", type=Path)
    args = parser.parse_args()
    report = gguf_handoff_preflight(adapter_directory=args.adapter_directory, converter_path=args.converter_path, validation_artifact=args.validation_artifact, user_confirmed_release=args.confirm_release)
    if args.report_path is not None:
        if args.report_path.exists():
            raise FileExistsError(f"refusing to overwrite D5 evidence: {args.report_path}")
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        args.report_path.chmod(0o600)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
