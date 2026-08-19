from __future__ import annotations

from pathlib import Path

import pytest

from agnes_brain.measure_clean_sorting import PREREGISTRATION, run_negative_control


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CPU_SMOKE_ARTIFACT = REPOSITORY_ROOT / "reports" / "v13" / "beast-brain-cpu-smoke-20260819" / "experiment.json"


def test_preregistered_negative_control_rejects_invalid_guidance_and_requires_identical_arms(tmp_path: Path) -> None:
    artifact = run_negative_control(
        tmp_path / "negative-control",
        cpu_smoke_artifact=CPU_SMOKE_ARTIFACT,
        raw_guidance="not-json",
    )

    assert artifact["preregistration"] == PREREGISTRATION
    assert artifact["guidance_decision"]["accepted"] is False
    assert artifact["guidance_decision"]["reason"] == "invalid_json"
    assert artifact["guidance_effect"] == "no_op_rejected_guidance"
    assert artifact["baseline"] == artifact["guidance_arm"]
    assert artifact["result_interpretation"]["outcome"] == "neutral_negative_control"
    assert artifact["execution_boundary"]["network_calls"] == 0
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        run_negative_control(tmp_path / "negative-control", cpu_smoke_artifact=CPU_SMOKE_ARTIFACT, raw_guidance="not-json")
