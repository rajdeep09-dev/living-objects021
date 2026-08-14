from __future__ import annotations

import pytest

from evolution.fitness import AbsoluteDifferenceEvaluator
from evolution.gp_engine import DEFAULT_PRIMITIVES, FLOAT, GPGenome, GPNode
from evolution.program_market import VerifiedProgramMarket


def _absolute_difference() -> GPGenome:
    primitives = {item.name: item for item in DEFAULT_PRIMITIVES}
    left = GPNode(terminal_name="left", value_type=FLOAT)
    right = GPNode(terminal_name="right", value_type=FLOAT)
    return GPGenome(GPNode(primitive=primitives["abs1"], children=[
        GPNode(primitive=primitives["sub"], children=[left, right]),
    ]))


def test_verified_market_uses_non_monetary_credits_and_detached_genomes() -> None:
    market = VerifiedProgramMarket()
    market.grant_research_credits("buyer", 25)
    offer = market.list_program(
        seller_id="seller", offer_id="abs-diff", genome=_absolute_difference(),
        evaluator=AbsoluteDifferenceEvaluator(), task="absolute_difference", price_credits=10,
    )
    acquired = market.acquire(buyer_id="buyer", offer_id=offer.offer_id)
    assert offer.held_out.correctness == 1.0
    assert acquired.to_dict() == _absolute_difference().to_dict()
    assert acquired is not _absolute_difference()
    assert market.balance("buyer") == 15
    assert market.balance("seller") == 10
    assert [event["event"] for event in market.history()] == ["listed", "acquired"]


def test_market_rejects_unverified_or_unfunded_exchange() -> None:
    market = VerifiedProgramMarket()
    incorrect = GPGenome(GPNode(terminal_value=0.0, value_type=FLOAT))
    with pytest.raises(ValueError, match="no demonstrated"):
        market.list_program(
            seller_id="seller", offer_id="wrong", genome=incorrect,
            evaluator=AbsoluteDifferenceEvaluator(), task="absolute_difference", price_credits=1,
        )
    market.grant_research_credits("buyer", 1)
    market.list_program(
        seller_id="seller", offer_id="right", genome=_absolute_difference(),
        evaluator=AbsoluteDifferenceEvaluator(), task="absolute_difference", price_credits=2,
    )
    with pytest.raises(ValueError, match="insufficient"):
        market.acquire(buyer_id="buyer", offer_id="right")
