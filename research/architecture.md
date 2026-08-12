# Architecture

## Proposed Living Object Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LIVING OBJECT RUNTIME                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Object A   │  │  Object B   │  │  Object C   │  │    ...          │  │
│  │  (Company)  │  │  (Customer) │  │  (Product)  │  │                 │  │
│  │             │  │             │  │             │  │                 │  │
│  │  Identity   │  │  Identity   │  │  Identity   │  │                 │  │
│  │  State      │  │  State      │  │  State      │  │                 │  │
│  │  Memory     │  │  Memory     │  │  Memory     │  │                 │  │
│  │  Methods    │  │  Methods    │  │  Methods    │  │                 │  │
│  │  Goals      │  │  Goals      │  │  Goals      │  │                 │  │
│  │  Constraints│  │  Constraints│  │  Constraints│  │                 │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────┘  │
│         │                │                │                                 │
│         └────────────────┴────────────────┘                                 │
│                          │                                                  │
│              ┌───────────┴───────────┐                                      │
│              │   RELATIONSHIP BUS    │  (capabilities, events, messages)   │
│              └───────────┬───────────┘                                      │
│                          │                                                  │
│  ┌───────────────────────┴───────────────────────┐                          │
│  │           STABLE EXECUTION LAYER              │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │                          │
│  │  │ Runtime │ │Sandbox  │ │Security │        │                          │
│  │  │ Engine  │ │(code)   │ │Policy   │        │                          │
│  │  └─────────┘ └─────────┘ └─────────┘        │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │                          │
│  │  │Storage  │ │Scheduler│ │Audit Log│        │                          │
│  │  │(events) │ │(reason) │ │(signed) │        │                          │
│  │  └─────────┘ └─────────┘ └─────────┘        │                          │
│  └───────────────────────────────────────────────┘                          │
│  ┌───────────────────────┬───────────────────────┐                          │
│  │      ADAPTABLE INTELLIGENCE LAYER            │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │                          │
│  │  │Memory   │ │Strategy │ │Policy   │        │                          │
│  │  │System   │ │Evolution│ │Evolution│        │                          │
│  │  └─────────┘ └─────────┘ └─────────┘        │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │                          │
│  │  │Experim. │ │Config   │ │Workflow │        │                          │
│  │  │Engine   │ │Evolution│ │Evolution│        │                          │
│  │  └─────────┘ └─────────┘ └─────────┘        │                          │
│  └───────────────────────────────────────────────┘                          │
│  ┌───────────────────────────────────────────────┐                          │
│  │         MODEL ABSTRACTION LAYER               │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │                          │
│  │  │Frontier │ │Cheap    │ │Local    │        │                          │
│  │  │Model    │ │Model    │ │Model    │        │                          │
│  │  └─────────┘ └─────────┘ └─────────┘        │                          │
│  └───────────────────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Primitives

### 1. Identity
- UUID (v4 or v7)
- Cryptographic keypair (Ed25519)
- Created timestamp
- Version history
- Immutable core attributes

### 2. State
- Current configuration (JSON/typed)
- Versioned via event sourcing
- Snapshot + delta
- Deterministic serialization

### 3. Memory
- **Episodic:** Raw experiences (observation, action, result, timestamp)
- **Semantic:** Facts, beliefs, relationships (with confidence, provenance)
- **Procedural:** Learned strategies, heuristics, workflows
- **Relational:** Memory about other objects
- **Experience:** Structured: observation → action → result → outcome → lesson → future behavior

### 4. Methods
- **Deterministic:** Normal Python code. Fast, reliable, testable.
- **Intelligent:** LLM-driven via docstring prompt + type contract. Like NOOA `...` body.
- **Hybrid:** Deterministic pre-check → intelligent fallback.

### 5. Relationships
- **Capability-based:** Object A holds a capability token for Object B granting specific permissions.
- **Event-driven:** Objects emit events. Other objects subscribe.
- **Direct:** Method calls with capability verification.
- **No ambient authority:** Objects cannot access anything without explicit capability.

### 6. Events
- Internal (state change, memory update)
- External (incoming message, timer, anomaly)
- Relationship (capability granted, revoked)
- Audit (action taken, experiment run)

### 7. Reasoning
- **Trigger:** Event, anomaly, scheduled, explicit request.
- **Budget:** Token limit per reasoning cycle. Model tier selection.
- **Output:** Decision, plan, hypothesis, or action.
- **Observability:** Full trace of reasoning chain.

