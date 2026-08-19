# BEAST v15 Final Verification

**Release date:** 2026-08-19
**Scope:** finite local structured-JSON instruction tuning of the v14 native byte transformer.

## Measured result

| Field | Observed value |
|---|---:|
| Architecture | Native byte-level causal transformer, 28,864,544 parameters |
| Base checkpoint | v14 local checkpoint; read-only during the v15 branch |
| Instruction data | 56 provenance-labelled default-profile primitive records |
| Held-out evaluator | 10 source-disjoint primitive records |
| Local tuning steps | 1,000 |
| Elapsed time | 352.30 seconds |
| Held-out byte NLL before / after | 2.471145 / 0.096428 |
| Valid JSON / exact schema / profile compliance / controller admission | 0% / 0% / 0% / 0% |
| Controller rejection | `invalid_json` |

The finite run improved the declared byte-level held-out NLL. It did **not** produce a parseable JSON response for the bounded deterministic completion, so it did not produce controller-admitted guidance and did not alter a grammar, execute text, or rerun a BEAST benchmark.

## Runtime and publication boundaries

The run used no model/data/weight download, network call, cloud inference, persistent worker, external action, or generated-text execution. It did not receive parent-model weights from Manus or this assistant. The custom byte transformer is not a documented Ollama import architecture; no Ollama runtime, GGUF converter, or compatible GGUF was present. Consequently, native PyTorch checkpoint inference is the only supported runtime, and no `.gguf` file exists to publish.

The local v15 tuning checkpoint is 346,516,701 bytes and exceeds ordinary repository-hosting practical limits. It remains local evidence and is deliberately excluded from Git history. This release contains reproducible source, dataset manifests, metric artifacts, digests, and tests, but not the binary checkpoint weights.

## Evidence

| Artifact | Purpose |
|---|---|
| `reports/v15/beast-brain-28m-json-instruction-20260819/run.json` | Primary bounded-run metrics, data digest, timing, and schema evaluation |
| `docs/v15-json-instruction-data-contract.md` | Source-labelled 56/10 structured-JSON data contract |
| `docs/v15-native-json-instruction-tuning.md` | Checkpoint branching, budget, and non-execution contract |
| `docs/v15-json-instruction-results.md` | Concise result and zero-admission boundary |
| `docs/v15-gguf-ollama-feasibility-audit.md` | Native-only compatibility analysis and official Ollama import reference |
