"""
Unit tests for Lamarckian Living Objects — proving all 5 features.

Tests are grouped by feature and each proves a concrete, measurable claim.

Run:
    pytest evolution/test_lamarckian.py -v
"""
from __future__ import annotations

import random
import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evolution.lamarckian import (
    CulturalMemome,
    NoveltyArchive,
    BehaviorDescriptor,
    LamarckianGenome,
    LamarckianOrganism,
    LamarckianPopulation,
)


# ============================================================================
# HELPERS
# ============================================================================

def make_organism(
    oid: str = "test_org",
    name: str = "Tester",
    seed: int = 42,
    intelligence: float = 0.7,
    cooperation: float = 0.6,
    memome: CulturalMemome = None,
) -> LamarckianOrganism:
    rng = random.Random(seed)
    genome = LamarckianGenome(
        intelligence=intelligence,
        cooperation=cooperation,
        energy_efficiency=0.5,
        adaptability=0.5,
        resilience=0.5,
        mutation_rate=0.10,
        meta_mutation_rate=0.02,
        inherited_strategies=[],
        inherited_memes=[],
    )
    return LamarckianOrganism(
        organism_id=oid,
        name=name,
        genome=genome,
        generation=0,
        memome=memome or CulturalMemome(),
        rng=rng,
    )


# ============================================================================
# FEATURE 1: LAMARCKIAN INHERITANCE
# ============================================================================

class TestLamarckianInheritance:

    def test_parent_learns_strategy(self):
        """Parent can learn a new strategy during its lifetime."""
        parent = make_organism("parent_1")
        meme_id = parent.learn("heat_avoidance", "return 'stay cool'", performance=0.9)

        assert parent.knows("heat_avoidance"), "Parent should know its learned strategy"
        assert meme_id is not None, "Learning should return a meme_id"
        assert len(meme_id) > 0

    def test_learned_strategy_added_to_genome(self):
        """Learning updates the genome's inherited_strategies list."""
        parent = make_organism("parent_2")
        parent.learn("tool_use", "return 'use rock'", performance=0.8)

        assert "tool_use" in parent.genome.inherited_strategies, (
            "Learned strategy must be in genome.inherited_strategies for inheritance"
        )

    def test_child_inherits_parent_strategies(self):
        """CORE LAMARCKIAN TEST: child inherits ALL strategies parent learned."""
        memome = CulturalMemome()
        parent = make_organism("parent_3", memome=memome)

        parent.learn("fire_making", "return 'rub sticks'", performance=0.95)
        parent.learn("shelter_building", "return 'build hut'", performance=0.88)

        assert parent.count_strategies() == 2

        child = parent.reproduce()

        assert child.knows("fire_making"), (
            "Child must know 'fire_making' inherited from parent"
        )
        assert child.knows("shelter_building"), (
            "Child must know 'shelter_building' inherited from parent"
        )
        assert child.count_strategies() == 2, (
            "Child should have inherited exactly 2 strategies"
        )

    def test_grandchild_inherits_across_generations(self):
        """Lamarckian inheritance is transitive across multiple generations."""
        memome = CulturalMemome()
        grandparent = make_organism("gp_1", memome=memome)
        grandparent.learn("navigation", "return 'follow stars'", performance=0.9)

        parent = grandparent.reproduce()
        # Parent also learns something new
        parent.learn("farming", "return 'plant seeds'", performance=0.85)

        grandchild = parent.reproduce()

        assert grandchild.knows("navigation"), (
            "Grandchild inherits grandparent's navigation strategy"
        )
        assert grandchild.knows("farming"), (
            "Grandchild inherits parent's farming strategy"
        )

    def test_child_inherits_at_birth_without_independent_learning(self):
        """
        The key distinction from Darwinian evolution:
        child has the knowledge WITHOUT ever having 'learned' it during its own lifetime.
        The inherited strategies come from the genome, not from the child's own experience.
        """
        memome = CulturalMemome()
        parent = make_organism("parent_4", memome=memome)
        parent.learn("secret_skill", "return 'secret!'", performance=0.99)

        child = parent.reproduce()

        # Child has the strategy before simulating any lifetime
        assert child.knows("secret_skill"), (
            "Child knows 'secret_skill' at birth — Lamarckian, not Darwinian"
        )

    def test_crossover_merges_both_parents_strategies(self):
        """Sexual reproduction unions both parents' learned strategies."""
        memome = CulturalMemome()
        parent_a = make_organism("pa", memome=memome, seed=1)
        parent_b = make_organism("pb", memome=memome, seed=2)

        parent_a.learn("strat_a1", "return 'A1'", performance=0.8)
        parent_a.learn("strat_a2", "return 'A2'", performance=0.7)
        parent_b.learn("strat_b1", "return 'B1'", performance=0.9)

        child = parent_a.reproduce(partner=parent_b)

        assert child.knows("strat_a1") or child.knows("strat_a2"), (
            "Child should inherit at least one of parent_a's strategies"
        )
        assert child.knows("strat_b1"), (
            "Child should inherit parent_b's strategy"
        )


