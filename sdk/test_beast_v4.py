from __future__ import annotations

import io
from urllib.error import HTTPError

import pytest

from sdk.beast_v4 import BeastV4Client, BeastV4Error
import sdk.beast_v4 as sdk_module


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_sdk_serializes_json_and_bearer_header(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> _Response:
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response(b'{"ok": true}')

    monkeypatch.setattr(sdk_module, "urlopen", fake_urlopen)
    result = BeastV4Client("http://example.test", token="signed-token").run_computation(
        transition_table={"q0|_": ["accept", "_", "S"]}
    )
    request = captured["request"]
    assert result == {"ok": True}
    assert request.full_url == "http://example.test/v4/computation/run"
    assert request.get_header("Authorization") == "Bearer signed-token"
    assert b"transition_table" in request.data


def test_sdk_convenience_methods_use_v4_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    paths: list[str] = []

    def fake_urlopen(request: object, timeout: float) -> _Response:
        paths.append(request.full_url)
        return _Response(b"{}")

    monkeypatch.setattr(sdk_module, "urlopen", fake_urlopen)
    client = BeastV4Client("http://example.test")
    client.snapshot()
    client.universes()
    client.memory_snapshot()
    client.evolve_writing()
    assert paths == [
        "http://example.test/v4/snapshot",
        "http://example.test/v4/universes",
        "http://example.test/v4/memory/snapshot",
        "http://example.test/v4/writing/evolve",
    ]


def test_sdk_surfaces_http_errors_as_domain_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, _timeout: float | None = None, **_kwargs: object) -> _Response:
        raise HTTPError("http://example.test/v4/snapshot", 401, "unauthorized", {}, io.BytesIO(b"denied"))

    monkeypatch.setattr(sdk_module, "urlopen", fake_urlopen)
    with pytest.raises(BeastV4Error, match="denied"):
        BeastV4Client("http://example.test").snapshot()
