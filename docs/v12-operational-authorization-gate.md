# BEAST v12 Operational Authorization Gate

> **Current state:** BEAST v12 has no network-enabled organisms, no persistent worker, no user data store, no public service, no outbound action primitive, and no multi-agent production deployment. This document is a release gate, not an implementation claim.

## Phase-to-gate matrix

| v12 phase | Required before implementation or activation | Current status |
|---|---|---|
| Tier 3 patterns | A subprocess integration with a measured wall-time and memory limit, fixed-pattern-only API, and adversarial timeout regressions | **Not implemented.** Local named pattern helpers are deliberately not represented as sandboxed organism primitives. |
| Lead Record Evaluator | At least 500 lawfully sourced, anonymised, provenance-recorded records; a written purpose; retention/deletion rule; contamination split; and owner confirmation | **Blocked.** No dataset is loaded, collected, or fabricated. |
| HTML/network operations | Owner-approved per-domain allowlist, HTTPS-only transport, service authentication, request quotas, response-size cap, timeout, retry/backoff, audit log, and a test server | **Not implemented.** No organism network primitive exists. |
| Persistent agent loop | Explicit owner authorization, configured runtime, bounded task queue, durable checkpointing, kill switch, cost budget, telemetry, and incident runbook | **Blocked.** No scheduler or unattended process is created. |
| External side effects | Human approval immediately before each action, least-privilege credential, idempotency key, immutable audit event, and a rollback/incident path | **Not implemented.** No messaging, CRM, email, account, or browser-writing capability is present. |
| Federation or multi-agent network | Service identities, rotated signing keys in secrets management, replay protection, peer allowlist, rate limit, provenance schema, and revocation test | **Blocked.** The existing signed local exchange does not constitute a live federation. |
| Public API/dashboard | Published URL, authentication on every mutation, rate limiting, threat model, observability, privacy review, and independent endpoint verification | **Not deployed.** The managed development preview is not public hosting. |
| Multi-day campaign | The v10 campaign gate plus authorized persistent compute, staged pilot result, checkpoint restore test, resource alerting, and explicit launch confirmation | **Blocked.** No 100,000-generation campaign has started. |

## Approved data and privacy boundary

No v12 code may ingest, scrape, infer, enrich, retain, or export real lead data until the owner supplies an explicitly authorized dataset or source specification with a stated purpose and legal basis. The implementation must use only the fields necessary for the approved purpose, retain provenance and timestamps, support deletion, prevent use for outreach without a separate action approval, and exclude sensitive or special-category data unless a documented lawful basis and safeguards are reviewed.

Synthetic unit fixtures are allowed only to prove deterministic primitive semantics. They must not be described as market research, lead quality, contact verification, deliverability, or business-development results.

## Network and credential boundary

Organism code has no `http_get`, `http_post`, socket, browser, shell, filesystem-write, environment-read, subprocess, or arbitrary-import primitive. Introducing any equivalent capability requires a new primitive approval entry that identifies its execution environment, maximum inputs/outputs, timeout, memory quota, hostname policy, credential handle, audit event, and test coverage.

Secrets must be injected through the runtime secret mechanism, never committed to source, artifacts, fixtures, documentation, checkpoints, or browser code. A new connector or third-party service cannot be assumed available; it must be separately configured and verified before use.

## Persistence and hosting decision

The sandbox used for local verification can hibernate and cannot be treated as a durable worker. If an always-on bounded worker becomes necessary, first evaluate managed Reserved hosting after an explicit owner decision; it provides one persistent process but has a 1 vCPU / 512 MB ceiling. A user-owned machine is the zero-cost alternative when it can remain online. A persistent VM is justified only when an identified OS-level or resource requirement cannot fit the managed option; that choice requires a separate infrastructure decision and cost review.

## Release assertion

The presence of this gate does **not** authorize any listed capability. A future release may change a row from `Blocked` or `Not implemented` only after all prerequisites in that row have been completed, regression-tested, and independently recorded in the corresponding evidence artifact.
