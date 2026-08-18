"""Machine-check the v12 operational non-claims and prerequisite gates."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "docs" / "v12-operational-authorization-gate.md"


def test_operational_gate_preserves_all_external_activation_boundaries() -> None:
    text = GATE.read_text(encoding="utf-8")
    required = (
        "no network-enabled organisms",
        "no persistent worker",
        "No dataset is loaded, collected, or fabricated",
        "No organism network primitive exists",
        "No scheduler or unattended process is created",
        "The managed development preview is not public hosting",
        "No 100,000-generation campaign has started",
        "Human approval immediately before each action",
        "Secrets must be injected through the runtime secret mechanism",
    )
    for boundary in required:
        assert boundary in text


def test_operational_gate_requires_concrete_network_and_lead_prerequisites() -> None:
    text = GATE.read_text(encoding="utf-8")
    for prerequisite in (
        "per-domain allowlist",
        "request quotas",
        "response-size cap",
        "At least 500 lawfully sourced, anonymised, provenance-recorded records",
        "retention/deletion rule",
        "kill switch",
        "replay protection",
    ):
        assert prerequisite in text
