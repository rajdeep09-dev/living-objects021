"""Small HMAC-chained JSONL audit trail for locally bounded runs.

This is tamper-evident only for parties who protect the caller-supplied signing
key.  It does not make a local file immutable, replace access control, or
provide a distributed transparency log.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


GENESIS_DIGEST = "0" * 64


class AuditTrailIntegrityError(ValueError):
    """Raised when a local audit record is malformed or its digest chain changes."""


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    event: Mapping[str, Any]
    previous_digest: str
    digest: str
    signature: str


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class HmacAuditTrail:
    """Append and verify an ordered HMAC chain without serializing executable code."""

    def __init__(self, path: str | Path, signing_key: bytes) -> None:
        if len(signing_key) < 16:
            raise ValueError("audit signing key must contain at least 16 bytes")
        self.path = Path(path)
        self._key = bytes(signing_key)

    def _records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AuditTrailIntegrityError(f"invalid audit JSON at line {line_number}") from exc
            if not isinstance(record, dict):
                raise AuditTrailIntegrityError(f"audit record at line {line_number} is not an object")
            records.append(record)
        return records

    def append(self, event: Mapping[str, Any]) -> AuditEvent:
        if not isinstance(event, Mapping):
            raise TypeError("audit event must be a mapping")
        records = self._records()
        self.verify()
        previous_digest = records[-1]["digest"] if records else GENESIS_DIGEST
        payload = {"sequence": len(records), "event": dict(event), "previous_digest": previous_digest}
        digest = hashlib.sha256(_canonical(payload)).hexdigest()
        signature = hmac.new(self._key, digest.encode("ascii"), hashlib.sha256).hexdigest()
        record = payload | {"digest": digest, "signature": signature}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        finally:
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        return AuditEvent(**record)

    def verify(self) -> tuple[AuditEvent, ...]:
        previous_digest = GENESIS_DIGEST
        verified: list[AuditEvent] = []
        for index, record in enumerate(self._records()):
            required = {"sequence", "event", "previous_digest", "digest", "signature"}
            if set(record) != required or record["sequence"] != index or record["previous_digest"] != previous_digest:
                raise AuditTrailIntegrityError(f"audit chain mismatch at record {index}")
            payload = {key: record[key] for key in ("sequence", "event", "previous_digest")}
            digest = hashlib.sha256(_canonical(payload)).hexdigest()
            signature = hmac.new(self._key, digest.encode("ascii"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(record["digest"], digest) or not hmac.compare_digest(record["signature"], signature):
                raise AuditTrailIntegrityError(f"audit digest or signature mismatch at record {index}")
            previous_digest = digest
            verified.append(AuditEvent(**record))
        return tuple(verified)


__all__ = ["AuditEvent", "AuditTrailIntegrityError", "HmacAuditTrail"]
