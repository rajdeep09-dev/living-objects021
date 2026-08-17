"""Regression checks for v9 public evidence boundaries.

These checks intentionally validate only concrete, evidence-linked wording. They
do not turn documentation into proof of an experimental result.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_v9_claims_registry_preserves_retractions_negative_result_and_gates() -> None:
    registry = _read("docs/v9-claims-registry.md")
    for required_text in (
        "**RETRACTED**",
        "**NEGATIVE_RESULT**",
        "**GATED**",
        "`sort1`",
        "0/5 eligible",
        "100,000-generation",
        "not a deployed federation",
    ):
        assert required_text in registry


def test_v9_paper_links_persisted_artifacts_and_figure_generator() -> None:
    paper = _read("docs/v9-paper.md")
    for artifact in (
        "reports/v8/manhattan-distance/summary.json",
        "reports/v8/clean-sorting/summary.json",
        "docs/v8-contamination-audit.json",
        "scripts/run_v8_multiseed.py",
        "scripts/build_v9_paper_figure.py",
    ):
        assert artifact in paper
    assert (ROOT / "docs/v9-manhattan-fitness-curves.png").is_file()


def test_readme_uses_evidence_first_sdk_and_deployment_boundaries() -> None:
    readme = _read("README.md")
    for required_text in (
        "**5/5 eligible fixed-seed runs**",
        "**0/5 eligible runs**",
        "**Retracted**",
        "living-objects audit manhattan-distance",
        "not a public deployment",
        "not submitted",
    ):
        assert required_text in readme


def test_v9_verification_record_reports_actual_count_and_visible_target_gap() -> None:
    verification = _read("docs/v9-test-verification.md")
    for required_text in (
        "**473 tests**",
        "**473 tests** in **97.58 seconds**",
        "527 below 1,000",
        "**unmet aspirational coverage target**",
        "473 passed, 12 warnings",
    ):
        assert required_text in verification


def test_v9_long_run_and_external_operation_materials_remain_explicitly_gated() -> None:
    preregistration = _read("docs/v9-clean-sorting-long-run-preregistration.md")
    operations = _read("docs/v9-operational-and-submission-gates.md")
    for required_text in (
        "**Not launched.**",
        "BEAST-V9-PREREG-20260817-A",
        "`bounded_execution_completed`",
        "No result is filtered",
    ):
        assert required_text in preregistration
    for required_text in (
        "Not selected",
        "not a deployment, live-run, or submission claim",
        "does not claim a continuously running evolution worker",
        "not an arXiv submission",
    ):
        assert required_text in operations
