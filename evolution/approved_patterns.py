"""Named, fixed, bounded regular-expression operations for supplied text.

This module accepts a reviewed pattern *name*, never an arbitrary regular
expression. It does not fetch data, validate identity documents, or establish
the truth of a detected value.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


TEXT_LIMIT = 16_384
MAX_MATCHES = 256


class PatternApprovalError(ValueError):
    """Raised when code requests a pattern outside the reviewed fixed registry."""


@dataclass(frozen=True)
class ApprovedPattern:
    name: str
    expression: str
    purpose: str
    approved_on: str = "2026-08-18"


_PATTERN_DEFINITIONS = (
    ApprovedPattern("email", r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})+", "Email format detection only."),
    ApprovedPattern("url", r"https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}(?:/[^\s<>\"']{0,2048})?", "HTTP(S) URL format detection."),
    ApprovedPattern("us_phone", r"(?:\+?1[ .-]?)?(?:\([0-9]{3}\)|[0-9]{3})[ .-]?[0-9]{3}[ .-]?[0-9]{4}", "US phone format detection only."),
    ApprovedPattern("linkedin_profile", r"https?://(?:[A-Za-z]{2,3}\.)?linkedin\.com/in/[A-Za-z0-9-]{1,100}", "LinkedIn profile URL format."),
    ApprovedPattern("twitter_handle", r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{1,15}\b", "Twitter/X handle format."),
    ApprovedPattern("github_username", r"(?<![A-Za-z0-9-])[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\b", "GitHub username-shaped token."),
    ApprovedPattern("date_iso", r"\b[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])\b", "ISO date format."),
    ApprovedPattern("time_hhmm", r"\b(?:[01][0-9]|2[0-3]):[0-5][0-9]\b", "24-hour time format."),
    ApprovedPattern("ipv4", r"\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b", "IPv4 format."),
    ApprovedPattern("postal_code", r"\b(?:[0-9]{5}(?:-[0-9]{4})?|[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2})\b", "US or UK postal-code format."),
    ApprovedPattern("company_registration", r"\b[A-Z0-9]{6,12}\b", "Company-registration-shaped token only."),
    ApprovedPattern("iban", r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b", "IBAN format detection only."),
    ApprovedPattern("credit_card_16", r"\b(?:[0-9]{4}[ -]?){3}[0-9]{4}\b", "16-digit payment-card format detection only; no validation."),
    ApprovedPattern("ssn_format", r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "US SSN format detection only; no validation or retention."),
)

APPROVED_PATTERNS = {pattern.name: pattern for pattern in _PATTERN_DEFINITIONS}
_COMPILED = {name: re.compile(pattern.expression) for name, pattern in APPROVED_PATTERNS.items()}


def _pattern(name: str) -> re.Pattern[str]:
    try:
        return _COMPILED[name]
    except KeyError as exc:
        raise PatternApprovalError(f"pattern is not in the approved registry: {name}") from exc


def _text(value: object) -> str:
    return str(value)[:TEXT_LIMIT]


def regex_match(pattern_name: str, text: object) -> bool:
    return bool(_pattern(pattern_name).search(_text(text)))


def regex_extract(pattern_name: str, text: object) -> str:
    match = _pattern(pattern_name).search(_text(text))
    return match.group(0) if match else ""


def regex_extract_all(pattern_name: str, text: object) -> list[str]:
    return [match.group(0) for match in _pattern(pattern_name).finditer(_text(text))][:MAX_MATCHES]


def regex_replace(pattern_name: str, text: object, replacement: object) -> str:
    return _pattern(pattern_name).sub(_text(replacement), _text(text))[:TEXT_LIMIT]


__all__ = [
    "APPROVED_PATTERNS", "ApprovedPattern", "MAX_MATCHES", "PatternApprovalError",
    "regex_extract", "regex_extract_all", "regex_match", "regex_replace",
]
