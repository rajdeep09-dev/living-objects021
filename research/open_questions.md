# Open Questions

## Identity
1. What makes an intelligent object the same object tomorrow?
2. Can identity survive process restart? (Yes, via persistent storage + UUID)
3. Can identity survive migration across machines? (Yes, if state is portable)
4. Can identity survive model replacement? (Unknown — does changing the LLM change the object's "personality"?)
5. Should identity include a cryptographic keypair for signing actions?
6. How do we handle object cloning vs forking vs branching?

## State
7. What is state versus memory? (State = current configuration. Memory = accumulated experience.)
8. What must be durable? (Identity, state, memory, relationships, audit log.)
9. How should state be versioned? (Event sourcing? Snapshotting?)
10. Should state include the object's own code/strategies, or only data?
11. How do we reconcile state across distributed replicas?

## Memory
12. What should be remembered? (Facts, experiences, relationships, skills, failures.)
13. What should be forgotten? (Outdated facts, irrelevant noise, contradicted beliefs.)
14. How should contradictions be handled? (Confidence scoring? Provenance tracking? Temporal versioning?)
15. How should obsolete memories be invalidated? (Explicit invalidation? TTL? Replacement?)
16. What is the right granularity of memory? (Per-object? Per-relationship? Global?)
17. How does memory consolidation work? (Sleep-like offline processing?)
18. Can memories be shared between objects? (Should they be?)

## Reasoning
19. When should an object reason? (On every method call? Only on anomaly detection? Event-triggered? Scheduled?)
20. When should deterministic code be used vs LLM invocation? (Deterministic for known paths, LLM for novel situations.)
21. How should reasoning budgets be allocated? (Per-object token budget? Global budget?)
22. Can objects reason about their own reasoning? (Meta-cognition.)
23. Should reasoning be observable/inspectable by developers?

## Relationships
24. How should objects communicate? (Message passing? Direct method calls? Event bus?)
25. Can one object modify another? (Only with explicit capability delegation.)
26. What permissions are required? (Capability-based: each relationship grants specific abilities.)
27. Should objects have private memory? (Yes. Private memory + shared memory layers.)
28. How are relationships discovered and established? (Registry? Introduction? Self-organization?)
29. Can relationships be revoked? (Yes, with audit trail.)

## Experimentation
30. What distinguishes an experiment from ordinary execution? (Explicit hypothesis, controlled variables, measurement, rollback plan.)
31. How do we determine whether an adaptation genuinely improved behavior? (A/B testing against previous version. Statistical significance.)
32. How do we prevent overfitting? (Cross-validation. Holdout sets. Domain randomization.)
33. Can an object experiment on itself without side effects? (Sandboxed simulation.)
34. Who approves experiments? (Developer-defined policy. Object can propose, human/system approves.)

## Evolution
35. What can change? (Memory, strategies, heuristics, decision policies, configuration, tool selection, workflows.)
36. What must remain immutable? (Core identity, security policy, resource limits, audit log.)
37. Who authorizes changes? (Capability holders. Developer override.)
38. How can changes be rolled back? (Versioned memory + state. Event sourcing.)
39. How can improvement be proven? (Benchmarks. A/B tests. Regression suites.)
40. Can evolution lead to emergent goals? (Dangerous. Must be constrained by developer-defined goal boundaries.)

## Economics
41. What happens when there are thousands or millions of intelligent objects? (Most dormant. Event-triggered awakening.)
42. Can most objects remain dormant? (Yes, with event-driven architecture.)
43. Can cheap/local models handle routine cognition? (Yes. Tiered model strategy.)
44. How should reasoning be scheduled? (Priority queue. Importance threshold. Batch processing.)
45. What is the cost per object per day at rest? (Near zero if using local storage + no model calls.)
46. What is the cost per object per day active? (Depends on model tier. Must be measurable and budgeted.)

## Developer Experience
47. Does this reduce code? (Hypothesis: yes, for domain-heavy apps.)
48. Does it reduce orchestration? (Hypothesis: yes, because objects self-coordinate.)
49. Does it improve maintainability? (Unknown. Needs empirical study.)
50. Is the mental model easier than agent graphs? (Unknown. Needs user study.)
51. How do you debug an intelligent object? (Trace viewer. State inspector. Memory inspector. Replay.)
52. How do you test an intelligent object? (Unit tests for deterministic methods. Evals for intelligent methods.)

## Security
53. How do we prevent prompt injection into object memory? (Input validation. Memory provenance. Sandboxing.)
54. How do we prevent memory poisoning? (Cryptographic signatures. Trust boundaries. Anomaly detection.)
55. How do we prevent cross-object attacks? (Capability isolation. No ambient authority.)
56. How do we prevent privilege escalation? (Immutable capability graph. No transitive delegation without audit.)
57. How do we audit autonomous actions? (Complete event log. Signed actions. Immutable audit trail.)
58. What happens when a malicious object is introduced? (Sandbox containment. Capability revocation. Quarantine.)

## Paradigm
59. Is this a framework, runtime, programming model, protocol, language, database, or platform?
60. Can it be expressed as a library, or does it need language support?
61. What programming languages are suitable? (Python first. TypeScript second.)
62. Can it interoperate with existing systems? (Yes, via APIs, MCP, A2A.)
63. What is the smallest possible expression of the paradigm? (A single persistent intelligent object with one deterministic method and one intelligent method.)
