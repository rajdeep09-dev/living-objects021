from __future__ import annotations

import pytest

from agnes_brain.ollama_client import OllamaClient


def test_ollama_client_rejects_nonlocal_and_credentialed_endpoints() -> None:
    with pytest.raises(ValueError, match="local"):
        OllamaClient(base_url="https://example.com")
    with pytest.raises(ValueError, match="credentials"):
        OllamaClient(base_url="http://user:pass@127.0.0.1:11434")


def test_ollama_client_fails_closed_when_no_local_service_is_listening() -> None:
    client = OllamaClient(base_url="http://127.0.0.1:9", timeout_seconds=1)

    availability = client.availability("missing")

    assert availability.available is False
    assert availability.reason == "local_api_unreachable"
