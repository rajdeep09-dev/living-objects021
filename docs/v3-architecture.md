# BEAST v3 Architecture

BEAST v3 extends the v2 evolution engine with a guarded frontier layer. The system remains a research platform: the new modules make explicit, testable computations around self-improvement, culture, trade, uncertainty, neural-style strategies, archaeology, diplomacy, benchmark generation, and awareness proxies.

## Runtime layers

1. **Core evolution.** v1/v2 organisms, constitutions, morphogenomes, memomes, DSL genomes, thermodynamic scoring, typed events, and durable strategy storage remain the base vocabulary.
2. **Safety plane.** `IsolatedSandbox`, `ResourceLimits`, the sandbox worker, route authorization, CORS validation, rate limiting, and validated store identifiers protect the control plane.
3. **Frontier modules.** `recursive_improvement.py`, `market.py`, `quantum_genome.py`, `spiking.py`, `archaeology.py`, `diplomacy.py`, `benchmark_synth.py`, and `consciousness.py` are composable Python research primitives with deterministic tests.
4. **API plane.** `production/api/v3/routes.py` owns an authenticated in-memory control adapter for frontier operations. `production/api/v3/websocket.py` defines typed events for market trades, exchanges, resurrections, benchmark synthesis, and consciousness measurements.
5. **Observatory.** The Signal Loom UI connects with an operator JWT, calls the v3 endpoints, displays explicit disconnected/error states, and does not invent organism, market, or awareness data when the API is unavailable.

## Frontier contracts

| Phase | Module | Computation |
|---|---|---|
| 11 | `recursive_improvement.py` | Deep-copy candidate, run a deterministic witness stream, and accept only if every configured invariant passes. |
| 12 | `market.py` | Scarcity/effectiveness pricing, wallet transactions, direct purchases, escrowed bids, and highest-bidder settlement. |
| 13 | `quantum_genome.py` | Classical amplitude weights, stochastic measurement, correlated entanglement, and additive interference. |
| 14 | `spiking.py` | Leaky integrate-and-fire neurons, sparse synapses, topology mutation, and reward-based Hebbian updates. |
| 15 | `archaeology.py` | Find extinct memome entries, score descriptor relevance, and inject qualifying strategies into living targets. |
| 16 | `diplomacy.py` | Escrow bilateral strategy lists, require explicit acceptance, transfer both sides atomically, and report compatibility. |
| 17 | `benchmark_synth.py` | Generate deterministic challenges whose difficulty increases over a 30-generation arms race. |
| 18 | `consciousness.py` | Compute bounded integrated-information, self-model, workspace-breadth, and composite awareness proxies. |

## State and event flow

The current v3 API uses `V3ControlState` as a process-local adapter because v3 frontier state is still experimental. The v2 SQLite store remains the durable source for strategy records and lineage. A production federation should replace the process-local adapter with a transactional store and publish events through Redis or a durable message bus. WebSocket admission is bounded per IP, and event payloads are typed Pydantic models.

## Operational boundary

The Autoscale web application is suitable for the dashboard and request/response experiments. A continuously running federation, high-volume Redis stream, or hostile code execution service should use reserved or separately managed infrastructure with cgroups and a hardened sandbox. The repository’s Docker and Helm changes provide the intended shape—no exposed sandbox port, read-only worker filesystem, no network, and bounded CPU/memory—but operators must verify the cluster’s runtime actually enforces those policies.
