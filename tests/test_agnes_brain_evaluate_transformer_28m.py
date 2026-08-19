"""No-execution contracts for post-training transformer evaluation."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from agnes_brain.evaluate_transformer_28m import greedy_byte_continuation  # noqa: E402


class _FakeModel:
    class config:
        block_size = 8

    def eval(self):
        return self

    def __call__(self, tokens):
        logits = torch.zeros((1, tokens.shape[1], 256), dtype=torch.float32)
        logits[0, -1, 65] = 1.0
        return logits, None


def test_greedy_continuation_is_bounded_deterministic_bytes() -> None:
    model = _FakeModel()
    first = greedy_byte_continuation(model, b"{", max_new_bytes=4)
    second = greedy_byte_continuation(model, b"{", max_new_bytes=4)
    assert first == second == b"{AAAA"


def test_greedy_continuation_refuses_oversized_or_empty_prompt() -> None:
    model = _FakeModel()
    with pytest.raises(ValueError, match="non-empty"):
        greedy_byte_continuation(model, b"")
    with pytest.raises(ValueError, match="context"):
        greedy_byte_continuation(model, b"123456789")
