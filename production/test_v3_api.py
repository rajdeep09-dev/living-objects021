from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("JWT_SECRET", "beast-v3-local-test-secret-012345678901234567890123")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from production.api.main import app, settings  # noqa: E402
from production.api.v3 import routes as v3_routes  # noqa: E402
from production.auth import encode_jwt  # noqa: E402


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    fresh = v3_routes.V3ControlState()
    monkeypatch.setattr(v3_routes, "state", fresh)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    token = encode_jwt({"sub": settings.operator_username, "role": "operator"}, settings.jwt_secret, settings.jwt_ttl_seconds)
    return {"Authorization": f"Bearer {token}"}


def test_v3_requires_bearer_token(client: TestClient) -> None:
    assert client.get("/v3/market/listings").status_code == 401


def test_v3_rejects_non_operator_token(client: TestClient) -> None:
    token = encode_jwt({"sub": "reader", "role": "reader"}, settings.jwt_secret, settings.jwt_ttl_seconds)
    assert client.get("/v3/market/listings", headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_v3_market_register_buy_and_price_feed(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/v3/market/listings", headers=auth_headers, json={"name": "coordination", "source_code": "return 1", "descriptor": "coordination", "effectiveness": 1.0, "author_id": "seller"})
    assert response.status_code == 201
    first_price = response.json()["price"]
    purchase = client.post("/v3/market/listings/coordination/buy", headers=auth_headers, json={"buyer_id": "buyer"})
    assert purchase.status_code == 200
    listings = client.get("/v3/market/listings", headers=auth_headers).json()["items"]
    assert listings[0]["price"] < first_price


def test_v3_identifier_validation_blocks_pathological_market_names(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/v3/market/listings", headers=auth_headers, json={"name": "x;DROP TABLE strategies", "source_code": "return 1", "descriptor": "bad", "effectiveness": 0.5, "author_id": "attacker"})
    assert response.status_code == 422


def test_v3_diplomacy_exchange_round_trip(client: TestClient, auth_headers: dict[str, str]) -> None:
    for ecosystem_id in ("alpha", "beta"):
        assert client.post("/v3/ecosystems", headers=auth_headers, json={"ecosystem_id": ecosystem_id}).status_code == 201
    for index in range(5):
        client.post("/v3/market/listings", headers=auth_headers, json={"name": f"a{index}", "source_code": "return 1", "descriptor": "a", "effectiveness": 0.8, "author_id": "alpha"})
        client.post("/v3/market/listings", headers=auth_headers, json={"name": f"b{index}", "source_code": "return 1", "descriptor": "b", "effectiveness": 0.8, "author_id": "beta"})
        v3_routes.state.ecosystems["alpha"].memome.contribute(v3_routes.state.market.listings[f"a{index}"].strategy)
    # The public API uses the shared v3 memome for listings; seed both ecosystem ledgers explicitly for the exchange.
    for index in range(5):
        v3_routes.state.ecosystems["alpha"].memome.contribute(v3_routes.state.market.listings[f"a{index}"].strategy)
        v3_routes.state.ecosystems["beta"].memome.contribute(v3_routes.state.market.listings[f"b{index}"].strategy)
    proposal = client.post("/v3/diplomacy/proposals", headers=auth_headers, json={"our_ecosystem_id": "alpha", "their_ecosystem_id": "beta", "our_offer": [f"a{i}" for i in range(5)], "our_request": [f"b{i}" for i in range(5)]})
    assert proposal.status_code == 201
    accepted = client.post(f"/v3/diplomacy/proposals/{proposal.json()['proposal_id']}/accept", headers=auth_headers)
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True


def test_v3_benchmark_quantum_spiking_and_improvement_endpoints(client: TestClient, auth_headers: dict[str, str]) -> None:
    benchmark = client.post("/v3/benchmarks/synthesize", headers=auth_headers, json={"difficulty": 0.4})
    assert benchmark.status_code == 200 and benchmark.json()["difficulty"] == 0.4
    measured = client.post("/v3/quantum/measure", headers=auth_headers, json={"amplitudes": {"mutation_rate:0.1": 1.0}, "seed": 7})
    assert measured.status_code == 200
    spikes = client.post("/v3/spiking/forward", headers=auth_headers, json={"inputs": [2.0, 0.0], "timesteps": 3})
    assert spikes.status_code == 200 and 0 in spikes.json()["spikes"]
    proof = client.post("/v3/improvement/prove", headers=auth_headers, json={"invariant": "population_viability", "witness_runs": 1000})
    assert proof.status_code == 200 and proof.json()["accepted"] is True


def test_v3_archaeology_and_consciousness_endpoints(client: TestClient, auth_headers: dict[str, str]) -> None:
    listing = client.post("/v3/market/listings", headers=auth_headers, json={"name": "forgotten", "source_code": "return 1", "descriptor": "rare", "effectiveness": 0.8, "author_id": "dead", "generation": 0}).json()
    # Registering the organism creates its adapter; the strategy remains unused and is therefore archaeologically eligible.
    archaeology = client.post("/v3/archaeology/pass", headers=auth_headers, json={"target_id": "new", "cutoff_generation": 10})
    assert archaeology.status_code == 200
    assert archaeology.json()["resurrected"] >= 1
    awareness = client.get("/v3/consciousness/new", headers=auth_headers)
    assert awareness.status_code == 200 and 0 <= awareness.json()["composite"] <= 1


def test_v3_websocket_rejects_invalid_token(client: TestClient) -> None:
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/v3/evolution?token=bad"):
            pass
