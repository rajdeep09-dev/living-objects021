"""Prometheus metrics used by API and evolution workers."""

from __future__ import annotations

from typing import Any

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except ImportError:  # pragma: no cover - only used before package installation
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _Metric:
        def __init__(self, *_: Any, **__: Any) -> None:
            self.value = 0.0

        def inc(self, amount: float = 1.0) -> None:
            self.value += amount

        def set(self, value: float) -> None:
            self.value = value

        def observe(self, _: float) -> None:
            pass

    Counter = Gauge = Histogram = _Metric  # type: ignore

    def generate_latest() -> bytes:
        return b"# prometheus-client is not installed\n"


ORGANISMS = Gauge("living_objects_organisms", "Current organism count")
FITNESS = Gauge("living_objects_average_fitness", "Average current fitness")
CULTURE = Gauge("living_objects_cultural_complexity", "Current cultural complexity")
NOVELTY = Counter("living_objects_novelty_total", "Novel behavioral descriptors discovered")
GENERATIONS = Counter("living_objects_generations_total", "Completed evolution generations")
REQUESTS = Counter("living_objects_api_requests_total", "API requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("living_objects_api_request_seconds", "API request latency")
ARCHIVE_ERRORS = Counter("living_objects_archive_errors_total", "Archive errors")

