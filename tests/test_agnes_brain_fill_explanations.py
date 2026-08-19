from __future__ import annotations

import json
from pathlib import Path

import pytest

from agnes_brain.training_data.fill_explanations import pending_records, review_handoff, write_handoff


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHAMPION_CORPUS = REPOSITORY_ROOT / "agnes_brain" / "training_data" / "explanations" / "from_champions.jsonl"


def test_explanation_handoff_preserves_incomplete_source_records_and_provenance() -> None:
    pending = pending_records(CHAMPION_CORPUS)
    handoff = review_handoff(pending)

    assert len(pending) == 16
    assert len(handoff) == len(pending)
    assert all(record["explanation"] == "FILL" for record in pending)
    assert all(row["status"] == "pending_human_review" for row in handoff)
    assert all(row["source"]["kind"] == "real_beast_run" for row in handoff)


def test_explanation_handoff_writes_new_local_checklist_without_mutating_source(tmp_path: Path) -> None:
    original = CHAMPION_CORPUS.read_text(encoding="utf-8")
    handoff_path = tmp_path / "manual_review_handoff.jsonl"

    assert write_handoff(handoff_path, source=CHAMPION_CORPUS) == handoff_path
    rows = [json.loads(line) for line in handoff_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 16
    assert CHAMPION_CORPUS.read_text(encoding="utf-8") == original
    assert handoff_path.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError, match="already exists"):
        write_handoff(handoff_path, source=CHAMPION_CORPUS)
