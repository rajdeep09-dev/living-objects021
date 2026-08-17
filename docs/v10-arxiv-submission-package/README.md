# BEAST v10 arXiv source bundle

## Status

This directory is a **locally prepared submission source bundle**. It is **not submitted**, has **no arXiv identifier**, and is **not peer reviewed**. The author and affiliation fields in `main.tex` are placeholders deliberately retained until the owner explicitly confirms authorship and submission metadata.

The manuscript preserves the narrow v8 evidence claim: five declared bounded Manhattan-distance trials achieved the recorded fresh-evaluator outcomes, while historical contaminated benchmark claims are retracted and the clean-sorting result remains a negative 0/5 outcome. It does not claim a PyPI release, public Observatory URL, continuous worker, 100,000-generation campaign, or general autonomous software engineering result.

## Package layout

| Path | Purpose |
|---|---|
| `main.tex` | Top-level single-spaced 11-point LaTeX manuscript with one-inch margins. |
| `references.bib` | BibTeX reference database required by `main.tex`. |
| `figure_manhattan_fitness_curves.png` | Persisted-evidence figure included by the manuscript. |
| `anc/reproducibility.md` | Ancillary reproduction map and exact historical commands. |
| `../v10-arxiv-submission-checklist.md` | Submission-status record and human account/metadata gates. |

The package uses only standard `article`, `geometry`, `fontenc`, `inputenc`, `graphicx`, `booktabs`, `hyperref`, and `url` packages. No submission has been uploaded or queued from this workspace.

## Local build command

With a standard TeX Live installation that includes BibTeX, compile from this directory:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The expected article PDF is a local review artifact; do not add a PDF generated from these TeX files to the arXiv source upload. arXiv requests source for TeX/PDFLaTeX papers and generates the public PDF itself. See the official guidance cited in the checklist.
