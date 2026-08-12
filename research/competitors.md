# Competitors

## Direct Competitors (Agent Frameworks)

| Framework | Paradigm | Multi-Agent | Memory | Persistence | OO Model | Evolution | Maturity |
|-----------|----------|-------------|--------|-------------|----------|-----------|----------|
| **NOOA** | Python class | No | SQLite + reflection | In-memory state | **Yes** | No | Alpha v0.0.8 |
| **LangGraph** | Graph | Yes | Checkpoint + state | Durable execution | No | No | Production |
| **CrewAI** | Role-based crews | Yes | Unified Memory | Task outputs | No | No | Production |
| **OpenClaw** | Runtime | Yes (skills) | Chat history | Local state | No | No | Production |
| **Claude Agent SDK** | Tool-use chain | Subagents | Sessions | Session state | No | No | Production |
| **OpenAI Agents SDK** | Handoffs | Yes | Sessions | Context variables | No | No | Production |
| **Pydantic AI** | Type-safe agent | No | Manual | Durable execution | No | No | Production |
| **Mastra** | TS full-stack | Yes | 4 types + observational | Workflow memory | No | No | Beta |
| **AutoGen/AG2** | Conversational | Yes | Conversation history | In-memory | No | No | Maintenance |
| **Microsoft Agent Framework** | Graph + middleware | Yes | Pluggable | Checkpointing | No | No | 1.0 GA |
| **Google ADK** | Hierarchical tree | Yes | Session state | Session persistence | No | No | Production |
| **Smolagents** | Minimal code | Limited | Light | None | No | No | Production |
| **Agno** | AgentOS runtime | Yes | Memory + tracing | API-backed | No | No | Production |

## Adjacent Competitors (Evolution / Memory)

| System | Focus | Evolution | Memory Type | OO |
|--------|-------|-----------|-------------|-----|
| **Mem²Evolve** | Self-evolving agents | **Yes** | Dual: Asset + Experience | No |
| **EvoHarness-RL** | Harness learning | **Yes** | BPE: Belief/Progress/Experience | No |
| **Self-Evolving Software Agents** | BDI+LLM evolution | **Yes** | BDI beliefs | No |
| **MemEvolve** | Memory system evolution | **Yes** | Evolvable architecture | No |
| **ReasoningBank** | Reasoning strategies | No | External memory bank | No |
| **AFlow** | Workflow optimization | Partial (MCTS) | Search history | No |
| **SkillOS** | Skill learning | Partial | Skill bank | No |

## Competitive Moat Analysis

### What NOOA has that others don't:
- Native Python OO model
- Code-as-action
- Live object pass-by-reference
- Model-callable harness APIs

### What Mem²Evolve has that others don't:
- Co-evolution of capabilities AND experience
- Dynamic asset creation guided by experience
- Forward-backward evolution loop

### What LangGraph has that others don't:
- Durable execution with checkpointing
- Time-travel debugging
- Human-in-the-loop interrupts
- Largest ecosystem

### What Living Objects MUST have to compete:
1. **Persistent identity** beyond checkpointing (survives restart, migration, model swap)
2. **Object-graph relationships** with permissions (not just multi-agent handoffs)
3. **Controlled experimentation** as a first-class primitive
4. **Structured experience** (observation→action→result→lesson→behavior)
5. **Capability-based security** intrinsic to the object model
6. **Deterministic + intelligent methods** coexisting (like NOOA)
7. **Evolution of strategies/policies** (like Mem²Evolve but for object behavior)

If Living Objects cannot demonstrate that the COMBINATION of these creates a genuinely different developer experience, the project should be documented and abandoned.
