# Temporal Revision and Safety

Temporal revision in BEAST v4 edits a bounded ancestry graph and recomputes affected descendants. A proposal identifies a target organism, an ancestor, revised code, and a strategy name. The engine rejects unknown ancestry, self-revision paradoxes, and proposals exceeding the butterfly budget.

This is a causal-graph rewrite, not literal time travel. Safe deployment requires immutable event history, human approval for high-impact revisions, replayable snapshots, and both old and new strategy hashes.
