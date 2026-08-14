# BEAST v3 API Reference

All write endpoints require an operator JWT. Read endpoints are intentionally separated. The API is mounted under `/v3`; the frontier WebSocket is `/ws/v3/evolution?token=<jwt>`.

## Market and wallets

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v3/market/listings` | List strategy name, seller, price, adoption count, and effectiveness. |
| `POST` | `/v3/market/listings` | Register a strategy listing. |
| `POST` | `/v3/market/listings/{strategy_name}/buy` | Deduct buyer tokens, transfer the strategy, and credit the seller. |
| `POST` | `/v3/market/listings/{strategy_name}/bid` | Place or replace a sealed bid. |
| `POST` | `/v3/market/listings/{strategy_name}/auction` | Settle the highest bid. |

## Ecosystems and diplomacy

`POST /v3/ecosystems` registers an ecosystem identifier, constitution, DSL vocabulary, and strategy names. `POST /v3/diplomacy/proposals` creates an escrowed proposal; `POST /v3/diplomacy/proposals/{proposal_id}/accept` releases both sides atomically; and `/reject` returns escrowed assets. `GET /v3/diplomacy/compatibility` reports DSL overlap, constitutional similarity, and novelty-distance proxies.

## Frontier operations

`POST /v3/archaeology/pass` runs an excavation and returns `excavated`, `resurrected`, and `resurrected_names`. `POST /v3/benchmarks/synthesize` creates a bounded challenge; `POST /v3/benchmarks/co-evolve` returns the benchmark list, difficulty series, and solver scores. `POST /v3/quantum/measure` collapses amplitude weights into a classical genome, while `/quantum/interfere` returns combined amplitudes. `POST /v3/spiking/forward` runs a bounded spike simulation. `POST /v3/improvement/prove` runs the configured safety witness proof. `GET /v3/consciousness/{organism_id}` returns `phi`, `self_model_accuracy`, `workspace_breadth`, and `composite`.

## WebSocket events

The typed event union includes `market_trade`, `diplomatic_exchange`, `strategy_resurrected`, `benchmark_synthesized`, and `consciousness_measured`. Clients must treat events as telemetry, not as authorization to perform a mutation without a fresh authenticated request.
