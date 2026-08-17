# BEAST v9 Operational and Submission Gates

This document separates code that is implemented and tested from work that requires an authorized external environment. It is a gate record, **not a deployment, live-run, or submission claim**.

## Long-run operating choices

| Option | Suitable for 5 × 100,000 generations? | Benefits | Constraints | Decision state |
|---|---|---|---|---|
| User-managed 4+ core, 8+ GB machine with durable disk | Yes, subject to a measured pilot | No hosting migration; full local control | Must remain powered, backed up, and observable for the campaign | Not selected |
| User-authorized cloud compute with 4+ cores, 8+ GB RAM, durable volume | Yes, subject to a measured pilot | Recoverable storage and an explicit operating window | Requires the user’s provider, budget, and access authorization | Not selected |
| Managed reserved web worker (1 vCPU, 512 MB) | No | Useful for a lightweight observatory gateway | Resource ceiling is unsuitable for the declared campaign; metered ceiling is up to about $37.50/month before the included $10 monthly credit, plus usage-based storage/egress | Explicitly rejected for the campaign |

The current development sandbox is not a campaign host because it can hibernate. The campaign must not be launched until the user selects one viable host, confirms data retention and compute budget, and a 10,000-generation pilot measures CPU, RAM, disk growth, checkpoint restore, and recovery time on that host.

## Required launch gate

Before execution, an operator must confirm all of the following:

1. The commit hash is recorded and the complete engine suite passes on the selected host.
2. A distinct persistent volume contains the report directory and exact checkpoints; restore is exercised from a copied checkpoint.
3. The v9 preregistration file is unchanged, and the launcher reports the declared five seeds before start.
4. The 10,000-generation pilot stays inside the measured resource envelope with a checkpoint/restart drill.
5. The operator has a recovery owner and a stop rule for infrastructure failure. A low fitness score is **not** a stop rule and remains a result.

## Public observatory gate

The authenticated observatory and its v9 evidence panel are implemented in the managed project and remain a development preview until a user authorizes publication. Public deployment additionally requires a secure execution design for visitor input, an independently tested sandbox worker, a real worker data source, health checks, rollback evidence, and a successful smoke test. The current panel does not claim a continuously running evolution worker or a public playground.

## arXiv submission gate

`docs/v9-paper.md` is a reviewable manuscript source, not an arXiv submission. Submission requires a human submitting author, account/category selection, author confirmation, final PDF source, and the author’s explicit authorization to submit. After any submission, the registry and README may link only to the actual identifier supplied by arXiv.
