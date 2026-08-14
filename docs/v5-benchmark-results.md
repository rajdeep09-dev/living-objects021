# BEAST v5 Benchmark Results

This report records one reproducible, local smoke benchmark of the v5 worker. It is intentionally smaller than the recommended 100,000-generation experiment so it can serve as a quick integration check. It is **not** evidence that a longer run has the same runtime, fitness, or cost characteristics.

## Measured compression-profile run

```bash
ENVIRONMENT=development APP_ENV=development JWT_SECRET=dev-only-v5-secret-for-tests \
python3 scripts/run_v5_benchmarks.py \
  --task compress \
  --generations 1000 \
  --population 8 \
  --workers 2 \
  --checkpoint-interval 250 \
  --batch-size 250 \
  --workspace /tmp/beast-v5-benchmark \
  --reports-dir /tmp/beast-v5-reports
```

| Metric | Measured value |
|---|---:|
| Task profile | Compression strategy evolution |
| Status | Completed |
| Generations | 1,000 / 1,000 |
| Population | 8 |
| Local scoring workers | 2 |
| Peak fitness | 0.934153 |
| Average fitness | 0.933384 |
| Cultural complexity | 6.620977 |
| Novel descriptors | 1,191 |
| Memome strategies | 1,191 |
| Elapsed wall time | 40.475 seconds |

The run wrote checkpoints at generations 500, 750, and 1,000, with a persisted terminal event at generation 1,000. The worker uses an explicit local task registry and performs no network request in the per-generation path. It does **not** evaluate user text as code, and its score measures a deterministic trait-and-culture profile rather than compression correctness for arbitrary input files.

## How to reproduce a full v5 task run

Use a persistent host and durable volume for a 100,000-generation experiment. The default runner checkpoints every 1,000 generations and can resume a stopped process.

```bash
python3 scripts/run_v5_benchmarks.py --task compress --generations 100000
python3 scripts/run_v5_benchmarks.py --task compress --generations 100000 --resume
```

The one-worker guard is one million generations. A request for longer work should be decomposed into reviewed finite runs with explicit quotas rather than removing the bound.