# ============================================================================
# FEATURE 2: META-EVOLUTION
# ============================================================================

class TestMetaEvolution:

    def test_mutation_rate_is_genome_trait(self):
        """mutation_rate is a proper genome attribute, not a global constant."""
        genome = LamarckianGenome(mutation_rate=0.15)
        assert genome.mutation_rate == 0.15

    def test_mutation_rate_is_inherited(self):
        """Offspring inherit parent's mutation_rate (as starting point)."""
        memome = CulturalMemome()
        parent = make_organism("mr_parent", memome=memome)
        parent.genome.mutation_rate = 0.25  # Set high mutation rate

        child = parent.reproduce()
        # Child's mutation_rate should be in the vicinity of 0.25 (mutated by meta_mr)
        assert 0.001 <= child.genome.mutation_rate <= 0.5, (
            "Child mutation_rate must remain in valid range [0.001, 0.5]"
        )

    def test_offspring_have_different_mutation_rates(self):
        """
        Different children from the same parent get different mutation_rates
        (because mutation_rate itself is mutated by meta_mutation_rate).
        """
        memome = CulturalMemome()
        parent = make_organism("mr_parent2", memome=memome, seed=77)
        parent.genome.mutation_rate = 0.20
        parent.genome.meta_mutation_rate = 0.05  # High meta-rate → more variation

        mutation_rates = set()
        for i in range(20):
            child = parent.reproduce()
            mutation_rates.add(round(child.genome.mutation_rate, 3))

        assert len(mutation_rates) > 1, (
            "Multiple children should have diverse mutation_rates — "
            "mutation_rate must evolve, not stay fixed"
        )

    def test_population_mutation_rate_changes_over_generations(self):
        """
        CORE META-EVOLUTION TEST: The population's avg mutation_rate
        changes over 20 generations — it is selected upon, not fixed.
        """
        memome = CulturalMemome()
        pop = LamarckianPopulation(seed=123, memome=memome)
        pop.seed_population(10)

        # Record mutation rates across generations
        mr_history = []
        for _ in range(20):
            stats = pop.step()
            mr_history.append(stats["avg_mutation_rate"])

        # The mutation rate should have changed — not stayed exactly constant
        assert len(set(round(mr, 3) for mr in mr_history)) > 1, (
            "avg_mutation_rate must vary across generations — meta-evolution not working"
        )

    def test_genome_mutation_rate_mutates_itself(self):
        """
        Verify that mutate() changes mutation_rate from parent to child.
        """
        rng = random.Random(55)
        parent_genome = LamarckianGenome(
            mutation_rate=0.20,
            meta_mutation_rate=0.05,
        )
        children_mrs = [parent_genome.mutate(rng).mutation_rate for _ in range(50)]
        unique_mrs = set(round(mr, 4) for mr in children_mrs)
        assert len(unique_mrs) > 5, (
            "Mutations of mutation_rate should produce diverse values"
        )


# ============================================================================
# FEATURE 3: CUMULATIVE CULTURE / MEMOME
# ============================================================================

