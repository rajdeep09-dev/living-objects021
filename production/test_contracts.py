from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from production.api import main as api_module
from production.auth import JWTError, decode_jwt, encode_jwt
from production.config import Settings
from production.store import OrganismRecord, RedisCache, StateStore, utc_now


@pytest.fixture()
def store(tmp_path: Path):
    instance = StateStore(f"sqlite:///{tmp_path / 'contracts.sqlite3'}")
    yield instance
    instance.close()


@pytest.fixture()
def api_client(tmp_path: Path):
    previous = api_module.runtime
    api_module.runtime = api_module.Runtime(Settings(database_url=f"sqlite:///{tmp_path / 'api.sqlite3'}"))
    with TestClient(api_module.app) as client:
        yield client
    api_module.runtime.close()
    api_module.runtime = previous


def _token(client: TestClient) -> str:
    response = client.post("/auth/token", json={"username": "operator", "password": "living-objects"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_settings_default_database_is_sqlite():
    assert Settings.from_env().database_url.startswith("sqlite:///")


def test_settings_rejects_unrelated_database_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "mysql://example")
    assert Settings.from_env().database_url.startswith("sqlite:///")


def test_settings_accepts_postgresql_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LIVING_OBJECTS_DATABASE_URL", "postgresql://u:p@db/living")
    assert Settings.from_env().database_url.startswith("postgresql://")


def test_settings_parses_operator_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LO_OPERATOR_USERNAME", "ops")
    monkeypatch.setenv("LO_OPERATOR_PASSWORD", "secret-value")
    settings = Settings.from_env()
    assert (settings.operator_username, settings.operator_password) == ("ops", "secret-value")


def test_settings_creates_sqlite_parent(tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'nested' / 'state.sqlite3'}")
    settings.ensure_local_state()
    assert (tmp_path / "nested").is_dir()


def test_utc_now_is_timezone_aware():
    assert utc_now().endswith("+00:00")


def test_jwt_round_trip():
    token = encode_jwt({"sub": "operator"}, "test-secret")
    assert decode_jwt(token, "test-secret")["sub"] == "operator"


def test_jwt_rejects_wrong_secret():
    token = encode_jwt({"sub": "operator"}, "test-secret")
    with pytest.raises(JWTError, match="invalid signature"):
        decode_jwt(token, "wrong-secret")


def test_jwt_rejects_expired_token():
    token = encode_jwt({"sub": "operator"}, "test-secret", ttl_seconds=-1)
    with pytest.raises(JWTError, match="token expired"):
        decode_jwt(token, "test-secret")


def test_store_starts_empty(store: StateStore):
    assert store.list_organisms() == []
    assert store.query_memes() == []


def test_store_upsert_and_get(store: StateStore):
    record = OrganismRecord("org-1", "producer", 3, 0.8, 0.2, "alive", utc_now(), {"zone": "a"})
    assert store.upsert_organism(record) == record
    assert store.get_organism("org-1") == record


def test_store_upsert_replaces_state(store: StateStore):
    first = OrganismRecord("org-1", "consumer", 1, 0.1, 0.2, "alive", utc_now(), {})
    second = OrganismRecord("org-1", "consumer", 2, 0.9, 0.4, "paused", first.created_at, {"x": 1})
    store.upsert_organism(first)
    store.upsert_organism(second)
    assert store.get_organism("org-1") == second


def test_store_list_orders_by_generation(store: StateStore):
    for generation in [1, 5, 3]:
        store.upsert_organism(OrganismRecord(f"org-{generation}", "adaptive", generation, 0.5, 0.1, "alive", utc_now(), {}))
    assert [item.generation for item in store.list_organisms()] == [5, 3, 1]


def test_store_delete_missing_is_false(store: StateStore):
    assert store.delete_organism("missing") is False


def test_store_delete_existing_is_true(store: StateStore):
    store.upsert_organism(OrganismRecord("org-1", "adaptive", 0, 0.1, 0.1, "alive", utc_now(), {}))
    assert store.delete_organism("org-1") is True
    assert store.get_organism("org-1") is None


def test_store_meme_query_orders_effectiveness(store: StateStore):
    store.add_meme("weak", "route-a", 0.2, "org-1", 1)
    store.add_meme("strong", "route-a", 0.9, "org-2", 2)
    assert store.query_memes("route-a")[0]["name"] == "strong"


def test_store_meme_metadata_round_trip(store: StateStore):
    store.add_meme("bridge", "river", 0.7, "org-1", 1, {"source": "field"})
    assert store.query_memes("bridge")[0]["metadata"] == {"source": "field"}


def test_store_event_contains_payload(store: StateStore):
    event = store.record_event("generation.completed", 4, {"fitness": 0.8})
    assert event["event_type"] == "generation.completed"
    assert event["payload"]["fitness"] == 0.8


def test_redis_cache_is_disabled_without_url():
    assert RedisCache("").enabled is False


def test_api_health_is_public(api_client: TestClient):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_token_contains_expiry(api_client: TestClient):
    payload = api_client.post("/auth/token", json={"username": "operator", "password": "living-objects"}).json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] > 0


def test_api_metrics_is_prometheus_text(api_client: TestClient):
    response = api_client.get("/metrics")
    assert response.headers["content-type"].startswith("text/plain")
    assert "living_objects_" in response.text


def test_api_evolution_step_accepts_generation(api_client: TestClient):
    token = _token(api_client)
    response = api_client.post(
        "/evolution/step",
        headers=_headers(token),
        json={"generation": 12, "organism_count": 1000, "average_fitness": 0.8, "cultural_complexity": 3.1, "novelty_delta": 2},
    )
    assert response.status_code == 200
    assert response.json()["event"]["generation"] == 12


def test_api_archive_empty_query_is_stable(api_client: TestClient):
    token = _token(api_client)
    response = api_client.get("/archive/strategies", headers=_headers(token))
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_api_rejects_empty_species(api_client: TestClient):
    token = _token(api_client)
    response = api_client.post("/organisms", headers=_headers(token), json={"species": ""})
    assert response.status_code == 422


def test_deployment_artifacts_are_present():
    root = Path(__file__).parents[1]
    for relative in ["Dockerfile", "docker-compose.yml", "production/k8s/deployment.yaml", "production/helm/living-objects/Chart.yaml", "production/monitoring/alerts.yaml"]:
        assert (root / relative).exists()
