"""API, auth, persistence, metrics, and WebSocket contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from production import api as api_package
from production.api import main as api
from production.config import Settings


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    old_runtime = api.runtime
    api.runtime = api.Runtime(Settings(database_url=f"sqlite:///{tmp_path / 'state.sqlite3'}"))
    with TestClient(api.app) as test_client:
        yield test_client
    api.runtime.close()
    api.runtime = old_runtime


@pytest.fixture()
def token(client: TestClient) -> str:
    response = client.post("/auth/token", json={"username": "operator", "password": "living-objects"})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_is_public(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_is_available(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Living Objects" in response.text


def test_invalid_credentials_are_rejected(client: TestClient):
    response = client.post("/auth/token", json={"username": "operator", "password": "wrong"})
    assert response.status_code == 401


def test_missing_bearer_is_rejected(client: TestClient):
    assert client.get("/organisms").status_code == 401


def test_token_is_jwt_shaped(token: str):
    assert len(token.split(".")) == 3


@pytest.mark.parametrize("species", ["producer", "consumer", "decomposer", "adaptive", "research"])
def test_create_organism_preserves_species(client: TestClient, token: str, species: str):
    response = client.post("/organisms", headers=auth(token), json={"species": species})
    assert response.status_code == 201
    assert response.json()["species"] == species


def test_crud_lifecycle(client: TestClient, token: str):
    headers = auth(token)
    created = client.post(
        "/organisms", headers=headers, json={"species": "adaptive", "fitness": 0.4, "metadata": {"region": "lab"}}
    )
    assert created.status_code == 201
    organism_id = created.json()["organism_id"]
    assert client.get(f"/organisms/{organism_id}", headers=headers).json()["fitness"] == 0.4
    updated = client.patch(f"/organisms/{organism_id}", headers=headers, json={"fitness": 0.9, "status": "paused"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "paused"
    assert client.delete(f"/organisms/{organism_id}", headers=headers).status_code == 204
    assert client.get(f"/organisms/{organism_id}", headers=headers).status_code == 404


def test_list_paginates(client: TestClient, token: str):
    headers = auth(token)
    for index in range(6):
        assert client.post("/organisms", headers=headers, json={"metadata": {"i": index}}).status_code == 201
    response = client.get("/organisms?limit=2&offset=2", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["offset"] == 2


def test_get_missing_organism_is_404(client: TestClient, token: str):
    assert client.get("/organisms/does-not-exist", headers=auth(token)).status_code == 404


def test_update_missing_organism_is_404(client: TestClient, token: str):
    assert client.patch("/organisms/does-not-exist", headers=auth(token), json={"fitness": 0.2}).status_code == 404


def test_delete_missing_organism_is_404(client: TestClient, token: str):
    assert client.delete("/organisms/does-not-exist", headers=auth(token)).status_code == 404


def test_evolution_step_is_persisted_and_streamed(client: TestClient, token: str):
    headers = auth(token)
    response = client.post(
        "/evolution/step",
        headers=headers,
        json={"generation": 7, "organism_count": 1000, "average_fitness": 0.72, "cultural_complexity": 2.1, "novelty_delta": 4},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    with client.websocket_connect(f"/ws/evolution?token={token}") as websocket:
        event = websocket.receive_json()
        assert event["type"] == "generation.completed"


def test_bad_websocket_token_is_closed(client: TestClient):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/evolution?token=bad-token"):
            pass


def test_archive_query_requires_auth(client: TestClient):
    assert client.get("/archive/strategies").status_code == 401


def test_archive_query_returns_memes(client: TestClient, token: str):
    meme = api.runtime.store.add_meme("bridge", "river-crossing", 0.9, "org-1", 2)
    response = client.get("/archive/strategies?q=river", headers=auth(token))
    assert response.status_code == 200
    assert response.json()["items"][0]["meme_id"] == meme["meme_id"]


def test_metrics_endpoint_exposes_platform_names(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "living_objects_organisms" in response.text
    assert "living_objects_average_fitness" in response.text


@pytest.mark.parametrize(
    ("field", "value"),
    [("fitness", -0.1), ("fitness", 1.1), ("mutation_rate", -0.1), ("mutation_rate", 1.1), ("generation", -1)],
)
def test_create_validates_bounds(client: TestClient, token: str, field: str, value: float):
    response = client.post("/organisms", headers=auth(token), json={field: value})
    assert response.status_code == 422

