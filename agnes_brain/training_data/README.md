# AGNES-BRAIN Local Training Data

> **Status:** scaffold only. No model has been downloaded, trained, called, or registered. No web request, cloud request, credential, lead record, or persistent worker is used by this directory.

This directory keeps reviewable, local inputs for later bounded AGNES-BRAIN experiments. Every record must preserve its origin and must not treat a synthetic, template-derived, or teacher-generated text as a measured BEAST result.

| Directory | Intended contents | Mandatory provenance rule |
|---|---|---|
| `primitives/` | One declarative example for each approved interpreter primitive. | Include the declared primitive profile and approval metadata; do not copy or execute function bodies. |
| `test_cases/` | Deterministic input/output examples emitted by an approved local evaluator. | Include evaluator class, seed, and case indices; do not attach candidate fitness. |
| `explanations/` | Champion source-audit exports and manually reviewed explanations. | Preserve artifact path and digest for all score fields; an unfinished explanation remains visibly incomplete. |

The local collector scripts use only repository artifacts and the bounded evaluator interfaces. Future provider-assisted explanation filling, local-model installation, model downloads, fine-tuning, network primitives, lead data, and background jobs remain independently gated by the operational authorization policy.

The `fill_explanations.py` command is intentionally **not** a cloud client. It produces a new, owner-reviewable `manual_review_handoff.jsonl` for records whose explanation remains `FILL`; it neither reads credentials nor changes the source corpus. A future provider-assisted filling path requires explicit approval, provider/credential review, and a provenance policy that distinguishes teacher-generated text from measured BEAST evidence.

`build_dataset.py` creates `dataset.jsonl` and a paired `dataset.manifest.json`. The manifest reports primitive, evaluator-pattern, complete-explanation, and excluded-incomplete-explanation counts. Therefore the current local dataset is usable for bounded format and checkpoint experiments, but it must not be described as a complete explanation-supervision corpus.

`augment.py` does **not** alter that base dataset. It writes a separate `dataset.augmented.jsonl` with an augmentation manifest. Primitive task-name substitutions, including the hypothetical `lead_scraping` label, are explicitly marked `synthetic_template_variation` and are never a measured BEAST run or lead-data collection. The evaluator additions are fixed-seed, approved local case generations with zero candidate-program executions.
