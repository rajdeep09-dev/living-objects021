from __future__ import annotations

import json

from scripts.build_v9_observatory_evidence import OUTPUT, SCHEMA, build_payload, write


def test_v9_observatory_artifact_is_derived_from_contracts_and_keeps_v8_boundaries(tmp_path) -> None:
    written = write(tmp_path / "v9-observatory-evidence.json")
    payload = json.loads(written.read_text(encoding="utf-8"))

    assert payload == build_payload()
    assert payload["schema"] == SCHEMA
    assert payload["curriculum"]["profile"] == "clean-sorting-v9-five-stage"
    assert len(payload["curriculum"]["stages"]) == 5
    assert payload["federation"]["verified_record_count"] == 5
    assert payload["federation"]["network_transport"] == "not implemented by this local exchange MVP"
    assert payload["service"]["persistent_worker_configured"] is False
    assert payload["measured_results"]["clean_sorting"]["status"] == "NEGATIVE_RESULT"
    assert len(payload["measured_results"]["manhattan"]["eligible_records"]) == 5


def test_committed_v9_observatory_artifact_matches_the_deterministic_compiler() -> None:
    assert json.loads(OUTPUT.read_text(encoding="utf-8")) == build_payload()