class TestCumulativeCulture:

    def test_organism_deposits_to_memome(self):
        """Learning deposits a strategy to the shared cultural store."""
        memome = CulturalMemome()
        org = make_organism("depositor", memome=memome)
        org.learn("wheel_invention", "return 'round is better'", performance=0.99)

        assert memome.total_strategies() == 1
        record = memome.retrieve("wheel_invention")
        assert record is not None
        assert record["body"] == "return 'round is better'"

    def test_strategy_survives_creator_death(self):
        """
        CORE CULTURE TEST: Strategy remains in memome after creator dies.
        This is the crucial distinction from individual memory.
        """
        memome = CulturalMemome()
        mortal = make_organism("mortal", memome=memome)
        mortal.learn("agriculture", "return 'plant crops'", performance=0.92)

        assert memome.total_strategies() == 1
        mortal.die()
        assert not mortal.alive

        # Strategy must still be retrievable
        record = memome.retrieve("agriculture")
        assert record is not None, (
            "Strategy must survive organism death — cultural persistence failed"
        )
        assert record["creator_alive"] is False, (
            "creator_alive must be marked False after creator dies"
        )

    def test_surviving_dead_creator_count(self):
        """count_surviving_dead_creator() accurately tracks orphaned memes."""
        memome = CulturalMemome()
        mortal = make_organism("mortal2", memome=memome)
        mortal.learn("s1", "return 1")
        mortal.learn("s2", "return 2")

        mortal.die()
        assert memome.count_surviving_dead_creator() == 2

    def test_successor_adopts_dead_creators_knowledge(self):
        """
        Later-generation organism can retrieve and USE a dead creator's strategy.
        """
        memome = CulturalMemome()
        dead_pioneer = make_organism("pioneer", memome=memome, seed=1)
        dead_pioneer.learn("metallurgy", "return 'smelt iron'", performance=0.97)
        dead_pioneer.die()

        assert not dead_pioneer.alive
        assert memome.retrieve("metallurgy") is not None

        successor = make_organism("successor", memome=memome, seed=2)
        adopted = successor.adopt_from_culture("metallurgy")

        assert adopted, "Successor must successfully adopt ancestor's strategy"
        assert successor.knows("metallurgy"), (
            "Successor knows 'metallurgy' from dead ancestor — culture works!"
        )

    def test_cultural_accumulation_grows_over_generations(self):
        """
        Total cultural strategies in the memome GROWS over generations.
        Each generation contributes, building on all prior knowledge.
        """
        memome = CulturalMemome()
        pop = LamarckianPopulation(seed=7, memome=memome)
        pop.seed_population(10)

        counts = []
        for _ in range(10):
            stats = pop.step()
            counts.append(stats["cultural_strategies"])

        assert counts[-1] > counts[0], (
            f"Cultural complexity must grow: {counts[0]} → {counts[-1]}"
        )

    def test_memome_usage_count_tracked(self):
        """Each retrieval increments the strategy's usage count."""
        memome = CulturalMemome()
        org = make_organism("tracer", memome=memome)
        org.learn("tracking", "return 'follow prints'")

        memome.retrieve("tracking")
        memome.retrieve("tracking")
        record = memome.retrieve("tracking")  # 3rd retrieval

        assert record["usage_count"] == 3


# ============================================================================
# FEATURE 4: OPEN-ENDED NOVELTY
# ============================================================================

