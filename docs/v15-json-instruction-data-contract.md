# v15 Structured-JSON Instruction Data Contract

The local JSON instruction corpus is a **syntax-and-governance** dataset, not a reasoning or coding benchmark. It contains only checked-in primitive-registry records that are already approved for the `default` controller profile. Each target is an exact JSON object with the controller’s five required keys: `name`, `description`, `input_types`, `output_type`, and `rationale`.

| Property | Contract |
|---|---|
| Source | `agnes_brain/training_data/primitives/from_codebase.jsonl` only |
| Target source | Existing registry metadata and its rule-based rationale |
| Train/holdout rule | SHA-256 of source record identifier modulo 5 |
| Leakage control | Primitive names and source records are disjoint between partitions |
| Model-generated targets | Prohibited |
| Synthetic targets | Prohibited |
| Candidate execution | Prohibited |

The source row itself supplies the target; the project does not invent explanations, names, signatures, or scores. A syntactically valid JSON response is evaluated separately from controller admission. Admission still requires the registered signature, the declared profile, and the v12 side-effect controls.

> A high JSON-validity rate on this compact registry task demonstrates only local output-format learning. It does not demonstrate general reasoning, code generation, task planning, safe autonomy, or Claude-equivalent behavior.
