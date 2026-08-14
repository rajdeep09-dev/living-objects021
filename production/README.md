# Living Objects Production Platform

The `production/` package is the control plane for the Living Objects runtime. It provides an authenticated FastAPI API, a durable state store with SQLite/PostgreSQL-compatible URLs, an optional Redis cache, a bounded in-process evolution event broker, Prometheus metrics, container manifests, Kubernetes resources, and a Helm chart.

## Local install and launch

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[production,test]"
uvicorn production.api.main:app --host 0.0.0.0 --port 8000
```

The development token endpoint accepts `operator` / `living-objects` unless overridden by `LO_OPERATOR_USERNAME` and `LO_OPERATOR_PASSWORD`. Set `JWT_SECRET` and both operator variables in staging or production. The production deployment must never use the example defaults.

The interactive API is available at `http://localhost:8000/docs`, health is exposed at `/health`, Prometheus exposition at `/metrics`, and the authenticated evolution stream at `/ws/evolution?token=<jwt>`.

## Compose

```bash
cp production/config/config.yaml .env
docker compose up --build
```

Compose starts three API replicas behind the `api` service name, Redis for the cache layer, and a named volume for SQLite state. SQLite is suitable for a single-writer local or development deployment. Use PostgreSQL for a multi-replica production control plane; the API accepts `postgresql://` and `postgres://` URLs through `LIVING_OBJECTS_DATABASE_URL`.

## Kubernetes and Helm

The plain manifests are in `production/k8s/`. For a managed AWS EKS, Google GKE, or Azure AKS cluster, install the chart:

```bash
helm upgrade --install living-objects production/helm/living-objects \
  --set image.repository=your-registry/living-objects \
  --set image.tag=<immutable-tag> \
  --set secrets.jwtSecret=<random-strong-secret> \
  --set secrets.operatorPassword=<secret-from-your-secret-manager>
```

The chart exposes a `Deployment`, `Service`, persistent state volume, optional Redis URL, and an HPA using CPU, memory, and custom organism-count metrics where the cluster adapter supports them. For a real cloud rollout, use a managed PostgreSQL service, managed Redis, a container registry, a secret manager, TLS termination, network policies, and an ingress controller. The included chart is cloud-neutral Kubernetes input; it does not provision cloud accounts, IAM, databases, or certificates.

## Operational boundaries

The self-modifying behavior engine is intentionally not exposed as an unrestricted API endpoint. Any future code-generation integration must execute generated code in a separate sandbox with a read-only filesystem, no ambient credentials, bounded CPU/memory, network egress policy, and an approval or rollback path. The current API only accepts organism state and evolution telemetry.

