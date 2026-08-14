# BEAST v2 API Reference

The v2 router is mounted at `/v2` and is protected by the same JWT dependency as the production API. Obtain a token through the existing operator login flow, then send `Authorization: Bearer <token>` for REST calls. All examples use JSON.

## Constitution

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v2/constitution` | Return the current rulebook. |
| `PATCH` | `/v2/constitution` | Apply a validated partial rulebook update. Numeric fields are bounded to `[0, 1]`; enum fields are checked by `EvolutionConstitution`. |
| `POST` | `/v2/constitution/mutate?seed=7` | Mutate the current rulebook with an optional deterministic seed and return before/after plus generated scorer code. |

Patch example:

```json
{
  "selection_pressure": 0.62,
  "novelty_weight": 0.38,
  "mutation_distribution": "cauchy"
}
```

## Organisms and ancestry

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v2/organisms` | Spawn a v2 organism. Body: `{"organism_id":"beast-01","parent_ids":[]}`. |
| `GET` | `/v2/organisms` | List live process organisms. |
| `GET` | `/v2/organisms/{organism_id}` | Return a complete runtime snapshot. |
| `POST` | `/v2/organisms/{organism_id}/reproduce?seed=11` | Create a child from the organism's inherited modules and mutable traits. |
| `GET` | `/v2/ancestry/{organism_id}` | Return the champion snapshot, known ancestors, and strategy lineage edges. |

## Strategies and federated memome

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v2/strategies?q=cache&limit=100` | Query durable strategy records. |
| `POST` | `/v2/strategies` | Publish a strategy record. Required fields: `name`, `source_code`, `descriptor`, `effectiveness`, `author_id`; optional `generation`, `parent_ids`, and `node_id`. |
| `POST` | `/v2/strategies/{strategy_id}/adopt` | Install a published strategy into an organism. Body: `{"organism_id":"beast-01"}`. |
| `POST` | `/v2/memome/gossip` | Merge a peer node's strategy payloads. Body contains `peer_node_id` and a `strategies` list using the publish shape. |
| `GET` | `/v2/memome/lineage` | Return durable `[{"parent_id":"...","child_id":"..."}]` edges. |

## Red team and embodied tools

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v2/red-team/attack?target_id=beast-01` | Attack a target. Body: `{"attacker_id":"red-01","attack_power":0.5}`. Returns validation, damage, outcome event, and target state. |
| `GET` | `/v2/tools` | List the registered allowlisted tools and descriptions. |
| `POST` | `/v2/organisms/{organism_id}/tools/{tool_name}` | Use a registered tool. Body: `{"kwargs":{...}}`. Results are truncated to 2,000 characters. |

The built-ins are `python_exec`, `file_read`, `http_get`, and `shell_cmd`. They are restricted research tools. Do not treat this endpoint as a production sandbox for arbitrary code.

## DSL and thermodynamics

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v2/dsl/express` | Encode `{condition, action, fallback}` into the current DSL. |
| `POST` | `/v2/dsl/parse` | Parse `{"source":"WHEN(high) -> coop; ELSE -> defect"}` back into intent. |
| `POST` | `/v2/dsl/mutate` | Add a new compound token to the process DSL genome. |
| `POST` | `/v2/energy/measure` | Measure quality per operation for an organism. Body: `organism_id`, `quality`, `operations`, `memory_allocated`, and optional `budget`. |

Energy response shape:

```json
{
  "score": {
    "result_quality": 0.8,
    "operations": 10,
    "memory_allocated": 128,
    "efficiency": 0.08,
    "affordable": true
  },
  "organism": {"organism_id": "beast-01"}
}
```

## Events and WebSocket

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v2/events?limit=100` | Return recent bounded event history. |
| `WebSocket` | `/ws/v2/evolution?token=<jwt>` | Stream typed v2 evolution events. |

Event `type` values are `organism_born`, `strategy_adopted`, `constitution_mutated`, and `red_team_attack`. Event payloads include the organism or strategy identifiers needed to hydrate the Species Inspector and ancestry view. The WebSocket sends an initial `connected` message and then forwards live events.

## Operational notes

The default SQLite path is `state/v2_memome.sqlite3`; override it with `V2_MEMOME_PATH`. The live control state is currently process-local. For multiple replicas, use a shared durable store, an authenticated event bus, and sticky or fan-out WebSocket delivery. Validate all strategy source outside the API process before allowing external side effects.
