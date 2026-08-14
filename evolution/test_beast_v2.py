from __future__ import annotations

import random
from types import SimpleNamespace

import pytest

from evolution.beast_v2 import (
    DefenseLayer,
    EnvironmentState,
    EvolutionConstitution,
    GoalSynthesizer,
    Morphogenome,
    RedTeamOrganism,
)
from evolution.beast_v2_culture import (
    AncestryCredit,
    DSLGenome,
    EmbodiedOrganism,
    EnergyBudget,
    FederatedMemome,
    GenerationSnapshot,
    ThermodynamicFitness,
    register_builtin_tools,
)
from evolution.beast_v2_runtime import BeastOrganism


def test_constitution_is_serializable_and_mutable() -> None:
    parent = EvolutionConstitution()
    child = parent.mutate(random.Random(7))
    assert parent.to_dict().keys() == child.to_dict().keys()
    assert child.crossover_strategy in parent.CROSSOVER_STRATEGIES
    assert child.mutation_distribution in parent.MUTATION_DISTRIBUTIONS
    assert parent.diff(child) or child == parent


def test_constitution_code_is_valid_and_contains_rule_values() -> None:
    constitution = EvolutionConstitution(selection_pressure=0.8, novelty_weight=0.2)
    source = constitution.to_code()
    compile(source, "<constitution>", "exec")
    assert "0.80000000" in source
    assert "0.20000000" in source


def test_morphogenome_grows_valid_module_with_requested_complexity() -> None:
    source = Morphogenome().grow_module("bridge signal", complexity=4)
    compile(source, "<grown>", "exec")
    assert source.count("value =") >= 5


def test_morphogenome_grafts_and_mutates_vocabulary() -> None:
    left = Morphogenome(templates=("identity",), operators=("add",))
    right = Morphogenome(templates=("scale",), operators=("compose",))
    grafted = left.graft(right)
    mutated = grafted.mutate(random.Random(2))
    assert "scale" in grafted.templates
    assert len(mutated.templates) >= len(grafted.templates)


def test_defense_accepts_safe_strategy() -> None:
    result = DefenseLayer().validate_strategy("def act(x):\n    return x + 1")
    assert result.accepted is True
    assert result.fingerprint


@pytest.mark.parametrize(
    "source",
    [
        "import os\n\ndef act(x):\n    return os.getcwd()",
        "def act(x):\n    return eval(x)",
        "def act(x):\n    return x.__class__",
        "def act(x):\n    return open(x).read()",
    ],
)
def test_defense_rejects_dangerous_strategy(source: str) -> None:
    result = DefenseLayer().validate_strategy(source)
    assert result.accepted is False
    assert result.risk_flags


def test_red_team_attack_is_detected_and_immune_strength_adapts() -> None:
    target = BeastOrganism("target")
    before = target.defense.immune_strength
    attack = RedTeamOrganism("attacker").attack(target)
    target.record_attack(attack)
    assert attack.detected is True
    assert target.defense.immune_strength > before
    assert target.defense_events[0]["detected"] is True


def test_goal_synthesizer_rewards_unvisited_state() -> None:
    synthesizer = GoalSynthesizer()
    synthesizer.observe(EnvironmentState((0, 0), {"resource": 0.1}, 0.1))
    synthesizer.observe(EnvironmentState((0, 1), {"resource": 0.2}, 0.2))
    goal = synthesizer.synthesize_goal()
    unseen = goal(EnvironmentState((8, 8), {"resource": 1.0}, 1.0))
    seen = goal(EnvironmentState((0, 0), {"resource": 0.1}, 0.1))
    assert unseen > seen


def test_goal_parameters_are_inherited_by_child_synthesizer() -> None:
    parent = GoalSynthesizer(goal_parameters={"coverage_weight": 0.8})
    child = GoalSynthesizer()
    parent.evolve_goal(child)
    assert child.goal_parameters["coverage_weight"] == 0.8
    assert child.to_dict()["observations"] == 0


def test_beast_organism_grows_and_inherits_code_and_goals() -> None:
    parent = BeastOrganism("parent")
    parent.observe({"coordinates": (1,), "features": {"signal": 0.9}, "outcome": 0.8})
    parent.grow("bridge", complexity=3)
    child = parent.reproduce(random.Random(4))
    assert child.parent_ids == ("parent",)
    assert child.learned_modules == parent.learned_modules
    assert child.goal_synthesizer.to_dict()["visited_states"] == 1
    assert child.generation == 1


def _strategy(node: FederatedMemome, name: str, quality: float):
    return node.publish(
        name=name,
        source_code=f"def {name}(x):\n    return {quality}",
        descriptor=name,
        effectiveness=quality,
        author_id=node.node_id,
        generation=0,
    )


