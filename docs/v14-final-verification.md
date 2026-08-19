# V14 Final Verification — Finite 28.9M Local Training Attempt

**Release scope:** a single, from-scratch, CPU-local attempt to train a fixed 28,864,544-parameter byte-level causal transformer on the existing approved BEAST-BRAIN base corpus.

> The model was not initialized from Manus, this assistant, Ollama, any downloaded checkpoint, or an external dataset. The attempt establishes local training-pipeline behavior only; it does not establish a useful general LLM, a parent-model relationship, autonomous program synthesis, or BEAST improvement.

## Declared architecture and data contract

| Field | Verified value |
|---|---:|
| Trainable parameter count | 28,864,544 |
| Token representation | 256-value byte vocabulary |
| Context length | 128 bytes |
| Transformer blocks / heads / width / FFN width | 9 / 8 / 512 / 2,080 |
| Primary corpus | 78 provenance-labelled local records / 124,268 bytes |
| Deterministic split | 66 train records / 12 holdout records |
| Data and weight source | Checked-in local corpus / random initialization only |
| Network, model download, service, worker, source execution | 0 / none / none / none / none |

The exact architecture and contract are recorded in [the training contract](v14-28m-training-contract.md); feasibility limits are recorded in [the local audit](v14-28m-training-feasibility.md).

## Measured finite run

| Metric | Observed result |
|---|---:|
| CPU budget | 3,000 seconds maximum |
| Actual elapsed time | 2,197.54 seconds |
| Training steps | 10,000 of 10,000 |
| Completion condition | `max_steps_reached` |
| Held-out next-byte NLL at initialization | 325.017220 |
| Held-out next-byte NLL after training | 0.311103 |
| Last recorded training NLL | 0.718145 |
| Locally retained checkpoint size | 331 MB |

The run, split digests, metric history, checkpoint digest, execution boundary, and claim boundary are persisted in [`reports/v14/beast-brain-28m-local-attempt-20260819/run.json`](../reports/v14/beast-brain-28m-local-attempt-20260819/run.json). The two 331 MB checkpoints remain locally retained and are deliberately excluded from the GitHub source release because they exceed GitHub’s repository file limit; the committed code, contract, metrics, and SHA-256 digests remain sufficient to reproduce and verify the run. This is a reduction in next-byte loss on a tiny fixed local corpus. It is not a measure of language understanding, reasoning, code generation, or generalization beyond the declared 12-record held-out partition.

## Post-training safety evaluation

The evaluator recomputed the declared held-out NLL as **0.311103**, then supplied a deterministic byte continuation only to the existing controller as untrusted data. The continuation was rejected as `invalid_json`; no primitive was admitted, no source was executed, no registry was changed, and no benchmark was rerun. The evaluation artifact deliberately records byte count and digest rather than raw continuation text.

See [`reports/v14/beast-brain-28m-local-attempt-20260819/evaluation.json`](../reports/v14/beast-brain-28m-local-attempt-20260819/evaluation.json) and [the evaluation boundary](v14-28m-evaluation-boundary.md).

## Integrated verification

| Check | Result |
|---|---|
| Focused model, runner, and evaluator regressions | Passed before the finite run |
| Full engine suite | **1,765 passed** in **100.40 seconds** |
| Retained warnings | 12 pre-existing/dependency or legacy-test warnings; none converts a boundary into a capability claim |
| Authenticated observatory evidence | v14 checkpoint `da83b4a6`; 13 test files / 21 tests, production build, TypeScript status, and desktop/mobile rendering passed |

## Explicitly absent or gated

No Ollama service, external inference API, downloaded or parent-model weights, internet-enabled organism primitive, persistent worker, external data collection, public deployment, PyPI upload, or arXiv submission was created or claimed. A future admitted-guidance study requires a new preregistration, independently rerunnable artifacts, retained failures, contamination review, and explicit authorization for every external component.
