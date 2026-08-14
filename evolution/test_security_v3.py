from __future__ import annotations

from evolution.sandbox import IsolatedSandbox, ResourceLimits


def test_sandbox_runs_arithmetic_outside_calling_process() -> None:
    result = IsolatedSandbox().run("2 + 2")
    assert result.ok
    assert result.stdout.strip() == "4"


def test_sandbox_rejects_mro_escape_and_imports() -> None:
    result = IsolatedSandbox().run("().__class__.__bases__[0].__subclasses__()")
    assert not result.ok
    assert "blocked" in result.stderr or "PermissionError" in result.stderr
    imported = IsolatedSandbox().run("import os\nos.system('id')")
    assert not imported.ok


def test_sandbox_kills_infinite_loop_within_wall_clock_bound() -> None:
    result = IsolatedSandbox(ResourceLimits(max_cpu_ms=100)).run("while True:\n    pass")
    assert result.timed_out
    assert result.exit_code != 0
