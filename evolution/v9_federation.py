"""Signed discovery exchange for verified, bounded BEAST evidence.

This is deliberately an exchange *format and local admission boundary*, not a
claim of a deployed peer-to-peer network. Each receiving peer verifies both the
issuer signature and its own immutable local evidence before admitting a record
to its local discovery memome. No generated source is executed.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


EXCHANGE_SCHEMA = "beast-v9-signed-discovery-exchange-v1"
_ROOT = Path(__file__).resolve().parents[1]
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(_IDENTIFIER.fullmatch(value))


def _load_local_record(record_id: str) -> dict[str, Any]:
    """Load an eligible discovery record and cross-check its trial artifact."""
    path = _ROOT / "docs" / "v8-discovery-log.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    for record in ledger.get("records", []):
        if record.get("record_id") != record_id:
            continue
        if record.get("task") != "manhattan-distance" or record.get("promotion_eligible") is not True:
            raise ValueError("local record is not an eligible Manhattan discovery")
        fresh = record.get("fresh_suite", {})
        if fresh.get("correctness") != 1.0 or fresh.get("passed") != fresh.get("cases"):
            raise ValueError("local record does not meet its recorded fresh-suite boundary")
        trial_path = _ROOT / str(record["trial_artifact"])
        trial = json.loads(trial_path.read_text(encoding="utf-8"))
        if trial.get("final", {}).get("tree_sha256") != record.get("tree_sha256"):
            raise ValueError("local trial tree hash does not match discovery record")
        return dict(record)
    raise ValueError(f"unknown local discovery record: {record_id}")


def available_discoveries() -> list[dict[str, Any]]:
    """List locally persisted, independently importable discovery records."""
    path = _ROOT / "docs" / "v8-discovery-log.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [_load_local_record(str(record["record_id"])) for record in raw.get("records", [])]


@dataclass(frozen=True)
class Admission:
    accepted: bool
    reason: str
    record_id: str | None
    issuer: str | None
    local_verification: str


class SignedDiscoveryExchange:
    """A local peer identity, trust set, and verified discovery memome."""

    def __init__(self, node_id: str, signing_key: bytes, *, trusted_peers: Mapping[str, bytes] | None = None) -> None:
        if not _valid_identifier(node_id):
            raise ValueError("node_id must be a safe 1..128 character identifier")
        if not isinstance(signing_key, bytes) or len(signing_key) < 16:
            raise ValueError("signing_key must contain at least 16 bytes")
        self.node_id = node_id
        self._signing_key = signing_key
        self._trusted_peers = dict(trusted_peers or {})
        self._admitted: dict[str, dict[str, Any]] = {}
        self._seen_nonces: set[tuple[str, str]] = set()

    def trust_peer(self, peer_id: str, verification_key: bytes) -> None:
        if not _valid_identifier(peer_id) or not isinstance(verification_key, bytes) or len(verification_key) < 16:
            raise ValueError("peer identity and verification key are invalid")
        self._trusted_peers[peer_id] = verification_key

    @staticmethod
    def _unsigned(envelope: Mapping[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in envelope.items() if key != "signature"}

    @staticmethod
    def _signature(key: bytes, envelope: Mapping[str, Any]) -> str:
        return hmac.new(key, _canonical_json(SignedDiscoveryExchange._unsigned(envelope)).encode("utf-8"), hashlib.sha256).hexdigest()

    def publish(self, record_id: str, *, nonce: str | None = None, issued_at: str | None = None) -> dict[str, Any]:
        """Create a signed envelope from a locally verified persisted record."""
        if not _valid_identifier(record_id):
            raise ValueError("record_id must be a safe identifier")
        issued_nonce = nonce or secrets.token_hex(16)
        if not _valid_identifier(issued_nonce):
            raise ValueError("nonce must be a safe identifier")
        envelope: dict[str, Any] = {
            "schema": EXCHANGE_SCHEMA,
            "issuer": self.node_id,
            "nonce": issued_nonce,
            "issued_at": issued_at or datetime.now(timezone.utc).isoformat(),
            "record": _load_local_record(record_id),
        }
        envelope["signature"] = self._signature(self._signing_key, envelope)
        return envelope

    def import_envelope(self, envelope: Mapping[str, Any]) -> Admission:
        """Verify signature, anti-replay nonce, and local evidence before admission."""
        if not isinstance(envelope, Mapping) or envelope.get("schema") != EXCHANGE_SCHEMA:
            return Admission(False, "unsupported discovery envelope schema", None, None, "not attempted")
        issuer = envelope.get("issuer")
        nonce = envelope.get("nonce")
        if not _valid_identifier(issuer) or not _valid_identifier(nonce):
            return Admission(False, "invalid issuer or nonce", None, str(issuer) if isinstance(issuer, str) else None, "not attempted")
        verification_key = self._trusted_peers.get(issuer)
        if verification_key is None:
            return Admission(False, "issuer is not trusted", None, issuer, "not attempted")
        signature = envelope.get("signature")
        expected = self._signature(verification_key, envelope)
        if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
            return Admission(False, "signature verification failed", None, issuer, "not attempted")
        nonce_key = (issuer, nonce)
        if nonce_key in self._seen_nonces:
            return Admission(False, "replayed signed envelope", None, issuer, "not attempted")
        record = envelope.get("record")
        if not isinstance(record, Mapping) or not _valid_identifier(record.get("record_id")):
            return Admission(False, "record is missing a valid identifier", None, issuer, "not attempted")
        record_id = str(record["record_id"])
        try:
            local = _load_local_record(record_id)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return Admission(False, f"local verification unavailable: {exc}", record_id, issuer, "failed")
        if _canonical_json(dict(record)) != _canonical_json(local):
            return Admission(False, "remote record differs from independently verified local evidence", record_id, issuer, "failed")
        self._seen_nonces.add(nonce_key)
        if record_id in self._admitted:
            return Admission(False, "record was already admitted", record_id, issuer, "passed")
        self._admitted[record_id] = local
        return Admission(True, "signature and local evidence verified", record_id, issuer, "passed")

    def admitted_records(self) -> list[dict[str, Any]]:
        return [dict(self._admitted[key]) for key in sorted(self._admitted)]

    def evidence_summary(self) -> dict[str, Any]:
        """Return a source-only summary suitable for an authenticated observatory."""
        return {
            "schema": EXCHANGE_SCHEMA,
            "node_id": self.node_id,
            "trusted_peer_ids": sorted(self._trusted_peers),
            "admitted_record_ids": sorted(self._admitted),
            "execution_boundary": {
                "network_transport": "not implemented by this local exchange MVP",
                "generated_source_executed": False,
                "admission_requires_local_artifact_verification": True,
            },
        }


__all__ = ["Admission", "EXCHANGE_SCHEMA", "SignedDiscoveryExchange", "available_discoveries"]
