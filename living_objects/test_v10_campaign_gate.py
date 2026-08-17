from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = (ROOT / "docs" / "v10-campaign-launch-gate.md").read_text(encoding="utf-8")
PREREGISTRATION = (ROOT / "docs" / "v9-clean-sorting-long-run-preregistration.md").read_text(encoding="utf-8")


def test_v10_campaign_gate_preserves_the_unlaunched_preregistration_boundary():
    assert "**not launched**" in GATE.lower()
    assert "BEAST-V9-PREREG-20260817-A" in GATE
    assert "100,000" in GATE
    assert "0/5 eligible successes" in GATE
    assert "bounded_execution_completed" in GATE
    assert "eligible_for_declared_campaign_analysis" in GATE
    assert "does not select one" in GATE
    assert "not a campaign host" in GATE
    assert "not an instruction that has been executed" in GATE
    assert "**Not launched.**" in PREREGISTRATION


def test_v10_campaign_gate_requires_authorization_pilot_restore_and_artifact_milestones():
    for required_phrase in (
        "Required owner authorization record",
        "Mandatory 10,000-generation pilot",
        "Restore drill",
        "checkpoint.json",
        "fitness_history.json",
        "milestone_10000.json",
        "Full-campaign authorization and milestones",
        "zero LLM calls",
        "zero network calls",
    ):
        assert required_phrase in GATE
