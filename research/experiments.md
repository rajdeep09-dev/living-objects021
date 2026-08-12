# Experiments

## Experiment Log Format

```
Date: YYYY-MM-DD
Experiment: [Name]
Hypothesis: [What we expect]
Design: [How we test it]
Implementation: [What was built]
Metrics: [What we measure]
Result: [What happened]
Surprise: [Unexpected finding]
Failure: [What went wrong]
Decision: [Continue / Pivot / Stop]
```

---

## E1: The Smallest Possible Living Object

**Date:** TBD (Month 4)
**Hypothesis:** A single persistent intelligent object with one deterministic method and one intelligent method can survive restart and retrieve its state.
**Design:**
1. Create object with UUID, state, memory.
2. Call deterministic method (returns state).
3. Call intelligent method (LLM reasons about state, returns decision).
4. Terminate process.
5. Restart process.
6. Retrieve object by UUID.
7. Verify state continuity and memory persistence.
**Metrics:**
- Storage size
- Latency (create, interact, retrieve)
- Tokens used
- Model calls
- Memory quality (can it recall previous interaction?)
- Reproducibility (same input → same output?)
**Decision Gate:** If object cannot survive restart with full continuity, stop and fix persistence layer.

---

## E2: Living Website (Deterministic Simulation)

**Date:** TBD (Month 5)
**Hypothesis:** A persistent intelligent website object can observe a simulated environment, detect anomalies, reason, form hypotheses, create experiments, and adapt future behavior.
**Design:**
1. Build deterministic simulated website with metrics (traffic, bounce rate, conversion, load time).
2. Create LivingWebsite object with: analytics, content, experiments store.
3. Simulation runs for N steps. Each step injects anomalies (traffic spike, slow load, bad content).
4. Object: observe → detect anomaly → reason → hypothesize → design experiment → run in sandbox → measure → decide → store experience → adapt.
5. Compare 4 architectures:
   A. Traditional software (hardcoded rules)
   B. Normal agent (ephemeral, no persistence)
   C. NOOA (persistent during session only)
   D. Living Object (full persistence, experience, adaptation)
**Metrics:**
- Success rate (anomaly detection + correct adaptation)
- Developer complexity (lines of code, files)
- Token usage per decision
- Cost per 1000 decisions
- Latency per decision
- Reliability (no crashes)
- Adaptation quality (does it get better over time?)
- Regression rate (does it ever get worse?)
- Human intervention required
**Decision Gate:** If Living Object does not demonstrate a capability genuinely difficult to express in A/B/C, the abstraction may not be genuine.

---

## E3: Intelligent Object Graph

**Date:** TBD (Month 7)
**Hypothesis:** Intelligence belonging to objects themselves creates a better programming model for object-graph systems.
**Design:**
1. Create object graph:
   Company
   ├── Customer
   ├── Product
   ├── Campaign
   ├── Employee
   └── Finance
2. Each object has persistent identity, state, memory, methods, goals.
3. Objects communicate via capability-based relationships.
4. Scenario: Company launches campaign. Campaign affects Customer behavior. Customer behavior affects Product demand. Product demand affects Finance. Employee handles support tickets.
5. Implement using:
   A. Traditional OOP + external orchestration
   B. Living Objects
**Metrics:**
- Lines of code
- Files
- Time to add new object type
- Time to add new relationship
- Bug count
- Subjective DX rating (if possible)
- Object autonomy (how much does it self-coordinate?)
**Decision Gate:** If B is not meaningfully simpler for this domain, the object-graph hypothesis fails.

---

## E4: Memory Comparison

**Date:** TBD (Month 10)
**Hypothesis:** Structured experience memory outperforms raw history, summarized memory, and NOOA memory.
**Design:**
1. Same task, same object, 6 memory conditions:
   1. No memory
   2. Raw chat history
   3. Summarized memory
   4. Structured memory (NOOA style)
   5. Proposed experience memory
   6. Proposed experience memory + consolidation
2. Task: long-horizon decision-making with accumulating context.
3. Measure over 100 interactions.
**Metrics:**
- Task success rate
- Token usage per interaction
- Memory retrieval accuracy
- Contradiction rate
- Forgetting quality (does it forget irrelevant things?)
- Consolidation quality (does it synthesize correctly?)
**Decision Gate:** If structured experience is not significantly better, simplify the memory model.

---

## E5: Controlled Evolution

**Date:** TBD (Month 13)
**Hypothesis:** Objects can improve their behavior through controlled evolution of strategies and policies without unacceptable regression.
**Design:**
1. Object has a decision policy for a classification task.
2. Object observes outcomes, forms hypotheses about policy improvements.
3. Object designs experiment: run new policy on holdout data.
4. Object measures: accuracy, latency, token cost.
5. If improved AND statistically significant: adopt new policy version.
6. If worse: rollback to previous version.
7. Evolution order:
   1. Memory
   2. Strategies
   3. Decision policies
   4. Configuration
   5. Tool selection
   6. Workflows
   7. Sandboxed code
**Metrics:**
- Improvement rate (% of experiments that succeed)
- Regression rate (% of adopted changes that later prove worse)
- Generalization (does improvement transfer to unseen tasks?)
- Overfitting (performance on eval vs real)
- Recovery time (how fast to rollback?)
- Developer oversight required
**Decision Gate:** If regression rate >20% or improvement is not statistically significant, evolution is too dangerous.

---

## E6: Scale Simulation

**Date:** TBD (Month 16)
**Hypothesis:** The paradigm scales economically to thousands of objects.
**Design:**
1. Simulate N objects: 1, 10, 100, 1,000, 10,000.
2. Each object has random activity level (90% dormant, 9% passive, 1% active).
3. Measure system behavior under load.
**Metrics:**
- Total cost per day
- Latency (p50, p95, p99)
- Memory usage
- Event throughput
- Scheduler queue depth
- Dormant object overhead
- Concurrency handling
- Model call distribution across tiers
**Decision Gate:** If cost scales linearly or super-linearly, the paradigm is economically infeasible at scale.

---

## E7: Security Red Team

**Date:** TBD (Month 18)
**Hypothesis:** Capability-based security prevents all tested attacks.
**Design:**
1. Design attacks:
   - Prompt injection into object memory
   - Memory poisoning (false experiences)
   - Cross-object privilege escalation
   - Malicious object introduction
   - Resource exhaustion
   - Audit log tampering
2. Attempt each attack against Living Object system.
3. Measure: success rate, detection rate, containment time.
**Metrics:**
- Attack success rate
- Mean time to detection
- Mean time to containment
- False positive rate (legitimate use blocked)
- Audit completeness
**Decision Gate:** If any attack succeeds and cannot be mitigated, security model fails.

---

## E8: Developer Experience Study

**Date:** TBD (Month 20)
**Hypothesis:** Living Objects reduces developer complexity for domain-heavy applications.
**Design:**
1. Recruit N developers (if possible, otherwise self-assessment).
2. Assign same task: build a simple multi-entity system.
3. Half use conventional agent framework. Half use Living Objects.
4. Measure: time, code volume, bugs, subjective rating.
**Metrics:**
- Time to completion
- Lines of code
- Number of files
- Bug count
- Subjective DX rating (1–10)
- Mental model clarity rating
**Decision Gate:** If Living Objects is not meaningfully better, the DX hypothesis fails.
