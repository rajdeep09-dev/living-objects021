# BEAST v3 Security Model

BEAST v3 treats generated organism code as **untrusted research input**. The v2 in-process `exec` path remains available only as a compatibility mechanism for controlled experiments; the v3 execution path uses `evolution.sandbox.IsolatedSandbox` and the no-network `production/sandbox_worker.py` adapter.

## Threat model

The primary adversary is an organism-generated payload that attempts to escape its execution context, consume unbounded resources, read host files, open network connections, forge identity, flood mutation endpoints, or inject SQL through user-controlled identifiers. The API also assumes that a browser client may be malicious and that a compromised operator token must not become an implicit database administrator.

| Threat | v3 control | Residual risk |
|---|---|---|
| Python object-model escape | Subprocess worker, AST rejection, restricted builtins, isolated interpreter | A subprocess is not a complete kernel sandbox; use a hardened container or microVM for hostile tenants. |
| Infinite loop / memory bomb | Wall-clock timeout, `RLIMIT_CPU`, `RLIMIT_AS`, output cap | Host-level cgroup enforcement remains the deployment responsibility. |
| Shell abuse | Command allowlist plus child resource limits; worker has no shell listener | The allowlist must remain narrow and reviewed when expanded. |
| Brute-force token attempts | Per-IP rate limiter with Redis backend when available and `429`/`Retry-After` | A distributed deployment must use shared Redis, not the local fallback. |
| CORS abuse | Wildcards rejected in production; production origins must be HTTPS | Operators must configure the real origin list rather than copy development settings. |
| JWT forgery | Production rejects missing or short secrets; development default emits a warning | Secret rotation and key custody remain deployment controls. |
| SQL injection | Parameterized SQLite queries and identifier regex validation | Every future store path must follow the same validation rule. |
| Unauthorized mutation | v2/v3 write routes depend on `require_operator`; read routes are separately identified | Authorization is only as strong as the identity provider and operator secret. |

## Sandbox architecture

`IsolatedSandbox.run()` writes a short-lived script into a temporary directory, starts `python -I -S -c` in a child process, applies CPU and address-space limits, captures bounded stdout/stderr, and returns a `SandboxResult` for success, failure, or timeout. It never propagates an organism exception to the caller. The worker forces `allow_network=False` and `allow_filesystem=False` even when a request attempts to override them.

The design is deliberately honest: process isolation and AST checks reduce accidental and low-effort escapes, but **they are not equivalent to a production kernel boundary**. For public multi-tenant deployment, place the worker inside a read-only, no-network container with seccomp/AppArmor, cgroups, a non-root UID, and a separate node pool or microVM boundary.

## Security verification

The proof suite covers arithmetic success, object-model escape rejection, import and shell rejection, timeout behavior, resource policy defaults, production CORS validation, production JWT-secret rejection, SQL-injection identifiers, route authorization, rate-limit `429` semantics, and WebSocket admission. These are regression tests, not a substitute for an external penetration test.
