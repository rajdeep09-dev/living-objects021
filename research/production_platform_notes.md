# Production Platform Notes

## Architecture facts

- FastAPI exposes native WebSocket routes and supports dependency injection for WebSocket authentication. The production implementation will keep the HTTP and WebSocket auth paths explicit.
- The official Prometheus Python client exposes application metrics in the standard text format and supports multiprocess mode. The first implementation will use process-safe counters and gauges, with Redis-backed cross-replica event state where aggregate consistency matters.
- Kubernetes Horizontal Pod Autoscaler scales a Deployment or StatefulSet using resource or custom metrics. The manifest will use `autoscaling/v2`, resource requests, and a custom organism-count metric target.

## Boundary decisions

- SQLite remains the default local state store to satisfy the requested `docker compose up` path. PostgreSQL is supported through a repository interface and environment configuration rather than being required for unit tests.
- Redis is the shared memome/event bus in containerized deployments. The API must degrade to an in-process broker for local tests and single-process development.
- JWT verification is self-contained and uses an environment-provided secret. No credential is committed to the repository.
- Agnes integration is optional and isolated behind an adapter. If unavailable or misconfigured, the evolution engine continues with deterministic local evaluation and records the degraded mode.
- The current platform package remains portable Python. Docker, Kubernetes, Helm, and the UI are delivery layers around it rather than hard-coded assumptions inside the evolution model.

## Official references

1. FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
2. Prometheus Python client: https://prometheus.github.io/client_python/
3. Kubernetes HPA: https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/