### 8. Experimentation
- **Hypothesis:** Explicit statement of expected outcome.
- **Design:** Controlled variables, measurement plan.
- **Execution:** Sandboxed simulation or limited real execution.
- **Evaluation:** Statistical comparison against baseline.
- **Decision:** Adopt, reject, or iterate.
- **Storage:** Experience memory updated.

### 9. Evolution
- **What can evolve:** Memory, strategies, policies, configuration, workflows, tool selection.
- **What cannot evolve:** Core identity, security policy, resource limits, audit log, execution layer.
- **Process:** Version → Reason → Prediction → Experiment → Measurement → Rollback plan.
- **Approval:** Developer-defined policy (auto, human-in-loop, mandatory approval).

### 10. Constraints
- **Resource:** Token budget, compute budget, storage budget.
- **Security:** Capability boundaries, sandbox, audit.
- **Behavioral:** Goal boundaries, forbidden actions, ethical constraints.
- **Temporal:** Max reasoning time, max experiment duration.

## Memory System Design

```
┌─────────────────────────────────────────────┐
│              MEMORY HIERARCHY               │
├─────────────────────────────────────────────┤
│  L1: Working Memory (in-object, fast)       │
│      - Current context                       │
│      - Active goals                          │
│      - Recent experiences (last N)           │
├─────────────────────────────────────────────┤
│  L2: Episodic Memory (retrieved on demand)  │
│      - Full experience records               │
│      - Indexed by time, topic, outcome       │
│      - ACT-R activation + graph retrieval    │
├─────────────────────────────────────────────┤
│  L3: Semantic Memory (consolidated facts)    │
│      - Beliefs with confidence               │
│      - Provenance                            │
│      - Contradiction handling                │
├─────────────────────────────────────────────┤
│  L4: Procedural Memory (learned strategies)  │
│      - Heuristics                            │
│      - Decision policies                     │
│      - Workflows                             │
├─────────────────────────────────────────────┤
│  L5: Relational Memory (other objects)       │
│      - Object directory                      │
│      - Relationship history                  │
│      - Trust scores                          │
└─────────────────────────────────────────────┘
```

## Event Sourcing for Persistence

Every state change, memory update, relationship change, and action is an event:

```
Event {
  event_id: UUID
  object_id: UUID
  timestamp: ISO8601
  type: "state_change" | "memory_update" | "relationship_change" | "action" | "experiment" | "reasoning"
  payload: { ... }
  signature: Ed25519(object_id + timestamp + payload)
  parent_event_id: UUID  // for causal chains
}
```

Current state = fold(all events). Snapshots for fast recovery.

## Security Model

```
┌─────────────────────────────────────────────┐
│         CAPABILITY-BASED SECURITY           │
├─────────────────────────────────────────────┤
│  Object A wants to call Object B.method()   │
│                                             │
│  1. A presents capability token for B       │
│     (signed by B, grants specific rights)   │
│  2. B verifies token signature + expiry     │
│  3. B checks if method is in granted rights │
│  4. B executes method in sandbox            │
│  5. B logs action to audit trail            │
│  6. B returns result                        │
│                                             │
│  No ambient authority. No global namespace. │
│  Objects are capability-isolated.           │
└─────────────────────────────────────────────┘
```

## Model Tier Strategy

| Tier | Model | Cost | Use Case |
|------|-------|------|----------|
| T0 | Local (Llama 3.1 8B) | ~$0 | Routine cognition, pattern matching, fast pre-filter |
| T1 | Cheap API (GPT-4o-mini, Claude 3.5 Haiku) | Low | Standard reasoning, memory retrieval, summarization |
| T2 | Mid (GPT-4o, Claude 3.5 Sonnet) | Medium | Complex reasoning, experimentation, learning |
| T3 | Frontier (o3, Claude 3.5 Opus, Gemini 2.5 Pro) | High | Novel situations, critical decisions, evolution |

Objects auto-select tier based on: anomaly score, task criticality, budget remaining.

## Scheduling

- **Dormant:** No events, no scheduled tasks. Zero cost.
- **Passive:** Event-driven. Wake on message/timer/anomaly. Cheap model pre-filter.
- **Active:** Continuous reasoning loop. Budgeted.
- **Experimental:** Sandboxed. Isolated from production state.

Scheduler maintains priority queue. Importance = f(anomaly, goal urgency, budget, history).
