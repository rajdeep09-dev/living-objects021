# BEAST v7 Foundation Security Review

## Scope and method

This review covers the code changed for the v7 foundation release: candidate-only repair search, typed-GP bloat/seed/checkpoint changes, capability-bounded cellular evolution, the real GP event broadcaster, polyglot audit validation, the bounded marathon runner, and the observatory artifact contract. It is a repository-level engineering review, not an external penetration test or a production deployment certification.

The review was checked against the executable regressions listed in the table below and the final engine suite (`435 passed`). The observatory suite passes with the protected evidence contract and component rendering regression included.

## Findings and disposition

| Surface | Review finding | Implemented control and evidence | Disposition |
|---|---|---|---|
| Candidate-only repair | A repair component could become a path to arbitrary repository writes or command execution. | `CandidateOnlyBugFixer` emits source proposals only and routes checks through `IsolatedSandbox`; its survivor metric runs assertion fragments in isolation. `evolution/test_bug_fixer.py` proves proposal behavior, not source application. | **Controlled within the tested boundary.** |
| GP tree growth | Unbounded trees could cause resource exhaustion during prolonged runs. | A deterministic post-reproduction sweep hoists oversized roots to a type-compatible subtree at or below 64 nodes. The 100-generation regression asserts the bound for every organism. | **Closed for the stated 64-node population contract.** |
| Evaluator contamination | A caller or a static evaluator seed could make program scores untrustworthy. | Training uses one deterministic seed per generation; `VerifiedProgramMarket` owns its fixed holdout seed and offers no score parameter. Seed/market regressions prove the contract. | **Closed for current evaluator APIs.** |
| Cellular actions | A mutable action field could become arbitrary callable or code execution. | Genomes contain only a validated subset of a finite enum-backed universe. World and tissue execution reject absent capabilities. | **Closed for the current allowlisted universe.** |
| Live WebSocket stream | Synthetic telemetry, unbounded queues, or unauthenticated WebSocket access would mislead observers or enable resource abuse. | The broadcaster advances an actual `GPPopulation`, retains at most 500 event records, and gives each client a bounded queue of 50. The active WebSocket endpoint continues to require its token boundary. `production/test_v6_api.py` receives ten real messages with real champion source. | **Controlled for the single-process bounded broadcaster; not a multi-instance public gateway.** |
| Champion source | Rendering or exporting source could accidentally execute evolved programs in the API/UI path. | GP selection remains typed-AST interpreter execution. Python/JS exports are audit artifacts; the Node test executes only a deterministic test export subprocess for equivalence validation, not API-supplied champion source. | **Controlled in the release scope.** |
| Checkpoint integrity | A resumed run might silently reset to random state or deserialize invalid primitive references. | Checkpoints serialize full trees by primitive name and resume tests continue 100 generations beyond a saved generation 100 population. | **Controlled for trusted local checkpoint files.** |
| Artifact-backed observatory | A dashboard might show transcribed or synthetic claims. | The v7 panel imports committed `run_result.json` and `v7_live_gp_stream.json`. The component explicitly displays the false 100k-marathon flag; authenticated-slot and artifact-contract tests execute it. | **Controlled for the read-only artifact view.** |

## Open deployment risks

The following are not vulnerabilities fixed by a source-only v7 foundation release; they are operational prerequisites that block a broader production claim.

| Risk | Why it remains open | Required mitigation before public launch |
|---|---|---|
| Persistent execution | The default development sandbox can hibernate, so it cannot substantiate a 24/7 worker or 100,000-generation public-marathon claim. | Use a measured persistent worker target, durable checkpoints, a restart drill, and an observed run manifest. |
| Multi-instance fan-out | The current event registry is intentionally in-process and does not coordinate across replicas. | Separate worker and WebSocket gateway processes; use a durable checkpoint store and Redis or equivalent pub/sub only for ephemeral fan-out. |
| Playground execution | The public Champion Playground described by the guide is not implemented. | Use isolated worker processes/containers with no network egress, strict CPU/memory limits, rate limiting, and explicit request schemas. |
| Public archive/federation | No public write path, signature registry, or immutable external timestamp service has been launched. | Threat-model identity, signature rotation, archive append-only controls, local re-evaluation, abuse reporting, and key revocation. |
| Production secrets | Development defaults and test environment variables are not production credentials. | Supply a strong secret through deployment secret management; disable all example credentials and verify startup refusal on missing configuration. |

## Release decision

**Foundation release decision: approved for a bounded local/repository evidence release.** The release is not approved to claim persistent public operation, multi-replica streaming, one-million-user capacity, a public playground, or completion of the 100,000-generation marathon. Those claims require the separate measured gates in [`v7-operational-roadmap.md`](v7-operational-roadmap.md).
