"""Executable proofs for the Lamarckian living-object implementation."""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from evolution.lamarckian import LamarckianEcosystem, LamarckianGenome, Memome


def test_lamarckian_inheritance_parent_learns_child_inherits(tmp_path):
    """A strategy acquired by a parent during life is present in its child."""
    with LamarckianEcosystem(tmp_path / "memome.sqlite", seed=3, population_size=2) as ecosystem:
        parent = ecosystem.spawn("parent", genome=LamarckianGenome(inheritance_rate=1.0))
        learned = parent.learn(
            "shelter",
            "def action_shelter(self):\n    return 0.91\n",
            descriptor="shelter:windproof",
            effectiveness=0.91,
        )
        child = parent.reproduce(ecosystem.rng)

        assert learned.strategy_id in child.learned_strategies
        assert child.get_behavior("shelter") == learned.source_code
        assert child.execute_strategy("shelter") == 0.91


def test_meta_evolution_changes_population_mutation_rate(tmp_path):
    """Mutation rate is heritable, mutable, and changes at the population level."""
    with LamarckianEcosystem(tmp_path / "memome.sqlite", seed=17, population_size=12) as ecosystem:
        results = ecosystem.run_evolution(generations=50, report=False)
        history = results["history"]
        start = history[0]
        finish = history[-1]
        final_rates = {round(organism.genome.mutation_rate, 6) for organism in ecosystem.population}

        assert abs(finish["average_mutation_rate"] - start["average_mutation_rate"]) > 0.001
        assert len(final_rates) > 1


def test_memome_persists_after_creator_death_and_is_reused(tmp_path):
    """Cultural knowledge outlives its author and is usable by a later organism."""
    archive_path = tmp_path / "durable-memome.sqlite"
    with LamarckianEcosystem(archive_path, seed=9, population_size=2) as ecosystem:
        founder = ecosystem.spawn("founder")
        legacy = founder.learn(
            "bridge",
            "def action_bridge(self):\n    return 0.87\n",
            descriptor="bridge:ravine",
            effectiveness=0.87,
        )
        founder.die("test-lifecycle-end")

    with Memome(archive_path) as reopened:
        restored = reopened.get(legacy.strategy_id)
        assert restored is not None
        assert restored.author_id == founder.object_id

    with LamarckianEcosystem(archive_path, seed=9, population_size=2) as later_ecosystem:
        later = later_ecosystem.spawn("later-generation")
        adopted = later.adopt_from_memome(limit=3, minimum_effectiveness=0.80)

        assert legacy.strategy_id in adopted
        assert later.execute_strategy("bridge") == 0.87


def test_open_ended_novelty_and_cultural_complexity_rise(tmp_path):
    """New descriptors accumulate, culture expands, and fitness rises by generation 50."""
    with LamarckianEcosystem(tmp_path / "memome.sqlite", seed=21, population_size=12) as ecosystem:
        results = ecosystem.run_evolution(generations=50, report=False)
        start = results["history"][0]
        finish = results["history"][-1]

        assert finish["novelty_count"] > start["novelty_count"]
        assert finish["cultural_complexity"] > start["cultural_complexity"]
        assert finish["average_fitness"] > start["average_fitness"]
        assert finish["archive_size"] >= finish["novelty_count"]


def test_program_self_modification_has_safe_fallback(tmp_path):
    """Runtime replacement changes behavior; malformed and crashing code cannot kill it."""
    with LamarckianEcosystem(tmp_path / "memome.sqlite", seed=5, population_size=2) as ecosystem:
        organism = ecosystem.spawn("self-modifier")
        assert organism.set_behavior("runtime_switch", "def action_runtime_switch(self):\n    return 0.93\n")
        assert organism.execute_strategy("runtime_switch") == 0.93

        assert not organism.set_behavior("broken", "def action_broken(self):\n    not valid python")
        assert organism.set_behavior("crashy", "def action_crashy(self):\n    raise RuntimeError('boom')\n")
        assert organism.execute_strategy("crashy") == "default_crashy"
