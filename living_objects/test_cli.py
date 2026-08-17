from __future__ import annotations

import io
import json

from living_objects.cli import main


def _invoke(argv: list[str]) -> tuple[int, dict[str, object], str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(argv, stdout=stdout, stderr=stderr)
    payload = json.loads(stdout.getvalue()) if stdout.getvalue() else {}
    return code, payload, stderr.getvalue()


def test_cli_runs_reproduces_and_exports_a_bounded_interpreter_only_artifact(tmp_path) -> None:
    base = ["--artifact-dir", str(tmp_path)]
    code, run, error = _invoke(base + ["evolve", "manhattan-distance", "--generations", "2", "--seed", "703", "--population-size", "4"])

    assert code == 0, error
    assert run["execution_boundary"]["generated_source_executed"] is False
    run_id = str(run["run_id"])
    reproduction_code, reproduction, error = _invoke(base + ["reproduce", run_id])
    assert reproduction_code == 0, error
    assert reproduction["verified"] is True
    export_code, source, error = _invoke(base + ["export", run_id, "python"])
    assert export_code == 0, error
    assert "source-only" in str(source["execution_boundary"])


def test_cli_exposes_persisted_audit_and_real_discovery_records() -> None:
    code, audit, error = _invoke(["audit", "clean-sorting"])
    assert code == 0, error
    assert audit["status"] == "NEGATIVE_RESULT"
    code, discoveries, error = _invoke(["discoveries"])
    assert code == 0, error
    assert len(discoveries["records"]) == 5


def test_cli_publishes_and_imports_signed_local_evidence_without_network_transport(tmp_path, monkeypatch) -> None:
    envelope_path = tmp_path / "record.json"
    monkeypatch.setenv("PUBLISHER_KEY", "publisher-test-key-for-cli-000000")
    monkeypatch.setenv("RECEIVER_KEY", "receiver-test-key-for-cli-0000000")
    code, publication, error = _invoke([
        "publish-discovery", "BEAST-V8-MANHATTAN-20260814", "--node-id", "peer-publisher", "--key-env", "PUBLISHER_KEY", "--output", str(envelope_path),
    ])
    assert code == 0, error
    assert publication["transport"] == "not implemented by this local exchange MVP"
    code, admission, error = _invoke([
        "import-discovery", "--input", str(envelope_path), "--node-id", "peer-receiver", "--key-env", "RECEIVER_KEY", "--trusted-issuer", "peer-publisher", "--trusted-key-env", "PUBLISHER_KEY",
    ])
    assert code == 0, error
    assert admission["admission"]["accepted"] is True


def test_cli_reports_missing_signing_key_without_fabricating_an_envelope(tmp_path) -> None:
    code, _, error = _invoke([
        "publish-discovery", "BEAST-V8-MANHATTAN-20260814", "--node-id", "peer-publisher", "--key-env", "MISSING_KEY", "--output", str(tmp_path / "record.json"),
    ])
    assert code == 2
    assert "MISSING_KEY" in error
