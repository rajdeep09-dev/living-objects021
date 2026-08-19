# V18 Ollama Pivot Feasibility Record

**Status:** local runtime feasible for a measured optional experiment; not a deployment claim.

## Local assessment

On 2026-08-19, the development sandbox had no `ollama` executable. It had 6 CPU cores, approximately 20 GiB available memory, and 34 GiB free disk space. The official Ollama library lists `qwen2.5-coder:1.5b` as a 986 MB Q4_K_M artifact, so installing the runtime and downloading that single model is feasible in this temporary development environment. This does **not** establish a persistent hosted runtime: the sandbox can hibernate, and the existing observatory’s deployed service has no Ollama process or model weights.

## API and evaluation contract

The official local API exposes `POST http://localhost:11434/api/generate` with `stream: false`. It supports both raw text output and provider-enforced `format: "json"` or a JSON Schema. The initial baseline will deliberately use **raw output**, so raw JSON validity is measured rather than guaranteed by an API-level schema constraint. A later, separately labelled integration may use a schema only as a transport safeguard; provider-enforced format compliance must never be counted as model-semantic capability.

The baseline must record three separate outcomes for each prompt:

| Measure | Meaning |
|---|---|
| Raw JSON validity | `json.loads` accepts the unmodified model response. |
| Contract validity | Required fields and type constraints pass. |
| Task appropriateness | A deterministic, prompt-specific rule validates the returned name, required type shape, or explanation/test-case condition. |

The client must be local-only and fail closed: connection errors, malformed responses, unknown models, or invalid outputs return unavailable values and cannot affect evolutionary selection, execute generated code, or authorize a primitive.

## Architecture boundary

This pivot does not convert the 28.9M native byte transformer into GGUF, does not transfer its weights into Qwen, and does not demonstrate Claude-class reasoning or coding. It evaluates a separate, instruction-tuned, third-party local model as an optional explanation/proposal service. Any measured capability is limited to the preregistered prompts and deterministic validation rules.

## References

1. [Ollama Generate API](https://docs.ollama.com/api/generate) — local generation endpoint, `stream: false`, and `format` request field.
2. [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs) — JSON and JSON-schema enforcement, plus low-temperature guidance.
3. [Ollama qwen2.5-coder:1.5b library entry](https://ollama.com/library/qwen2.5-coder:1.5b) — local model identifier and published 986 MB Q4_K_M artifact size.
