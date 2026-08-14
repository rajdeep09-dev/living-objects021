from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np
import pytest

from evolution.archaeology import ExtinctStrategy, KnowledgeArchaeologist
from evolution.beast_v2 import RedTeamOrganism
from evolution.beast_v2_culture import Strategy
from evolution.epistemic import EpistemicState, UncertaintyAwareEvolution
from evolution.immunity import CivilizationImmunity
from evolution.lamarckian import LamarckianGenome
from evolution.memory_palace import MemoryPalace
from evolution.morphogenetic_ai import MorphogeneticProgram
from evolution.physics import CausalityLaw, FormalSafetyProof, ParallelUniverse, UniversePhysics
from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse
from evolution.substrate import SubstrateExporter
from evolution.temporal import TemporalRevisionEngine
from evolution.tournament import EvolutionaryTournament, MatchResult, TournamentResult
from evolution.turing import OrganismTuringMachine
from evolution.writing_system import Context, StrategyIntent, WritingSystem


@dataclass
class Organism:
    object_id: str
    generation: int = 0
    fitness: float = 0.5
    behavior_descriptors: dict[str, str] = field(default_factory=dict)
    learned_strategies: dict[str, Strategy] = field(default_factory=dict)
    resurrected_strategies: list[str] = field(default_factory=list)
    token_wallet: object | None = None

    def install_strategy(self, strategy: Strategy | str) -> bool:
        if isinstance(strategy, str):
            self.behavior_descriptors[strategy] = strategy
            return True
        self.learned_strategies[strategy.strategy_id] = strategy
        self.behavior_descriptors[strategy.name] = strategy.descriptor
        return True

    def learn(self, _name: str, _source: str) -> bool:
        return True


def strategy(name: str, effectiveness: float = 0.8, source: str | None = None) -> Strategy:
    return Strategy(
        strategy_id=f"s-{name}",
        name=name,
        source_code=source or "return 1",
        descriptor=name,
        effectiveness=effectiveness,
        author_id="tester",
        generation=0,
    )


def test_physics_default_laws_have_named_invariants() -> None:
    physics = UniversePhysics()
    assert {law.name for law in physics.laws} == {"conservation_of_tokens", "causality", "entropy_gradient", "information_limit"}
    assert physics.fingerprint()


def test_physics_application_produces_invariant_snapshot() -> None:
    left, right = Organism("left", generation=2), Organism("right", generation=1)
    left.behavior_descriptors["a"] = "cooperate"
    right.behavior_descriptors["b"] = "explore"
    ecosystem = type("Ecosystem", (), {"generation": 2})()
    physics = UniversePhysics()
    physics.apply(ecosystem, [left, right])
    snapshot = physics.invariant_snapshot([left, right])
    assert snapshot["generations_monotonic"] and snapshot["law_count"] == 4
    assert ecosystem.diversity == 2


def test_physics_law_mutation_requires_formal_proof() -> None:
    physics = UniversePhysics()
    organism = Organism("law-maker")
    rejected = physics.propose_law_mutation(organism, CausalityLaw("new_causality"), FormalSafetyProof("", False))
    accepted = physics.propose_law_mutation(organism, CausalityLaw("new_causality"), FormalSafetyProof("generation monotonicity", True))
    assert not rejected and accepted and organism.physics_credits == 1
    assert physics.mutation_history[-1]["law"] == "new_causality"


def test_parallel_universe_branch_preserves_parent_and_diverges() -> None:
    parent = ParallelUniverse()
    child = parent.branch(CausalityLaw("alternate_causality"))
    assert child.parent_universe is parent
    assert child.branch_generation == 1
    assert child.divergence_score > 0
    assert child.observe()["parent_id"] == parent.universe_id


@pytest.mark.parametrize("law_name", ["conservation_of_tokens", "causality", "entropy_gradient", "information_limit"])
def test_physics_law_lookup_is_stable(law_name: str) -> None:
    assert getattr(UniversePhysics(), law_name).name == law_name


