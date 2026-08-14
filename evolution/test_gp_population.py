from __future__ import annotations

from evolution.fitness import SortingEvaluator
from evolution.gp_population import GPPopulation


def test_population_initialises_and_measures_real_fitness() -> None:
    population = GPPopulation(SortingEvaluator(), population_size=12, seed=31)
    population.initialize()
    assert len(population.population) == 12
    assert len(population.history) == 1
    assert all(0.0 <= organism.fitness <= 1.0 for organism in population.population)


def test_population_step_is_deterministic_for_same_seed() -> None:
    left = GPPopulation(SortingEvaluator(), population_size=10, seed=41)
    right = GPPopulation(SortingEvaluator(), population_size=10, seed=41)
    left.initialize(); right.initialize()
    left.step(); right.step()
    assert left.history[-1] == right.history[-1]
    assert left.champion.genome.to_dict() == right.champion.genome.to_dict()


def test_population_run_stops_at_generation_budget() -> None:
    population = GPPopulation(SortingEvaluator(), population_size=8, seed=51)
    summary = population.run(5)
    assert summary.generations == 5
    assert len(population.history) == 6


def test_hall_of_fame_is_bounded_over_many_generations() -> None:
    population = GPPopulation(SortingEvaluator(), population_size=6, seed=61)
    population.run(120)
    assert len(population.hall_of_fame) == population.HALL_OF_FAME_MAX


def test_checkpoint_is_json_only_and_contains_population(tmp_path) -> None:
    population = GPPopulation(SortingEvaluator(), population_size=6, seed=71)
    population.run(2)
    destination = tmp_path / "gp-checkpoint.json"
    population.save_checkpoint(destination)
    payload = destination.read_text(encoding="utf-8")
    assert '"population"' in payload
    assert '"generation": 2' in payload


def test_elites_and_offspring_do_not_share_tree_objects() -> None:
    population = GPPopulation(SortingEvaluator(), population_size=8, seed=81)
    population.initialize()
    population.step()
    trees = [organism.genome.tree for organism in population.population]
    assert len({id(tree) for tree in trees}) == len(trees)
