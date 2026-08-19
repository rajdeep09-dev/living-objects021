"""D3 preflight only: validate local LoRA prerequisites without training or downloads."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def _completed_d2_manifest(path: Path, teacher_data_path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(payload.get("schema_version") == "beast-brain-d2-teacher-generation-manifest-v1" and payload.get("status") == "completed" and Path(str(payload.get("output_path", ""))).resolve() == teacher_data_path.resolve() and int(payload.get("counts", {}).get("retained_rows", 0)) > 0)


def lora_preflight(*, base_model_directory: str | Path, teacher_data_path: str | Path, adapter_output_directory: str | Path, corpus_manifest_path: str | Path | None = None) -> dict[str, Any]:
    """Return a deterministic readiness report; this function never trains or downloads."""

    base, data, output = Path(base_model_directory), Path(teacher_data_path), Path(adapter_output_directory)
    manifest = Path(corpus_manifest_path) if corpus_manifest_path is not None else None
    reasons: list[str] = []
    if not base.is_dir():
        reasons.append("base_model_directory_missing")
    elif not (base / "config.json").is_file():
        reasons.append("local_model_config_missing")
    if not data.is_file():
        reasons.append("teacher_data_missing")
    elif not data.read_text(encoding="utf-8").strip():
        reasons.append("teacher_data_empty")
    if manifest is None:
        reasons.append("corpus_manifest_missing")
    elif not manifest.is_file() or not _completed_d2_manifest(manifest, data):
        reasons.append("corpus_manifest_not_completed_or_mismatched")
    if output.exists():
        reasons.append("adapter_output_already_exists")
    for dependency in ("torch", "transformers", "peft", "trl"):
        if importlib.util.find_spec(dependency) is None:
            reasons.append(f"dependency_missing:{dependency}")
    return {
        "schema_version": "beast-brain-d3-lora-preflight-v1",
        "status": "ready_for_explicit_external_runner" if not reasons else "blocked",
        "reasons": reasons,
        "paths": {"base_model_directory": str(base), "teacher_data_path": str(data), "corpus_manifest_path": str(manifest) if manifest is not None else None, "adapter_output_directory": str(output)},
        "execution_boundary": {"model_downloaded": False, "training_started": False, "adapter_exported": False, "checkpoint_published": False},
        "claim_boundary": "A ready preflight is not a trained adapter, model improvement, or GGUF conversion result.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect D3 local LoRA prerequisites without performing training.")
    parser.add_argument("--base-model-directory", type=Path, required=True)
    parser.add_argument("--teacher-data-path", type=Path, required=True)
    parser.add_argument("--corpus-manifest-path", type=Path)
    parser.add_argument("--adapter-output-directory", type=Path, required=True)
    parser.add_argument("--report-path", type=Path)
    args = parser.parse_args()
    report = lora_preflight(base_model_directory=args.base_model_directory, teacher_data_path=args.teacher_data_path, corpus_manifest_path=args.corpus_manifest_path, adapter_output_directory=args.adapter_output_directory)
    if args.report_path is not None:
        if args.report_path.exists():
            raise FileExistsError(f"refusing to overwrite D3 evidence: {args.report_path}")
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        args.report_path.chmod(0o600)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
