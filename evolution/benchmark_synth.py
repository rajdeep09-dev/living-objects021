"""Self-directed benchmark generation and solver/synthesizer co-evolution."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Benchmark:
    benchmark_id: str
    difficulty: float
    challenge: str
    generation: int


@dataclass(frozen=True)
class CoEvolutionHistory:
    benchmarks: tuple[Benchmark, ...]
    difficulty_series: tuple[float, ...]
    solver_scores: tuple[float, ...]


class BenchmarkSynthesizer:
    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)
        self.generation = 0
        self.history: list[Benchmark] = []

    def synthesize_benchmark(self, difficulty: float) -> Benchmark:
        difficulty = max(0.0, min(1.0, float(difficulty)))
        self.generation += 1
        challenge = f"descriptor:{self.rng.choice(['coordination', 'novelty', 'energy', 'prediction'])}:threshold:{difficulty:.3f}"
        benchmark_id = hashlib.sha256(f"{challenge}:{self.generation}".encode()).hexdigest()[:16]
        benchmark = Benchmark(benchmark_id, difficulty, challenge, self.generation)
        self.history.append(benchmark)
        return benchmark

    def evaluate(self, organism: Any, benchmark: Benchmark) -> float:
        descriptors = set(getattr(organism, "behavior_descriptors", {}).values())
        quality = float(getattr(organism, "behavior_quality", lambda: 0.0)())
        descriptor_match = any(token in descriptors for token in benchmark.challenge.split(":") if token not in {"descriptor", "threshold"})
        competence = min(1.0, 0.55 * quality + 0.45 * float(descriptor_match))
        return round(max(0.0, min(1.0, competence - 0.35 * benchmark.difficulty + 0.35)), 6)

    def co_evolve(self, synthesizers: list["BenchmarkSynthesizer"], solvers: list[Any], generations: int) -> CoEvolutionHistory:
        if generations < 1 or not synthesizers:
            raise ValueError("generations and synthesizers must be non-empty")
        benchmarks: list[Benchmark] = []
        difficulties: list[float] = []
        scores: list[float] = []
        difficulty = 0.05
        for _ in range(generations):
            difficulty = min(1.0, difficulty + 0.025)
            benchmark = synthesizers[0].synthesize_benchmark(difficulty)
            benchmarks.append(benchmark)
            difficulties.append(benchmark.difficulty)
            scores.append(max((synthesizers[0].evaluate(organism, benchmark) for organism in solvers), default=0.0))
        return CoEvolutionHistory(tuple(benchmarks), tuple(difficulties), tuple(scores))


__all__ = ["Benchmark", "BenchmarkSynthesizer", "CoEvolutionHistory"]
