"""Evaluator-cell curriculum and independent verification for BEAST cells.

Evaluator cells are adaptive *test-probe selectors*. They can learn which
training worlds separate policies and evolve their own parameters.  They do not
own final truth: a frozen ``ExternalTruthLayer`` scores candidate and baseline
on disjoint held-out worlds and is the only component allowed to promote an
adaptive-cell policy.
"""
from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, Mapping, Optional, Sequence

from evolution.cellular import AdaptiveCell, evaluate_cell


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


@dataclass(frozen=True)
class EvaluatorGenome:
    """Mutable parameters of an evaluator cell's probe-selection policy."""

    learning_rate: float = 0.35
    exploration_rate: float = 0.20
    mutation_rate: float = 0.08
    generation_born: int = 0

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def mutate(self, rng: random.Random, *, generation_born: Optional[int] = None) -> "EvaluatorGenome":
        next_rate = self._clamp(
            self.mutation_rate + rng.gauss(0.0, self.mutation_rate * 0.18 + 0.005),
            0.01,
            0.35,
        )
        return EvaluatorGenome(
            learning_rate=self._clamp(
                self.learning_rate + rng.gauss(0.0, next_rate * 0.45), 0.05, 0.90
            ),
            exploration_rate=self._clamp(
                self.exploration_rate + rng.gauss(0.0, next_rate * 0.45), 0.01, 0.55
            ),
            mutation_rate=next_rate,
            generation_born=self.generation_born + 1 if generation_born is None else generation_born,
        )


@dataclass(frozen=True)
class ProbeEvidence:
    """Evidence from one training-world comparison; never a promotion decision."""

    seed: int
    baseline_score: float
    candidate_score: float
    predicted_gain: float

    @property
    def observed_gain(self) -> float:
        return self.candidate_score - self.baseline_score


