# Substrate Independence

The v4 exporter expresses one organism through a minimal WASM module, a hardened container specification, and a SystemVerilog circuit description. The current artifacts are declarative research outputs; they are not evidence of silicon execution or unrestricted deployment.

`production/substrate_worker.py` accepts only `organism_id` and one of `wasm`, `container`, or `circuit`. It never executes source code. Run it with no network, a read-only filesystem, dropped capabilities, no-new-privileges, a memory-backed non-executable temporary directory, and a resource quota.

The production path should be export → schema validation → isolated compilation → disposable smoke test → digest signing → provenance storage.
