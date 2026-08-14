from __future__ import annotations

import os

import pytest

from evolution.sandbox import IsolatedSandbox, ResourceLimits
from production.store_v2 import V2Store


@pytest.mark.parametrize(
    "code",
    [
        "import os",
        "from os import system",
        "open('/etc/passwd').read()",
        "input()",
        "eval('2+2')",
        "exec('pass')",
        "compile('pass', '', 'exec')",
        "().__class__",
        "().__class__.__bases__",
        "().__class__.__subclasses__()",
        "().__class__.__mro__",
        "globals()",
        "object.__getattribute__(1, '__class__')",
    ],
)
def test_sandbox_blocks_escape_constructs(code: str) -> None:
    result = IsolatedSandbox().run(code)
    assert not result.ok


def test_sandbox_allows_only_safe_arithmetic() -> None:
    result = IsolatedSandbox().run("sum(range(5))")
    assert result.ok and result.stdout.strip() == "10"


def test_sandbox_enforces_wall_clock_timeout() -> None:
    result = IsolatedSandbox(ResourceLimits(max_cpu_ms=100)).run("while True:\n    pass")
    assert result.timed_out and result.exit_code != 0


def test_sandbox_bounds_output() -> None:
    result = IsolatedSandbox(ResourceLimits(max_output_bytes=32)).run("print('x' * 100000)")
    assert len(result.stdout) <= 32


def test_sandbox_reports_syntax_failure() -> None:
    result = IsolatedSandbox().run("def")
    assert not result.ok and "SyntaxError" in result.stderr


@pytest.mark.parametrize("identifier", ["x' OR '1'='1", "name;DROP TABLE v2_strategies", "../escape"])
def test_store_rejects_sql_injection_identifiers(tmp_path, identifier: str) -> None:
    store = V2Store(tmp_path / "security.sqlite3")
    with pytest.raises(ValueError):
        store.get(identifier)
    store.close()


def test_store_rejects_malicious_publish_fields(tmp_path) -> None:
    store = V2Store(tmp_path / "security.sqlite3")
    with pytest.raises(ValueError):
        store.publish_fields(name="safe", source_code="return 1", descriptor="x';DROP", effectiveness=0.5, author_id="author", generation=0)
    store.close()


def test_worker_accepts_json_and_returns_json() -> None:
    import json
    import subprocess
    import sys

    process = subprocess.run([sys.executable, "production/sandbox_worker.py"], input=json.dumps({"code": "6 * 7"}), text=True, capture_output=True, check=False)
    payload = json.loads(process.stdout)
    assert payload["stdout"].strip() == "42"


def test_worker_never_enables_network_or_filesystem() -> None:
    import json
    import subprocess
    import sys

    process = subprocess.run([sys.executable, "production/sandbox_worker.py"], input=json.dumps({"code": "import socket"}), text=True, capture_output=True, check=False)
    assert json.loads(process.stdout)["exit_code"] != 0


def test_production_jwt_secret_policy_rejects_short_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "too-short")
    from production.config import Settings

    with pytest.raises(RuntimeError):
        Settings.from_env()


def test_production_cors_policy_rejects_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    from production.middleware.cors import CORSConfig

    with pytest.raises(ValueError):
        CORSConfig("production").validate_origins(["*"])


def test_rate_limiter_returns_retry_after_after_limit() -> None:
    from production.middleware.rate_limit import RateLimiter

    limiter = RateLimiter()
    assert limiter.allow("security", 1, 60)[0]
    allowed, retry_after = limiter.allow("security", 1, 60)
    assert not allowed and retry_after >= 1
