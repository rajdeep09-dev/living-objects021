# Lamarckian Living Object — Executable Proof Contracts

| Requirement | Concrete mechanism | Testable assertion |
|---|---|---|
| Lamarckian inheritance | `learn()` compiles, installs, and records a strategy; `reproduce()` copies the learned records and behavior code to the child. | A named strategy learned by a parent exists in the child and yields the same executable behavior. |
| Meta-evolution | `mutation_rate` is a genome field. Genome mutation changes that field and descendants are selected through an adaptive, novelty-aware score. | Mean mutation rate at generation 50 differs from the founder mean; observed descendant rates are not all identical. |
| Persistent memome | `Memome` stores strategy records in SQLite, independently of organism state or life. | After an organism dies and the memome is reopened, the strategy remains retrievable and a later organism installs it. |
| Open-ended novelty | The ecosystem creates behavior descriptors from accumulated archived lineages. Selection scores include a bounded novelty bonus in addition to changing environmental performance. | The number of unique novelty descriptors rises over the run, and the last novelty count is greater than the initial count. |
| Safe self-modification | Organisms subclass `SelfModifyingObject`; code is compiled before installation and delegated with the existing guarded executor. | A valid runtime replacement changes output. Invalid syntax is rejected; a runtime exception returns the safe default without crashing. |

The simulation is deterministic under a supplied random seed. Its score is adaptive rather than a single static target: each generation uses a changing environmental context and adds a novelty contribution based on strategy descriptors that were not previously present in the shared archive. This does not assert biological equivalence or open-ended general intelligence; it establishes the five specified computational properties in runnable software.
