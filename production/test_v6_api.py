from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("JWT_SECRET", "beast-v6-local-test-secret-012345678901234567890123")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import production.api.main as api_main  # noqa: E402
from production.api.main import app, settings  # noqa: E402
from production.api.v6 import routes as v6_routes  # noqa: E402
from production.auth import encode_jwt  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    fresh = v6_routes.V6ControlState()
    monkeypatch.setattr(v6_routes, "state", fresh)
    monkeypatch.setattr(api_main, "v6_state", fresh)
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


def test_v6_requires_operator_and_exposes_only_named_tasks(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/v6/snapshot").status_code == 401
    response = client.get("/v6/snapshot", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["allowed_tasks"] == ["absolute_difference", "sorting"]
    invalid = client.post("/v6/runs", headers=auth_headers, json={"task": "shell"})
    assert invalid.status_code == 422


def test_v6_evolves_interpreted_program_and_rejects_source_submission(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/v6/runs",
        headers=auth_headers,
        json={"task": "absolute_difference", "population_size": 8, "generations": 3, "seed": 41},
    )
    assert response.status_code == 201
    run = response.json()["run"]
    assert run["validation"] == {
        "typed_ast": True,
        "interpreter_execution_only": True,
        "user_source_accepted": False,
        "external_network_calls": 0,
    }
    assert len(run["source_sha256"]) == 64
    assert "program_source" in run
    boundary = client.post("/v6/validate-rejection", headers=auth_headers, json={"source": "import os"})
    assert boundary.status_code == 200
    assert boundary.json()["accepted"] is False


def test_v6_stream_replays_bounded_program_events(client: TestClient, auth_headers: dict[str, str]) -> None:
    token = auth_headers["Authorization"].split()[-1]
    with client.websocket_connect(f"/ws/v6/evolution?token={token}") as websocket:
        v6_routes.state.emit(v6_routes.ProgramRejectedEvent(run_id="boundary", reason="named tasks only"))
        event = websocket.receive_json()
        assert event["event_type"] == "program_rejected"
