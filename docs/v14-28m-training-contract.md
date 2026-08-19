# BEAST-BRAIN 28.9M Local Transformer Contract

The local training target is a **28,864,544-parameter** byte-level causal transformer. It has a 256-byte vocabulary, 128-byte context window, 512-dimensional embeddings, 8 attention heads, 9 transformer blocks, and 2,080-unit feed-forward layers. Input and output byte embeddings are tied.

> The architecture is approximately 28.9M parameters. It is not a downloaded checkpoint, a fine-tuned external model, a copy of the assistant, or an Ollama service.

| Contract element | Fixed value | Reason |
|---|---:|---|
| Vocabulary | 256 byte values | Avoids downloaded tokenizer assets and keeps encoding auditable. |
| Context window | 128 bytes | Bounds CPU memory and per-step cost. |
| Trainable parameters | 28,864,544 | Meets the declared approximately-28.9M architecture target. |
| Primary data | 66 train / 12 held-out local records | Reuses the v13 deterministic record split and excludes synthetic augmentation from the primary loss claim. |
| Checkpoints | Create-once, atomic, local-only | Enables interruption recovery without mutable historical results. |
| Runtime | CPU PyTorch, finite deadline | No GPU, network model endpoint, worker, scheduler, or automatic retry loop. |

The training contract is written before the first optimization step. It must store the model count, dataset digest, record digest, seed, deadline, and explicit zero-network boundary. The only planned measurement is held-out next-byte loss on the declared local corpus; it does not measure general language ability, code synthesis, or BEAST improvement.
