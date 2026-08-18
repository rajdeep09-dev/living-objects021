"""Deterministic primitive-contamination audits for bounded GP task profiles.

The audit does not infer a task's semantics from prose.  It enumerates every
one-operation tree constructible from the evaluator's declared terminals and
the supplied primitive profile, then measures those candidates on multiple
evaluator-owned suites.  It separately measures the actual initialized random
population, which makes a profile's baseline inspectable rather than assumed.
"""
from __future__ import annotations

import itertools
import statistics
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

from evolution.fitness import (
    AbsoluteDifferenceEvaluator, CompressionEvaluator, FibonacciEvaluator,
    FitnessEvaluator, GameStrategyEvaluator, ManhattanDistanceEvaluator,
    MaxSubarrayEvaluator, PathfindingEvaluator, PrimeEvaluator,
    SortingEvaluator, StringReverseEvaluator,
)
from evolution.gp_engine import DEFAULT_PRIMITIVES, GPGenome, GPNode, Primitive, Terminal
from evolution.gp_population import GPPopulation


AUDIT_SEEDS = (101, 211, 307)
AUDIT_CASES_PER_SEED = 50
BASELINE_POPULATION_SIZE = 500
BASELINE_SEED = 1_729


@dataclass(frozen=True)
class TaskDefinition:
    task_id: str
    evaluator_factory: Callable[[], FitnessEvaluator]
    expected_batch_semantics: bool = True


IMPLEMENTED_TASKS: tuple[TaskDefinition, ...] = (
    TaskDefinition("sorting", SortingEvaluator),
    TaskDefinition("prime", PrimeEvaluator),
    TaskDefinition("fibonacci", FibonacciEvaluator),
    TaskDefinition("string-reverse", StringReverseEvaluator),
    TaskDefinition("max-subarray", MaxSubarrayEvaluator),
    TaskDefinition("absolute-difference", AbsoluteDifferenceEvaluator),
    TaskDefinition("manhattan-distance", ManhattanDistanceEvaluator),
    TaskDefinition("compression", CompressionEvaluator),
    TaskDefinition("pathfinding", PathfindingEvaluator),
    # The evaluator overrides both single and population paths to use the same
    # deterministic tournament. A no-one-operation-match result is still only
    # an audit observation, never a general game-strategy benchmark claim.
    TaskDefinition("game-strategy", GameStrategyEvaluator),
)


def _terminal_nodes(terminals: Iterable[Terminal], expected_type: str) -> tuple[GPNode, ...]:
    return tuple(
        GPNode(terminal_name=terminal.name, terminal_value=terminal.value, value_type=terminal.value_type)
        for terminal in terminals if terminal.value_type == expected_type
    )


def enumerate_one_operation_genomes(
    evaluator: FitnessEvaluator, primitives: Iterable[Primitive] = DEFAULT_PRIMITIVES,
) -> list[tuple[str, GPGenome]]:
    """Enumerate typed roots whose arguments are terminals only.

    This is deliberately narrower than a universal theorem prover. It detects
    the operationally dangerous situation that made `sort1` invalid: a direct
    complete solution reachable in a one-operation tree. Results with no match
    are labelled *no one-operation match observed*, never *mathematically clean*.
    """
    genomes: list[tuple[str, GPGenome]] = []
    for terminal in evaluator.terminals:
        genomes.append((f"terminal:{terminal.name or repr(terminal.value)}", GPGenome(
            tree=GPNode(terminal_name=terminal.name, terminal_value=terminal.value, value_type=terminal.value_type)
        )))
    for primitive in primitives:
        choices = [_terminal_nodes(evaluator.terminals, expected_type) for expected_type in primitive.arg_types]
        if not choices or any(not candidate_nodes for candidate_nodes in choices):
            continue
        for children in itertools.product(*choices):
            genomes.append((
                f"primitive:{primitive.name}",
                GPGenome(tree=GPNode(primitive=primitive, value_type=primitive.return_type, children=[child.copy() for child in children])),
            ))
    return genomes


def _is_direct_solution(evaluator: FitnessEvaluator, genome: GPGenome) -> bool:
    for seed in AUDIT_SEEDS:
        result = evaluator.batch_evaluate([genome], seed=seed, n=AUDIT_CASES_PER_SEED)[0]
        if result.correctness != 1.0:
            return False
    return True


