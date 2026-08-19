from __future__ import annotations

import json
from pathlib import Path

import pytest

from evolution.evaluator_safety import EvaluatorNotApprovedError
from evolution.fitness import GameStrategyEvaluator, ManhattanDistanceEvaluator
from evolution.primitive_registry import approved_primitives
from living_objects.beast_brain import (
    ProvenanceError,
    collect_champion_card,
    collect_evaluator_case_cards,
    collect_primitive_cards,
    write_jsonl_new,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REAL_ARTIFACT = REPOSITORY_ROOT / "reports" / "v11" / "artifacts" / "BEAST-SDK-V1-5312CD4D9BDDC82C.json"


def test_collect_primitive_cards_exports_only_the_declared_default_profile() -> None:
    cards = collect_primitive_cards()

    assert len(cards) == len(approved_primitives("default"))
    assert {card["name"] for card in cards} == {primitive.name for primitive in approved_primitives("default")}
    assert all(card["source"]["profile"] == "default" for card in cards)
    assert all(len(card["record_id"]) == 64 for card in cards)


def test_collect_evaluator_cases_is_deterministic_and_does_not_score_programs() -> None:
    evaluator = ManhattanDistanceEvaluator()

    first = collect_evaluator_case_cards(evaluator, seed=14, case_count=4)
    second = collect_evaluator_case_cards(evaluator, seed=14, case_count=4)

    assert first == second
    assert len(first) == 4
    assert all("fitness" not in card for card in first)
    assert all(card["source"]["evaluator"] == "ManhattanDistanceEvaluator" for card in first)


def test_collect_evaluator_cases_respects_the_existing_disabled_evaluator_gate() -> None:
    with pytest.raises(EvaluatorNotApprovedError):
        collect_evaluator_case_cards(GameStrategyEvaluator.__new__(GameStrategyEvaluator), seed=1, case_count=1)


def test_collect_champion_card_preserves_local_provenance_and_measured_scores() -> None:
    card = collect_champion_card(REAL_ARTIFACT)

    assert card["source"]["kind"] == "real_beast_run"
    assert card["measured_scores"]["training_fitness"]["value"] == 1.0
    assert card["measured_scores"]["fresh_correctness"]["value"] == 1.0
    assert card["execution_boundary"]["network_calls"] == 0
    assert card["execution_boundary"]["llm_calls"] == 0


def test_collect_champion_card_rejects_nonlocal_execution_evidence(tmp_path: Path) -> None:
    altered = tmp_path / "nonlocal.json"
    payload = json.loads(REAL_ARTIFACT.read_text(encoding="utf-8"))
    payload["result"]["execution_boundary"]["network_calls"] = 1
    altered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ProvenanceError, match="zero network"):
        collect_champion_card(altered)


def test_write_jsonl_new_rejects_tampering_duplicates_and_overwrite(tmp_path: Path) -> None:
    card = collect_champion_card(REAL_ARTIFACT)
    destination = tmp_path / "dataset" / "champions.jsonl"
    written = write_jsonl_new([card], destination)

    assert written == destination
    assert json.loads(destination.read_text(encoding="utf-8"))["record_id"] == card["record_id"]
    assert destination.stat().st_mode & 0o077 == 0
    with pytest.raises(ProvenanceError, match="already exists"):
        write_jsonl_new([card], destination)
    with pytest.raises(ProvenanceError, match="duplicate"):
        write_jsonl_new([card, card], tmp_path / "duplicates.jsonl")


def test_write_jsonl_new_rejects_a_record_with_changed_content() -> None:
    changed = collect_champion_card(REAL_ARTIFACT)
    changed["task"] = "fabricated-task"

    with pytest.raises(ProvenanceError, match="does not match"):
        write_jsonl_new([changed], REPOSITORY_ROOT / "reports" / "v13" / "should-not-exist.jsonl")
