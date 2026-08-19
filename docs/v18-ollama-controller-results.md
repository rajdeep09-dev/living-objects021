# v18 Local Ollama Controller Measurements

## Purpose and preregistered gate

Version 18 evaluated a temporary local `qwen2.5-coder:1.5b` Ollama model on ten source-backed, deterministic records held out from the v15 instruction-training split. The task was narrow: translate redacted approved-primitive metadata into the existing controller JSON contract. Expected primitive names were withheld from prompts and saved only as digests. The evaluator persisted no generated text, did not execute it, did not mutate the primitive registry, and did not select a primitive for evolution.

The promotion gate was **exact expected primitive name plus accepted controller decision** on held-out records. JSON syntax or controller acceptance alone could not pass the gate.

## Measurements

| Mode | JSON form | Required fields | Exact expected name | Controller accepted | Exact name and accepted | Gate result |
|---|---:|---:|---:|---:|---:|---|
| Raw local decoding, `temperature=0` | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | Failed |
| Ollama provider-side JSON Schema, `temperature=0` | 10/10 | 10/10 | 0/10 | 2/10 | 0/10 | Failed |

The provider-side JSON Schema parameter changed response **form** only. Its two accepted controller records named already registered but incorrect primitives; none recovered the expected held-out primitive. Therefore there is no semantic task-correct controller result, no SDK guidance surface, and no evolution integration.

## Boundaries

- The raw run remains the raw-decoding measurement; the JSON-Schema run is a separately labelled provider-constrained diagnostic, not a replacement baseline.
- This tested one downloaded instruction-tuned model, ten records, one local host, and one controller contract. It is not evidence of reasoning, coding, general language ability, autonomous improvement, or frontier-model equivalence.
- The custom 28.9M byte transformer remains a separate native architecture. It was not converted to GGUF or loaded by Ollama.
- Ollama was temporary local development infrastructure. No model weights are tracked in the repository, no public model service is deployed, and no persistent worker is configured.

## Evidence

- Raw compact artifact: `reports/v18/ollama-raw-controller-baseline/run.json`
- Corrected provider-constrained compact artifact: `reports/v18/ollama-json-schema-controller-diagnostic-v2/run.json`
- Client and evaluator: `agnes_brain/ollama_client.py`, `agnes_brain/ollama_controller_benchmark.py`
- Feasibility and documentation references: `docs/v18-ollama-pivot-feasibility.md`
