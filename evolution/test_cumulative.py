"""Regression tests for persistent cumulative cultural evolution."""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from evolution.cumulative import CulturalArchive, CumulativeEvolution


def test_cultural_archive_persistence(tmp_path):
    """Knowledge remains available after its contributor's process is gone."""
    archive_path = tmp_path / "culture.sqlite"
    with CulturalArchive(archive_path) as archive:
        meme = archive.contribute(
            action="forage",
            source_code="def action_forage(self):\n    return 0.80\n",
            niche="resource",
            generation=3,
            fitness=0.80,
            author_id="organism-that-died",
        )

    with CulturalArchive(archive_path) as restarted_archive:
        restored = restarted_archive.get(meme.meme_id)
        assert restored is not None
        assert restored.author_id == "organism-that-died"
        assert restored.fitness == 0.80
        assert restarted_archive.size == 1


def test_behavioral_inheritance(tmp_path):
    """An offspring can adopt a proven program deposited by an ancestor."""
    archive_path = tmp_path / "culture.sqlite"
    with CumulativeEvolution(archive_path, population_size=4, random_seed=4) as system:
        system.initialize_population()
        ancestor = system.population[0]
        meme = system.archive.contribute(
            action="build_shelter",
            source_code="def action_build_shelter(self):\n    return 0.88\n",
            niche="shelter",
            generation=1,
            fitness=0.88,
            author_id=ancestor.object_id,
        )
        offspring = system._create_organism("descendant", parent=ancestor)

        assert offspring.get_behavior("build_shelter") == meme.source_code
        assert offspring.behavior_origins["build_shelter"] == meme.meme_id


def test_cumulative_complexity(tmp_path):
    """Archive-mediated inheritance increases the population's repertoire."""
    with CumulativeEvolution(
        tmp_path / "culture.sqlite", population_size=10, random_seed=11
    ) as system:
        history = system.run(generations=100, report=False)
        start = next(metric for metric in history if metric.generation == 0)
        finish = next(metric for metric in history if metric.generation == 100)

        assert finish.behaviors_per_organism > start.behaviors_per_organism
        assert finish.archive_size > 3


def test_novelty_creation(tmp_path):
    """Recombination creates culturally named niches beyond founding actions."""
    with CumulativeEvolution(
        tmp_path / "culture.sqlite", population_size=10, random_seed=12
    ) as system:
        history = system.run(generations=100, report=False)
        finish = next(metric for metric in history if metric.generation == 100)
        new_actions = {meme.action for meme in system.archive.all_memes() if meme.action.startswith("niche_")}

        assert finish.novel_behaviors > 0
        assert len(new_actions) == finish.novel_behaviors
        assert all(action not in {"forage", "cooperate", "explore"} for action in new_actions)


def test_archive_effectiveness(tmp_path):
    """Populations that use shared knowledge outperform isolated lineages."""
    with CumulativeEvolution(
        tmp_path / "with-archive.sqlite", population_size=10, random_seed=23, use_archive=True
    ) as cultural:
        cultural_history = cultural.run(generations=80, report=False)
        cultural_final = cultural_history[-1]

    with CumulativeEvolution(
        tmp_path / "without-archive.sqlite", population_size=10, random_seed=23, use_archive=False
    ) as isolated:
        isolated_history = isolated.run(generations=80, report=False)
        isolated_final = isolated_history[-1]

    assert cultural_final.average_fitness > isolated_final.average_fitness
    assert cultural_final.behaviors_per_organism > isolated_final.behaviors_per_organism
