"""Executable proofs for the BEAST cellular-foundation runtime."""
from __future__ import annotations

import random

import pytest

from evolution.cellular import (
    ACTION_UNIVERSE,
    AdaptiveCell,
    CellAction,
    CellGenome,
    CellPolicy,
    CellSensors,
    CellWorld,
    evaluate_cell,
)
from evolution.cellular_eval import (
    CellImprovementGate,
    EvaluatorCell,
    ExternalTruthLayer,
)
from evolution.tissue import Tissue


def _prefer(cell: AdaptiveCell, world: CellWorld, action: CellAction, *, tissue: Tissue | None = None) -> None:
    """Set one deterministic test action while preserving the runtime learner."""

    sensors = tissue.sense(cell) if tissue is not None else cell.sense(world)
    row = cell.policy._row(sensors.key())
    row[action] = 8.0


def test_cell_learns_from_actual_harvest_outcome_and_inherits_policy_memory():
    """A real harvest changes policy value and a child retains learned state."""

    world = CellWorld(seed=11, width=5, height=5, resource_sites=0, hazard_sites=0)
    world.resource_map = {(2, 2): 1}
    parent = AdaptiveCell(position=(2, 2))
    _prefer(parent, world, CellAction.HARVEST)
    state = parent.sense(world).key()
    before = parent.policy._row(state)[CellAction.HARVEST]

    outcome = parent.step(world, random.Random(3))
    assert outcome.harvested == 1
    assert parent.carried_resource == 1
    assert parent.policy._row(state)[CellAction.HARVEST] != before

    child = parent.reproduce(random.Random(4), home=world.home)
    assert child.parent_id == parent.cell_id
    assert state in child.policy.values
    assert child.policy.values[state] == parent.policy.values[state]


def test_cell_action_capabilities_are_bounded_mutable_and_inherited():
    required = {"signal_alarm", "coordinate_with_neighbour", "cache_resource", "predict_hazard"}
    assert len(ACTION_UNIVERSE) >= 10
    assert required.issubset(ACTION_UNIVERSE)
    parent = AdaptiveCell(genome=CellGenome(action_capabilities=frozenset({
        "move_north", "move_south", "move_west", "move_east",
    })))
    children = [parent.reproduce(random.Random(seed), home=(0, 0)) for seed in range(20, 35)]
    assert all(child.genome.action_capabilities <= ACTION_UNIVERSE for child in children)
    assert all(
        len(child.genome.action_capabilities.symmetric_difference(parent.genome.action_capabilities)) == 1
        for child in children
    )
    assert any(child.genome.action_capabilities != parent.genome.action_capabilities for child in children)


def test_world_rejects_action_that_is_absent_from_cell_capabilities():
    world = CellWorld(seed=18, width=5, height=5, resource_sites=0, hazard_sites=0)
    world.hazard_map = {(1, 1): 1}
    cell = AdaptiveCell(position=(1, 1))
    assert CellAction.REPAIR.value not in cell.genome.action_capabilities
    outcome = world.apply(cell, CellAction.REPAIR)
    assert not outcome.accepted
    assert outcome.note == "capability_unavailable"


def test_cell_world_enforces_energy_and_lifetime_bounds():
    """A cell cannot act indefinitely or obtain energy without environmental action."""

    world = CellWorld(seed=12, width=5, height=5, resource_sites=0, hazard_sites=0)
    cell = AdaptiveCell(position=world.home, energy=0.34, max_energy=24.0, max_age=100)
    _prefer(cell, world, CellAction.WAIT)

    outcome = cell.step(world, random.Random(5))
    assert outcome.energy_delta < 0
    assert cell.energy == 0.0
    assert not cell.alive
    assert cell.step(world, random.Random(6)).accepted is False
    with pytest.raises(RuntimeError):
        cell.reproduce(random.Random(7), home=world.home)


