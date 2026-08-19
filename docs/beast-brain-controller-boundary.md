# BEAST-BRAIN Controller Boundary

> **The controller is an admission filter, not a code generator.** It can resolve an untrusted JSON suggestion to one already-registered interpreter primitive only when the primitive name, signature, and declared v12 profile all match exactly.

`agnes_brain/controller.py` is deliberately narrow. Its input is text; the text is parsed as JSON data and never passed to `eval`, `exec`, an interpreter, a subprocess, a network client, or a global-registry mutation. An accepted decision returns the original `Primitive` object from the existing registry. It therefore cannot add capability, change a function body, activate a network primitive, or bypass the evaluator and primitive approval contracts.

| Decision state | Meaning | Engine effect |
|---|---|---|
| `approved_existing_primitive` | An existing name, exact signature, and profile approval matched. | Caller may use that same already-approved primitive in a separately authorized population configuration. |
| `invalid_json`, `invalid_schema_keys`, or `invalid_signature_fields` | The response cannot be trusted as contract-shaped data. | No primitive is returned. |
| `unregistered_primitive` or `primitive_not_approved_for_profile` | The response names absent or out-of-profile capability. | No primitive is returned. |
| `response_too_large` or text-length rejection | The response exceeds bounded local input limits. | No primitive is returned. |

Every decision can be emitted as an audit record containing only response length/digest, acceptance state, primitive approval metadata, and fixed zero-side-effect fields. It intentionally omits raw model output. The CPU byte-bigram smoke model is not expected to produce reliable valid JSON; its typical rejection is a **successful enforcement result**, not a model capability claim.
