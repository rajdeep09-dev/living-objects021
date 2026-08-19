# Reconciliation of the Attached `BEAST_UPDATE_v14.md` Guide After the v15 Release

**Status:** implementation audit and completed bounded native-only follow-up

## Purpose

The attached guide proposes transforming BEAST-BRAIN’s 28.9M custom byte transformer into an instruction-following GGUF/Ollama model, integrating its outputs into evolution, and comparing it with Claude. This audit maps each request to the actual released code and evidence rather than treating expected success criteria as observed results.

The relevant current result is the v15 native checkpoint attempt: 56 provenance-labelled train records, 10 source-disjoint held-out records, 1,000 finite CPU steps, and held-out byte NLL falling from 2.471145 to 0.096428. Its sole deterministic generated continuation was invalid JSON. Therefore measured JSON validity, exact-schema conformance, profile compliance, and controller admission were all **0%**. No generated text was executed. [1]

## Requirement-by-requirement disposition

| Attached guide module | Requested work | Released evidence or technical constraint | Disposition |
|---|---|---|---|
| A1.01 | Build an instruction dataset from the augmented corpus | v15 ships a source-labelled 56/10 source-disjoint controller-JSON corpus from approved local primitive metadata. It deliberately excludes invented explanations and does not rebrand templates as observed capability. | **Completed in a stricter form** |
| A1.02 | Prompt-only loss masking for instruction tuning | v16 implemented record-aware target-only loss masking with checked-in `instruction`, `input`, and `controller_json:` prompt serialization. Prompt labels are ignored and only declared controller-JSON bytes are scored. | **Implemented and locally tested** |
| A1.03–A1.05 | Train until an NLL target or 14/20 JSON pass rate | v16 ran one preregistered 1,800-second attempt rather than training until a desired score. It stopped at 3,248 steps, worsened held-out target NLL from 0.2009989224 to 0.2654667787, and had 0/10 valid JSON/schema/admission. | **Completed negative result; target not met** |
| B1.01–B1.06 | Export the custom checkpoint through Hugging Face into GGUF and quantize it | The model uses custom byte-transformer tensors and runtime semantics. Ollama documents supported Safetensors architecture imports and imports GGUF only after a genuine compatible conversion; the required architecture-aware converter/runtime is absent. [2] [3] | **Incompatible; do not fabricate a GGUF** |
| C1.01–C1.04 | Release, attach, and run a GGUF/Ollama Modelfile | No genuine GGUF exists, so a release asset, remote `FROM` URL, and Ollama test would misrepresent the runtime. Native checkpoints are intentionally excluded from Git history due to size. | **Blocked by B; not publishable** |
| D1.01–D1.06 | Ollama HTTP client | The requested client would depend on an inactive Ollama service and unavailable model artifact. Implementing it now would produce an API shell with no verified model. | **Deferred until genuine runtime and admission evidence exist** |
| E1.01–E1.05 | Auto-inject suggestions, explanations, and generated cases into evolution | The current output fails JSON parsing and controller admission. Auto-detection or evaluator augmentation must not be added before an objective proof of valid, safe output; no model output may alter registries or test cases automatically. | **Not safe to implement** |
| F1.01–F1.03 | Claude comparison and predicted superiority | There is no valid Agnes output baseline, no approved external-model evaluation setup, and no human scoring protocol. The guide’s predicted rates are not evidence. | **Not runnable or claimable** |
| G1.01–G1.03 | Full verification, README, and pushed release | v15 passed 1,772 collected engine cases in 127.98 seconds and was pushed as source and compact artifacts only. The README records the negative result and native-only boundary. | **Completed with corrected claims** |

## Verified compatibility boundary

Ollama’s current documentation describes importing listed Safetensors model architectures, or importing an already-valid GGUF file; conversion requires architecture-aware mapping of model configuration, tensor names, and tokenizer metadata. [2] [3] The current BEAST-BRAIN checkpoint is a project-specific PyTorch dictionary for a custom byte transformer, not a supported imported architecture. Relabelling tensors as GPT-style weights, renaming a file to `.gguf`, or publishing a Modelfile that downloads such a file would not establish a working model.

> **Decision:** do not create a GGUF file, Ollama Modelfile, Ollama client, release asset, or benchmark comparison from the current checkpoint. Those requests remain inactive, not merely unfinished.

## Completed bounded native-only follow-up

The v15 corpus already contains a declared input and exact JSON target. The released runner serialized entire records into one byte stream and evaluated generation from a bare opening brace. Version 16 therefore added a record-aware, target-only loss mode and an evaluator that conditioned on each held-out prompt while retaining source-disjointness and controller validation.

The completed follow-up used the existing approved local corpus, fixed deterministic seed 20260820, a finite 1,800-second CPU budget, atomic checkpoints, a new create-once artifact directory, and no execution of generated text. Its outcomes are measurements—not a promised threshold:

| Metric | Required reporting rule |
|---|---|
| Metric | v16 observed outcome |
|---|---|
| Held-out target NLL | **0.2009989224 → 0.2654667787**; worsened after the finite attempt. |
| JSON and exact-schema rates | **0 / 10 (0%)** for both; each 513-byte candidate retained only as a digest, length, and validation decision. |
| Controller admission | **0 / 10 (0%)**; all candidates were `invalid_json`, and none was executed or registered. |
| Task correctness | **Not measured**; no semantic evaluator was introduced. |
| Capability claim | None; no reasoning, coding, benchmark improvement, or Claude-comparability conclusion follows. |

The retained result is [`docs/v16-prompt-conditioned-json-results.md`](v16-prompt-conditioned-json-results.md) with the create-once compact artifact at `reports/v16/prompt-conditioned-json-instruction-tuning-28m-local/run.json`.

## References

[1]: `docs/v15-json-instruction-results.md` — released native JSON instruction-tuning result in this repository.

[2]: https://docs.ollama.com/import "Ollama — Importing a Model"

[3]: https://huggingface.co/docs/transformers/en/community_integrations/llama_cpp "Hugging Face — llama.cpp integration and conversion registry"
