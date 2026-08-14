# BEAST v4 Developer Guide

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[production,test,dev]"
export ENVIRONMENT=development APP_ENV=development
pytest -q
python3 scripts/run_v4_benchmarks.py --output docs/v4-benchmark-results.md
uvicorn production.api.main:app --reload --port 8000
```

For the observatory, run `cd web && pnpm install && pnpm dev`. The lightweight SDK is importable as `from sdk import BeastV4Client` and uses only the Python standard library.

## Extension rules

New engines should have a small public contract, deterministic fixtures, explicit limits, and a clear research-mode caveat. New API writes must validate identifiers, preserve operator attribution, publish a typed event, and have a negative test. New execution paths must use the isolated boundary; never add a direct `exec`, `eval`, shell, or network call to an organism-facing module.

## Release checklist

Run the full Python suite, compile `evolution production sdk`, run the benchmark harness, type-check and build both web worktrees, render the observatory at desktop and mobile widths, scan tracked files for credentials, and record the commit in the release notes.
