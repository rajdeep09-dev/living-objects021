from __future__ import annotations

import random

from evolution.fitness import SortingEvaluator
from evolution.gp_control import GPRunController
from evolution.gp_engine import DEFAULT_PRIMITIVES, FLOAT, GPGenome, GPNode, GPTreeBuilder, Terminal
from evolution.gp_population import GPPopulation
from evolution.program_validation import ProgramValidator
from evolution.safe_improvement import SafeImprovementGate


def test_validator_accepts_typed_tree_and_generated_source() -> None:
    tree = GPNode(terminal_name="x", value_type=FLOAT)
    genome = GPGenome(tree=tree)
    validator = ProgramValidator()
    assert validator.validate_tree(tree).valid
    assert validator.validate_source(genome.to_python("candidate", ["x"])).valid


def test_validator_rejects_blocked_source_and_malformed_tree() -> None:
    validator = ProgramValidator()
    assert not validator.validate_source("import os\ndef candidate(x):\n    return os.system('id')").valid
    malformed = GPNode(primitive=DEFAULT_PRIMITIVES[0], children=[])
    assert not validator.validate_tree(malformed).valid


def test_improvement_gate_requires_real_holdout_gain() -> None:
    evaluator = SortingEvaluator()
    baseline = GPGenome(tree=GPNode(terminal_value=[], value_type="list"))
    sort_primitive = next(primitive for primitive in DEFAULT_PRIMITIVES if primitive.name == "sort1")
    candidate = GPGenome(tree=GPNode(
        primitive=sort_primitive,
        children=[GPNode(terminal_name="x", value_type="list")],
    ))
    decision = SafeImprovementGate(
        evaluator, min_improvement=0.01, max_complexity_ratio=2.0
    ).evaluate(baseline, candidate)
    assert decision.accepted
    assert decision.candidate_score > decision.baseline_score


def test_controller_is_bounded_checkpointed_and_side_effect_free(tmp_path) -> None:
    evaluator = SortingEvaluator()
    population = GPPopulation(evaluator=evaluator, population_size=6, seed=7)
    controller = GPRunController(population, generation_budget=3, checkpoint_path=tmp_path / "gp.json")
    assert controller.start().state == "running"
    assert controller.advance(10).state == "completed"
    assert population.generation == 3
    assert (tmp_path / "gp.json").exists()
    assert controller.cancel().state == "completed"


def test_controller_resumes_the_json_checkpoint_deterministically(tmp_path) -> None:
    evaluator = SortingEvaluator()
    checkpoint = tmp_path / "resume.json"
    first = GPRunController(GPPopulation(evaluator=evaluator, population_size=6, seed=11), 4, checkpoint)
    first.start()
    first.advance(2)
    resumed = GPRunController.resume_from_checkpoint(evaluator, checkpoint)
    assert resumed.population.generation == 2
    assert resumed.state == "running"
    assert resumed.advance(2).state == "completed"
    assert resumed.population.generation == 4
