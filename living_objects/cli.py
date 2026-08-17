"""Command-line interface for the bounded, artifact-backed public SDK."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence, TextIO

from evolution.v9_federation import SignedDiscoveryExchange, available_discoveries
from living_objects.sdk import audit, evolve, export, reproduce


def _json(value: Any, stream: TextIO) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=lambda item: item.__dict__), file=stream)


def _key_from_environment(name: str) -> bytes:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"required signing key environment variable is missing: {name}")
    encoded = value.encode("utf-8")
    if len(encoded) < 16:
        raise ValueError(f"signing key in {name} must contain at least 16 bytes")
    return encoded


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="living-objects",
        description="Bounded, interpreter-only BEAST v9 research workflows.",
    )
    parser.add_argument("--artifact-dir", default=".living-objects/runs", help="directory for bounded run JSON artifacts")
    commands = parser.add_subparsers(dest="command", required=True)

    evolve_command = commands.add_parser("evolve", help="run a bounded typed-AST evolution task")
    evolve_command.add_argument("task", choices=("manhattan-distance", "clean-sorting"))
    evolve_command.add_argument("--generations", type=int, required=True)
    evolve_command.add_argument("--seed", type=int, required=True)
    evolve_command.add_argument("--population-size", type=int)

    audit_command = commands.add_parser("audit", help="show persisted contamination classification")
    audit_command.add_argument("task")

    reproduce_command = commands.add_parser("reproduce", help="rerun and compare a bounded run artifact")
    reproduce_command.add_argument("run_id")

    export_command = commands.add_parser("export", help="emit source-only audit text for a bounded run")
    export_command.add_argument("run_id")
    export_command.add_argument("target", choices=("python", "javascript", "rust", "go"))

    commands.add_parser("discoveries", help="list locally verified discovery records eligible for exchange")

    publish_command = commands.add_parser("publish-discovery", help="create a signed envelope for locally verified evidence")
    publish_command.add_argument("record_id")
    publish_command.add_argument("--node-id", required=True)
    publish_command.add_argument("--key-env", default="LIVING_OBJECTS_FEDERATION_KEY")
    publish_command.add_argument("--output", required=True)

    import_command = commands.add_parser("import-discovery", help="verify a signed envelope against local evidence before admission")
    import_command.add_argument("--input", required=True)
    import_command.add_argument("--node-id", required=True)
    import_command.add_argument("--key-env", default="LIVING_OBJECTS_FEDERATION_KEY")
    import_command.add_argument("--trusted-issuer", required=True)
    import_command.add_argument("--trusted-key-env", required=True)
    return parser


def _artifact_result(run_id: str, artifact_dir: str | Path) -> dict[str, Any]:
    path = Path(artifact_dir) / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("result", {}).get("run_id") != run_id:
        raise ValueError("run artifact does not contain the requested run identifier")
    return dict(payload["result"])


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "evolve":
            result = evolve(
                args.task,
                generations=args.generations,
                seed=args.seed,
                population_size=args.population_size,
                artifact_dir=args.artifact_dir,
            )
            _json(result.to_dict() | {"artifact_path": result.artifact_path}, out)
            return 0
        if args.command == "audit":
            _json(audit(args.task).__dict__, out)
            return 0
        if args.command == "reproduce":
            _json(reproduce(args.run_id, artifact_dir=args.artifact_dir).__dict__, out)
            return 0
        if args.command == "export":
            _json(export(_artifact_result(args.run_id, args.artifact_dir), args.target).__dict__, out)
            return 0
        if args.command == "discoveries":
            _json({"records": available_discoveries()}, out)
            return 0
        if args.command == "publish-discovery":
            exchange = SignedDiscoveryExchange(args.node_id, _key_from_environment(args.key_env))
            envelope = exchange.publish(args.record_id)
            Path(args.output).write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _json({"written": str(args.output), "record_id": args.record_id, "transport": "not implemented by this local exchange MVP"}, out)
            return 0
        if args.command == "import-discovery":
            envelope = json.loads(Path(args.input).read_text(encoding="utf-8"))
            exchange = SignedDiscoveryExchange(
                args.node_id,
                _key_from_environment(args.key_env),
                trusted_peers={args.trusted_issuer: _key_from_environment(args.trusted_key_env)},
            )
            admission = exchange.import_envelope(envelope)
            _json({"admission": admission.__dict__, "summary": exchange.evidence_summary()}, out)
            return 0 if admission.accepted else 2
        raise ValueError(f"unsupported command: {args.command}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"living-objects: {exc}", file=err)
        return 2


if __name__ == "__main__":  # pragma: no cover - exercised through the console entry point
    raise SystemExit(main())
