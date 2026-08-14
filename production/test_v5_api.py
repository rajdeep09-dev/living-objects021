from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("JWT_SECRET", "beast-v5-local-test-secret-012345678901234567890123")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import production.api.main as api_main  # noqa: E402
from production.api.main import app, settings  # noqa: E402
from production.api.v5 import routes as v5_routes  # noqa: E402
from production.auth import encode_jwt  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    fresh = v5_routes.V5ControlState(hall=v5_routes.HallOfEvolution(tmp_path / "hall.db"))
    monkeypatch.setattr(v5_routes, "state", fresh)
    monkeypatch.setattr(api_main, "v5_state", fresh)
    with TestClient(app) as test_client:
        yield test_client
    fresh.hall.close()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    token = encode_jwt(
        {"sub": settings.operator_username, "role": "operator"},
        settings.jwt_secret,
        settings.jwt_ttl_seconds,
    )
    return {"Authorization": f"Bearer {token}"}


def test_v5_requires_operator_auth(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/v5/snapshot").status_code == 401
    reader = encode_jwt({"sub": "reader", "role": "reader"}, settings.jwt_secret, settings.jwt_ttl_seconds)
    assert client.get("/v5/snapshot", headers={"Authorization": f"Bearer {reader}"}).status_code == 403
    assert client.get("/v5/snapshot", headers=auth_headers).status_code == 200


def test_v5_epoch_hall_and_pollination_routes(client: TestClient, auth_headers: dict[str, str]) -> None:
    epoch = client.post(
        "/v5/epochs/check",
        headers=auth_headers,
        json={
            "generation": 100,
            "previous_scores": [0.98, 0.01, 0.01],
            "current_scores": [0.01, 0.98, 0.01],
            "dominant_strategy_type": "compression",
        },
    )
    assert epoch.status_code == 200
    assert epoch.json()["changed"] is True
    assert epoch.json()["event"]["type"] == "epoch_change"

    hall = client.post(
        "/v5/hall/immortalize",
        headers=auth_headers,
        json={"generation": 100, "task_name": "compress", "fitness": 0.91, "strategy_count": 3},
    )
    assert hall.status_code == 201
    assert hall.json()["record"]["strategy_count"] == 3
    assert hall.json()["event"]["type"] == "immortalization"

    pollination = client.post(
        "/v5/pollination",
        headers=auth_headers,
        json={"generation": 100, "source": "compress", "target": "sort", "donated_strategies": 2},
    )
    assert pollination.status_code == 201
    assert pollination.json()["total_donated_strategies"] == 2
    assert pollination.json()["event"]["type"] == "pollination"


def test_v5_stream_admits_valid_tokens_and_replays_bounded_events(client: TestClient, auth_headers: dict[str, str]) -> None:
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/v5/evolution?token=invalid"):
            pass
    token = auth_headers["Authorization"].split()[-1]
    with client.websocket_connect(f"/ws/v5/evolution?token={token}") as websocket:
        v5_routes.state.emit({"type": "pollination", "generation": 1, "source": "a", "target": "b", "donated_strategies": 1})
        event = websocket.receive_json()
        assert event["type"] == "pollination"
