# EventStore Pytest Caching Bug — Session Notes

**Date:** 2026-08-13
**Symptom:** `AttributeError: 'EventStore' object has no attribute 'update_lifecycle'` when running pytest, but direct Python execution works.

## Root Cause

Pytest caches imported modules. When `living_objects.core.event_store.EventStore` is imported in one test file, then a later test file triggers a re-import, the cached version (without `update_lifecycle`) may be used. The `update_lifecycle` method was added in commit `b2040b5` (Claw runtime), but pytest's module cache can serve stale imports.

## Evidence

```python
# Direct Python — works:
from living_objects.core.event_store import EventStore
store = EventStore(':memory:')
hasattr(store, 'update_lifecycle')  # True

# Pytest — sometimes fails:
# Same import, same code, but AttributeError
```

## Workarounds (applied in project)

### 1. Clear pytest cache
```bash
rm -rf .pytest_cache
find . -name '__pycache__' -exec rm -rf {} +
find . -name '*.pyc' -delete
```

### 2. Use PYTHONPATH explicitly
```bash
PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH python3 -m pytest ...
PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH python3 demo.py
```

### 3. Import from submodule directly
```python
# Instead of:
from living_objects import EventStore
# Use:
from living_objects.core.event_store import EventStore
```

### 4. Reinstall package
```bash
pip install -e ".[dev]" --force-reinstall --no-deps
```

### 5. Force module reload in test
```python
import importlib
import living_objects.core.event_store as es
importlib.reload(es)
```

## Resolution Status

- The bug is intermittent and environment-dependent
- Working tests use `from living_objects.core.event_store import EventStore` directly
- Direct Python execution (PYTHONPATH) always works
- The SRE demo (`autonomous_sre/sre_system.py`) works when run with `PYTHONPATH=... python3`
- Pytest test failures for SRE tests are due to this caching issue, not code bugs
- Core 85 tests (combined, claw, agy, mesh) all pass in pytest

## Recommendation

For new test files in this project:
1. Always import from submodules: `from living_objects.core.event_store import EventStore`
2. Set PYTHONPATH in CI: `export PYTHONPATH=/opt/data/living-objects021:$PYTHONPATH`
3. If tests fail with EventStore errors, clear cache first