def test_temporal_revision_follows_causal_chain() -> None:
    ancestor, child = Organism("ancestor"), Organism("child", generation=1)
    engine = TemporalRevisionEngine([ancestor, child], {"ancestor": None, "child": "ancestor"})
    proposal = engine.propose_revision(child, "ancestor", "return 2", "retro-coordination")
    result = engine.apply_revision(proposal)
    assert result.applied and result.affected_organisms == 2
    assert "retro-coordination" in ancestor.temporal_revisions


def test_temporal_revision_rejects_unknown_ancestor() -> None:
    engine = TemporalRevisionEngine([Organism("child")], {"child": None})
    with pytest.raises(ValueError, match="causal chain"):
        engine.propose_revision(engine.organisms["child"], "missing", "return 1", "x")


def test_temporal_revision_rejects_budget_overrun() -> None:
    organisms = [Organism(f"o{i}") for i in range(4)]
    lineage = {"o0": None, "o1": "o0", "o2": "o1", "o3": "o2"}
    engine = TemporalRevisionEngine(organisms, lineage, butterfly_budget=2)
    with pytest.raises(ValueError, match="butterfly budget"):
        engine.propose_revision(organisms[-1], "o0", "return 1", "too-far")


def test_temporal_revision_flags_self_revision_as_paradox() -> None:
    organism = Organism("same")
    engine = TemporalRevisionEngine([organism], {"same": None})
    proposal = engine.propose_revision(organism, "same", "return 1", "self")
    assert engine.revision_paradox_check(proposal)
    assert engine.apply_revision(proposal).paradox


def accepting_machine() -> OrganismTuringMachine:
    return OrganismTuringMachine(
        transition_table={("q0", "_"): ("accept", "_", "S")},
    )


def test_turing_machine_accepts_within_bound() -> None:
    result = accepting_machine().run("_", step_limit=3)
    assert result.halted and result.accepted and result.steps_used == 1


def test_turing_machine_rejects_missing_transition() -> None:
    result = OrganismTuringMachine().run("1")
    assert result.halted and not result.accepted


def test_turing_machine_respects_step_limit() -> None:
    machine = OrganismTuringMachine(transition_table={("q0", "_"): ("q0", "_", "S")})
    result = machine.run("_", step_limit=4)
    assert not result.halted and result.steps_used == 4


def test_turing_machine_rejects_invalid_limits_and_directions() -> None:
    with pytest.raises(ValueError):
        accepting_machine().run("_", step_limit=0)
    machine = OrganismTuringMachine(transition_table={("q0", "_"): ("accept", "_", "X")})
    with pytest.raises(ValueError, match="direction"):
        machine.run("_")


def test_turing_machine_can_simulate_another_machine() -> None:
    result = accepting_machine().simulate_organism(accepting_machine())
    assert result.simulated and result.reason == "bounded self-simulation"


def test_turing_complexity_and_universality_are_measurable() -> None:
    machine = accepting_machine()
    assert machine.kolmogorov_complexity() > 0
    assert 0 < machine.universality_score() <= 1


def test_immunity_donation_clamps_and_indexes_antibody() -> None:
    registry = CivilizationImmunity(max_antibodies=2)
    antibody_id = registry.donate_defense(Organism("donor", generation=3), "attack", "reject", 4.0)
    assert len(antibody_id) == 20
    assert registry.antibodies()[0]["effectiveness"] == 1.0


def test_immunity_prefers_more_effective_duplicate() -> None:
    registry = CivilizationImmunity()
    registry.donate_defense(Organism("a"), "same", "weak", 0.2)
    registry.donate_defense(Organism("b"), "same", "strong", 0.8)
    assert registry.antibodies()[0]["defense"] == "strong"


def test_immunity_pre_immunizes_newborn() -> None:
    registry = CivilizationImmunity()
    registry.donate_defense(Organism("a"), "one", "guard", 0.9)
    newborn = Organism("newborn")
    assert registry.pre_immunize(newborn) == 1
    assert registry.antibodies()[0]["usage_count"] == 1


