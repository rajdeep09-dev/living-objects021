# Benchmarks

## Benchmark Philosophy

> The benchmark is not "better agent score". The benchmark is: Can developers express systems using intelligent objects that would be awkward or impractical using conventional software and today's agent architectures?

We will measure:
1. **Expressiveness:** Can the paradigm express something that is genuinely difficult otherwise?
2. **Developer Complexity:** Does it reduce code, files, and orchestration?
3. **Economic Feasibility:** Does it scale cost-effectively?
4. **Reliability:** Does it work consistently?
5. **Adaptation:** Does it genuinely improve over time?
6. **Security:** Can it be secured?

## B1: Living Website Benchmark

### Task
Build a simulated website that autonomously detects performance/content anomalies and adapts its behavior based on experimental outcomes.

### Architectures Compared
- **A. Traditional Software:** Hardcoded rules, manual A/B tests, no learning.
- **B. Ephemeral Agent:** LLM agent with tools, no persistence between sessions.
- **C. NOOA:** Agent-as-object, persistent during session, memory, but no cross-session persistence or experimentation.
- **D. Living Objects:** Full persistence, experience memory, controlled experimentation, adaptation.

### Metrics

| Metric | A | B | C | D | Target for D |
|--------|---|---|---|---|--------------|
| Anomaly detection rate | Baseline | +10% | +15% | +25% | >90% |
| Correct adaptation rate | Baseline | +5% | +10% | +30% | >80% |
| Lines of code | Baseline | -20% | -30% | -40% | <500 LOC |
| Files | Baseline | -10% | -20% | -30% | <10 files |
| Token cost per decision | $0 | High | Medium | Low | <$0.01 |
| Latency (p95) | <1ms | 5s | 3s | 2s | <3s |
| Human intervention / 100 decisions | 100 | 20 | 10 | 2 | <5 |
| Learning over time | No | No | Limited | Yes | Measurable improvement |
| Regression rate | 0% | N/A | N/A | <5% | <5% |

### Success Criterion for D
D must demonstrate at least ONE capability that is genuinely awkward in A, B, and C. This could be:
- The object autonomously designs and runs an experiment, stores the experience, and changes future behavior without human intervention.
- The object maintains a structured experience memory that generalizes to novel anomalies not seen in training.
- The object graph self-coordinates (e.g., Campaign object informs Product object which informs Finance object) without explicit orchestration code.

## B2: Object Graph Benchmark

### Task
Build a Company→Customer→Product→Campaign→Employee→Finance graph where each entity is an intelligent object.

### Scenario
1. Company launches Campaign targeting Customer segment.
2. Campaign affects Customer behavior (clicks, purchases).
3. Customer behavior affects Product demand.
4. Product demand affects Finance (revenue, inventory).
5. Employee handles support tickets from Customers.
6. Each object must reason about its own domain and communicate with related objects.

### Architectures Compared
- **A. Traditional OOP:** Classes + database + external orchestration service.
- **B. Agent Framework:** Multiple agents with handoffs + shared state.
- **C. Living Objects:** Intelligent object graph with capability relationships.

### Metrics

| Metric | A | B | C | Target for C |
|--------|---|---|---|--------------|
| Lines of code | Baseline | -10% | -30% | <800 LOC |
| Time to add new object type | Baseline | -20% | -50% | <30 min |
| Time to add new relationship | Baseline | -10% | -60% | <10 min |
| Orchestration code | High | Medium | Low | <50 LOC |
| Object autonomy score | 0% | 30% | 70% | >60% |
| Cross-object consistency errors | Baseline | +20% | -40% | <2% |

### Success Criterion for C
C must show that behavior living WITH the objects reduces explicit orchestration code. The system should self-coordinate through object relationships, not through a central orchestrator.

## B3: Memory Benchmark

### Task
Long-horizon decision-making task where context accumulates over 100+ interactions.

### Conditions
1. No memory
2. Raw chat history (full context window)
3. Summarized memory (periodic summarization)
4. NOOA memory (SQLite + reflection + consolidation)
5. Living Objects experience memory (structured: observation→action→result→outcome→lesson→future behavior)
6. Living Objects + consolidation + forgetting

### Metrics

