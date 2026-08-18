# BEAST v11 Federation Secret-Safety Boundary

> **Never commit a federation secret, private key, `.env` file, or signing-key configuration file to a repository.** Treat a federation signing secret as a credential that can authenticate discovery records.

## Shipped implementation boundary

The current signed-discovery exchange is a **local, file-transfer MVP**. `SignedDiscoveryExchange` accepts key bytes supplied by the caller; it does not load, create, or persist a plaintext configuration file. The CLI obtains an explicit signing key from an environment variable and rejects a missing or too-short value. No network transport, peer registry, or background federation worker is implemented.

| Property | v11 status |
|---|---|
| Key source in shipped CLI | Caller-provided environment variable |
| Plaintext configuration-file parser | Not implemented |
| Public key registry / remote transport | Not implemented |
| Secret suitable for source control | **No** |

## Operator requirements

1. Supply a high-entropy key through the operating system’s secret manager or environment injection at runtime.
2. Add local secret files, if any future integration needs them, to `.gitignore` before use; set owner-only permissions.
3. Rotate the key and invalidate prior trust records if a key is exposed.
4. Do not describe a signed local record as a network-federated result. The receiving installation must independently re-evaluate the imported program.

This document does not make secret exchange, key rotation, remote transport, or multi-installation federation operational. It preserves the exact security boundary of the shipped local exchange.
