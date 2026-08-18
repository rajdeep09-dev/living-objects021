from __future__ import annotations

from evolution.fitness import FitnessEvaluator, SortingEvaluator
from evolution.gp_engine import ALL_REGISTERED_PRIMITIVES, CONVENIENCE_PRIMITIVES, DEFAULT_PRIMITIVES, FLOAT, LIST, GPGenome, GPNode
from evolution.gp_population import GPPopulation


class SeedRecordingEvaluator(FitnessEvaluator):
    """Objective identity task that records the exact shared batch suite."""

    def __init__(self) -> None:
        self.batch_records: list[tuple[int, tuple[tuple[float, float], ...], int]] = []

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[float, float]]:
        return [(float(seed + index), float(seed + index)) for index in range(n)]

    def batch_evaluate(self, genomes, seed: int, n: int = 20):
        candidates = list(genomes)
        cases = tuple(self.generate_test_cases(seed=seed, n=n))
        self.batch_records.append((seed, cases, len(candidates)))
        return [self._eval_on_cases(genome, cases) for genome in candidates]


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


def test_population_never_exceeds_max_size_across_100_generations() -> None:
    population = GPPopulation(
        SortingEvaluator(), population_size=8, seed=97, max_depth=8,
        crossover_rate=1.0, mutation_rate=1.0,
    )
    population.initialize()
    square = next(primitive for primitive in DEFAULT_PRIMITIVES if primitive.name == "sq")
    oversized = GPNode(terminal_name="x", value_type=FLOAT)
    for _ in range(79):
        oversized = GPNode(primitive=square, value_type=FLOAT, children=[oversized])
    population.population[0].genome.tree = oversized
    for _ in range(100):
        population.step()
        assert all(
            organism.genome.complexity() <= population.BLOAT_MAX_NODES
            for organism in population.population
        )


def test_fitness_seed_rotates_every_generation_but_is_consistent_within_one_generation() -> None:
    evaluator = SeedRecordingEvaluator()
    population = GPPopulation(evaluator, population_size=6, seed=101)
    population.initialize()
    first_seed, first_cases, first_count = evaluator.batch_records[-1]
    assert first_seed == population.TRAIN_SEED_OFFSET
    assert first_count == population.population_size
    population.step()
    second_seed, second_cases, second_count = evaluator.batch_records[-1]
    assert second_seed == first_seed + 1
    assert second_cases != first_cases
    assert second_count == population.population_size


def test_population_saves_and_loads_without_fitness_regression(tmp_path) -> None:
    population = GPPopulation(SortingEvaluator(), primitives=ALL_REGISTERED_PRIMITIVES, population_size=8, seed=131)
    population.run(100)
    generation_100_fitness = population.champion.fitness
    checkpoint = tmp_path / "generation-100.json"
    population.save_checkpoint(checkpoint)

    resumed = GPPopulation.load_checkpoint(SortingEvaluator(), checkpoint)
    assert resumed.generation == 100
    assert len(resumed.population) == population.population_size
    assert resumed.champion.genome.to_dict() == population.champion.genome.to_dict()

    resumed.run(100)
    assert resumed.generation == 200
    assert resumed.champion.fitness >= generation_100_fitness


def test_python_audit_export_binds_sorting_input_alias_to_canonical_argument() -> None:
    sort1 = next(primitive for primitive in CONVENIENCE_PRIMITIVES if primitive.name == "sort1")
    genome = GPGenome(GPNode(
        primitive=sort1, value_type=LIST,
        children=[GPNode(terminal_name="input", value_type=LIST)],
    ))
    source = genome.to_python("sorting_champion")
    compile(source, "<gp-audit-export>", "exec")
    assert "def sorting_champion(x):" in source
    assert "input = x" in source
    assert "sorted(list(input))" in source