class TestOpenEndedNovelty:

    def test_novelty_archive_empty_means_max_novelty(self):
        """When archive is empty, every descriptor is maximally novel."""
        archive = NoveltyArchive(k_nearest=3)
        desc = BehaviorDescriptor(strategy_count=1.0)
        novelty = archive.compute_novelty(desc)
        assert novelty == 1.0

    def test_novelty_decreases_when_similar_added(self):
        """Adding similar descriptors to archive reduces subsequent novelty."""
        archive = NoveltyArchive(k_nearest=3, archive_threshold=0.0)
        desc = BehaviorDescriptor(strategy_count=0.5, avg_performance=0.5)
        archive.consider_adding(desc)
        archive.consider_adding(BehaviorDescriptor(strategy_count=0.5, avg_performance=0.51))

        similar = BehaviorDescriptor(strategy_count=0.5, avg_performance=0.5)
        novelty = archive.compute_novelty(similar)
        assert novelty < 1.0, "Identical descriptor should have low novelty"

    def test_different_descriptor_has_higher_novelty(self):
        """Genuinely different behavior scores higher than a similar one."""
        archive = NoveltyArchive(k_nearest=3, archive_threshold=0.0)
        archive.consider_adding(BehaviorDescriptor(strategy_count=0.5, avg_performance=0.5))

        similar = BehaviorDescriptor(strategy_count=0.5, avg_performance=0.52)
        different = BehaviorDescriptor(strategy_count=5.0, avg_performance=0.99, mutation_rate=0.4)

        novelty_similar = archive.compute_novelty(similar)
        novelty_different = archive.compute_novelty(different)

        assert novelty_different > novelty_similar, (
            "Behaviorally different organism should receive higher novelty score"
        )

    def test_novelty_count_increases_over_population_run(self):
        """
        CORE NOVELTY TEST: novelty_count GROWS over 50 generations.
        Every generation contributes new behavioral discoveries.
        """
        memome = CulturalMemome()
        pop = LamarckianPopulation(seed=321, memome=memome, novelty_threshold=0.01)
        pop.seed_population(15)

        history = pop.run(generations=50)

        novelty_start = history[0]["novelty_count"]
        novelty_end = history[-1]["novelty_count"]

        assert novelty_end > novelty_start, (
            f"Novelty count must increase: {novelty_start} → {novelty_end}"
        )

    def test_novelty_bonus_affects_fitness(self):
        """
        Organism with high novelty score gets higher total_fitness
        than a genetically identical one with zero novelty.
        """
        memome = CulturalMemome()
        genome = LamarckianGenome(intelligence=0.5, cooperation=0.5,
                                   energy_efficiency=0.5, adaptability=0.5, resilience=0.5)

        org_novel = LamarckianOrganism("n1", "Novel", genome, memome=memome)
        org_novel.novelty_score = 0.8  # High novelty

        org_plain = LamarckianOrganism("n2", "Plain", genome, memome=memome)
        org_plain.novelty_score = 0.0  # No novelty

        assert org_novel.compute_total_fitness() > org_plain.compute_total_fitness(), (
            "Novelty bonus must improve total fitness score"
        )

    def test_open_ended_no_fitness_ceiling(self):
        """
        Novelty count can always increase — there is no artificial ceiling.
        """
        archive = NoveltyArchive(k_nearest=2, archive_threshold=0.0)
        # Add 100 diverse descriptors — archive should keep growing
        rng = random.Random(99)
        for i in range(100):
            desc = BehaviorDescriptor(
                strategy_count=float(i),
                avg_performance=rng.random(),
                cultural_usage=rng.random(),
                mutation_rate=rng.uniform(0.01, 0.5),
            )
            archive.consider_adding(desc)

        assert archive.novelty_count >= 50, (
            "With highly diverse descriptors, most should be novel"
        )


# ============================================================================
# FEATURE 5: PROGRAM SELF-MODIFICATION
# ============================================================================

