"""Contract coverage for bounded v12 text and fixed-pattern capabilities."""
from __future__ import annotations

import pytest

from evolution.approved_patterns import (
    APPROVED_PATTERNS,
    PatternApprovalError,
    regex_extract,
    regex_extract_all,
    regex_match,
    regex_replace,
)
from evolution.gp_engine import STRING_PRIMITIVES
from evolution.primitive_registry import PRIMITIVE_APPROVALS, primitive_approval


def _operations() -> dict[str, object]:
    return {primitive.name: primitive.fn for primitive in STRING_PRIMITIVES}


def test_string_grammar_contains_nine_baseline_and_thirty_one_v12_operations() -> None:
    names = {primitive.name for primitive in STRING_PRIMITIVES}
    assert len(STRING_PRIMITIVES) == 40
    assert {
        "extract_between", "is_email", "remove_html_tags", "count_occurrences",
        "extract_domain", "normalise_company_name", "extract_first_number",
    } <= names


def test_tier_two_text_operations_are_bounded_pure_and_approved() -> None:
    for primitive in STRING_PRIMITIVES:
        approval = primitive_approval(primitive.name)
        assert approval.tier == 2
        assert approval.execution_environment == "main-process-pure"
        assert not approval.has_side_effects
        assert not approval.requires_network
        assert not approval.requires_filesystem
    assert set(PRIMITIVE_APPROVALS) >= {primitive.name for primitive in STRING_PRIMITIVES}


def test_text_extraction_validation_normalisation_pattern_and_domain_contracts() -> None:
    operation = _operations()
    assert operation["extract_between"]("a<target>b", "<", ">") == "target"
    assert operation["extract_after"]("name: Ada", ": ") == "Ada"
    assert operation["extract_before"]("Ada <ada@example.test>", " <") == "Ada"
    assert operation["nth_word"]("one two three", 1.0) == "two"
    assert operation["nth_line"]("a\nb\nc", 2.0) == "c"
    assert operation["is_email"]("ada@example.test") is True
    assert operation["is_url"]("https://example.test/path") is True
    assert operation["is_phone"]("+1 (415) 555-0100") is True
    assert operation["is_numeric"](" -2.5 ") is True
    assert operation["contains_digit"]("v12") is True
    assert operation["contains_alpha"]("123a") is True
    assert operation["remove_punctuation"]("Acme, Inc.! @") == "Acme Inc @"
    assert operation["collapse_whitespace"](" a\t b\n") == "a b"
    assert operation["to_lowercase"]("ADA") == "ada"
    assert operation["to_titlecase"]("ada lovelace") == "Ada Lovelace"
    assert operation["remove_html_tags"]("<b>Ada</b>") == "Ada"
    assert operation["decode_html_entities"]("A &amp; B") == "A & B"
    assert operation["count_occurrences"]("aaaa", "aa") == 2.0
    assert operation["find_first"]("abca", "a") == 0.0
    assert operation["find_last"]("abca", "a") == 3.0
    assert operation["split_on"]("a,b,c", ",") == ["a", "b", "c"]
    assert operation["join_with"](["a", "b"], "-") == "a-b"
    assert operation["pad_left"]("7", 3.0, "0") == "007"
    assert operation["pad_right"]("7", 3.0, "0") == "700"
    assert operation["truncate"]("abcdef", 3.0) == "abc"
    assert operation["extract_domain"]("https://example.test/path") == "example.test"
    assert operation["extract_email_domain"]("ada@example.test") == "example.test"
    assert operation["extract_tld"]("example.test") == "test"
    assert operation["strip_protocol"]("https://example.test") == "example.test"
    assert operation["normalise_company_name"]("Acme, Inc.") == "Acme"
    assert operation["extract_first_number"]("v12 release") == 12.0


def test_named_patterns_are_fixed_bounded_and_cannot_accept_arbitrary_regex() -> None:
    assert len(APPROVED_PATTERNS) == 14
    assert regex_match("email", "reach ada@example.test") is True
    assert regex_extract("linkedin_profile", "See https://linkedin.com/in/ada-lovelace now") == "https://linkedin.com/in/ada-lovelace"
    assert regex_extract_all("date_iso", "2026-08-18 and 2026-08-19") == ["2026-08-18", "2026-08-19"]
    assert regex_replace("email", "ada@example.test", "[redacted]") == "[redacted]"
    with pytest.raises(PatternApprovalError, match="approved registry"):
        regex_match("(a+)+$", "a" * 500)
