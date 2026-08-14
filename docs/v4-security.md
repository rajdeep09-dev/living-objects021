# BEAST v4 Security and Threat Model

BEAST v4 treats generated strategies, signed proposals, wallets, and substrate artifacts as hostile inputs. The design is defense-in-depth and does not claim that an in-process Python sandbox is a complete multi-tenant trust boundary.

| Surface | Failure mode | Mitigation |
|---|---|---|
| Credential comparison | Timing leakage | `hmac.compare_digest` |
| Sandbox cleanup | Orphaned directories | Recursive cleanup and observable cleanup records |
| Wallets | Concurrent spend race | Lock-protected atomic debit |
| Diplomacy | Tampered or replayed proposal | Nonce, expiry, HMAC signature, consumed-nonce registry |
| Quantum measurement | Predictable randomness | Secure default RNG with deterministic test injection |
| Spiking state | NaN/overflow | Finite-value checks and hard clamps |
| Archaeology | Unsafe resurrection | Isolated sandbox validation before memome injection |
| Consciousness proxy | Unbounded Phi | Sigmoid normalization in `[0, 1]` |

Production requires TLS, rotated credentials, shared rate limiting, seccomp/AppArmor, cgroups, a read-only root filesystem, dropped capabilities, no service-account token, and no network for execution workers. Exported artifacts should carry a source hash, evaluator version, operator identity, and signature.
