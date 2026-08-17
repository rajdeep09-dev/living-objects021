# BEAST v10 Package-Release Record

> **Status:** local distribution artifacts built and verified; **not published to PyPI**.

## Package identity

| Field | Recorded value |
|---|---|
| Distribution | `living-objects` |
| Version | `0.3.0` |
| Supported Python | `>=3.10` |
| Core runtime dependencies | None |
| Optional deployment extra | `living-objects[production]` |
| Console entry point | `living-objects` |

The public SDK is deliberately dependency-free at installation time.  FastAPI,
Pydantic, Prometheus, Redis, database, and server dependencies are isolated in
the optional `production` extra because they are not needed to import or run a
bounded local SDK evolution experiment.

## Built artifacts

| Artifact | SHA-256 |
|---|---|
| `living_objects-0.3.0-py3-none-any.whl` | `5887d21ad64c8005b06bd554f9993140785607401cd739ff03741db3d309e205` |
| `living_objects-0.3.0.tar.gz` | `516ee71382ed61b531e9c1233910c6da2cab123680cd14b58fa389a28ba3d2c0` |

Both artifacts were built locally with `uv build` on 2026-08-17.

## Isolated wheel validation

The wheel was installed with no dependencies into clean, repository-external
environments and ran `scripts/v10_distribution_smoke.py`.  That smoke test
imports only `living_objects`, performs a one-generation bounded Manhattan
run, verifies the documented `fitness` and `source_code` accessors, persists
its run artifact, and checks the zero-LLM / zero-network interpreter boundary.

| Python | Wheel installation | Public-SDK smoke run |
|---|---:|---:|
| 3.10.20 | Passed | Passed |
| 3.11.15 | Passed | Passed |
| 3.12.3 | Passed | Passed |

## PyPI gate

No PyPI project exists in this evidence record and no package has been
uploaded.  Publication requires all of the following before any upload is
attempted:

1. A PyPI owner creates or confirms the `living-objects` project namespace.
2. The owner supplies a scoped trusted-publishing configuration or a scoped
   upload token through the release environment.
3. The owner explicitly confirms the irreversible upload after reviewing the
   version and the artifact checksums above.
4. A release operator uploads the already verified artifacts and records the
   returned PyPI URL and immutable hashes in a follow-up evidence record.

Until those gates occur, installation is supported from a locally built wheel
or source checkout only; it is incorrect to claim `pip install living-objects`
will resolve from PyPI.