def test_evaluator_cells_learn_probe_values_but_cannot_promote_an_unchanged_policy():
    """Self-scoring is insufficient: equal policies fail a disjoint holdout gate."""

    baseline = AdaptiveCell()
    candidate = AdaptiveCell.from_state(baseline.to_state())
    evaluator = EvaluatorCell("evaluator-proof")
    truth = ExternalTruthLayer(holdout_seeds=(901, 902, 903), ticks=25, minimum_improvement=0.01)
    gate = CellImprovementGate(truth_layer=truth, train_seeds=(1, 2, 3, 4), probe_budget=3, ticks=25)

    decision = gate.compare(
        baseline=baseline,
        candidate=candidate,
        evaluator=evaluator,
        rng=random.Random(9),
    )
    assert not decision.promoted
    assert decision.measurement.seeds == (901, 902, 903)
    assert set(evaluator.probe_values).issubset({1, 2, 3, 4})
    assert "holdout" in decision.reason


def test_truth_layer_rejects_training_holdout_overlap():
    """No evaluator curriculum may inspect a truth-layer seed."""

    truth = ExternalTruthLayer(holdout_seeds=(77,), ticks=10)
    with pytest.raises(ValueError, match="disjoint"):
        CellImprovementGate(truth_layer=truth, train_seeds=(10, 77), ticks=10)


def test_tissue_signal_produces_delayed_credit_only_after_real_neighbor_harvest():
    """A resource broadcast earns credit only when another cell actually harvests it."""

    world = CellWorld(seed=13, width=5, height=5, resource_sites=0, hazard_sites=0)
    world.resource_map = {(2, 1): 1}
    deterministic_genome = CellGenome(
        exploration_rate=0.0,
        action_capabilities=frozenset({
            "move_north", "move_south", "move_west", "move_east", "harvest", "broadcast",
        }),
    )
    broadcaster = AdaptiveCell(
        cell_id="a-broadcaster", position=(2, 1), genome=deterministic_genome
    )
    worker = AdaptiveCell(
        cell_id="b-worker", position=(2, 0), genome=deterministic_genome
    )
    tissue = Tissue(world=world, cells=[broadcaster, worker], signal_radius=3)

    _prefer(broadcaster, world, CellAction.BROADCAST, tissue=tissue)
    # After the first cell publishes its signal, the worker has a different
    # sensor key and learns the action sequence toward the evidence.
    post_broadcast = CellSensors(0, 0, 1, 3, 0, signal_bucket=1, signal_direction=2)
    worker.policy._row(post_broadcast.key())[CellAction.MOVE_SOUTH] = 8.0
    after_move = CellSensors(1, 0, 1, 3, 0, signal_bucket=1, signal_direction=0)
    worker.policy._row(after_move.key())[CellAction.HARVEST] = 8.0

    tissue.tick(random.Random(14))
    tissue.tick(random.Random(15))
    tissue.tick(random.Random(16))
    assert worker.position == (2, 1)
    assert worker.carried_resource == 1
    assert tissue.metrics().cooperation_credit > 0.0


def test_cell_checkpoint_round_trip_preserves_bounded_policy_state():
    """The cell's learned policy is durable data, not source code or a hidden callback."""

    world = CellWorld(seed=16, width=5, height=5, resource_sites=0, hazard_sites=0)
    cell = AdaptiveCell(position=(1, 1), policy=CellPolicy(max_states=8))
    _prefer(cell, world, CellAction.WAIT)
    cell.step(world, random.Random(17))
    restored = AdaptiveCell.from_state(cell.to_state())

    assert restored.cell_id == cell.cell_id
    assert restored.policy.to_state() == cell.policy.to_state()
    assert restored.policy.max_states == 8


def test_independent_evaluation_resets_previous_lifetime_state():
    """Past cargo and self-reported survival cannot inflate a fresh held-out rollout."""

    fresh = AdaptiveCell()
    stale = AdaptiveCell.from_state(fresh.to_state())
    stale.position = (6, 6)
    stale.energy = 0.0
    stale.alive = False
    stale.age = 79
    stale.carried_resource = 7
    stale.delivered_resource = 99
    stale.repairs_completed = 55

    seeds = (601, 607, 613)
    assert evaluate_cell(fresh, world_seeds=seeds, ticks=20) == evaluate_cell(
        stale, world_seeds=seeds, ticks=20
    )
