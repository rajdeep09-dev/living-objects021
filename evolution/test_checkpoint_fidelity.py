from __future__ import annotations

import copy
from dataclasses import asdict

import pytest

from evolution.clean_sorting import CleanSortingEvaluator, PHASES
from evolution.gp_engine import FLOAT, LIST, GPGenome, GPNode
from evolution.gp_population import GPPopulation


def _by_name():
    return {primitive.name: primitive for primitive in PHASES[-1].primitives}


def _custom_clean_tree() -> GPNode:
    primitives = _by_name()
    x = GPNode(terminal_name="x", value_type=LIST)
    empty = GPNode(terminal_value=[], value_type=LIST)
    zero = GPNode(terminal_value=0.0, value_type=FLOAT)
    head = GPNode(primitive=primitives["head"], value_type=FLOAT, children=[x.copy()])
    condition = GPNode(primitive=primitives["sub"], value_type=FLOAT, children=[head.copy(), zero])
    singleton = GPNode(
        primitive=primitives["cons"], value_type=LIST,
        children=[head, empty.copy()],
    )
    choice = GPNode(
        primitive=primitives["choose_list"], value_type=LIST,
        children=[condition, singleton, empty.copy()],
    )
    tail = GPNode(primitive=primitives["tail"], value_type=LIST, children=[x.copy()])
    return GPNode(primitive=primitives["concat_lists"], value_type=LIST, children=[choice, tail])


def _population() -> GPPopulation:
    population = GPPopulation(
        CleanSortingEvaluator(), primitives=PHASES[-1].primitives,
        population_size=10, seed=844, tournament_size=4, max_depth=6,
    )
    population.initialize()
    population.population[0].genome = GPGenome(tree=_custom_clean_tree())
    population._evaluate_current()
    return population


def _trajectory_snapshot(population: GPPopulation) -> tuple:
    return (
        population.generation,
        tuple(organism.organism_id for organism in population.population),
        tuple(organism.parent_ids for organism in population.population),
        tuple(organism.genome.to_dict() for organism in population.population),
        tuple(asdict(stat) for stat in population.history),
    )


def test_checkpoint_round_trip_preserves_recursive_custom_tree_and_full_payload() -> None:
    population = _population()
    payload = population.checkpoint_payload()
    restored = GPPopulation.from_checkpoint_payload(CleanSortingEvaluator(), copy.deepcopy(payload))
    assert payload["version"] == 2
    assert restored.checkpoint_payload() == payload
    original = population.population[0].genome.tree
    recovered = restored.population[0].genome.tree
    assert recovered.to_dict() == original.to_dict()
    assert recovered.evaluate({"x": [3, -1, 2]}) == original.evaluate({"x": [3, -1, 2]})
    assert {node["primitive"] for node in [recovered.to_dict(), *recovered.to_dict()["children"]]} >= {"concat_lists"}


def test_checkpoint_resume_matches_uninterrupted_ten_generation_trajectory() -> None:
    uninterrupted = _population()
    uninterrupted.run(5)
    resumed = GPPopulation.from_checkpoint_payload(CleanSortingEvaluator(), uninterrupted.checkpoint_payload())
    assert _trajectory_snapshot(resumed) == _trajectory_snapshot(uninterrupted)
    for _ in range(10):
        assert uninterrupted.step() == resumed.step()
        assert _trajectory_snapshot(resumed) == _trajectory_snapshot(uninterrupted)


def test_checkpoint_rejects_unknown_primitive_instead_of_degrading_tree() -> None:
    population = _population()
    payload = population.checkpoint_payload()
    payload["population"][0]["genome"]["tree"]["primitive"] = "unregistered_operation"
    with pytest.raises(ValueError, match="unregistered primitive"):
        GPPopulation.from_checkpoint_payload(CleanSortingEvaluator(), payload)