def test_immunity_evolves_predictive_variants() -> None:
    registry = CivilizationImmunity(max_antibodies=4)
    registry.donate_defense(Organism("a"), "one", "guard", 0.9)
    assert registry.evolve_antibodies() == 1
    assert len(registry.antibodies()) == 2


@pytest.mark.parametrize("attack", ["novel", "prompt-injection", "tamper"])
def test_immunity_logs_novel_attacks(attack: str) -> None:
    registry = CivilizationImmunity()
    assert registry.detect_novel_attack(attack)
    assert registry.attack_log[-1]["pattern"] == attack


def test_epistemic_update_shrinks_uncertainty() -> None:
    state = EpistemicState()
    before = state.fitness_belief.variance
    state.update_belief(0.9, 0.8)
    assert state.fitness_belief.mean > 0.5 and state.fitness_belief.variance < before


@pytest.mark.parametrize("alpha", [0.5, 0.9, 0.95])
def test_epistemic_confidence_interval_is_bounded(alpha: float) -> None:
    low, high = EpistemicState().confidence_interval(alpha)
    assert 0 <= low <= high <= 1


def test_epistemic_exploration_bonus_is_bounded() -> None:
    assert 0 <= EpistemicState().exploration_bonus() <= 0.5


def test_uncertainty_aware_evolution_protects_wide_beliefs() -> None:
    organism = Organism("uncertain", generation=4)
    organism.epistemic_state = EpistemicState()
    policy = UncertaintyAwareEvolution(grace_generations=2, ci_width_threshold=0.1)
    assert policy.should_protect(organism)
    organism.generation = 5
    assert policy.should_protect(organism)


def test_memory_palace_embeddings_are_deterministic() -> None:
    first, second = strategy("same"), strategy("same")
    palace = MemoryPalace(dimension=8)
    assert np.allclose(palace.embed(first), palace.embed(second))


def test_memory_palace_adds_entries_and_reports_snapshot() -> None:
    palace = MemoryPalace(dimension=8)
    palace.add(strategy("a"))
    palace.add(strategy("b"))
    snapshot = palace.snapshot()
    assert snapshot["strategies"] == 2 and snapshot["dimension"] == 8


def test_memory_palace_nearest_neighbors_excludes_query_identity() -> None:
    palace = MemoryPalace(dimension=8)
    query = strategy("query")
    palace.add(strategy("other"))
    neighbors = palace.nearest_neighbors(query, k=2)
    assert neighbors and neighbors[0][0].name == "other"


def test_memory_palace_navigate_requires_nonzero_direction() -> None:
    palace = MemoryPalace(dimension=8)
    palace.add(strategy("anchor"))
    with pytest.raises(ValueError):
        palace.navigate(Organism("navigator"), np.zeros(8))


def test_memory_palace_creates_named_rooms_and_clusters() -> None:
    palace = MemoryPalace(dimension=8)
    center = strategy("center")
    palace.add(center)
    room = palace.create_room("coordination", center)
    assert room.name == "coordination" and palace.cluster_count() >= 1


def test_tournament_empty_round_robin_is_a_valid_generation() -> None:
    result = EvolutionaryTournament().round_robin(1)
    assert result.generation == 1 and result.matches == ()


def test_tournament_elo_update_moves_winner_up() -> None:
    tournament = EvolutionaryTournament()
    match = MatchResult("attacker", "defender", True, False, False, 0.0, 1)
    tournament.update_elo(TournamentResult(1, (match,), 1, 0, 0))
    assert tournament.elo_registry["attacker"] > tournament.elo_registry["defender"]


def test_tournament_hall_of_fame_orders_by_wins() -> None:
    tournament = EvolutionaryTournament()
    tournament.championship_history = [
        TournamentResult(2, (), 1, 0, 0),
        TournamentResult(1, (), 3, 0, 0),
    ]
    assert tournament.hall_of_fame(1)[0].generation == 1


def test_morphogenetic_program_divides_seed_neurons() -> None:
    program = MorphogeneticProgram([{"type": "divide", "condition": "always", "parameters": {}}], max_neurons=4)
    genome = program.develop(LIFNeuron(0), steps=2)
    assert len(genome.neurons) >= 2


