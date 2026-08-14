# BEAST v4 Benchmark Results

> These are reproducible mechanism measurements for bounded research implementations, not claims about physical universes or subjective consciousness.

| Area | Measurement |
|---|---:|
| Distinct physics regimes | `3` |
| Antibodies by generation 50 | `20` |
| Verified WASM export | `True` |
| Memory-palace clusters | `5` |
| Vocabulary at generation 100 | `99` |
| Grammar layers | `3` |
| Tournament ELO ratio | `1.1408` |
| Epistemic CI shrink | `0.930424` |
| Turing self-simulation | `True` |

## Reproduction

```bash
python3 scripts/run_v4_benchmarks.py --output docs/v4-benchmark-results.md
```

```json
{
  "epistemic": {
    "final_width": 0.069576,
    "initial_width": 1.0,
    "shrink": 0.930424
  },
  "immunity": {
    "antibody_pool": 20,
    "generation": 50
  },
  "memory_palace": {
    "clusters": 5,
    "rooms": 5
  },
  "substrate": {
    "verified_running": true,
    "wasm_bytes": 36
  },
  "temporal": {
    "affected_organisms": 2,
    "applied": true,
    "paradox": false
  },
  "tournament": {
    "top_to_bottom_elo_ratio": 1.1408
  },
  "turing": {
    "simulated": true,
    "universality_score": 1.0
  },
  "universes": {
    "branches": 102,
    "distinct_physics_regimes": 3,
    "generations": 100
  },
  "writing_system": {
    "generation": 100,
    "grammar_layers": 3,
    "vocabulary": 99,
    "vocabulary_growth": 96
  }
}
```
