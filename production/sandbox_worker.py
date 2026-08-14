"""Stdin/stdout adapter for the isolated organism-code worker.

The worker accepts one JSON object from stdin and emits one JSON result. It has
no network listener and is intended to run in a separately constrained container
or pod. The actual code execution remains delegated to evolution.sandbox.
"""

from __future__ import annotations

import json
import sys

from evolution.sandbox import IsolatedSandbox, ResourceLimits


def main() -> int:
    raw = sys.stdin.read(1_000_001)
    if len(raw) > 1_000_000:
        print(json.dumps({"stdout": "", "stderr": "request too large", "exit_code": 1, "timed_out": False}))
        return 1
    try:
        request = json.loads(raw)
        limits = ResourceLimits(
            max_cpu_ms=int(request.get("max_cpu_ms", 500)),
            max_memory_mb=int(request.get("max_memory_mb", 32)),
            max_output_bytes=int(request.get("max_output_bytes", 4096)),
            allow_network=False,
            allow_filesystem=False,
        )
        result = IsolatedSandbox(limits).run(str(request.get("code", "")), request.get("timeout_ms"))
        print(json.dumps({"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code, "timed_out": result.timed_out}))
        return 0 if result.ok else 1
    except Exception as exc:
        print(json.dumps({"stdout": "", "stderr": f"{type(exc).__name__}: {exc}", "exit_code": 1, "timed_out": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
