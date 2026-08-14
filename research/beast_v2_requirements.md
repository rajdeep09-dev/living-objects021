# BEAST v2 Requirement Classification

## Implementation strategy

The v2 prompt contains three kinds of requirements. The first kind is directly testable in-process: mutable constitutions, deterministic code-module generation, red-team/defense behavior, intrinsic goal scoring, memome gossip, ancestry credit, a constrained DSL, and energy accounting. The second kind needs an explicit boundary around it: generated Python, shell execution, file access, HTTP access, and network gossip. The third kind is a research claim rather than an acceptance fact: outperforming every other system, universal token savings, biological consciousness, and benchmark superiority cannot be asserted without controlled, reproducible comparisons.

The implementation will provide deterministic research-mode contracts for all nine v2 phases. It will prefer safe representations such as structured strategies and a constrained DSL over arbitrary source execution. Where the prompt explicitly asks for generated Python, the system will generate, parse, compile-check, and execute only in a test-controlled path. Production deployment documentation will require an external sandbox boundary for untrusted code.

## Shared proof vocabulary

Every v2 component should expose serializable state, deterministic seeds, provenance, and measurable events. A strategy has an identifier, creator, parent strategy identifiers, generation, descriptor, code or DSL representation, fitness, energy cost, validation status, and adoption count. An organism has an identifier, species, parent identifiers, generation, genome, constitution, strategy references, goal parameters, energy budget, and defense state. A benchmark must return both the time-series result and the seed/configuration used to produce it.

## Safety boundaries

Generated code is untrusted data. AST validation, restricted globals, and exception handling are useful filters but are not a sufficient security boundary for a production Python sandbox. Any production tool execution must be isolated in a separate process/container/runtime with explicit CPU, memory, wall-clock, filesystem, network, and credential restrictions. The default test tools will be deterministic and allowlisted.

The red-team phase is implemented as adversarial simulation against in-memory copies and validated strategies. It must not become a general-purpose exploit framework. The embodiment phase exposes safe adapters with path allowlists, URL scheme/host policy, shell command allowlists, output limits, and timeouts. Human-controlled constitutional edits are versioned and applied only at generation boundaries.

## Acceptance policy

The code will prove the requested mechanisms with tests and benchmark output. It will not claim that a local deterministic simulation beats published state of the art without reproducing the relevant baselines under identical conditions. It will not claim that token savings are universal; it will measure the difference between discovery calls and verified strategy reuse for a specified workload.

## Compatibility findings

The canonical `Strategy` record includes immutable identity, source code, descriptor, effectiveness, author, generation, parent identifiers, usage counts, contribution counts, and creation time. The canonical `LamarckianOrganism` constructor requires the persisted runtime adapters and memome, so BEAST v2 uses a composable `BeastOrganism` runtime for standalone research contracts while preserving v1 inheritance APIs.