def test_morphogenetic_program_connects_without_self_edges() -> None:
    program = MorphogeneticProgram([
        {"type": "divide", "condition": "always", "parameters": {}},
        {"type": "connect", "condition": "always", "parameters": {"weight": 0.4}},
    ])
    genome = program.develop(LIFNeuron(0), steps=2)
    assert all(edge.source != edge.target for edge in genome.synapses)


def test_morphogenetic_apoptosis_renumbers_survivors() -> None:
    program = MorphogeneticProgram([
        {"type": "divide", "condition": "always", "parameters": {}},
        {"type": "apoptosis", "condition": "always", "parameters": {}},
    ])
    genome = program.develop(LIFNeuron(0), steps=2)
    assert [neuron.neuron_id for neuron in genome.neurons] == list(range(len(genome.neurons)))


def test_morphogenetic_empty_mutation_inserts_instruction() -> None:
    mutated = MorphogeneticProgram().mutate_instruction(random.Random(2))
    assert mutated.instructions


def test_morphogenetic_crossover_preserves_caps_and_complexity() -> None:
    left = MorphogeneticProgram([{"kind": "divide", "parameters": {}}], max_neurons=5)
    right = MorphogeneticProgram([{"kind": "connect", "parameters": {}}], max_neurons=7)
    child = left.crossover(right)
    assert child.max_neurons == 5 and child.complexity() >= 1


def test_writing_system_round_trips_strategy_intent() -> None:
    system = WritingSystem()
    text = system.write(StrategyIntent("observe", {"confidence": 0.8}))
    decoded = system.read(text)
    assert decoded.action == "observe" and decoded.parameters["confidence"] == 0.8


def test_writing_system_handles_urgent_context() -> None:
    system = WritingSystem()
    text = system.write(StrategyIntent("cooperate"), Context({"mood": "urgent"}))
    assert system.read(text).action == "cooperate"


def test_writing_system_grows_vocabulary_lazily() -> None:
    system = WritingSystem()
    before = system.vocabulary_size
    system.write(StrategyIntent("new-concept"))
    assert system.vocabulary_size == before + 1


def test_writing_system_evolution_records_generation() -> None:
    child = WritingSystem().evolve(random.Random(4))
    assert child.generation == 1 and child.vocabulary_size >= 3


def test_writing_system_translation_preserves_known_meaning() -> None:
    source, target = WritingSystem(), WritingSystem()
    text = source.write(StrategyIntent("observe"))
    assert target.read(source.translate(text, target)).action == "observe"


def test_writing_system_grammar_has_three_layers() -> None:
    assert len(WritingSystem().grammar.layers) == 3


def substrate_organism() -> Organism:
    organism = Organism("Champion/42")
    organism.spiking_genome = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1)], [Synapse(0, 1, 0.3)])
    return organism


def test_substrate_exporter_emits_wasm() -> None:
    artifact = SubstrateExporter().export_wasm(substrate_organism())
    assert artifact[:4] == b"\x00asm"


def test_substrate_exporter_sanitizes_container_name() -> None:
    spec = SubstrateExporter().export_container(substrate_organism())
    assert spec.image == "living-objects/champion-42:v4" and "no-new-privileges" in spec.security


def test_substrate_exporter_emits_hardware_circuit() -> None:
    circuit = SubstrateExporter().export_circuit(substrate_organism())
    assert "module living_object" in circuit.source and "spike_0" in circuit.source


def test_substrate_breadth_is_complete_for_spiking_organism() -> None:
    assert SubstrateExporter().fitness_substrate_breadth(substrate_organism()) == 1.0


def test_measurement_adapter_returns_legacy_genome() -> None:
    from evolution.quantum_genome import QuantumGenome

    measured = QuantumGenome({"mutation_rate:0.1": 1 + 0j}).measure(random.Random(1))
    assert isinstance(measured, LamarckianGenome) and measured.mutation_rate == 0.1
