# V15 GGUF and Ollama Feasibility Audit

**Purpose:** determine whether the existing BEAST-BRAIN 28.9M custom byte-level transformer can be represented as a standards-compatible GGUF artifact and loaded by Ollama without fabricating compatibility.

## Official compatibility requirement

The official Ollama import documentation states that it imports listed Safetensors architectures, including Llama, Mistral, Gemma, and Phi3, and imports a GGUF model from a supplied GGUF file. It describes producing a GGUF model by converting supported Safetensors weights with the Llama.cpp conversion utility. [1]

| Requirement | Existing BEAST-BRAIN state | Audit status |
|---|---|---|
| Supported model architecture and tensor naming | Custom byte-level causal transformer | Pending architecture-level compatibility test |
| Safetensors-compatible source layout | Native PyTorch checkpoint | Not yet demonstrated |
| Genuine GGUF conversion | No converter or generated GGUF artifact | Not implemented |
| Ollama local service | Not installed, configured, or authorized as a persistent service | Inactive |
| Quantized artifact | No compatible FP16/FP32 import exists to quantize | Not implemented |
| GitHub model artifact | Large native checkpoint is local-only; compact GGUF does not exist | Not publishable at this time |

## Local architecture and runtime findings

The checked-in `ByteTransformer28M` is a custom PyTorch byte model with a 256-token byte vocabulary, bespoke causal-attention/block names, and a tied embedding/output projection. Its persisted run uses a project-specific Torch dictionary schema containing `model_state`, `optimizer_state`, the local byte-data digest, and local run configuration. It is not a Llama, Mistral, Gemma, or Phi3 model layout.

The audited environment has no `ollama` executable, `llama-quantize` executable, or `convert_hf_to_gguf.py` conversion utility. Installing a runtime or converter would still not make this custom architecture compatible by itself; an architecture-aware exporter and matching llama.cpp/Ollama inference implementation would be required.

> A file with a `.gguf` extension is **not** a GGUF model. No such file will be generated unless it satisfies the conversion and runtime compatibility requirements.

## Provisional conclusion

The project can evaluate and instruction-tune the existing native checkpoint through its checked-in PyTorch inference path. A standards-compatible Ollama/GGUF export is **not currently supported**: the model is a custom byte transformer rather than one of the documented import architectures, and no conversion/runtime path is present. It remains inactive unless a genuine architecture adapter or a compatible training architecture is implemented and independently tested. The project will report incompatibility rather than substitute a fake export.

## References

[1]: https://docs.ollama.com/import "Ollama — Importing a Model"