def _baseline(evaluator: FitnessEvaluator, primitives: tuple[Primitive, ...], population_size: int, seed: int) -> dict[str, Any]:
    population = GPPopulation(
        evaluator=evaluator, primitives=primitives, population_size=population_size,
        seed=seed, max_depth=8, crossover_rate=0.85, mutation_rate=0.12,
        tournament_size=min(7, population_size), elitism_count=min(5, population_size - 1),
    )
    population.initialize()
    scores = [organism.fitness for organism in population.population]
    return {
        "population_size": population_size,
        "seed": seed,
        "evaluation_seed": population.TRAIN_SEED_OFFSET,
        "mean_fitness": statistics.fmean(scores),
        "median_fitness": statistics.median(scores),
        "best_fitness": max(scores),
        "perfect_programs": sum(score == 1.0 for score in scores),
    }


def audit_task(
    task: TaskDefinition,
    primitives: Iterable[Primitive] = DEFAULT_PRIMITIVES,
    *,
    baseline_population_size: int = BASELINE_POPULATION_SIZE,
    baseline_seed: int = BASELINE_SEED,
) -> dict[str, Any]:
    """Return a JSON-serializable contamination record for one actual evaluator."""
    primitive_tuple = tuple(primitives)
    evaluator = task.evaluator_factory()
    direct_matches: list[dict[str, Any]] = []
    for label, genome in enumerate_one_operation_genomes(evaluator, primitive_tuple):
        if _is_direct_solution(evaluator, genome):
            direct_matches.append({
                "candidate": label,
                "tree": genome.tree.to_dict(),
                "node_count": genome.complexity(),
            })
    baseline = _baseline(evaluator, primitive_tuple, baseline_population_size, baseline_seed)
    if not task.expected_batch_semantics:
        status = "INVALID_EVALUATOR_CONTRACT"
        decision = "Do not rank or evolve with this evaluator until batch_evaluate matches declared scoring semantics."
    elif direct_matches:
        status = "RETRACTED_DIRECT_PRIMITIVE"
        decision = "Retract algorithm-discovery claims and replace the task primitive profile."
    else:
        status = "NO_ONE_OPERATION_MATCH_OBSERVED"
        decision = "Eligible for a separately preregistered benchmark only after reviewing near-direct compositions."
    return {
        "schema": "beast-v8-contamination-audit-v1",
        "task_id": task.task_id,
        "status": status,
        "decision": decision,
        "profile": {
            "primitive_names": [primitive.name for primitive in primitive_tuple],
            "primitive_count": len(primitive_tuple),
            "terminal_count": len(evaluator.terminals),
            "audit_seeds": list(AUDIT_SEEDS),
            "audit_cases_per_seed": AUDIT_CASES_PER_SEED,
        },
        "one_operation_candidates_tested": len(enumerate_one_operation_genomes(evaluator, primitive_tuple)),
        "direct_solution_matches": direct_matches,
        "baseline": baseline,
    }


def audit_all_tasks(
    tasks: Iterable[TaskDefinition] = IMPLEMENTED_TASKS,
    primitives: Iterable[Primitive] = DEFAULT_PRIMITIVES,
    *,
    baseline_population_size: int = BASELINE_POPULATION_SIZE,
    baseline_seed: int = BASELINE_SEED,
) -> dict[str, Any]:
    """Audit each implemented evaluator under the same declared primitive profile."""
    records = [
        audit_task(task, primitives, baseline_population_size=baseline_population_size, baseline_seed=baseline_seed)
        for task in tasks
    ]
    return {
        "schema": "beast-v8-contamination-audit-report-v1",
        "task_count": len(records),
        "baseline_population_size": baseline_population_size,
        "tasks": records,
        "unimplemented_planned_domains": 14,
        "summary": {
            "retracted_direct_primitive": sum(record["status"] == "RETRACTED_DIRECT_PRIMITIVE" for record in records),
            "invalid_evaluator_contract": sum(record["status"] == "INVALID_EVALUATOR_CONTRACT" for record in records),
            "no_one_operation_match_observed": sum(record["status"] == "NO_ONE_OPERATION_MATCH_OBSERVED" for record in records),
        },
    }
