from __future__ import annotations

import json
from pathlib import Path

import pytest

from agnes_brain.training_data.collect_champions import build_examples, collect, normalize_artifact
from living_objects.beast_brain import ProvenanceError


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REPORTS_ROOT = REPOSITORY_ROOT / "reports"
V8_TRIAL = REPORTS_ROOT / "v8" / "manhattan-distance" / "seed_20260814" / "trial.json"


def test_champion_collector_preserves_v8_artifact_provenance_and_incomplete_explanation() -> None:
    record = normalize_artifact(V8_TRIAL)

    assert record is not None
    assert record["task"] == "manhattan-distance"
    assert record["fitness"]["value"] == 1.0
    assert record["source"]["kind"] == "real_beast_run"
    assert record["execution_boundary"]["network_calls"] == 0
    assert record["execution_boundary"]["llm_calls"] == 0
    assert record["explanation"] == "FILL"


def test_champion_collector_rejects_an_artifact_with_network_or_source_execution(tmp_path: Path) -> None:
    altered = tmp_path / "unsafe.json"
    payload = json.loads(V8_TRIAL.read_text(encoding="utf-8"))
    payload["execution_boundary"]["network_calls"] = 1
    altered.write_text(json.dumps(payload), encoding="utf-8")

    assert normalize_artifact(altered) is None


def test_champion_collector_builds_and_writes_only_unique_local_report_records(tmp_path: Path) -> None:
    records = build_examples(REPORTS_ROOT)
    output = tmp_path / "from_champions.jsonl"

    assert len(records) >= 10
    assert len({record["record_id"] for record in records}) == len(records)
    assert all(record["explanation"] == "FILL" for record in records)
    assert all(record["execution_boundary"]["generated_source_executed"] is False for record in records)
    assert collect(output, reports_root=REPORTS_ROOT) == output
    assert len(output.read_text(encoding="utf-8").splitlines()) == len(records)
    with pytest.raises(ProvenanceError, match="already exists"):
        collect(output, reports_root=REPORTS_ROOT)
