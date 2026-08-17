from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("JWT_SECRET", "beast-v9-local-test-secret-012345678901234567890123")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import production.api.main as api_main  # noqa: E402
from production.api.main import app, settings  # noqa: E402
from production.api.v9 import routes as v9_routes  # noqa: E402
from production.auth import encode_jwt  # noqa: E402
from production.middleware.rate_limit import RateLimiter  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    fresh = v9_routes.V9ControlState(artifact_dir=tmp_path)
    monkeypatch.setattr(v9_routes, "state", fresh)
    monkeypatch.setattr(api_main, "v9_state", fresh)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    token = encode_jwt({"sub": settings.operator_username, "role": "operator"}, settings.jwt_secret, settings.jwt_ttl_seconds)
    return {"Authorization": f"Bearer {token}"}


def test_v9_requires_operator_and_discloses_bounded_no_worker_contract(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/v9/snapshot").status_code == 401
    response = client.get("/v9/snapshot", headers=auth_headers)
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["worker"]["configured"] is False
    assert snapshot["execution_boundary"]["generated_source_executed"] is False


def test_v9_evidence_exposes_real_discoveries_and_clean_curriculum_boundaries(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v9/evidence", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["discoveries"]) == 5
    assert body["audits"]["clean-sorting"]["status"] == "NEGATIVE_RESULT"
    assert len(body["curriculum"]["stages"]) == 5


def test_v9_runs_only_short_inline_experiments_and_can_reproduce_and_export_them(client: TestClient, auth_headers: dict[str, str]) -> None:
    deferred = client.post("/v9/runs", headers=auth_headers, json={"generations": 26})
    assert deferred.status_code == 201
    assert deferred.json()["status"] == "requires_preregistered_campaign"

    response = client.post(
        "/v9/runs",
        headers=auth_headers,
        json={"task": "manhattan-distance", "generations": 2, "population_size": 4, "seed": 91},
    )
    assert response.status_code == 201
    run = response.json()["run"]
    assert run["execution_boundary"]["network_calls"] == 0
    reproduced = client.post("/v9/reproduce", headers=auth_headers, json={"run_id": run["run_id"]})
    assert reproduced.status_code == 200
    assert reproduced.json()["reproduction"]["verified"] is True
    exported = client.post("/v9/export", headers=auth_headers, json={"run_id": run["run_id"], "target": "python"})
    assert exported.status_code == 200
    assert "source-only" in exported.json()["export"]["execution_boundary"]


def test_v9_rejects_unconfigured_federation_import_without_admitting_any_record(client: TestClient, auth_headers: dict[str, str]) -> None:
    snapshot = client.get("/v9/federation", headers=auth_headers)
    assert snapshot.status_code == 200
    assert snapshot.json()["configured"] is False
    rejected = client.post("/v9/federation/import", headers=auth_headers, json={"envelope": {}})
    assert rejected.status_code == 409


def test_v9_inline_run_rate_policy_allows_three_requests_per_minute_and_rejects_the_fourth() -> None:
    limiter = RateLimiter()
    outcomes = [limiter.allow("127.0.0.1:POST:/v9/runs:3/minute", 3, 60) for _ in range(4)]

    assert [allowed for allowed, _ in outcomes] == [True, True, True, False]
    assert outcomes[-1][1] >= 1
