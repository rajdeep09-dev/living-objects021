"""Small dependency-free HS256 JWT implementation for the platform API."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from typing import Any, Mapping


class JWTError(ValueError):
    """Raised when a token is malformed, expired, or incorrectly signed."""


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def encode_jwt(payload: Mapping[str, Any], secret: str, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    claims = dict(payload)
    claims.setdefault("iat", now)
    claims.setdefault("exp", now + ttl_seconds)
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64(json.dumps(header, separators=(",", ":")).encode())
    encoded_payload = _b64(json.dumps(claims, separators=(",", ":")).encode())
    message = f"{encoded_header}.{encoded_payload}".encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64(signature)}"


def decode_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        header = json.loads(_unb64(encoded_header))
        payload = json.loads(_unb64(encoded_payload))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise JWTError("malformed token") from exc
    if header.get("alg") != "HS256":
        raise JWTError("unsupported signing algorithm")
    expected = hmac.new(
        secret.encode(), f"{encoded_header}.{encoded_payload}".encode(), hashlib.sha256
    ).digest()
    try:
        provided = _unb64(encoded_signature)
    except (ValueError, binascii.Error) as exc:  # pragma: no cover - defensive branch
        raise JWTError("malformed signature") from exc
    if not hmac.compare_digest(expected, provided):
        raise JWTError("invalid signature")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise JWTError("token expired")
    return payload
