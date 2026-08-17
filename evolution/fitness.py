"""Empirical fitness evaluators for bounded BEAST v6 program evolution."""
from __future__ import annotations

import math
import random
import statistics
import time
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from evolution.gp_engine import BOOL, FLOAT, LIST, STRING, GPGenome, Terminal


@dataclass(frozen=True)
class FitnessResult:
    """Measured result from executing a program on a finite test suite."""

    score: float
    correctness: float
    efficiency: float
    robustness: float
    description_length: int
    wall_time_ms: float
    test_cases_passed: int
    test_cases_total: int
    error_message: str = ""


class FitnessEvaluator(ABC):
    """Base evaluator: scores derive from task outcomes, never template values."""

    output_type = FLOAT
    terminals: tuple[Terminal, ...] = (Terminal(name="x", value_type=FLOAT), Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT))

    @abstractmethod
    def generate_test_cases(self, seed: int, n: int) -> list[tuple[Any, Any]]:
        """Return deterministic (input, expected-output) cases for one generation."""

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        return self._eval_on_cases(genome, self.generate_test_cases(seed=42, n=20))

    def batch_evaluate(self, genomes: Iterable[GPGenome], seed: int, n: int = 20) -> list[FitnessResult]:
        """Evaluate a collection through the bounded interpreter on deterministic cases."""
        cases = self.generate_test_cases(seed=seed, n=n)
        return [self._eval_on_cases(genome, cases) for genome in genomes]

    def context_for(self, input_value: Any) -> dict[str, Any]:
        return {"x": input_value, "input": input_value, "data": input_value}

    def checkpoint_state(self) -> dict[str, Any]:
        """Return evaluator-owned JSON state needed for an exact population resume."""
        return {}

    def restore_checkpoint_state(self, state: Mapping[str, Any]) -> None:
        """Restore a state emitted by :meth:`checkpoint_state`.

        Stateless evaluators deliberately accept an empty mapping only. A stateful
        evaluator must override both hooks rather than relying on source parsing
        or implicit constructor defaults during a resume.
        """
        if state:
            raise ValueError("this evaluator does not accept checkpoint state")

    def _eval_on_cases(self, genome: GPGenome, cases: Sequence[tuple[Any, Any]]) -> FitnessResult:
        passed = 0
        durations: list[float] = []
        for input_value, expected in cases:
            started = time.perf_counter()
            actual = genome.execute(self.context_for(input_value))
            durations.append((time.perf_counter() - started) * 1000.0)
            if self._is_correct(actual, expected):
                passed += 1
        total = len(cases)
        correctness = passed / max(1, total)
        average_ms = statistics.fmean(durations) if durations else 0.0
        efficiency = max(0.0, min(1.0, 1.0 - average_ms / 25.0))
        # Wall-clock variance is host-noise, not a program property.  The
        # deterministic task suite itself supplies robustness: a program is
        # robust only to the degree that it succeeds across all sampled cases.
        # Measured latency remains separately visible in ``wall_time_ms``.
        robustness = correctness
        # Correctness is deliberately the primary score; other measurements are
        # reported separately so a fast wrong program cannot outscore a correct one.
        return FitnessResult(
            score=correctness, correctness=correctness, efficiency=efficiency,
            robustness=robustness, description_length=genome.description_length(),
            wall_time_ms=average_ms, test_cases_passed=passed, test_cases_total=total,
        )

    def _is_correct(self, actual: Any, expected: Any) -> bool:
        if isinstance(expected, float):
            return isinstance(actual, (int, float)) and math.isfinite(float(actual)) and abs(float(actual) - expected) <= 1e-6
        if isinstance(expected, list):
            return isinstance(actual, list) and len(actual) == len(expected) and all(self._is_correct(a, b) for a, b in zip(actual, expected))
        return actual == expected


class SortingEvaluator(FitnessEvaluator):
    output_type = LIST
    terminals = (Terminal(name="x", value_type=LIST), Terminal(name="input", value_type=LIST), Terminal(value=[], value_type=LIST))

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[list[int], list[int]]]:
        rng = random.Random(seed)
        return [
            (values := [rng.randint(-50, 50) for _ in range(rng.randint(3, 15))], sorted(values))
            for _ in range(n)
        ]


class PrimeEvaluator(FitnessEvaluator):
    output_type = BOOL
    terminals = (Terminal(name="x", value_type=FLOAT), Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT))

    def generate_test_cases(self, seed: int, n: int = 30) -> list[tuple[int, bool]]:
        rng = random.Random(seed)
        candidates = rng.sample(range(2, 200), min(n, 198))
        return [(candidate, _is_prime(candidate)) for candidate in candidates]


