# Intelligence Scheduler

## Concept

An OS scheduler allocates CPU time to processes. An Intelligence Scheduler allocates reasoning, model calls, memory consolidation, experiments, and object communication.

## Prior Art

### Dapr Scheduler Service

- Centralized, reliable scheduling of actor timers and reminders.
- Ensures global timing accuracy.
- Prevents duplicate executions.
- Handles actor migration.

### AI Agent Job Scheduling Patterns (2026)

1. **Cron Pattern:** Time-based triggers
2. **Interval Loop:** Periodic execution
3. **Event-Driven:** External event triggers
4. **Adaptive Scheduling:** Agent decides next run time
5. **Daisy-Chain:** Agent A's completion schedules Agent B

### Actor Model Coordination

- Message passing with bounded mailboxes.
- Backpressure when mailbox is full.
- Circuit breakers for failing actors.
- Supervision hierarchies for failure recovery.

---

## Proposed Intelligence Scheduler

### Priority Function

```
Priority(object, t) = 
    expected_value(object, t) × urgency(object, t) × uncertainty(object, t)
    ------------------------------------------------------------------------
    cost(object, t) × risk(object, t)
```

Where:
- **expected_value:** Estimated value of the object's next action
- **urgency:** Time-sensitivity (deadline proximity)
- **uncertainty:** How much the object doesn't know (information gap)
- **cost:** Tokens + latency + compute for reasoning
- **risk:** Probability of negative outcome

### Simplified Heuristic

```
Priority = base_priority
         + anomaly_boost × anomaly_score
         + goal_boost × goal_urgency
         + surprise_boost × surprise
         - cost_penalty × estimated_tokens
         - risk_penalty × risk_score
```

### Scheduling Policies

#### Policy 1: Priority Queue

```
Queue: [Object A (P=95), Object B (P=80), Object C (P=30), ...]
Scheduler: process highest priority first
```

**Pros:** Simple. High-value objects get attention.
**Cons:** Starvation of low-priority objects. No fairness.

#### Policy 2: Multi-Level Queue

```
Level 1 (Critical): Real-time, anomaly response
Level 2 (High): Goal-driven actions
Level 3 (Normal): Routine reasoning
Level 4 (Low): Memory consolidation, background tasks
Level 5 (Batch): Experiments, analytics
```

**Pros:** Predictable latency for critical tasks. Background tasks don't block.
**Cons:** Fixed levels may not match application needs.

#### Policy 3: Fair Share

```
Each object gets: budget_share = global_budget / N_active
Objects can borrow from future or lend to others
```

**Pros:** Fairness. Prevents starvation.
**Cons:** Inefficient if some objects need more than their share.

#### Policy 4: Economic Auction

```
Objects bid for compute using internal currency
Highest bidders get reasoning slots
```

**Pros:** Market-optimal allocation. Objects self-prioritize.
**Cons:** Complex. Gaming possible. Budget allocation is arbitrary.

#### Policy 5: Event-Driven + Importance Threshold

```
Event arrives → Importance filter (cheap model) → If important → Schedule reasoning
```

**Pros:** Simple. Efficient. Proven in event-driven systems.
**Cons:** May miss slowly-building issues that don't trigger events.

**Recommended:** Policy 5 (Event-Driven + Importance) as default, with Policy 2 (Multi-Level) for explicit scheduling.

---

## Scheduler Architecture

```
Event Stream
    ↓
Importance Filter (cheap model or heuristic)
    ↓
Priority Calculator
    ↓
Scheduler Queue (priority-ordered)
    ↓
Batch Collector (group similar requests)
    ↓
Model Tier Selector
    ↓
API Call (to LLM provider)
    ↓
Result Distributor
    ↓
Object receives result → updates state/memory
```

### Components

1. **Importance Filter:** Drops 90% of events as "not worth reasoning about"
2. **Priority Calculator:** Scores remaining events
3. **Queue:** Thread-safe priority queue
4. **Batch Collector:** Groups similar reasoning requests for efficiency
5. **Model Tier Selector:** Chooses cheapest model that can handle the task
6. **Rate Limiter:** Prevents API quota exhaustion
7. **Result Distributor:** Returns results to requesting objects

---

## Dormant Object Management

### States

```
DORMANT: No events, no scheduled tasks. Zero compute cost.
    ↓ event arrives
PASSIVE: Event received, importance filter running. Cheap compute.
    ↓ importance > threshold
ACTIVE: Reasoning scheduled or in progress. Medium compute.
    ↓ reasoning complete
PASSIVE: Result distributed. Waiting for next event.
    ↓ no events for timeout
DORMANT: Deactivated. State persisted. Zero cost.
```

### Activation Cost

```
Cold start: load state from DB + initialize memory + run importance filter
Warm start: state in cache + memory loaded + importance filter ready
Hot start: object never deactivated (for high-frequency objects)
```

**Strategy:** Keep "hot" objects warm. Let "cold" objects deactivate.

---

## Conclusion

**The Intelligence Scheduler is a solved problem at the architecture level.**

Dapr Scheduler + priority queues + importance filtering + batching + tiered models = viable scheduler.

**The research question is:** What priority function produces the best system behavior? This requires empirical testing.

**Critical experiment:** Build 1,000 objects with varying event rates. Test 3 priority functions. Measure: task completion rate, latency distribution, cost, object starvation rate.
