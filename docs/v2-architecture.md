# BEAST v2 Architecture

BEAST v2 extends the Living Objects runtime from inheritable behaviors into an auditable **population-level research platform**. Each mechanism is deterministic when supplied a seed, serializable where possible, and exercised by `evolution/test_v2.py` plus the focused primitive tests. The platform distinguishes research-mode in-process execution from production trust boundaries: arbitrary generated code must run in an external sandbox before deployment.

## System map

```text
                         ┌────────────────────────────┐
                         │ Signal Loom observatory UI │
                         │ six v2 intervention panels│
                         └─────────────┬──────────────┘
                                       │ JWT / REST / WS
                         ┌─────────────▼──────────────┐
                         │ FastAPI v2 control plane   │
                         │ routes.py + websocket.py   │
                         └───────┬───────────┬────────┘
                                 │           │
                   ┌─────────────▼───┐   ┌──▼────────────────┐
                   │ V2Store SQLite   │   │ BeastOrganism     │
                   │ durable memome   │   │ runtime composite │
                   └─────────────┬───┘   └──┬────────────────┘
                                 │          │
        ┌────────────────────────▼──────────▼──────────────────────┐
        │ constitution · morphogenome · red-team · goal synthesis  │
        │ federated memome · embodied tools · ancestry · DSL       │
        │ thermodynamic energy and selection                       │
        └───────────────────────────────────────────────────────────┘
```

## Phase contracts

| Phase | Public module | Runtime contract | Proof surface |
|---|---|---|---|
| 1. Evolving constitutions | `evolution/constitution.py` | `EvolutionConstitution` mutates heritable selection, adoption, novelty, overlap, and distribution fields; `to_code()` renders an auditable scorer. | 100-generation divergence from identical initial state under different seeds. |
| 2. Morphogenetic growth | `evolution/morphogenome.py` | `Morphogenome.grow_module()` emits syntax-checked Python; `graft()` combines template catalogs. Parent module names can be imported by child modules. | Four-generation cumulative code growth and importability checks. |
| 3. Red-team defense | `evolution/red_team.py` | `DefenseLayer` parses, fingerprints, and rejects unsafe strategies. `RedTeamOrganism.attack()` records adaptive attack pressure. | Malformed code is repulsed and immune strength increases. |
| 4. Goal synthesis | `evolution/goal_synthesis.py` | `GoalSynthesizer` scores surprise, leverage, and coverage from observed `EnvironmentState` values. Goal parameters are inherited by `evolve_goal()`. | Intrinsic goal is discovered without a supplied task reward. |
| 5. Federated memome | `evolution/federated_memome.py` | Nodes exchange missing strategies through fitness-weighted gossip and expose influence plus a lineage graph. | Three nodes converge on a strategy after gossip rounds; DOT output is available. |
| 6. Embodied tools | `evolution/embodied.py` | An allowlisted class registry exposes restricted Python, file, HTTP, and shell tools. Calls are recorded as fitness-bearing history. | Registered tools execute; unsafe paths/commands are rejected. |
| 7. Ancestry credit | `evolution/ancestry_credit.py` | Strategy credit combines descendant use count, generational span, and effectiveness, excluding strategies learned directly by the champion. | Credited strategies are inherited ancestor knowledge. |
| 8. Emergent DSL | `evolution/dsl.py` | `DSLGenome` evolves vocabulary, grammar markers, and semantic mappings; expressions parse back into intent dictionaries. | Five-token starting language grows compound tokens and round-trips. |
| 9. Thermodynamic fitness | `evolution/thermodynamic.py` | Quality is divided by operation cost; `EnergyBudget` makes calls, queries, and mutations finite resources. | Operations decrease, efficiency rises, and exhaustion is observable. |
| 10. Observatory | `web/client/src/pages/Home.tsx` | Operators inspect organisms, browse strategies, edit constitution YAML, launch attacks, inspect ancestry, and run DSL translations. | Browser build and responsive screenshot pass; controls have local simulation behavior. |

## Runtime composition

`BeastOrganism` is the v2 runtime aggregate. It owns an `EvolutionConstitution`, `Morphogenome`, `DefenseLayer`, `GoalSynthesizer`, learned module map, parent identifiers, and attack history. It intentionally keeps the primitive APIs small so an experiment can compose only the phases it needs.

`V2ControlState` is the API process boundary. It holds the current constitution, live organisms, DSL genome, energy budgets, recent typed events, and a `V2Store`. The state is process-local for the live control plane, while strategy records and lineage are durable in SQLite. A multi-replica deployment must move the control state and WebSocket fan-out into a shared service before claiming strong cross-replica consistency.

## Persistence and lineage

`production/store_v2.py` stores strategy identity, source, descriptor, effectiveness, author, generation, parent IDs, and timestamps. Strategy identity is a stable hash of name, descriptor, and source. Publishing an existing strategy is idempotent; a higher-effectiveness version wins during merge. The lineage query returns parent-to-child edges for both UI and research export.

The federated in-process implementation maintains a registry only to measure influence in experiments. It is not a network transport. Production gossip should be implemented as authenticated, signed record exchange over a dedicated service or queue, with replay protection, rate limits, schema validation, and an external code sandbox.

## Events and operator intervention

The v2 WebSocket uses four typed event models: `organism_born`, `strategy_adopted`, `constitution_mutated`, and `red_team_attack`. REST mutations append the same event payloads to a bounded event buffer. The browser can poll the event endpoint today and connect to `/ws/v2/evolution?token=<jwt>` for streaming integration.

Constitution edits are applied to the current control state immediately at the API boundary. A production generation coordinator should stage the patch and commit it at a generation barrier; the UI labels the editor as live YAML while the engine remains responsible for safe boundary application.

## Safety boundary

AST validation and restricted builtins are useful research checks, not a secure sandbox. Python can reach dangerous capabilities through implementation details, dependency behavior, resource exhaustion, or future code changes. Production execution therefore requires a separate sandbox process or microVM with no ambient credentials, bounded CPU/memory/time, restricted filesystem and network, signed strategy artifacts, and human approval for external side effects.

## Verification workflow

```bash
python3 -m pytest -q evolution/test_beast_v2.py evolution/test_v2.py production/test_v2_api.py
python3 scripts/run_v2_benchmarks.py --output docs/benchmark-results.md
```

The first command is the fast v2 proof gate. The second regenerates the benchmark report without editing source code. The repository's broader suite remains the regression gate before a release commit.