class FibonacciEvaluator(FitnessEvaluator):
    output_type = FLOAT
    terminals = (Terminal(name="x", value_type=FLOAT), Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT), Terminal(value=2.0, value_type=FLOAT))

    def generate_test_cases(self, seed: int, n: int = 15) -> list[tuple[int, int]]:
        values = [0, 1]
        for _ in range(2, max(2, n)):
            values.append(values[-1] + values[-2])
        return list(enumerate(values[:n]))


class StringReverseEvaluator(FitnessEvaluator):
    output_type = STRING
    terminals = (Terminal(name="x", value_type=STRING), Terminal(name="input", value_type=STRING), Terminal(value="", value_type=STRING))

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[str, str]]:
        words = ["hello", "world", "evolution", "organism", "memome", "culture", "darwin", "fitness", "living", "objects"]
        rng = random.Random(seed)
        return [(word := rng.choice(words), word[::-1]) for _ in range(n)]


class MaxSubarrayEvaluator(FitnessEvaluator):
    output_type = FLOAT
    terminals = (Terminal(name="x", value_type=LIST), Terminal(name="input", value_type=LIST), Terminal(value=0.0, value_type=FLOAT))

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[list[int], float]]:
        rng = random.Random(seed)
        cases: list[tuple[list[int], float]] = []
        for _ in range(n):
            values = [rng.randint(-10, 10) for _ in range(rng.randint(3, 12))]
            running = best = values[0]
            for value in values[1:]:
                running = max(value, running + value)
                best = max(best, running)
            cases.append((values, float(best)))
        return cases


class AbsoluteDifferenceEvaluator(FitnessEvaluator):
    """Compositional arithmetic benchmark: ``abs(left - right)``.

    The target operation is intentionally *not* a single registered primitive.
    A correct program must compose the bounded ``sub`` and ``abs1`` primitives,
    making baseline-versus-champion improvement meaningful rather than a lookup
    of an already-perfect task primitive.
    """

    output_type = FLOAT
    terminals = (
        Terminal(name="left", value_type=FLOAT), Terminal(name="right", value_type=FLOAT),
        Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT),
    )

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[tuple[int, int], float]]:
        rng = random.Random(seed)
        return [
            ((left := rng.randint(-50, 50), right := rng.randint(-50, 50)), float(abs(left - right)))
            for _ in range(n)
        ]

    def context_for(self, input_value: tuple[int, int]) -> dict[str, Any]:
        left, right = input_value
        return {"x": float(left), "left": float(left), "right": float(right)}


class ManhattanDistanceEvaluator(FitnessEvaluator):
    """Four-input compositional benchmark for ``|x2-x1| + |y2-y1|``.

    The target operation is deliberately absent from the primitive whitelist.
    A perfect program must discover a composition of generic subtraction,
    absolute-value, and addition operations.  Test cases are generated entirely
    from the recorded seed, so a holdout suite can be reproduced independently.
    """

    output_type = FLOAT
    terminals = (
        Terminal(name="x1", value_type=FLOAT), Terminal(name="y1", value_type=FLOAT),
        Terminal(name="x2", value_type=FLOAT), Terminal(name="y2", value_type=FLOAT),
        Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT),
    )

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[tuple[int, int, int, int], float]]:
        rng = random.Random(seed)
        return [
            ((x1 := rng.randint(-75, 75), y1 := rng.randint(-75, 75), x2 := rng.randint(-75, 75), y2 := rng.randint(-75, 75)),
             float(abs(x2 - x1) + abs(y2 - y1)))
            for _ in range(n)
        ]

    def context_for(self, input_value: tuple[int, int, int, int]) -> dict[str, Any]:
        x1, y1, x2, y2 = input_value
        return {"x": float(x1), "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}

    def _eval_on_cases(self, genome: GPGenome, cases: Sequence[tuple[Any, Any]]) -> FitnessResult:
        """Use real normalized absolute error to make a sparse symbolic task searchable.

        A reward is the arithmetic result of a program's actual numeric error,
        clipped only by the declared maximum distance (300).  It is not a
        simulated score; exact output agreement remains available through the
        separately reported ``correctness`` field and passed-case count.
        """
        errors: list[float] = []
        durations: list[float] = []
        passed = 0
        for input_value, expected in cases:
            started = time.perf_counter()
            actual = genome.execute(self.context_for(input_value))
            durations.append((time.perf_counter() - started) * 1000.0)
            if isinstance(actual, (int, float)) and math.isfinite(float(actual)):
                error = min(300.0, abs(float(actual) - float(expected)))
                if error <= 1e-6:
                    passed += 1
            else:
                error = 300.0
            errors.append(error)
        mean_error = statistics.fmean(errors) if errors else 300.0
        objective = max(0.0, min(1.0, 1.0 - mean_error / 300.0))
        average_ms = statistics.fmean(durations) if durations else 0.0
        return FitnessResult(
            score=objective,
            correctness=passed / max(1, len(cases)),
            efficiency=max(0.0, min(1.0, 1.0 - average_ms / 25.0)),
            robustness=objective,
            description_length=genome.description_length(),
            wall_time_ms=average_ms,
            test_cases_passed=passed,
            test_cases_total=len(cases),
        )


class CompressionEvaluator(FitnessEvaluator):
    """Measures a true compression-length estimate on a fixed local corpus."""

    output_type = FLOAT
    terminals = (Terminal(name="x", value_type=LIST), Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT))

    def generate_test_cases(self, seed: int, n: int = 15) -> list[tuple[list[int], float]]:
        rng = random.Random(seed)
        cases: list[tuple[list[int], float]] = []
        for _ in range(n):
            values: list[int] = []
            for _ in range(rng.randint(3, 8)):
                values.extend([rng.randint(0, 7)] * rng.randint(1, 6))
            cases.append((values, float(len(zlib.compress(bytes(values), level=1)))))
        return cases


