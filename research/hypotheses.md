# Hypotheses

## Core Thesis
> What becomes possible when software objects can think?

## H1: Object + LLM is meaningfully different from Agent + tools
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Build the same system using (A) conventional agent framework and (B) intelligent object architecture. Measure developer complexity, lines of code, mental model clarity, and ability to express object-graph relationships.
- **Prediction:** Intelligent objects reduce orchestration code when the domain naturally maps to entities (Company, Customer, Product).
- **Kill condition:** If A and B are equivalent in expressiveness and complexity, the abstraction is not genuine.

## H2: Persistence actually helps
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Compare ephemeral agents vs persistent intelligent objects on long-horizon tasks requiring accumulated context. Measure: task success rate over time, token efficiency, developer effort to maintain state.
- **Prediction:** Persistent objects outperform ephemeral agents on tasks spanning multiple sessions because they retain structured experience, not just raw history.
- **Kill condition:** If checkpointing/resuming ephemeral agents achieves the same results, persistence is just caching.

## H3: Intelligence belonging to objects creates a better programming model
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Build an object graph (Company → Customer, Product, Campaign, Employee, Finance). Implement using (A) traditional OOP + external agent orchestration and (B) intelligent objects with native reasoning. Measure: code clarity, testability, ability to add new object types.
- **Prediction:** Native object intelligence makes the system easier to extend because behavior lives with the entity.
- **Kill condition:** If external orchestration is always simpler, the paradigm fails.

## H4: Structured experience memory outperforms raw history
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Compare memory types: (1) no memory, (2) raw chat history, (3) summarized memory, (4) structured experience (observation→action→result→outcome→lesson→future behavior). Measure: task success, token usage, contradiction rate.
- **Prediction:** Structured experience provides better generalization and fewer contradictions.
- **Kill condition:** If raw history or simple summarization matches structured experience, the complexity is not justified.

## H5: Controlled evolution improves behavior without destroying stability
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Allow objects to evolve strategies, policies, and configuration (NOT source code). Every change requires version, reason, prediction, experiment, measurement, rollback. Measure: improvement rate, regression rate, recovery time.
- **Prediction:** Controlled evolution improves long-term performance while keeping regression rate below 5%.
- **Kill condition:** If regression rate exceeds 20% or improvement is not statistically significant, evolution is too dangerous.

## H6: Object-capability security is necessary and sufficient
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Design attacks: prompt injection, memory poisoning, cross-object privilege escalation, malicious object behavior. Test capability-based permissions vs other models.
- **Prediction:** Capability-based permissions prevent all tested attacks without breaking legitimate functionality.
- **Kill condition:** If attacks succeed despite capability model, or if legitimate use is too restricted, the security model fails.

## H7: The paradigm scales economically
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Simulate 1, 10, 100, 1,000, 10,000 objects. Measure: cost, latency, memory, scheduling efficiency. Test dormant objects, cheap models for routine cognition, batching, caching.
- **Prediction:** 90% of objects can remain dormant with near-zero cost. Routine cognition uses cheap/local models. Total cost scales sub-linearly with object count.
- **Kill condition:** If cost scales linearly or super-linearly, the paradigm is economically infeasible.

## H8: The abstraction reduces developer complexity
- **Status:** UNDER INVESTIGATION
- **Falsifiable experiment:** Have developers build systems using Living Objects vs conventional agents. Measure: time to completion, bugs, code volume, subjective DX rating.
- **Prediction:** Living Objects reduces time and bugs for domain-heavy applications.
- **Kill condition:** If developers are slower or produce more bugs, the DX hypothesis fails.

## Attack Hypotheses (Try to prove the idea wrong)

### A1: Living Objects is just NOOA with extra features
- **Attack:** NOOA already has agent-as-object, typed methods, state, memory, code-as-action. Adding persistence and evolution is incremental, not paradigm-shifting.
- **Defense:** Living Objects treats persistence, relationships, experimentation, and evolution as FIRST-CLASS primitives of the programming model, not add-ons. The object graph and capability security create a different architectural pattern.
- **Test:** Can you build a Company→Customer→Product graph in NOOA where each entity has persistent identity, controlled relationships, and autonomous experimentation? If yes, the idea is just a library on top of NOOA.

### A2: Agent frameworks already solve this
- **Attack:** LangGraph + Mem²Evolve + a database = everything Living Objects claims.
- **Defense:** The integration of these as a unified programming model with native OO semantics, capability security, and structured experience may create emergent properties that fragmented frameworks cannot express.
- **Test:** Build the Living Website prototype in LangGraph + Mem²Evolve. Compare expressiveness.

### A3: Persistent objects are just digital twins
- **Attack:** Digital twins already represent persistent stateful entities that reason about their environment.
- **Defense:** Digital twins mirror physical reality. Living Objects are software-native entities that may have no physical counterpart. They experiment, learn, and evolve their own behavior.
- **Test:** Can a digital twin autonomously design and run experiments to improve its own behavior?

### A4: Self-evolution is too dangerous
- **Attack:** Unrestricted self-modification leads to instability, security holes, and unpredictable behavior.
- **Defense:** Living Objects explicitly restricts evolution to the adaptable intelligence layer (strategies, policies, memory, configuration) while keeping the stable execution layer immutable.
- **Test:** Measure regression rates under controlled evolution.

### A5: The economics don't work
- **Attack:** Every object calling an LLM is prohibitively expensive at scale.
- **Defense:** Dormant objects cost nothing. Cheap/local models handle routine cognition. Only active reasoning triggers frontier models.
- **Test:** Cost simulation at 10,000 objects.
