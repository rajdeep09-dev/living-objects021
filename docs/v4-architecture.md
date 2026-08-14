# BEAST v4 Architecture

BEAST v4 extends the v3 civilization control plane into a bounded research substrate. A parallel universe is a versioned state branch, a physics law is a checked transformation, and consciousness is a normalized proxy metric rather than a claim about subjective experience.

| Layer | Responsibility | Primary modules |
|---|---|---|
| Safety boundary | Isolation, limits, validation, credentials, replay controls | `evolution/sandbox.py`, `production/middleware/` |
| Computation | Bounded universal machine and self-simulation | `evolution/turing.py` |
| Digital physics | Invariants, law mutation, branching, divergence fingerprints | `evolution/physics.py` |
| Temporal state | Ancestry, bounded revision, paradox checks | `evolution/temporal.py` |
| Civilization | Antibodies, epistemics, memory, tournaments | `immunity.py`, `epistemic.py`, `memory_palace.py`, `tournament.py` |
| Cultural expression | Morphogenesis, writing, substrate export | `morphogenetic_ai.py`, `writing_system.py`, `substrate.py` |
| Control plane | Authenticated routes and typed WebSocket events | `production/api/v4/` |
| Human observatory | Ten operator panels | `web/client/src/components/V4Panels.tsx` |

The v4 route state remains process-local for research reproducibility. Production deployments should replace it with a transactional shared store and Redis or NATS event fan-out. The substrate worker accepts structured export requests only and does not execute organism-provided source code.

```text
operator → authenticated /v4 route → bounded engine → typed event → WebSocket stream
                                      ↓
                              benchmark + audit record
```
