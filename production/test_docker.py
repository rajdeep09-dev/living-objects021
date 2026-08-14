"""Static deployment artifact tests that do not require Docker-in-Docker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_is_multistage_and_non_root():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert dockerfile.count("FROM ") >= 2
    assert "USER living" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "uvicorn" in dockerfile


def test_dockerignore_excludes_state_and_git():
    ignored = (ROOT / ".dockerignore").read_text()
    assert ".git" in ignored
    assert "state" in ignored


def test_compose_has_three_api_replicas_and_redis():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    assert compose["services"]["api"]["deploy"]["replicas"] == 3
    assert "redis" in compose["services"]
    assert "living_objects_state" in compose["volumes"]


@pytest.mark.parametrize("service", ["api", "redis", "prometheus", "grafana"])
def test_compose_declares_observability_services(service: str):
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    assert service in compose["services"]


@pytest.mark.parametrize("manifest", ["deployment.yaml", "service.yaml", "hpa.yaml", "secret.example.yaml"])
def test_kubernetes_manifest_is_valid_yaml(manifest: str):
    data = yaml.safe_load((ROOT / "production" / "k8s" / manifest).read_text())
    assert data["apiVersion"]
    assert data["kind"]
    assert data["metadata"]["name"]


def test_hpa_targets_deployment_and_has_organism_metric():
    data = yaml.safe_load((ROOT / "production/k8s/hpa.yaml").read_text())
    assert data["spec"]["scaleTargetRef"]["name"] == "living-objects-api"
    assert any(metric["type"] == "Pods" for metric in data["spec"]["metrics"])


def test_kubernetes_has_three_initial_replicas():
    data = yaml.safe_load((ROOT / "production/k8s/deployment.yaml").read_text())
    assert data["spec"]["replicas"] == 3


def test_scaling_policy_targets_million_memes_per_shard():
    data = yaml.safe_load((ROOT / "production/config/scaling_policy.yaml").read_text())
    assert data["spec"]["shardCapacity"] == 1_000_000
    assert data["spec"]["targetOrganismsPerReplica"] == 2_500


def test_monitoring_alerts_cover_fitness_and_archive():
    data = yaml.safe_load((ROOT / "production/monitoring/alerts.yaml").read_text())
    expressions = [rule["expr"] for group in data["groups"] for rule in group["rules"]]
    assert any("average_fitness" in expression for expression in expressions)
    assert any("archive_errors" in expression for expression in expressions)


def test_grafana_dashboard_is_json_and_covers_core_panels():
    data = json.loads((ROOT / "production/monitoring/grafana-dashboard.json").read_text())
    titles = {panel["title"] for panel in data["panels"]}
    assert {"Fitness", "Cultural complexity", "Novelty discoveries"}.issubset(titles)

