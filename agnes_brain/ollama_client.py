"""Fail-closed client for an explicitly local Ollama runtime.

This module intentionally has no dependency on the public internet, no model
download behavior, and no execution surface.  It only sends bounded requests to
``localhost`` and returns untrusted response text to a caller that must validate
it separately.  A missing runtime, missing model, malformed HTTP payload, or
oversized response is represented as an unavailable result.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
MAX_REQUEST_BYTES = 16_384
MAX_RESPONSE_BYTES = 16_384
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True)
class OllamaAvailability:
    """Local runtime and requested-model availability without side effects."""

    available: bool
    reason: str
    model: str
    model_names: tuple[str, ...]


@dataclass(frozen=True)
class OllamaResponse:
    """One bounded untrusted completion, kept in memory only by this client."""

    available: bool
    reason: str
    model: str
    text: str | None
    raw_sha256: str | None
    raw_bytes: int
    request_bytes: int
    elapsed_seconds: float | None


def _validate_local_base_url(base_url: str) -> str:
    parsed = urlparse(str(base_url))
    if parsed.scheme != "http" or parsed.hostname not in _LOCAL_HOSTS or parsed.path not in {"", "/"}:
        raise ValueError("Ollama base URL must be a local http://127.0.0.1, localhost, or [::1] endpoint")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Ollama base URL must not contain credentials, a query, or a fragment")
    return str(base_url).rstrip("/")


class OllamaClient:
    """Use only Ollama's loopback API and fail closed for every transport error."""

    def __init__(self, *, base_url: str = DEFAULT_OLLAMA_URL, timeout_seconds: float = 90.0) -> None:
        if not 1.0 <= float(timeout_seconds) <= 300.0:
            raise ValueError("timeout_seconds must be in [1, 300]")
        self.base_url = _validate_local_base_url(base_url)
        self.timeout_seconds = float(timeout_seconds)

    def _request(self, path: str, *, payload: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, str]:
        body = None if payload is None else json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if body is not None and len(body) > MAX_REQUEST_BYTES:
            return None, "request_too_large"
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method="POST" if body is not None else "GET",
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - base URL is validated as loopback.
                response_body = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, OSError, TimeoutError):
            return None, "local_api_unreachable"
        if len(response_body) > MAX_RESPONSE_BYTES:
            return None, "response_too_large"
        try:
            decoded = json.loads(response_body.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, "invalid_api_response"
        if not isinstance(decoded, dict):
            return None, "invalid_api_response"
        return decoded, "ok"

    def availability(self, model: str) -> OllamaAvailability:
        """Return whether a named model is already present in the local registry."""

        name = str(model).strip()
        if not name:
            raise ValueError("model must be non-empty")
        payload, reason = self._request("/api/tags")
        if payload is None:
            return OllamaAvailability(False, reason, name, ())
        models = payload.get("models")
        if not isinstance(models, list):
            return OllamaAvailability(False, "invalid_api_response", name, ())
        names = tuple(sorted(item["name"] for item in models if isinstance(item, dict) and isinstance(item.get("name"), str)))
        return OllamaAvailability(name in names, "available" if name in names else "model_unavailable", name, names)

    def _generate(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None,
        temperature: float,
        response_format: dict[str, Any] | None,
    ) -> OllamaResponse:
        """Request one bounded local completion, optionally with provider-side JSON Schema."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be non-empty text")
        if not 0.0 <= float(temperature) <= 1.0:
            raise ValueError("temperature must be in [0, 1]")
        request_payload: dict[str, Any] = {
            "model": str(model).strip(),
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": float(temperature)},
        }
        if system is not None:
            request_payload["system"] = str(system)
        if response_format is not None:
            request_payload["format"] = response_format
        encoded = json.dumps(request_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        started = time.monotonic()
        payload, reason = self._request("/api/generate", payload=request_payload)
        elapsed = time.monotonic() - started
        if payload is None:
            return OllamaResponse(False, reason, str(model).strip(), None, None, 0, len(encoded), elapsed)
        response_text = payload.get("response")
        if not isinstance(response_text, str):
            return OllamaResponse(False, "invalid_api_response", str(model).strip(), None, None, 0, len(encoded), elapsed)
        raw = response_text.encode("utf-8", errors="strict")
        if len(raw) > MAX_RESPONSE_BYTES:
            return OllamaResponse(False, "response_too_large", str(model).strip(), None, None, len(raw), len(encoded), elapsed)
        return OllamaResponse(True, "ok", str(model).strip(), response_text, hashlib.sha256(raw).hexdigest(), len(raw), len(encoded), elapsed)

    def generate_raw(self, *, model: str, prompt: str, system: str | None = None, temperature: float = 0.0) -> OllamaResponse:
        """Request one non-streaming raw completion without a JSON or schema format mask."""

        return self._generate(model=model, prompt=prompt, system=system, temperature=temperature, response_format=None)

    def generate_json_schema(
        self,
        *,
        model: str,
        prompt: str,
        json_schema: dict[str, Any],
        system: str | None = None,
        temperature: float = 0.0,
    ) -> OllamaResponse:
        """Request a completion under Ollama's documented provider-side JSON Schema parameter.

        This is not raw model decoding and callers must report it separately from
        any raw-output baseline.  The client still returns untrusted text only.
        """

        if not isinstance(json_schema, dict) or not json_schema:
            raise ValueError("json_schema must be a non-empty object")
        return self._generate(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            response_format=json_schema,
        )


__all__ = [
    "DEFAULT_OLLAMA_URL",
    "MAX_REQUEST_BYTES",
    "MAX_RESPONSE_BYTES",
    "OllamaAvailability",
    "OllamaClient",
    "OllamaResponse",
]
