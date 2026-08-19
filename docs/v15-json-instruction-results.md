# BEAST-BRAIN v15 Native JSON Instruction-Tuning Result

## Result

The exact 28,864,544-parameter native byte transformer was instruction-tuned from the verified v14 base checkpoint on **56** provenance-labelled, default-profile primitive JSON records. The held-out evaluator contained **10** source-disjoint records. The finite run completed **1,000** steps in **352.30 seconds**, under its 1,200-second deadline.

| Declared metric | Before | After | Interpretation |
|---|---:|---:|---|
| Held-out byte-level NLL | 2.471145 | 0.096428 | Local next-byte prediction improved on the declared JSON distribution. |
| Valid JSON rate | — | 0% | The deterministic generated continuation was not parseable JSON. |
| Exact controller-schema rate | — | 0% | No generated output matched the controller’s required key set. |
| Default-profile compliance | — | 0% | No generated primitive payload was eligible for profile validation. |
| Controller admission | — | 0% | The controller rejected the continuation as `invalid_json`. |

> The loss reduction is **not** evidence of Claude-like reasoning, coding competence, or usable BEAST guidance. The sole generated continuation failed the first safety boundary, JSON parsing, and was never executed.

## Runtime and artifact boundary

The run used a local native PyTorch checkpoint, a local source-labelled data manifest, deterministic seed `20260820`, and atomic checkpointing. It made no network calls, downloaded no model/data/weights, started no persistent worker, and did not execute generated text. The base v14 checkpoint was read-only; the v15 tuning checkpoint is a separately identified local artifact.

The project’s custom byte-transformer is not a supported Ollama import architecture, and the environment has neither Ollama nor a GGUF conversion utility. No GGUF was created. Native checkpoint inference is therefore the only supported runtime.

## References

[1]: https://docs.ollama.com/import "Ollama Import Models documentation"
