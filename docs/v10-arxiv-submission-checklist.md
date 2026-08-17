# BEAST v10 arXiv Submission Package and Authorization Checklist

## Status: source bundle prepared; **not submitted**; no external submission attempted

The repository now contains a locally prepared LaTeX source bundle at [`v10-arxiv-submission-package/`](v10-arxiv-submission-package/). This is a **pre-submission deliverable**, not evidence of an arXiv record. No arXiv account was accessed, no upload occurred, no license was selected, no moderation decision exists, and no arXiv identifier has been issued.

> **Submission boundary:** The manuscript may not be described as submitted, accepted, peer reviewed, or indexed until an authorized author completes arXiv's browser workflow and the resulting public record is independently checked.

## What was prepared and locally verified

| Package component | Local state | Claim allowed now |
|---|---|---|
| `main.tex` | Includes title, abstract, complete manuscript, figure reference, and bibliography call. | A LaTeX manuscript source was prepared. |
| `references.bib` | Contains the three works cited by the manuscript. | The source has a complete local bibliography file. |
| `figure_manhattan_fitness_curves.png` | Byte-for-byte copy of the persisted v9 evidence figure. | The article includes the audited persisted-evidence figure. |
| `anc/reproducibility.md` | Maps frozen evidence revision, artifacts, commands, and limitations. | A reproduction appendix was prepared as ancillary material. |
| `living_objects/test_v10_arxiv_package.py` | Checks the source layout, required boundaries, references, and figure identity. | The package structure and core no-overclaim language were regression-tested. |
| `v10-arxiv-source.tar.gz` | To be built from this directory after final author metadata confirmation. | No upload archive is claimed before final metadata review. |

## Author-controlled gates still required

| Gate | Why it cannot be automated locally | Required action by the authorized author |
|---|---|---|
| Authorship and affiliation | arXiv prohibits anonymous submissions and authorship is a personal scholarly assertion. [1] | Replace the placeholder in `main.tex` with the confirmed author name(s), affiliation(s), and any ORCID information the author wishes to disclose. |
| Account, endorsement, and category | arXiv accepts submissions from registered authors and may require a new author or category to obtain endorsement. [2] | Sign in to the author-owned arXiv account, choose the appropriate primary category, and satisfy any account or endorsement prompt. |
| License and submittal agreement | The author, not this workspace, must grant the distribution license and agree to the applicable terms. [2] | Review the license choices and agreement in the arXiv workflow, then explicitly authorize submission. |
| Metadata review | Title, abstract, category, comments, and author order are scholarly metadata. | Confirm metadata exactly matches the author-approved manuscript. |
| Generated-PDF review | arXiv requires authors to inspect the system-generated PDF before completion. [3] | Upload the final source archive, inspect compilation notes and the generated PDF, correct any issue, and explicitly finish the submission. |

## arXiv-compatible packaging procedure

The prepared source uses 11-point type, one-inch margins, complete references, and no line numbers, watermarks, advertisements, or referee material; these are aligned with arXiv's stated format requirements. [1] The official workflow accepts TeX/PDFLaTeX source, detects the top-level TeX file, requests review of automatically detected notes, and requires inspection of the generated PDF. [2] TeX source should therefore be uploaded rather than a PDF generated from the same TeX source. [2]

Before author authorization, keep the directory in review form. Once the author metadata is final, create a clean archive that contains only `main.tex`, `references.bib`, `figure_manhattan_fitness_curves.png`, and `anc/reproducibility.md`. Ancillary materials are supported only with TeX/PDFLaTeX source and must live under an `anc` directory at the archive root. [4] Do not include build logs, auxiliary files, personal notes, the local PDF, repository metadata, or unrelated files.

```bash
cd docs/v10-arxiv-submission-package
rm -f main.aux main.bbl main.blg main.log main.out main.pdf
tar -czf ../v10-arxiv-source.tar.gz \
  main.tex references.bib figure_manhattan_fitness_curves.png anc/reproducibility.md
sha256sum ../v10-arxiv-source.tar.gz > ../v10-arxiv-source.tar.gz.sha256
```

The final archive must be rebuilt after author metadata changes; any checksum recorded before that change is superseded. A source upload does not become a submission until the account holder deliberately completes arXiv's workflow.

## Final handoff checklist

- [x] Source manuscript prepared from the reviewable v9 manuscript and preserved evidence.
- [x] Figure copied from the persisted evidence figure and included from the TeX root.
- [x] BibTeX database and ancillary reproduction appendix prepared.
- [x] No arXiv identifier or completion claim appears in the package.
- [ ] Author name(s), order, affiliation(s), and optional ORCID confirmed.
- [ ] Target category and any endorsement requirement confirmed in the author-owned account.
- [ ] Author has selected a license and accepted the applicable agreement.
- [ ] Final metadata, source compilation log, and arXiv-generated PDF reviewed by the author.
- [ ] Authorized author explicitly requests the final submit action.

## References

[1] [arXiv, “Policies for Format Requirements.”](https://info.arxiv.org/help/policies/format_requirements.html)

[2] [arXiv, “Submission Guidelines.”](https://info.arxiv.org/help/submit/index.html)

[3] [arXiv, “TeX Submissions.”](https://info.arxiv.org/help/submit_tex.html)

[4] [arXiv, “Ancillary Files (data, code, images).”](https://info.arxiv.org/help/ancillary_files.html)
