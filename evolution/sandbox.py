"""Subprocess isolation for generated organism code.

This module deliberately treats CPython AST filtering as an input validator, not
as a security boundary. Generated code is executed in a separate process with
bounded CPU, address space, output, and wall-clock lifetime. Stronger production
deployments should add an OS/container sandbox with network namespaces and a
read-only root filesystem around this worker.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResourceLimits:
    max_cpu_ms: int = 500
    max_memory_mb: int = 32
    max_output_bytes: int = 4096
    allow_network: bool = False
    allow_filesystem: bool = False


@dataclass(frozen=True)
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


_WORKER = r'''
import ast
import builtins
import pathlib
import sys

source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(source, filename="<organism-python>")
blocked_names = {"__builtins__", "__import__", "eval", "exec", "compile", "open", "input"}
blocked_attrs = {"__class__", "__bases__", "__subclasses__", "__mro__", "__globals__", "__getattribute__"}
for node in ast.walk(tree):
    if isinstance(node, ast.Import | ast.ImportFrom):
        raise PermissionError("imports are disabled in the isolated sandbox")
    if isinstance(node, ast.Name) and node.id in blocked_names:
        raise PermissionError(f"name is blocked: {node.id}")
    if isinstance(node, ast.Attribute) and node.attr in blocked_attrs:
        raise PermissionError(f"attribute is blocked: {node.attr}")

safe_builtins = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
    "enumerate": enumerate, "float": float, "int": int, "len": len,
    "list": list, "max": max, "min": min, "print": print, "range": range,
    "repr": repr, "str": str, "sum": sum, "tuple": tuple,
}
namespace = {"__builtins__": safe_builtins}
if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
    value = eval(compile(ast.Expression(tree.body[0].value), "<organism-python>", "eval"), namespace, namespace)
    if value is not None:
        print(value)
else:
    exec(compile(tree, "<organism-python>", "exec"), namespace, namespace)
'''


def _set_limits(limits: ResourceLimits) -> None:
    import resource

    memory = max(1, limits.max_memory_mb) * 1024 * 1024
    cpu_seconds = max(1, (limits.max_cpu_ms + 999) // 1000)
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))


class IsolatedSandbox:
    """Run generated snippets outside the calling Python process."""

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self.limits = limits or ResourceLimits()

    def run(self, code: str, timeout_ms: int | None = None) -> SandboxResult:
        limits = self.limits
        timeout = max(1, timeout_ms if timeout_ms is not None else limits.max_cpu_ms) / 1000
        temp_dir = tempfile.mkdtemp(prefix="living-objects-sandbox-")
        code_path = os.path.join(temp_dir, "organism.py")
        try:
            with open(code_path, "w", encoding="utf-8") as handle:
                handle.write(code)
            environment = {"PATH": os.defpath, "PYTHONIOENCODING": "utf-8"}
            process = subprocess.Popen(
                [sys.executable, "-I", "-S", "-c", _WORKER, code_path],
                cwd=temp_dir,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=lambda: _set_limits(limits),
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return SandboxResult(
                    stdout=stdout[: limits.max_output_bytes],
                    stderr=stderr[: limits.max_output_bytes],
                    exit_code=process.returncode or 0,
                    timed_out=False,
                )
            except subprocess.TimeoutExpired as exc:
                process.kill()
                stdout, stderr = process.communicate()
                return SandboxResult(
                    stdout=(stdout or exc.stdout or "")[: limits.max_output_bytes],
                    stderr=(stderr or exc.stderr or "")[: limits.max_output_bytes],
                    exit_code=-9,
                    timed_out=True,
                )
        except Exception as exc:  # Never turn untrusted code into a server error.
            return SandboxResult(stdout="", stderr=f"{type(exc).__name__}: {exc}", exit_code=1, timed_out=False)
        finally:
            try:
                os.unlink(code_path)
                os.rmdir(temp_dir)
            except OSError:
                pass


__all__ = ["IsolatedSandbox", "ResourceLimits", "SandboxResult"]
