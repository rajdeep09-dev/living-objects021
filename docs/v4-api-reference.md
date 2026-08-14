# BEAST v4 API Reference

All v4 routes are mounted under `/v4` and use the same authenticated operator context as v3. Production write operations require the configured operator role and should be fronted by TLS and shared rate limiting.

| Method | Path | Purpose |
|---|---|---|
| GET | `/v4/snapshot` | Read the current frontier snapshot. |
| GET | `/v4/universes` | List process-local parallel-universe branches. |
| POST | `/v4/universes/{universe_id}/branch` | Branch a universe with a named law. |
| POST | `/v4/temporal/revise` | Submit a bounded temporal revision proposal. |
| POST | `/v4/computation/run` | Run a bounded universal-machine computation. |
| GET | `/v4/immunity` | Read civilization antibody state. |
| GET | `/v4/epistemic` | Read uncertainty and confidence telemetry. |
| GET | `/v4/memory/snapshot` | Read memory-palace geometry. |
| POST | `/v4/memory/navigate` | Navigate a memory direction with a step budget. |
| POST | `/v4/writing/evolve` | Evolve a writing-system token and grammar layer. |
| POST | `/v4/tournament/run` | Run the bounded adversarial tournament. |
| POST | `/v4/morphogenesis/develop` | Develop a morphogenetic neural program. |
| POST | `/v4/substrate/export` | Export a declarative WASM, container, or circuit artifact. |

The WebSocket stream is `/ws/v4/evolution?token=<jwt>`. Events are typed JSON objects with an event name, timestamp, generation, and payload. The stream is bounded by the same per-IP admission policy as v3.
