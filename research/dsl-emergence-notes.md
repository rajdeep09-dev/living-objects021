# Notes on DSL Emergence in BEAST v2

## Research question

Can a population reduce the cost of cultural transmission by evolving a compact language for strategy intent? The v2 DSL experiment does not claim that a language becomes conscious or that arbitrary grammar will emerge from a few mutations. It tests a narrower engineering proposition: **a heritable vocabulary and grammar can accumulate tokens that encode compositional strategy intent and can be decoded without a large model**.

## Representation

`DSLGenome` has three coupled parts:

1. `vocabulary` is an ordered tuple of tokens.
2. `grammar_rules` names available structural forms, beginning with `conditional` and adding `compound` after vocabulary growth.
3. `semantics` maps each token to a short meaning descriptor. The current implementation stores semantic descriptions as data rather than executable callbacks, keeping serialization and inspection straightforward.

The initial language has five tokens: `fit`, `coop`, `defect`, `high`, and `else`. An expression is shaped as `WHEN(condition) -> action; ELSE -> fallback`. That explicit shape makes round-trip parsing testable and allows the UI terminal to show both the compact artifact and its decoded intent.

## Growth model

Each mutation appends one `compound_N` token and a corresponding `compose:` semantic descriptor. Crossover performs ordered set union across vocabulary, grammar rules, and semantic pairs. This is a deliberately conservative emergence model: it grows the lexicon monotonically and preserves parent meaning, but it does not yet discover arbitrary syntax trees, resolve semantic conflicts through population fitness, or learn a tokenizer from raw communication.

The benchmark starts at five tokens and reaches 55 after 50 mutations, an 11× expansion. The important proof is not the number alone. The new token must be accepted by `express()`, survive `parse()`, and appear in the decoded intent. That is the minimum evidence that vocabulary growth changes usable expressive capacity rather than only increasing an archive counter.

## Cultural selection hypotheses

The next experimental layer should compare three pressures:

| Condition | Expected result |
|---|---|
| Random token mutation with no reuse reward | Vocabulary expands but many tokens remain unused. |
| Reuse reward for shorter valid expressions | Compact primitives spread through the memome. |
| Reuse plus semantic task success | Compound tokens that preserve task quality become culturally dominant. |

Useful measurements include token adoption rate, expression length, parse failure rate, semantic collision rate, and the number of independent lineages using a token after its creator disappears. A token used by many unrelated descendants is stronger evidence of cultural utility than a token that merely exists in one genome.

## Limitations and future work

The current DSL is a typed intent notation, not a general programming language. It has no recursive grammar, no formal type checker, and no learned semantics beyond descriptors. Future work should add immutable rule IDs, signed semantic proposals, fitness-weighted crossover, grammar complexity penalties, and a translation layer that produces an intermediate representation before any executable strategy is generated. The translator must remain behind the external sandbox boundary described in `research/beast_v2_security_findings.md`.

The correct scientific claim is therefore modest: BEAST v2 demonstrates a **runnable, inspectable path toward emergent strategy notation**. It does not prove open-ended language evolution or general intelligence.