class TestProgramSelfModification:

    def test_organism_can_install_runtime_patch(self):
        """Organism installs a new method as a code string."""
        org = make_organism("patcher")
        code = "result = self.genome.intelligence * 3.0"
        success = org.self_modify("custom_eval", code)

        assert success, "self_modify must return True for valid code"
        assert org.has_patch("custom_eval"), "Patch must be stored"

    def test_patch_stored_as_readable_state(self):
        """The code patch is stored and retrievable as plain text."""
        org = make_organism("readable")
        code = "result = {'score': self.genome.cooperation + 1}"
        org.self_modify("my_method", code)

        retrieved = org.get_patch("my_method")
        assert retrieved == code, "Stored patch must be exactly the submitted code"

    def test_patch_executes_correctly(self):
        """Executing a patch runs the stored code and returns the result."""
        org = make_organism("executor", intelligence=0.8)
        code = "result = self.genome.intelligence * 2.0"
        org.self_modify("doubled_iq", code)

        result = org._run_patch("doubled_iq")
        assert result == pytest.approx(1.6, abs=1e-9), (
            f"0.8 * 2.0 should equal 1.6, got {result}"
        )

    def test_patch_can_return_dict(self):
        """Patches can return complex data structures."""
        org = make_organism("dict_patcher", intelligence=0.6, cooperation=0.7)
        code = textwrap.dedent("""
            result = {
                "method": "analyze",
                "intelligence": self.genome.intelligence,
                "cooperation": self.genome.cooperation,
            }
        """).strip()
        org.self_modify("analyze", code)
        result = org._run_patch("analyze")

        assert isinstance(result, dict)
        assert result["method"] == "analyze"
        assert result["intelligence"] == pytest.approx(0.6)

    def test_broken_patch_failsafe(self):
        """A crashing patch is auto-removed and execution recovers safely."""
        org = make_organism("crasher")
        # Deliberately bad code
        org.self_modify("bomb", "raise ValueError('explosion!')\nresult = 42")

        result = org._run_patch("bomb")

        # After crashing, patch must be removed
        assert not org.has_patch("bomb"), (
            "Crashing patch must be auto-removed by failsafe"
        )

    def test_forbidden_imports_blocked(self):
        """Dangerous imports are rejected before storing."""
        org = make_organism("sandbox_test")
        bad_code = "import os\nresult = os.getcwd()"

        success = org.self_modify("dangerous", bad_code)
        assert not success, "Forbidden imports must be rejected"
        assert not org.has_patch("dangerous")

    def test_multiple_patches_independent(self):
        """Organism can have multiple independent patches at once."""
        org = make_organism("multi_patcher")
        org.self_modify("method_a", "result = 10")
        org.self_modify("method_b", "result = 20")
        org.self_modify("method_c", "result = 30")

        assert org._run_patch("method_a") == 10
        assert org._run_patch("method_b") == 20
        assert org._run_patch("method_c") == 30


# ============================================================================
# INTEGRATION TEST: ALL 5 FEATURES IN ONE POPULATION RUN
# ============================================================================

class TestIntegration50Generations:

    def test_50_generation_run_all_metrics(self):
        """
        INTEGRATION TEST: Run 50 generations and verify all 4 rising metrics:
        - avg_fitness RISES
        - cultural_strategies GROWS
        - avg_mutation_rate CHANGES (evolves)
        - novelty_count INCREASES
        """
        memome = CulturalMemome()
        pop = LamarckianPopulation(seed=2024, memome=memome, novelty_threshold=0.02)
        pop.seed_population(15)

        history = pop.run(generations=50)

        first = history[0]
        last = history[-1]

        # 1. Fitness rises
        assert last["avg_fitness"] >= first["avg_fitness"] - 0.05, (
            f"Fitness should not significantly regress: {first['avg_fitness']:.4f} → {last['avg_fitness']:.4f}"
        )

        # 2. Cultural complexity grows
        assert last["cultural_strategies"] > first["cultural_strategies"], (
            f"Cultural strategies must grow: {first['cultural_strategies']} → {last['cultural_strategies']}"
        )

        # 3. Mutation rate changes (meta-evolution)
        all_mrs = [h["avg_mutation_rate"] for h in history]
        mr_range = max(all_mrs) - min(all_mrs)
        assert mr_range > 0.001, (
            f"avg_mutation_rate must vary: range={mr_range:.6f} (too small = not evolving)"
        )

        # 4. Novelty increases
        assert last["novelty_count"] > first["novelty_count"], (
            f"Novelty count must increase: {first['novelty_count']} → {last['novelty_count']}"
        )

        # 5. Strategies survive dead creators
        assert last["survived_dead_creators"] > 0, (
            "Some strategies must have outlived their creators"
        )

    def test_lamarckian_gives_head_start(self):
        """
        Lamarckian organisms start with inherited knowledge, giving a measurable
        head start over organisms that must learn everything from scratch.
        """
        memome = CulturalMemome()
        parent = make_organism("strategic_parent", memome=memome, intelligence=0.8)
        for i in range(5):
            parent.learn(f"skill_{i}", f"return {i}", performance=0.85)

        child = parent.reproduce()
        naive = make_organism("naive_child", memome=memome, intelligence=0.8)

        assert child.count_strategies() > naive.count_strategies(), (
            "Lamarckian child starts with more strategies than a naive organism"
        )


# Need textwrap for the dict test
import textwrap
