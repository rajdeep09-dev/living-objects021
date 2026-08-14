"""Dependency-light Python client for the authenticated BEAST v4 API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class BeastV4Error(RuntimeError):
    """Raised when a v4 request cannot be completed or returns a non-2xx status."""


@dataclass
class BeastV4Client:
    base_url: str = "http://127.0.0.1:8000"
    token: str | None = None
    timeout: float = 10.0

    def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(dict(payload)).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(self.base_url.rstrip("/") + path, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except (HTTPError, URLError, TimeoutError) as exc:
            detail = getattr(exc, "read", lambda: b"")()
            raise BeastV4Error(detail.decode("utf-8", errors="replace") or str(exc)) from exc

    def snapshot(self) -> dict[str, Any]:
        return self._request("GET", "/v4/snapshot")

    def universes(self) -> dict[str, Any]:
        return self._request("GET", "/v4/universes")

    def branch_universe(self, universe_id: str, law: str) -> dict[str, Any]:
        return self._request("POST", f"/v4/universes/{universe_id}/branch", {"law": law})

    def run_computation(self, input_tape: str = "_", step_limit: int = 10_000, transition_table: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", "/v4/computation/run", {"input_tape": input_tape, "step_limit": step_limit, "transition_table": transition_table or {}})

    def memory_snapshot(self) -> dict[str, Any]:
        return self._request("GET", "/v4/memory/snapshot")

    def evolve_writing(self) -> dict[str, Any]:
        return self._request("POST", "/v4/writing/evolve")

    def export_substrate(self, organism_id: str, substrate: str = "wasm") -> dict[str, Any]:
        return self._request("POST", "/v4/substrate/export", {"organism_id": organism_id, "substrate": substrate})
