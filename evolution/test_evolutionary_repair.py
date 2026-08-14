from __future__ import annotations

import random

from evolution.evolutionary_repair import EvolutionaryRepair
from evolution.fitness import AbsoluteDifferenceEvaluator
from evolution.gp_engine import DEFAULT_PRIMITIVES, FLOAT, GPGenome, GPNode, GPTreeBuilder, Terminal


def _correct_candidate() -> GPGenome:
    primitives = {item.name: item for item in DEFAULT_PRIMITIVES}
    return GPGenome(GPNode(primitive=primitives["abs1"], children=[
        GPNode(primitive=primitives["sub"], children=[
            GPNode(terminal_name="left", value_type=FLOAT),
            GPNode(terminal_name="right", value_type=FLOAT),
        ]),
    ]))


def test_repair_proposes_but_never_applies_a_measured_ast_improvement() -> None:
    baseline = GPGenome(GPNode(terminal_value=0.0, value_type=FLOAT))
    builder = GPTreeBuilder(DEFAULT_PRIMITIVES, [Terminal(name="left"), Terminal(name="right")], random.Random(7))
    repair = EvolutionaryRepair(builder)
    proposal = repair.propose(baseline, AbsoluteDifferenceEvaluator(), candidates=[_correct_candidate()])
    assert proposal.accepted_for_review is True
    assert proposal.candidate_result.correctness == 1.0
    assert baseline.execute({"left": 9.0, "right": 2.0}) == 0.0
    assert proposal.candidate.execute({"left": 9.0, "right": 2.0}) == 7.0


def test_repair_returns_no_change_when_no_candidate_improves_holdout() -> None:
    baseline = _correct_candidate()
    builder = GPTreeBuilder(DEFAULT_PRIMITIVES, [Terminal(name="left"), Terminal(name="right")], random.Random(7))
    proposal = EvolutionaryRepair(builder).propose(baseline, AbsoluteDifferenceEvaluator(), candidates=[baseline])
    assert proposal.accepted_for_review is False
    assert proposal.reason == "no measured held-out improvement"
