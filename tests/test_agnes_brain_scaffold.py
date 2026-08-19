from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_agnes_brain_training_data_scaffold_is_present_and_locally_scoped() -> None:
    root = REPOSITORY_ROOT / "agnes_brain"
    training_data = root / "training_data"

    assert (root / "__init__.py").is_file()
    assert training_data.is_dir()
    assert (training_data / "primitives").is_dir()
    assert (training_data / "test_cases").is_dir()
    assert (training_data / "explanations").is_dir()
    readme = (training_data / "README.md").read_text(encoding="utf-8")
    assert "No model has been downloaded" in readme
    assert "Mandatory provenance rule" in readme
