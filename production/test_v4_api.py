from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("JWT_SECRET", "beast-v4-local-test-secret-012345678901234567890123")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import production.api.main as api_main  # noqa: E402
from production.api.main import app, settings  # noqa: E402
from production.api.v3 import routes as v3_routes  # noqa: E402
from production.api.v4 import routes as v4_routes  # noqa: E402
from production.auth import encode_jwt  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(v3_routes, "state", v3_routes.V3ControlState())
    fresh_v4 = v4_routes.V4ControlState()
    monkeypatch.setattr(v4_routes, "state", fresh_v4)
    monkeypatch.setattr(api_main, "v4_state", fresh_v4)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    token = encode_jwt(
        {"sub": settings.operator_username, "role": "operator"},
        settings.jwt_secret,
        settings.jwt_ttl_seconds,
    )
    return {"Authorization": f"Bearer {token}"}


def test_v4_requires_operator_auth(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/v4/snapshot").status_code == 401
    reader = encode_jwt({"sub": "reader", "role": "reader"}, settings.jwt_secret, settings.jwt_ttl_seconds)
    assert client.get("/v4/snapshot", headers={"Authorization": f"Bearer {reader}"}).status_code == 403
    assert client.get("/v4/snapshot", headers=auth_headers).status_code == 200


def test_v4_universe_branch_and_physics_mutation(client: TestClient, auth_headers: dict[str, str]) -> None:
    branch = client.post("/v4/universes/origin/branch", headers=auth_headers, json={"law": "entropy_gradient"})
    assert branch.status_code == 201
    child_id = branch.json()["universe"]["universe_id"]
    mutation = client.post(
        "/v4/physics/mutations",
        headers=auth_headers,
        json={"universe_id": child_id, "name": "bounded-information", "invariant": "information <= 1"},
    )
    assert mutation.status_code == 200
    assert mutation.json()["accepted"] is True


def test_v4_computation_memory_writing_and_substrate(client: TestClient, auth_headers: dict[str, str]) -> None:
    computation = client.post(
        "/v4/computation/run",
        headers=auth_headers,
        json={
            "input_tape": "_",
            "step_limit": 10,
            "transition_table": {"q0|_": ["accept", "_", "S"]},
        },
    )
    assert computation.status_code == 200
    assert computation.json()["halted"] is True

    memory = client.post(
        "/v4/memory/record",
        headers=auth_headers,
        json={
            "name": "v4-memory",
            "source_code": "return 1",
            "descriptor": "proof",
            "effectiveness": 0.9,
            "author_id": "operator",
        },
    )
    assert memory.status_code == 201
    assert memory.json()["cluster_count"] >= 1

    writing = client.post(
        "/v4/writing/encode",
        headers=auth_headers,
        json={"action": "cooperate", "parameters": {"intensity": 0.8}, "context": {"mode": "proof"}},
    )
    assert writing.status_code == 200
    assert writing.json()["vocabulary_size"] >= 1

    substrate = client.post(
        "/v4/substrate/export",
        headers=auth_headers,
        json={"organism_id": "substrate-organism", "substrate": "wasm"},
    )
    assert substrate.status_code == 200
    assert substrate.json()["artifact"]["bytes"] > 0


def test_v4_stream_admits_valid_tokens_and_rejects_invalid_tokens(client: TestClient, auth_headers: dict[str, str]) -> None:
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/v4/evolution?token=invalid"):
            pass
    with client.websocket_connect(f"/ws/v4/evolution?token={auth_headers['Authorization'].split()[-1]}") as websocket:
        v4_routes.state.emit({"type": "v4.test", "generation": 1})
        event = websocket.receive_json()
        assert event["type"] == "v4.test"
