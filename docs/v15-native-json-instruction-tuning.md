# Native 28.9M JSON Instruction-Tuning Contract

## Purpose and scope

This contract defines a finite local instruction-tuning branch for the existing **28,864,544-parameter** BEAST-BRAIN byte transformer. It tunes exact JSON formatting for one existing controller schema. It does not add a general-purpose instruction-following model, a coding model, or a reasoning system.

| Input | Rule | Reason |
|---|---|---|
| Base checkpoint | The completed local v14 checkpoint is read by digest and never overwritten. | Preserves the original training evidence. |
| Supervision | 56 checked-in, default-profile primitive records only. | No invented targets, explanations, model-generated data, network data, or learner self-training. |
| Held-out set | 10 source-disjoint primitive records. | Separates JSON language-loss measurement from tuning rows. |
| Runtime | Finite local CPU process, deterministic seed, maximum 3,600 seconds, atomic checkpoints. | Prevents indefinite or background operation. |
| Runtime format | Native PyTorch checkpoint. | The custom byte-transformer has no proven GGUF/Ollama conversion path. |

## Measured outputs

The run records held-out next-byte negative log likelihood and a single bounded, prefix-constrained JSON completion. The leading `{` is a formatting constraint; it does not provide a primitive name, signature, description, rationale, or answer. The full resulting text is passed unchanged to the existing fail-closed controller. The controller may reject it for any reason.

> A valid JSON object is only a syntax result. It is **not** treated as evidence of reasoning, code generation, task correctness, safe autonomy, or improvement of BEAST’s evolutionary benchmark.

The artifact stores completion hashes and controller audit metadata rather than generated text. It records zero network calls, zero downloads, zero persistent workers, and zero execution of generated text.
