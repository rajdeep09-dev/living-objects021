# Self-Directed Benchmark Findings

The v3 benchmark synthesizer creates bounded challenges with descriptors such as coordination, novelty, energy, and prediction. Difficulty increases by a deterministic 0.025 step per generation, producing a monotonic 30-generation arms race in the current research implementation. Solver scores remain observable, so future versions can replace the linear schedule with an adversarial generator driven by measured solver success.

The current result is a proof of the **co-evolution loop contract**, not proof of open-ended intelligence. A stronger experiment should use multiple independent synthesizers, hold out challenge descriptors, measure solver transfer, and compare generated difficulty against human-authored baselines. The reproducible harness is `scripts/run_v3_benchmarks.py`.
