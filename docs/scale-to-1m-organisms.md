# Scaling Living Objects to One Million Organisms

This guide describes the path from the current 10,000-organism benchmark to a one-million-organism deployment. The implementation already includes a memory-mapped population state, batch evolution, bounded parallel workers, sharded SQLite memomes, self-improvement records, and a three-species ecosystem. Those mechanisms make the scaling boundary explicit; they do not by themselves guarantee one million production organisms on a single machine.

## Capacity model

The runtime separates hot population state from durable cultural history. Hot state is a compact fixed-width memory map, which keeps per-organism numeric fields predictable. The memome is sharded by a stable hash so writes and reads can be distributed across files or, later, database partitions.

| Layer | Prototype/benchmark implementation | One-million-organism production direction |
|---|---|---|
| Organism state | Fixed-width `mmap` records | Partitioned worker-owned state segments, with snapshot and checksum manifests |
| Reproduction | Batch cloning with deterministic mutation | Queue-based generation jobs with backpressure and idempotent generation IDs |
| Memome | SQLite shards with one-million-record shard capacity | PostgreSQL partitioning or a distributed key-value/archive service with object-store snapshots |
| Parallelism | Process pool for CPU-bound scoring | One worker group per partition, autoscaled by queue depth and organism count |
| Metrics | Prometheus gauges/counters | Recording rules, exemplars, long-term metrics storage, and per-lineage sampling |
| API | FastAPI control plane | Stateless API replicas over managed PostgreSQL and Redis, with a separate evolution worker plane |

## Recommended rollout

Start with 10,000 organisms and 1,000 generations as the acceptance benchmark. Next, run 100,000 organisms with one worker partition and verify checkpoint recovery. Then scale to 1,000,000 organisms with at least 16 partitions, a managed PostgreSQL-compatible archive, and an object-store snapshot path. Each stage should compare fitness, novelty, cultural retention, event lag, memory use, write amplification, and recovery time against the previous stage.

The API replicas should not own the evolution loop. They should expose control and observation endpoints only. Evolution workers should claim a generation lease, process only their partition, write an idempotent generation result, publish a compact event, and release the lease. Redis is useful for ephemeral coordination and live stream fan-out, but it should not be the sole durable source of cultural truth.

## Safety and correctness gates

Before increasing population size, require deterministic replay for a fixed seed, archive checksum validation, bounded event queues, explicit generation leases, and a rollback snapshot. New self-improvement policies must be evaluated in a shadow arena before they are allowed to modify the production policy. A policy that improves fitness while degrading novelty, reliability, safety, or cost should not be promoted.

## What “self-improving” means here

The current `SelfImprovingEvolution` component tunes `mutation_rate`, `inheritance_rate`, and `novelty_bonus` from measured outcomes and records each accepted parameter set as an `evolution-improvement` meme. This is algorithm-parameter adaptation, not unrestricted self-rewriting. A future production system may evolve algorithm implementations, but only behind versioned policy artifacts, isolated evaluation, signed promotion, and automatic rollback.