@dataclass
class EvaluatorCell:
    """An adaptive evaluator that chooses informative training probes.

    ``probe_values`` estimates the magnitude of policy differences expected on
    each seed. Values change only after the evaluator observes actual training
    outcomes. This makes the evaluator an organism with a bounded memory and
    learning loop, while keeping it powerless to rewrite external verification.
    """

    evaluator_id: str
    genome: EvaluatorGenome = field(default_factory=EvaluatorGenome)
    probe_values: Dict[int, float] = field(default_factory=dict)
    probe_counts: Dict[int, int] = field(default_factory=dict)
    max_probes: int = 512
    parent_id: Optional[str] = None

    def select_probes(self, pool: Sequence[int], *, budget: int, rng: random.Random) -> list[int]:
        """Select a finite training subset using learned discrimination estimates."""

        if budget <= 0:
            raise ValueError("probe budget must be positive")
        normalized = list(dict.fromkeys(int(seed) for seed in pool))
        if not normalized:
            raise ValueError("training probe pool cannot be empty")
        budget = min(budget, len(normalized))
        if rng.random() < self.genome.exploration_rate:
            shuffled = list(normalized)
            rng.shuffle(shuffled)
            return sorted(shuffled[:budget])
        # Prefer probes whose learned observed differences were large, then use
        # the seed as a stable tie breaker for reproducibility.
        ranked = sorted(normalized, key=lambda seed: (-self.probe_values.get(seed, 0.0), seed))
        return ranked[:budget]

    def predict_gain(self, seed: int) -> float:
        return self.probe_values.get(int(seed), 0.0)

    def learn(self, evidence: ProbeEvidence) -> None:
        """Update a probe's estimated discriminative value from observed outcome."""

        key = int(evidence.seed)
        prior = self.probe_values.get(key, 0.0)
        target = abs(evidence.observed_gain)
        self.probe_values[key] = prior + self.genome.learning_rate * (target - prior)
        self.probe_counts[key] = self.probe_counts.get(key, 0) + 1
        if len(self.probe_values) > self.max_probes:
            oldest = next(iter(self.probe_values))
            self.probe_values.pop(oldest, None)
            self.probe_counts.pop(oldest, None)

    def reproduce(self, rng: random.Random) -> "EvaluatorCell":
        """Create a descendant that inherits probe evidence plus mutated traits."""

        inherited = {
            seed: value
            for seed, value in self.probe_values.items()
            if rng.random() <= 0.85
        }
        counts = {seed: self.probe_counts.get(seed, 0) for seed in inherited}
        return EvaluatorCell(
            evaluator_id=f"{self.evaluator_id}-g{self.genome.generation_born + 1}",
            genome=self.genome.mutate(rng),
            probe_values=inherited,
            probe_counts=counts,
            max_probes=self.max_probes,
            parent_id=self.evaluator_id,
        )

    def to_state(self) -> Dict[str, object]:
        return {
            "evaluator_id": self.evaluator_id,
            "genome": asdict(self.genome),
            "probe_values": dict(self.probe_values),
            "probe_counts": dict(self.probe_counts),
            "max_probes": self.max_probes,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_state(cls, payload: Mapping[str, object]) -> "EvaluatorCell":
        raw_genome = payload.get("genome", {})
        if not isinstance(raw_genome, Mapping):
            raise ValueError("evaluator state needs a genome mapping")
        known = {name: raw_genome[name] for name in EvaluatorGenome.__dataclass_fields__ if name in raw_genome}
        raw_values = payload.get("probe_values", {})
        raw_counts = payload.get("probe_counts", {})
        return cls(
            evaluator_id=str(payload.get("evaluator_id", "evaluator")),
            genome=EvaluatorGenome(**known),  # type: ignore[arg-type]
            probe_values={int(key): float(value) for key, value in raw_values.items()} if isinstance(raw_values, Mapping) else {},
            probe_counts={int(key): int(value) for key, value in raw_counts.items()} if isinstance(raw_counts, Mapping) else {},
            max_probes=max(1, min(4096, int(payload.get("max_probes", 512)))),
            parent_id=str(payload["parent_id"]) if payload.get("parent_id") is not None else None,
        )


@dataclass(frozen=True)
class HoldoutMeasurement:
    """Immutable result from the truth layer's frozen held-out worlds."""

    candidate_score: float
    baseline_score: float
    score_delta: float
    seeds: tuple[int, ...]


@dataclass(frozen=True)
class ExternalTruthLayer:
    """Independent immutable verifier for cell-policy changes.

    The class is frozen so callers cannot alter its declared seeds, budget, or
    margin during a run. It intentionally exposes no policy mutation or score
    injection interface.
    """

    holdout_seeds: tuple[int, ...]
    ticks: int = 70
    minimum_improvement: float = 0.015

    def __post_init__(self) -> None:
        if not self.holdout_seeds:
            raise ValueError("truth layer needs at least one held-out seed")
        if self.ticks <= 0:
            raise ValueError("truth layer ticks must be positive")
        if self.minimum_improvement < 0:
            raise ValueError("truth-layer margin cannot be negative")

    def measure(self, *, candidate: AdaptiveCell, baseline: AdaptiveCell) -> HoldoutMeasurement:
        candidate_score = evaluate_cell(candidate, world_seeds=self.holdout_seeds, ticks=self.ticks)
        baseline_score = evaluate_cell(baseline, world_seeds=self.holdout_seeds, ticks=self.ticks)
        return HoldoutMeasurement(
            candidate_score=candidate_score,
            baseline_score=baseline_score,
            score_delta=round(candidate_score - baseline_score, 6),
            seeds=self.holdout_seeds,
        )

    def accepts(self, measurement: HoldoutMeasurement) -> bool:
        return measurement.score_delta >= self.minimum_improvement


@dataclass(frozen=True)
class ImprovementDecision:
    """Full auditable decision from curriculum evidence plus holdout evidence."""

    promoted: bool
    training_baseline_score: float
    training_candidate_score: float
    training_delta: float
    evaluator_calibration: float
    measurement: HoldoutMeasurement
    probes: tuple[ProbeEvidence, ...]
    reason: str


@dataclass
class CellImprovementGate:
    """Combines adaptive evaluator curriculum with a non-negotiable truth gate."""

    truth_layer: ExternalTruthLayer
    train_seeds: tuple[int, ...]
    probe_budget: int = 5
    ticks: int = 70

    def __post_init__(self) -> None:
        if not self.train_seeds:
            raise ValueError("at least one training seed is required")
        if set(self.train_seeds) & set(self.truth_layer.holdout_seeds):
            raise ValueError("training seeds and held-out truth seeds must be disjoint")
        if self.probe_budget <= 0:
            raise ValueError("probe budget must be positive")

    def compare(
        self,
        *,
        baseline: AdaptiveCell,
        candidate: AdaptiveCell,
        evaluator: EvaluatorCell,
        rng: random.Random,
    ) -> ImprovementDecision:
        """Train the evaluator on selected probes, then defer promotion to truth."""

        selected = evaluator.select_probes(self.train_seeds, budget=self.probe_budget, rng=rng)
        probes: list[ProbeEvidence] = []
        for seed in selected:
            baseline_score = evaluate_cell(baseline, world_seeds=(seed,), ticks=self.ticks)
            candidate_score = evaluate_cell(candidate, world_seeds=(seed,), ticks=self.ticks)
            evidence = ProbeEvidence(
                seed=seed,
                baseline_score=baseline_score,
                candidate_score=candidate_score,
                predicted_gain=evaluator.predict_gain(seed),
            )
            evaluator.learn(evidence)
            probes.append(evidence)

        train_baseline = _mean([evidence.baseline_score for evidence in probes])
        train_candidate = _mean([evidence.candidate_score for evidence in probes])
        train_delta = train_candidate - train_baseline
        prediction_error = _mean(
            [abs(evidence.predicted_gain - abs(evidence.observed_gain)) for evidence in probes]
        )
        calibration = round(1.0 / (1.0 + prediction_error), 6)
        measurement = self.truth_layer.measure(candidate=candidate, baseline=baseline)
        promoted = self.truth_layer.accepts(measurement)
        if promoted:
            reason = "independent holdout improvement met the declared margin"
        elif train_delta > 0:
            reason = "training gain rejected because independent holdout margin was not met"
        else:
            reason = "candidate did not improve on selected training probes or independent holdout"
        return ImprovementDecision(
            promoted=promoted,
            training_baseline_score=round(train_baseline, 6),
            training_candidate_score=round(train_candidate, 6),
            training_delta=round(train_delta, 6),
            evaluator_calibration=calibration,
            measurement=measurement,
            probes=tuple(probes),
            reason=reason,
        )


@dataclass
class EvaluatorPopulation:
    """Small co-evolving population of curriculum cells with measured lineage."""

    cells: list[EvaluatorCell]
    generation: int = 0

    @classmethod
    def seeded(cls, *, size: int, seed: int) -> "EvaluatorPopulation":
        if size <= 0:
            raise ValueError("evaluator population size must be positive")
        rng = random.Random(seed)
        cells = [
            EvaluatorCell(
                evaluator_id=f"evaluator-{index}",
                genome=EvaluatorGenome(
                    learning_rate=round(rng.uniform(0.18, 0.55), 6),
                    exploration_rate=round(rng.uniform(0.08, 0.38), 6),
                    mutation_rate=round(rng.uniform(0.04, 0.16), 6),
                ),
            )
            for index in range(size)
        ]
        return cls(cells=cells)

    def evolve(self, calibration_by_id: Mapping[str, float], rng: random.Random) -> None:
        """Select evaluators by calibration, carry an elite, and mutate offspring."""

        if not self.cells:
            return
        ranked = sorted(
            self.cells,
            key=lambda cell: (-calibration_by_id.get(cell.evaluator_id, 0.0), cell.evaluator_id),
        )
        elites = ranked[: max(1, len(ranked) // 3)]
        next_cells = [EvaluatorCell.from_state(elite.to_state()) for elite in elites]
        while len(next_cells) < len(self.cells):
            parent = elites[len(next_cells) % len(elites)]
            next_cells.append(parent.reproduce(rng))
        self.cells = next_cells[: len(self.cells)]
        self.generation += 1

    @property
    def average_mutation_rate(self) -> float:
        return round(_mean([cell.genome.mutation_rate for cell in self.cells]), 6)
