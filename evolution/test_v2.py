from __future__ import annotations

import importlib.util
import random

import pytest

from evolution.ancestry_credit import AncestryCredit, GenerationSnapshot
from evolution.constitution import EvolutionConstitution
from evolution.dsl import DSLGenome
from evolution.embodied import EmbodiedOrganism
from evolution.federated_memome import FederatedMemome
from evolution.goal_synthesis import EnvironmentState, GoalSynthesizer
from evolution.morphogenome import Morphogenome
from evolution.red_team import DefenseLayer, RedTeamOrganism
from evolution.thermodynamic import EnergyBudget, ThermodynamicFitness


def test_constitution_is_mutable_and_seeded_regimes_diverge():
    initial = EvolutionConstitution()
    left = initial.mutate(random.Random(1))
    right = initial.mutate(random.Random(2))
    assert left != initial
    assert right != initial
    assert left.to_code() != right.to_code()


def test_constitution_can_diverge_over_one_hundred_generations():
    first = EvolutionConstitution()
    second = EvolutionConstitution()
    for generation in range(100):
        first = first.mutate(random.Random(1000 + generation))
        second = second.mutate(random.Random(2000 + generation))
    assert first != second
    assert first.to_code() != second.to_code()


def test_morphogenome_grows_importable_parent_module():
    source = Morphogenome().grow_module("A", complexity=2)
    spec = importlib.util.spec_from_loader("module_A", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, "module_A.py", "exec"), module.__dict__)
    assert hasattr(module, "solve_A")
    assert module.solve_A(3) is not None


def test_morphogenome_graft_contains_both_parent_signatures():
    parent_a = Morphogenome(templates=("alpha",))
    parent_b = Morphogenome(templates=("beta",))
    child = parent_a.graft(parent_b)
    assert "alpha" in child.templates
    assert "beta" in child.templates


def test_defense_rejects_import_and_accepts_small_strategy():
    defense = DefenseLayer()
    assert defense.validate_strategy("import os\ndef run(x):\n    return x").accepted is False
    assert defense.validate_strategy("def run(x):\n    return x + 1").accepted is True


def test_red_team_attack_is_detectable():
    attacker = RedTeamOrganism(organism_id="predator")
    target = RedTeamOrganism(organism_id="prey")
    initial_strength = 0.2
    result = attacker.attack(target)
    assert result.detected is True
    assert target.defense.immune_strength > initial_strength


def test_intrinsic_goal_rewards_surprise_and_is_inherited():
    synthesizer = GoalSynthesizer()
    synthesizer.observe(EnvironmentState(coordinates=(0, 0), features={"coverage": 0.1}))
    synthesizer.observe(EnvironmentState(coordinates=(1, 0), features={"coverage": 0.2}))
    goal = synthesizer.synthesize_goal()
    assert goal(EnvironmentState(coordinates=(2, 0), features={"coverage": 0.3})) >= 0
    child = synthesizer.evolve_goal(GoalSynthesizer())
    assert child.goal_parameters == synthesizer.goal_parameters


def test_federated_memome_spreads_one_strategy_to_three_nodes():
    nodes = [FederatedMemome(node_id=f"node-{i}") for i in range(3)]
    nodes[0].publish(
        name="alpha",
        source_code="def alpha(x):\n    return x",
        descriptor="identity",
        effectiveness=0.9,
        author_id="a",
        generation=0,
    )
    for _ in range(5):
        nodes[0].gossip(nodes[1])
        nodes[1].gossip(nodes[2])
        nodes[2].gossip(nodes[0])
    assert all(any(strategy.name == "alpha" for strategy in node.strategies()) for node in nodes)
    assert nodes[0].influence_score("alpha") == pytest.approx(1.0)


def test_embodied_python_tool_records_result():
    organism = EmbodiedOrganism(organism_id="tool")
    result = organism.use_tool("python_exec", code="print(3 * 3)")
    assert result == "9"
    assert organism.tool_history[-1]["tool"] == "python_exec"


def test_ancestry_credit_rewards_used_ancestor_strategy():
    credit = AncestryCredit()
    memome = FederatedMemome(node_id="credit-node")
    strategy = memome.publish(
        name="alpha",
        source_code="def alpha(x):\n    return x",
        descriptor="identity",
        effectiveness=0.8,
        author_id="ancestor",
        generation=0,
    )
    champion = type(
        "Champion",
        (),
        {"object_id": "champion", "learned_strategies": {strategy.strategy_id: strategy}},
    )()
    snapshots = [
        GenerationSnapshot(generation=0, organisms=({"strategy_ids": [strategy.strategy_id]},)),
        GenerationSnapshot(generation=1, organisms=({"strategy_ids": [strategy.strategy_id]},)),
        GenerationSnapshot(generation=2, organisms=({"strategy_ids": [strategy.strategy_id]},)),
    ]
    scores = credit.attribute(champion, memome, snapshots)
    assert scores[strategy.strategy_id] > 0


def test_dsl_vocabulary_grows_and_compound_strategy_round_trips():
    genome = DSLGenome()
    initial = len(genome.vocabulary)
    for seed in range(20):
        genome = genome.mutate(random.Random(seed))
    source = genome.express({"condition": "high", "action": "coop", "fallback": "defect"})
    assert len(genome.vocabulary) > initial
    assert genome.parse(source)["action"] == "coop"


def test_energy_budget_binds_and_efficiency_prefers_lower_cost():
    budget = EnergyBudget(initial=2.5)
    assert budget.can_afford("strategy_call") is True
    budget.spend("strategy_call")
    budget.spend("strategy_call")
    assert budget.can_afford("strategy_call") is False
    fitness = ThermodynamicFitness()
    efficient = fitness.measure(None, lambda: (0.8, 10, 10))
    wasteful = fitness.measure(None, lambda: (0.9, 1000, 1000))
    assert efficient.efficiency > wasteful.efficiency
