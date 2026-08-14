from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from production.api import main as api
from production.api.v2 import routes


@pytest.fixture()
def v2_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    old_state_routes = routes.control_state
    old_state_main = api.control_state
    monkeypatch.setenv("V2_MEMOME_PATH", str(tmp_path / "v2.sqlite3"))
    state = routes.V2ControlState()
    routes.control_state = state
    api.control_state = state
    with TestClient(api.app) as client:
        yield client
    state.store.close()
    routes.control_state = old_state_routes
    api.control_state = old_state_main


@pytest.fixture()
def auth_headers(v2_client: TestClient) -> dict[str, str]:
    response = v2_client.post("/auth/token", json={"username": "operator", "password": "living-objects"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def token_from(headers: dict[str, str]) -> str:
    return headers["Authorization"].split(" ", 1)[1]


def test_v2_routes_require_jwt(v2_client: TestClient):
    assert v2_client.get("/v2/constitution").status_code == 401
    assert v2_client.get("/v2/organisms").status_code == 401


def test_constitution_patch_and_mutation(v2_client: TestClient, auth_headers: dict[str, str]):
    response = v2_client.patch("/v2/constitution", headers=auth_headers, json={"novelty_weight": 0.7})
    assert response.status_code == 200
    assert response.json()["novelty_weight"] == pytest.approx(0.7)
    mutation = v2_client.post("/v2/constitution/mutate?seed=4", headers=auth_headers)
    assert mutation.status_code == 200
    assert mutation.json()["before"] != mutation.json()["after"]


def test_organism_spawn_inspect_and_reproduce(v2_client: TestClient, auth_headers: dict[str, str]):
    spawned = v2_client.post("/v2/organisms", headers=auth_headers, json={"organism_id": "alpha"})
    assert spawned.status_code == 201
    child = v2_client.post("/v2/organisms/alpha/reproduce?seed=2", headers=auth_headers)
    assert child.status_code == 201
    assert child.json()["parent_ids"] == ["alpha"]
    inspected = v2_client.get(f"/v2/organisms/{child.json()['organism_id']}", headers=auth_headers)
    assert inspected.status_code == 200
    assert inspected.json()["generation"] == 1


def test_strategy_publish_list_and_adopt(v2_client: TestClient, auth_headers: dict[str, str]):
    v2_client.post("/v2/organisms", headers=auth_headers, json={"organism_id": "adopter"})
    published = v2_client.post(
        "/v2/strategies",
        headers=auth_headers,
        json={
            "name": "bridge",
            "source_code": "def bridge(x):\n    return x + 1",
            "descriptor": "river-crossing",
            "effectiveness": 0.91,
            "author_id": "ancestor",
            "generation": 2,
        },
    )
    assert published.status_code == 201
    strategy_id = published.json()["strategy_id"]
    listed = v2_client.get("/v2/strategies?q=river", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    adopted = v2_client.post(
        f"/v2/strategies/{strategy_id}/adopt",
        headers=auth_headers,
        json={"organism_id": "adopter"},
    )
    assert adopted.status_code == 200
    assert adopted.json()["adopted"] is True


def test_gossip_and_lineage(v2_client: TestClient, auth_headers: dict[str, str]):
    parent = v2_client.post(
        "/v2/strategies",
        headers=auth_headers,
        json={"name": "parent", "source_code": "def p(x):\n    return x", "descriptor": "p", "effectiveness": 0.4, "author_id": "a", "generation": 0},
    ).json()
    child = v2_client.post(
        "/v2/strategies",
        headers=auth_headers,
        json={"name": "child", "source_code": "def c(x):\n    return x", "descriptor": "c", "effectiveness": 0.8, "author_id": "b", "generation": 1, "parent_ids": [parent["strategy_id"]]},
    )
    assert child.status_code == 201
    lineage = v2_client.get("/v2/memome/lineage", headers=auth_headers)
    assert {"parent": parent["strategy_id"], "child": child.json()["strategy_id"]} in lineage.json()["edges"]
    gossip = v2_client.post("/v2/memome/gossip", headers=auth_headers, json={"peer_node_id": "node-b", "strategies": []})
    assert gossip.status_code == 200


def test_red_team_emits_defense_event(v2_client: TestClient, auth_headers: dict[str, str]):
    v2_client.post("/v2/organisms", headers=auth_headers, json={"organism_id": "target"})
    response = v2_client.post("/v2/red-team/attack?target_id=target", headers=auth_headers, json={"attacker_id": "probe"})
    assert response.status_code == 200
    assert response.json()["result"]["detected"] is True
    assert response.json()["event"]["type"] == "red_team_attack"


def test_tools_and_dsl(v2_client: TestClient, auth_headers: dict[str, str]):
    v2_client.post("/v2/organisms", headers=auth_headers, json={"organism_id": "tool-user"})
    tools = v2_client.get("/v2/tools", headers=auth_headers)
    assert tools.status_code == 200
    assert {item["name"] for item in tools.json()["items"]} >= {"python_exec", "shell_cmd"}
    result = v2_client.post("/v2/organisms/tool-user/tools/python_exec", headers=auth_headers, json={"kwargs": {"code": "print(2 + 2)"}})
    assert result.status_code == 200
    assert result.json()["result"] == "4"
    expressed = v2_client.post("/v2/dsl/express", headers=auth_headers, json={"condition": "high", "action": "coop", "fallback": "defect"})
    assert expressed.status_code == 200
    parsed = v2_client.post("/v2/dsl/parse", headers=auth_headers, json={"source": expressed.json()["source"]})
    assert parsed.json()["intent"]["action"] == "coop"


def test_energy_and_ancestry(v2_client: TestClient, auth_headers: dict[str, str]):
    v2_client.post("/v2/organisms", headers=auth_headers, json={"organism_id": "root"})
    child = v2_client.post("/v2/organisms/root/reproduce", headers=auth_headers).json()["organism_id"]
    energy = v2_client.post("/v2/energy/measure", headers=auth_headers, json={"organism_id": child, "quality": 0.9, "operations": 10, "memory_allocated": 64})
    assert energy.status_code == 200
    assert energy.json()["score"]["efficiency"] == pytest.approx(0.09)
    ancestry = v2_client.get(f"/v2/ancestry/{child}", headers=auth_headers)
    assert ancestry.status_code == 200
    assert ancestry.json()["ancestors"][0]["organism_id"] == "root"


def test_v2_events_and_websocket(v2_client: TestClient, auth_headers: dict[str, str]):
    v2_client.post("/v2/organisms", headers=auth_headers, json={"organism_id": "streamed"})
    events = v2_client.get("/v2/events", headers=auth_headers)
    assert events.status_code == 200
    assert events.json()["items"][0]["type"] == "organism_born"
    with v2_client.websocket_connect(f"/ws/v2/evolution?token={token_from(auth_headers)}") as socket:
        streamed = socket.receive_json()
    assert streamed["type"] == "organism_born"
