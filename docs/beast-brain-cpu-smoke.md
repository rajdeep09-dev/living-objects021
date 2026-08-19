# BEAST-BRAIN CPU Smoke Experiment

> **Claim boundary:** This experiment is a local **byte-bigram statistical model**, not a transformer, not an LLM, not an Ollama model, and not a fine-tuned 1B-parameter model. Its purpose is to verify the dataset, deterministic split, CPU training, safe checkpoint, reload, held-out metric, and generation plumbing before any larger model work is considered.

The implementation is `agnes_brain/cpu_smoke.py`. It accepts only the checked-in, provenance-labelled base instruction corpus. The model counts transitions between UTF-8 bytes with additive smoothing. It cannot reason about programs, call tools, propose an approved primitive, execute generated code, or demonstrate benchmark superiority.

| Property | Local smoke implementation | Explicitly not established |
|---|---|---|
| Training | CPU-only NumPy count accumulation over a deterministic train split | LLM pretraining, fine-tuning, LoRA, or model downloading |
| Evaluation | Negative log likelihood on a stable held-out record set compared with uniform-byte baseline | Program-synthesis accuracy, JSON validity, task success, or benchmark performance |
| Checkpoint | `.npz` data-only file, loaded with `allow_pickle=False`, digest recorded | Portable production model serving or Ollama registration |
| Generation | Fixed-seed, bounded 96-byte continuation used to test serialization | Valid completion, candidate program, evaluator input, or external action |
| Boundaries | Zero network calls, zero LLM calls, interpreter source never executed, no worker | Internet access, cloud APIs, persistent autonomy, public deployment, or scientific capability claims |

Run the experiment from the repository root only after the base dataset is present:

```bash
python3 agnes_brain/cpu_smoke.py
```

The command creates `reports/v13/beast-brain-cpu-smoke-20260819/experiment.json` and its paired checkpoint exactly once. The artifact must be read alongside its `execution_boundary` and `claim_boundary` fields. A lower held-out byte NLL than the uniform-byte baseline would show only that the model captures byte regularities in this particular local corpus.