class PathfindingEvaluator(FitnessEvaluator):
    output_type = FLOAT
    terminals = (
        Terminal(name="cx", value_type=FLOAT), Terminal(name="cy", value_type=FLOAT),
        Terminal(name="gx", value_type=FLOAT), Terminal(name="gy", value_type=FLOAT),
        Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT),
    )

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[tuple[int, int, int, int], float]]:
        rng = random.Random(seed)
        return [
            ((cx := rng.randint(0, 10), cy := rng.randint(0, 10), gx := rng.randint(0, 10), gy := rng.randint(0, 10)), math.hypot(gx - cx, gy - cy))
            for _ in range(n)
        ]

    def context_for(self, input_value: tuple[int, int, int, int]) -> dict[str, Any]:
        cx, cy, gx, gy = input_value
        return {"x": float(cx), "cx": float(cx), "cy": float(cy), "gx": float(gx), "gy": float(gy)}

    def _is_correct(self, actual: Any, expected: Any) -> bool:
        return isinstance(actual, (int, float)) and math.isfinite(float(actual)) and abs(float(actual) - float(expected)) <= 2.0


class GameStrategyEvaluator(FitnessEvaluator):
    """Finite, deterministic iterated-prisoner's-dilemma tournament."""

    output_type = FLOAT
    terminals = (Terminal(name="x", value_type=FLOAT), Terminal(name="rnd", value_type=FLOAT), Terminal(value=0.0, value_type=FLOAT), Terminal(value=1.0, value_type=FLOAT))

    def generate_test_cases(self, seed: int, n: int = 1) -> list[tuple[None, None]]:
        return [(None, None)]

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        opponents = (
            lambda history: 1, lambda history: 0,
            lambda history: history[-1] if history else 1,
            lambda history: 0 if 0 in history else 1,
            lambda history: (len(history) % 2),
        )
        payoffs = {(1, 1): 3, (1, 0): 0, (0, 1): 5, (0, 0): 1}
        total = 0.0
        started = time.perf_counter()
        for opponent in opponents:
            history: list[int] = []
            for round_number in range(100):
                raw = genome.execute({"x": float(history[-1] if history else 1), "rnd": float(round_number), "n": float(round_number)})
                move = 1 if isinstance(raw, (int, float)) and float(raw) > 0.5 else 0
                opponent_move = opponent(history)
                total += payoffs[(move, opponent_move)]
                history.append(opponent_move)
        elapsed = (time.perf_counter() - started) * 1000.0
        score = total / (len(opponents) * 100 * 5)
        return FitnessResult(score=score, correctness=score, efficiency=max(0.0, 1.0 - elapsed / 100.0), robustness=1.0, description_length=genome.description_length(), wall_time_ms=elapsed, test_cases_passed=int(score * 100), test_cases_total=100)


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    for divisor in range(2, int(math.sqrt(value)) + 1):
        if value % divisor == 0:
            return False
    return True
