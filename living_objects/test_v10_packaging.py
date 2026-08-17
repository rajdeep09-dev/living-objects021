"""Metadata regressions for the v10 dependency-free public SDK distribution."""
from __future__ import annotations

import tomllib
from pathlib import Path

from living_objects.sdk import SDK_VERSION


ROOT = Path(__file__).resolve().parents[1]


def _metadata() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_v10_distribution_version_matches_public_sdk() -> None:
    metadata = _metadata()
    assert metadata["name"] == "living-objects"
    assert metadata["version"] == SDK_VERSION == "0.3.0"
    assert metadata["requires-python"] == ">=3.10"


def test_v10_public_sdk_has_no_deployment_hard_dependencies() -> None:
    metadata = _metadata()
    assert metadata["dependencies"] == []


def test_v10_production_extra_contains_deployment_dependencies() -> None:
    metadata = _metadata()
    extras = metadata["optional-dependencies"]
    production = extras["production"]
    assert any(item.startswith("fastapi") for item in production)
    assert any(item.startswith("pydantic") for item in production)
    assert any(item.startswith("redis") for item in production)
    assert any(item.startswith("prometheus-client") for item in production)


def test_v10_package_release_record_preserves_pypi_gate() -> None:
    record = (ROOT / "docs" / "v10-package-release.md").read_text(encoding="utf-8")
    assert "not published to PyPI" in record
    assert "explicitly confirms the irreversible upload" in record
    assert "3.10.20" in record and "3.11.15" in record and "3.12.3" in record
