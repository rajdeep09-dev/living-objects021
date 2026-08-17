"""Contract tests for the locally prepared, explicitly unsubmitted v10 arXiv source bundle."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs" / "v10-arxiv-submission-package"


def test_v10_arxiv_package_has_only_required_submission_inputs() -> None:
    required = {
        "main.tex",
        "references.bib",
        "figure_manhattan_fitness_curves.png",
        "anc/reproducibility.md",
        "README.md",
    }
    assert required <= {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }


def test_v10_arxiv_source_declares_portable_submission_geometry_and_inputs() -> None:
    source = (PACKAGE / "main.tex").read_text(encoding="utf-8")
    assert "\\documentclass[11pt]{article}" in source
    assert "\\usepackage[margin=1in]{geometry}" in source
    assert "\\includegraphics[width=\\linewidth]{figure_manhattan_fitness_curves.png}" in source
    assert "\\bibliography{references}" in source
    assert "\\date{}" in source


def test_v10_arxiv_source_preserves_narrow_claims_and_retractions() -> None:
    source = (PACKAGE / "main.tex").read_text(encoding="utf-8")
    for required_boundary in (
        "do not establish general intelligence",
        "not evidence of sorting discovery",
        "0/5 eligible successes",
        "not yet been run as the planned five-seed 100,000-generation study",
        "not evidence of a public always-on service",
    ):
        assert required_boundary in source


def test_v10_arxiv_figure_is_exact_copy_of_persisted_evidence_figure() -> None:
    source_figure = ROOT / "docs" / "v9-manhattan-fitness-curves.png"
    packaged_figure = PACKAGE / "figure_manhattan_fitness_curves.png"
    assert hashlib.sha256(source_figure.read_bytes()).digest() == hashlib.sha256(
        packaged_figure.read_bytes()
    ).digest()


def test_v10_arxiv_checklist_is_explicitly_unsubmitted_and_author_gated() -> None:
    checklist = (ROOT / "docs" / "v10-arxiv-submission-checklist.md").read_text(
        encoding="utf-8"
    )
    for required_statement in (
        "**not submitted**",
        "no arXiv identifier",
        "no upload occurred",
        "Author name(s), order, affiliation(s), and optional ORCID confirmed",
        "Authorized author explicitly requests the final submit action",
    ):
        assert required_statement in checklist
