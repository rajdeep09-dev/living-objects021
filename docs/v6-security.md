# BEAST v6 security and truthfulness boundaries

BEAST v6 intentionally narrows the execution model. Its goal is to measure small program-search mechanisms honestly, not to create unrestricted self-modifying software.

## Threat model

An input goal, an evolved AST, a checkpoint, a source export, or an API caller can be untrusted. The system therefore treats these artifacts as data and accepts only a constrained typed program representation. No component may convert an arbitrary goal description or source string into executable code in the main worker.

| Risk | v6 control | Verification evidence |
|---|---|---|
| Arbitrary source execution | The evaluator interprets registered AST nodes only; source strings are audit exports | `evolution/test_gp_engine.py` and `evolution/test_gp_safety.py` |
| Program bloat or recursion exhaustion | Tree depth, node, complexity, and evaluation limits are enforced before scoring | `evolution/program_validation.py` |
| Misleading self-improvement | Candidate changes require measured holdout comparison and a configured complexity budget | `evolution/safe_improvement.py` |
| Resume corruption | State uses JSON-safe, atomic checkpoint manifests and validates restore metadata | `evolution/gp_control.py` tests |
| Per-generation network dependency | The generation loop is local; APIs control lifecycle and read state only | Runtime and benchmark tests |
| Unbounded background cost | The controller requires finite generation budgets and worker/resource caps | v5/v6 controller tests |

## Explicit non-features

The release does not connect to live markets, place trades, make production changes, scrape private data, send outbound prompts for every generation, or execute arbitrary evolved source. It does not claim consciousness, general intelligence, or autonomous solution of a natural-language goal.

Any future integration with a production tool must use separate credentials, explicit user authorization, a review gate, bounded idempotent actions, and an audit trail. A genetic-programming score alone is not an authorization decision.

## Operational guidance

Run development tests with a non-production secret. Production deployments must provide a strong JWT secret and an external sandbox for any code path that evaluates untrusted artifacts. Long-lived work belongs on a persistent, quota-governed worker with a durable checkpoint volume, not on a serverless process that may stop while idle.

> A valid benchmark result means only that a constrained interpreter performed well on declared finite cases. Report the task, seed, train/holdout split, resource limits, and failures alongside every claimed result.
