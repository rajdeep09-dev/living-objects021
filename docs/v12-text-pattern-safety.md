# BEAST v12 Text and Pattern Capability Boundary

> **Status:** Locally implemented and regression-tested on 2026-08-18. These are bounded transformations of caller-supplied text; they do not collect leads, access the network, infer identities, or send messages.

The v12 interpreter now exposes **40 Tier 2 pure string operations**: the nine existing operations plus the 31 named extraction, validation, normalisation, pattern, and domain transforms specified in the v12 guide. Every one is present in `evolution/primitive_registry.py` with Tier 2 metadata, no network or filesystem access, no side effects, and a `main-process-pure` execution designation. Inputs and outputs of the new transforms are capped at 16,384 characters; padding is capped at 4,096 characters.

## Fixed-pattern boundary

The pattern helpers in `evolution/approved_patterns.py` operate on a **name from a 14-entry fixed registry**, not a caller-provided regular expression. They cap text at 16,384 characters and result lists at 256 matches. The helpers detect formats only. A detected IBAN, payment-card-shaped token, or SSN-shaped token is neither validated nor retained by this module.

| Capability | Local status | Boundary |
|---|---|---|
| Tier 2 text transforms | Implemented | Pure local transformation only. |
| Named fixed-pattern detection | Implemented | No arbitrary regular expressions or network access. |
| Lead Record Evaluator | Not implemented | The guide requires 500 real anonymised records. No lawful, consented, provenance-documented dataset has been supplied. |
| Email inference or outreach | Not implemented | This requires a separate privacy, consent, source, and human-approval workflow. |
| Network/HTML retrieval | Not implemented | No network primitive sandbox or allowlisted transport exists. |

The Phase 2 tests are deterministic **unit fixtures for primitive semantics only**. They are not a lead dataset, benchmark result, or evidence of real-world extraction performance.
