# One-Hour 28.9M BEAST-BRAIN Training Feasibility

**Audit date:** 2026-08-19
**Requested outcome:** a one-hour local attempt to train a 28.9M-parameter language-model architecture for BEAST-BRAIN.

> This is a **from-scratch local training attempt**. It cannot transfer Manus model weights or use the assistant as a parent model. No external model, weights, dataset, Ollama endpoint, or cloud inference service is used.

## Measured local environment

| Resource | Observed value | Consequence |
|---|---:|---|
| Logical CPU capacity | 6 | CPU-only training is possible but substantially slower than GPU training. |
| Available memory at audit | approximately 20 GiB | Sufficient headroom for 28.9M fp32 parameters, optimizer state, small batches, and checkpoints. |
| Available project disk | approximately 37 GiB | Sufficient for source, checkpoints, and reports. |
| Installed autodiff framework | None; NumPy only | A CPU numerical-training dependency is required; installing a framework does not download a model, dataset, or weights. |
| Base local corpus | 78 records / 124,268 bytes | Enough to validate a pipeline and reduce local-token loss, not enough to establish language competence. |
| Separate augmented corpus | 513 records / 855,709 bytes | Retained as labelled synthetic/diagnostic material; excluded from the primary model-quality claim. |

## Feasible claim boundary

The chosen architecture may contain approximately 28.9M trainable parameters, but the local corpus is under one megabyte and is largely structured repository metadata. A one-hour CPU attempt can therefore establish only that the architecture, tokenization, checkpointing, recovery, and held-out local-loss measurement work under a declared contract. It cannot demonstrate a useful general-purpose LLM, a capable parent model, autonomous program synthesis, model-assisted BEAST improvement, or performance against Claude, Codex, or other external systems.

The run will be bounded by a wall-clock deadline, deterministic seed, local byte vocabulary, finite sequence length, atomic checkpoints, and a held-out split. It must preserve failure and early-stop outcomes rather than retry indefinitely or silently substitute a smaller model.
