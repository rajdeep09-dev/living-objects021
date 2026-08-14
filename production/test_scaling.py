"""Scaling, persistence, self-improvement, and multi-species tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from evolution.multi_species import Consumer, Decomposer, MultiSpeciesEcosystem, Producer
from evolution.scalable import MMapPopulationState, ScalableEvolution, ScalableOrganism, ShardedMemome
from evolution.self_improving import EvolutionPolicy, SelfImprovingEvolution, SelfImprovingOrganism


def test_mmap_state_round_trip(tmp_path: Path):
    path = tmp_path / "population.mmap"
    organism = ScalableOrganism("org-1", fitness=0.7, mutation_rate=0.2, inheritance_rate=0.9, novelty_bonus=0.3)
    with MMapPopulationState(path, capacity=4) as state:
        state.write(0, organism)
        assert state.read(0) == pytest.approx((0.7, 0.2, 0.9, 0.3), rel=1e-6)
    assert path.stat().st_size > 0


@pytest.mark.parametrize("capacity", [1, 2, 3, 8, 32])
def test_sharded_memome_respects_capacity(tmp_path: Path, capacity: int):
    with ShardedMemome(tmp_path / "memome", shard_capacity=capacity) as memome:
        for index in range(capacity + 1):
            memome.contribute(f"meme-{index}", f"descriptor-{index}", effectiveness=index / 10)
        assert memome.count == capacity + 1
        assert memome.shard_count == 2
        assert len(memome.query("descriptor", limit=100)) == capacity + 1


def test_sharded_memome_deduplicates_ids(tmp_path: Path):
    with ShardedMemome(tmp_path / "memome") as memome:
        meme_id = "stable-meme"
        memome.contribute("same", "same", meme_id=meme_id)
        memome.contribute("same", "same", meme_id=meme_id)
        assert memome.count == 1


def test_10000_organism_population_can_step(tmp_path: Path):
    with ScalableEvolution(10_000, workers=1, state_path=tmp_path / "state.mmap", memome_dir=tmp_path / "memome") as engine:
        started = time.perf_counter()
        metric = engine.step()
        assert time.perf_counter() - started < 300
        assert metric.organism_count == 10_000
        assert metric.generation == 1
        assert metric.average_fitness > 0


def test_parallel_population_step(tmp_path: Path):
    with ScalableEvolution(256, workers=2, state_path=tmp_path / "state.mmap", memome_dir=tmp_path / "memome") as engine:
        metric = engine.step()
        assert metric.organism_count == 256
        assert metric.best_fitness >= metric.average_fitness


def test_batch_reproduction_is_chunked(tmp_path: Path):
    with ScalableEvolution(2505, state_path=tmp_path / "state.mmap", memome_dir=tmp_path / "memome") as engine:
        batches = list(engine.batch_reproduce(batch_size=1000))
        assert [len(batch) for batch in batches] == [1000, 1000, 505]


def test_thousand_generation_benchmark_is_bounded(tmp_path: Path):
    with ScalableEvolution(32, state_path=tmp_path / "state.mmap", memome_dir=tmp_path / "memome") as engine:
        started = time.perf_counter()
        history = engine.run(1000)
        elapsed = time.perf_counter() - started
        assert elapsed < 300
        assert history[-1].generation == 1000
        assert history[-1].average_fitness > history[0].average_fitness


def test_agnes_adapter_has_safe_fallback(tmp_path: Path):
    from evolution.scalable import AgnesEvaluator

    with ScalableEvolution(1, state_path=tmp_path / "state.mmap", memome_dir=tmp_path / "memome") as engine:
        evaluator = AgnesEvaluator(engine=None)
        value = evaluator.score(engine.population[0])
        assert 0.0 <= value <= 1.0
        assert evaluator.mode in {"local-fallback", "agnes-with-fallback"}


def test_self_improving_organism_records_policy_meme(tmp_path: Path):
    with ShardedMemome(tmp_path / "memome") as archive:
        organism = SelfImprovingOrganism("policy-1", EvolutionPolicy(mutation_rate=0.2))
        improvement = organism.improve_evolution(archive, observed_fitness=0.8, generation=1)
        assert improvement.after != improvement.before
        assert improvement.meme_id
        assert archive.query("policy:policy-1")


def test_self_improving_evolution_tunes_parameters(tmp_path: Path):
    with ShardedMemome(tmp_path / "memome") as archive:
        engine = SelfImprovingEvolution(size=16)
        history = engine.run(archive, generations=8)
        assert len(history) == 8
        assert history[-1]["improvement_count"] == 16 * 8
        assert history[-1]["average_mutation_rate"] != history[0]["average_mutation_rate"]


def test_multi_species_ecosystem_keeps_all_species_alive(tmp_path: Path):
    with ShardedMemome(tmp_path / "memome") as archive:
        ecosystem = MultiSpeciesEcosystem(archive, size=90)
        history = ecosystem.run(1000)
        assert history[-1].alive == 90
        assert ecosystem.species_counts() == {"producer": 30, "consumer": 30, "decomposer": 30}
        assert history[-1].recycled_memes > 0


@pytest.mark.parametrize("species_type", [Producer, Consumer, Decomposer])
def test_species_have_distinct_roles(tmp_path: Path, species_type: type):
    with ShardedMemome(tmp_path / "memome") as archive:
        ecosystem = MultiSpeciesEcosystem(archive, size=9)
        instance = species_type("test", 0)
        instance.step(ecosystem)
        assert instance.species in {"producer", "consumer", "decomposer"}
