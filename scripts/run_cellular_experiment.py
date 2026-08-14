#!/usr/bin/env python3
"""Run a bounded, reproducible BEAST cellular-foundation experiment.

The experiment does not inject a target policy or a synthetic score. Cells learn
only through ``CellWorld.apply`` outcomes, offspring receive a bounded policy
copy, selection sees training worlds only, and the final report is measured on
disjoint held-out seeds owned by ``ExternalTruthLayer``.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from evolution.cellular import AdaptiveCell, CellGenome, CellWorld, evaluate_cell, run_lifetime
from evolution.cellular_eval import CellImprovementGate, EvaluatorPopulation, ExternalTruthLayer


@dataclass(frozen=True)
class CellularGeneration:
    generation: int
    average_train_score: float
    champion_train_score: float
    champion_holdout_score: float
    average_mutation_rate: float
    average_policy_states: float
    evaluator_mutation_rate: float
    evaluator_calibration: float
    promoted: bool


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _fresh_population(*, size: int, rng: random.Random) -> list[AdaptiveCell]:
    cells: list[AdaptiveCell] = []
    for _ in range(size):
        genome = CellGenome(
            learning_rate=round(rng.uniform(0.18, 0.65), 6),
            discount=round(rng.uniform(0.45, 0.88), 6),
            exploration_rate=round(rng.uniform(0.18, 0.50), 6),
            mutation_rate=round(rng.uniform(0.04, 0.18), 6),
            inheritance_rate=round(rng.uniform(0.65, 1.0), 6),
            repair_bias=round(rng.uniform(0.0, 0.35), 6),
        )
        cells.append(AdaptiveCell(genome=genome, max_age=80))
    return cells


def _train_cell(cell: AdaptiveCell, *, seed: int, ticks: int, generation: int, offset: int) -> None:
    """Let one cell learn through one finite lifetime; no score is injected."""

    world = CellWorld(seed=int(seed))
    run_lifetime(cell, world, ticks=ticks, seed=(generation + 1) * 10_000 + offset * 97 + int(seed))


def run_experiment(
    *,
    generations: int,
    population_size: int,
    train_seeds: tuple[int, ...],
    holdout_seeds: tuple[int, ...],
    seed: int,
    ticks: int,
) -> dict[str, object]:
    if generations <= 0 or population_size < 4:
        raise ValueError("generations must be positive and population size must be at least 4")
    if set(train_seeds) & set(holdout_seeds):
        raise ValueError("training and held-out seeds must be disjoint")

    rng = random.Random(seed)
    population = _fresh_population(size=population_size, rng=rng)
    evaluator_population = EvaluatorPopulation.seeded(size=5, seed=seed + 1)
    truth = ExternalTruthLayer(holdout_seeds=holdout_seeds, ticks=ticks, minimum_improvement=0.005)
    gate = CellImprovementGate(
        truth_layer=truth,
        train_seeds=train_seeds,
        probe_budget=min(5, len(train_seeds)),
        ticks=ticks,
    )
    initial_champion = AdaptiveCell.from_state(population[0].to_state())
    history: list[CellularGeneration] = []
    promoted_champion = initial_champion

    for generation in range(generations):
        for index, cell in enumerate(population):
            episode_seed = train_seeds[(generation + index) % len(train_seeds)]
            _train_cell(
                cell,
                seed=episode_seed,
                ticks=ticks,
                generation=generation,
                offset=index,
            )
        scores = [evaluate_cell(cell, world_seeds=train_seeds, ticks=ticks) for cell in population]
        ranked = sorted(zip(scores, population), key=lambda item: (-item[0], item[1].cell_id))
        champion_train, champion = ranked[0]
        evaluator = evaluator_population.cells[generation % len(evaluator_population.cells)]
        decision = gate.compare(
            baseline=promoted_champion,
            candidate=champion,
            evaluator=evaluator,
            rng=rng,
        )
        if decision.promoted:
            promoted_champion = AdaptiveCell.from_state(champion.to_state())

        history.append(
            CellularGeneration(
                generation=generation,
                average_train_score=round(_mean(scores), 6),
                champion_train_score=round(champion_train, 6),
                champion_holdout_score=decision.measurement.candidate_score,
                average_mutation_rate=round(_mean([cell.genome.mutation_rate for cell in population]), 6),
                average_policy_states=round(_mean([len(cell.policy.values) for cell in population]), 6),
                evaluator_mutation_rate=evaluator_population.average_mutation_rate,
                evaluator_calibration=decision.evaluator_calibration,
                promoted=decision.promoted,
            )
        )
        evaluator_population.evolve({evaluator.evaluator_id: decision.evaluator_calibration}, rng)

        elite_count = max(2, population_size // 5)
        survivors = [cell for _, cell in ranked if cell.alive]
        if len(survivors) < elite_count:
            raise RuntimeError(
                "insufficient survivors for biological reproduction; lower ticks or increase initial energy"
            )
        elites = survivors[:elite_count]
        next_population = [AdaptiveCell.from_state(cell.to_state()) for cell in elites]
        while len(next_population) < population_size:
            parent = elites[len(next_population) % len(elites)]
            next_population.append(parent.reproduce(rng, home=(0, 0)))
        population = next_population

    final_measurement = truth.measure(candidate=promoted_champion, baseline=initial_champion)
    return {
        "configuration": {
            "generations": generations,
            "population_size": population_size,
            "train_seeds": list(train_seeds),
            "holdout_seeds": list(holdout_seeds),
            "seed": seed,
            "ticks": ticks,
        },
        "history": [asdict(metric) for metric in history],
        "initial_holdout_score": truth.measure(candidate=initial_champion, baseline=initial_champion).candidate_score,
        "promoted_holdout_score": final_measurement.candidate_score,
        "baseline_holdout_score": final_measurement.baseline_score,
        "holdout_delta": final_measurement.score_delta,
        "promoted": truth.accepts(final_measurement),
        "champion": promoted_champion.to_state(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded real cellular evolution experiment")
    parser.add_argument("--generations", type=int, default=30)
    parser.add_argument("--population-size", type=int, default=28)
    parser.add_argument("--ticks", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--output", type=Path, default=Path("docs/cellular-experiment-results.json"))
    args = parser.parse_args()
    result = run_experiment(
        generations=args.generations,
        population_size=args.population_size,
        train_seeds=(31, 47, 59, 71, 83, 97, 101, 113),
        holdout_seeds=(901, 907, 911, 919, 929),
        seed=args.seed,
        ticks=args.ticks,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("initial_holdout_score", "promoted_holdout_score", "holdout_delta", "promoted")}, indent=2))
    print(f"wrote reproducible result: {args.output}")


if __name__ == "__main__":
    main()