def test_federated_memome_gossip_propagates_strategy() -> None:
    left, right = FederatedMemome("left"), FederatedMemome("right")
    try:
        strategy = _strategy(left, "bridge", 0.8)
        assert right.get(strategy.strategy_id) is None
        assert right.gossip(left) >= 1
        assert right.get(strategy.strategy_id) == strategy
    finally:
        left.close()
        right.close()


def test_federated_memome_conflict_prefers_higher_effectiveness() -> None:
    left, right = FederatedMemome("left"), FederatedMemome("right")
    try:
        stable_source = "def same(x):\n    return 1"
        strong = left.publish(
            name="same",
            source_code=stable_source,
            descriptor="same",
            effectiveness=0.9,
            author_id="left",
            generation=0,
        )
        weak = right.publish(
            name="same",
            source_code=stable_source,
            descriptor="same",
            effectiveness=0.2,
            author_id="right",
            generation=0,
        )
        assert strong.strategy_id == weak.strategy_id
        left.gossip(right)
        assert right.get(strong.strategy_id).effectiveness == 0.9
    finally:
        left.close()
        right.close()


def test_federated_memome_exposes_lineage_graph_and_dot() -> None:
    node = FederatedMemome("node")
    try:
        parent = _strategy(node, "parent", 0.5)
        node.publish(
            name="child",
            source_code="def child(x):\n    return x",
            descriptor="child",
            effectiveness=0.7,
            author_id="node",
            generation=1,
            parent_ids=(parent.strategy_id,),
        )
        assert len(node.lineage_graph().nodes()) == 2
        assert "digraph" in node.to_dot()
    finally:
        node.close()


def test_embodied_python_tool_is_allowlisted() -> None:
    register_builtin_tools()
    organism = EmbodiedOrganism("embodied")
    assert organism.use_tool("python_exec", code="print(2 + 3)") == "5"
    with pytest.raises(PermissionError):
        organism.use_tool("shell_cmd", cmd="rm -rf /")


def test_embodied_tool_strategy_is_descriptive_and_auditable() -> None:
    register_builtin_tools()
    organism = EmbodiedOrganism("embodied")
    strategy = organism.evolve_tool_strategy("python_exec")
    assert "validated arguments" in strategy
    assert organism.tool_history == []


def test_ancestry_credit_rewards_reused_ancestor_strategy() -> None:
    node = FederatedMemome("ancestor")
    try:
        strategy = _strategy(node, "bridge", 0.8)
        champion = SimpleNamespace(object_id="champion", learned_strategies={strategy.strategy_id: strategy})
        history = [
            GenerationSnapshot(0, ({"strategy_ids": [strategy.strategy_id]},)),
            GenerationSnapshot(1, ({"strategy_ids": [strategy.strategy_id]},)),
        ]
        credit = AncestryCredit().attribute(champion, node, history)
        assert credit[strategy.strategy_id] > 0
    finally:
        node.close()


def test_dsl_expresses_and_parses_intent() -> None:
    genome = DSLGenome()
    source = genome.express({"condition": "high", "action": "coop", "fallback": "defect"})
    assert genome.parse(source) == {"condition": "high", "action": "coop", "fallback": "defect"}


def test_dsl_vocabularly_grows_across_generations() -> None:
    genome = DSLGenome()
    for _ in range(50):
        genome = genome.mutate(random.Random(_))
    assert len(genome.vocabulary) >= 55
    assert "compound" in genome.grammar_rules


def test_dsl_crossover_preserves_both_parent_vocabularies() -> None:
    left = DSLGenome().mutate(random.Random(1))
    right = DSLGenome().mutate(random.Random(2)).mutate(random.Random(3))
    child = left.crossover(right)
    assert set(left.vocabulary).issubset(child.vocabulary)
    assert set(right.vocabulary).issubset(child.vocabulary)


def test_energy_budget_exhausts_and_rejects_unaffordable_action() -> None:
    budget = EnergyBudget(1.0)
    budget.spend("strategy_call")
    assert not budget.can_afford("strategy_call")
    with pytest.raises(RuntimeError):
        budget.spend("strategy_call")


def test_thermodynamic_fitness_rewards_quality_per_operation() -> None:
    cheap = ThermodynamicFitness().measure(object(), lambda: (0.8, 10, 2), budget=100)
    expensive = ThermodynamicFitness().measure(object(), lambda: (0.9, 1000, 2), budget=100)
    assert cheap.efficiency > expensive.efficiency
    assert expensive.affordable is False


def test_thermodynamic_budget_can_kill_low_energy_organism() -> None:
    organism = SimpleNamespace(energy=1.0, dead=False)
    score = ThermodynamicFitness().measure(organism, lambda: (0.8, 1000, 4), budget=1000)
    assert score.affordable is True
    assert organism.dead is True
