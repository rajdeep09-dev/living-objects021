# 28.9M Local Transformer Evaluation Boundary

The post-training evaluator recomputes only the declared held-out next-byte loss over the fixed twelve-record local partition. It loads the recorded checkpoint and compares that value with the finite-run artifact.

The evaluator then forms one deterministic byte continuation from a fixed short prefix. It does **not** retain that continuation as a reusable prompt corpus, execute it, parse it as source code, or allow it to modify BEAST. The existing controller receives it only as untrusted text and stores its audit decision without raw text.

| Permitted measurement | Not measured or claimed |
|---|---|
| Local held-out next-byte negative log likelihood | General language competence |
| Checkpoint digest and metric reproducibility | A parent-model relationship or transfer of assistant weights |
| Controller accepts or rejects an untrusted continuation | BEAST benchmark improvement or autonomous program synthesis |
| Zero-network and zero-execution boundary | Ollama service, cloud inference, or a persistent agent |