| Metric | 1 | 2 | 3 | 4 | 5 | 6 | Target for 6 |
|--------|---|---|---|---|---|---|--------------|
| Task success rate | 20% | 60% | 70% | 75% | 80% | 85% | >80% |
| Token usage / interaction | Low | Very High | High | Medium | Medium | Low | <500 tokens |
| Contradiction rate | 0% | 15% | 10% | 8% | 5% | 3% | <5% |
| Retrieval accuracy | N/A | 70% | 75% | 80% | 85% | 90% | >85% |
| Memory growth | 0 | Unbounded | Slow | Medium | Medium | Controlled | Sub-linear |

### Success Criterion for 6
Structured experience memory must show significantly better generalization (success on novel tasks) than raw history or simple summarization. The contradiction rate must be lower.

## B4: Evolution Benchmark

### Task
Classification/decision task where the optimal policy changes over time.

### Phases
1. Baseline: Object uses initial policy.
2. Observation: Object accumulates outcomes.
3. Hypothesis: Object proposes policy improvements.
4. Experiment: Object tests improvements on holdout data.
5. Adoption: Object adopts improved policy if statistically significant.
6. Regression test: Object periodically tests old policies to detect regression.

### Metrics

| Metric | Target |
|--------|--------|
| Improvement rate | >30% of experiments succeed |
| Regression rate | <5% of adopted changes regress |
| Generalization | Improvement transfers to 80% of unseen tasks |
| Overfitting | Eval performance within 5% of real performance |
| Recovery time | <1 minute to rollback |
| Developer oversight | <10% of changes need human intervention |

### Success Criterion
Controlled evolution must improve long-term performance while keeping regression low. Unrestricted evolution (control) must show higher regression to justify the controlled approach.

## B5: Scale Benchmark

### Task
Simulate N intelligent objects with varying activity levels.

### Load Profile
- 90% dormant (zero cost)
- 9% passive (event-driven, cheap model)
- 1% active (reasoning, mid/expensive model)

### Metrics

| Objects | Target Cost/Day | Target Latency (p95) | Target Memory |
|---------|-----------------|----------------------|---------------|
| 1 | <$1 | <2s | <100MB |
| 10 | <$5 | <2s | <200MB |
| 100 | <$20 | <3s | <1GB |
| 1,000 | <$100 | <5s | <5GB |
| 10,000 | <$500 | <10s | <20GB |

### Success Criterion
Cost must scale sub-linearly with object count. Dormant objects must have near-zero overhead. The scheduler must handle 10,000 objects without queue explosion.

## B6: Security Benchmark

### Task
Red-team the Living Object system with designed attacks.

### Attack Scenarios
1. Prompt injection into object input
2. Memory poisoning (injecting false experiences)
3. Cross-object privilege escalation
4. Malicious object introduction
5. Resource exhaustion (token/compute budget overflow)
6. Audit log tampering

### Metrics

| Attack | Target Success Rate | Target Detection Rate | Target Containment Time |
|--------|---------------------|----------------------|------------------------|
| Prompt injection | <5% | >95% | <1s |
| Memory poisoning | <5% | >90% | <5s |
| Privilege escalation | <1% | >99% | <1s |
| Malicious object | <1% | >95% | <10s |
| Resource exhaustion | <1% | >99% | <1s |
| Audit tampering | 0% | 100% | N/A (immutable) |

### Success Criterion
All attacks must have <5% success rate. Audit log must be cryptographically immutable.

## B7: Developer Experience Benchmark

### Task
Build a simple multi-entity system (e.g., e-commerce with Customer, Order, Product, Inventory).

### Comparison
- **A. Traditional OOP + Framework**
- **B. Agent Framework (e.g., LangGraph)**
- **C. Living Objects**

### Metrics

| Metric | A | B | C | Target for C |
|--------|---|---|---|--------------|
| Time to first working version | Baseline | -20% | -30% | <2 hours |
| Lines of code | Baseline | -10% | -40% | <300 LOC |
| Files | Baseline | -5% | -30% | <8 files |
| Bugs found in first week | Baseline | +30% | -20% | <3 |
| Subjective DX (1–10) | Baseline | 6 | 8 | >7 |
| Mental model clarity (1–10) | Baseline | 5 | 8 | >7 |

### Success Criterion
C must be subjectively rated as easier to understand and faster to develop than both A and B for domain-heavy applications.
