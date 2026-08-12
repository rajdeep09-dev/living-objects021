# Prior Art

## Mission
Try hard to prove the Living Objects thesis wrong by finding everything that already solves it.

---

## 1. NVIDIA NOOA (NVIDIA Object-Oriented Agents)
- **Creators:** Paul Furgale, Severin Klingler, James Nolan, Matt Staats, et al. (NVIDIA Labs)
- **Date:** July 30, 2026 (v0.0.8 alpha)
- **URL:** https://github.com/NVIDIA-NeMo/labs-OO-Agents
- **Architecture:** Agent = single Python class. Methods = actions, fields = state, docstrings = prompts, type annotations = contracts. `...` body = LLM-driven. Normal body = deterministic Python. Code-as-action via Python REPL. MemoryManager with SQLite, reflection, consolidation. Model-agnostic via LiteLLM.
- **What it solves:** Eliminates fragmented prompt/template/tool-schema/callback sprawl. Makes agents testable, refactorable, traceable like normal software. Six combined capabilities: typed I/O, pass-by-reference live objects, code-as-action, programmable loops, explicit object state, model-callable harness APIs.
- **What it does not solve:** Persistent identity across process restarts (state is in-memory during execution). Controlled self-experimentation. Object-graph relationships with permissions. Evolution of strategies/policies. Security sandboxing is external (container/VM), not intrinsic to the object model.
- **Overlap with Living Objects:** The closest architectural foundation. Living Objects builds directly on NOOA's agent-as-object model.
- **Differences:** NOOA is an agent harness. Living Objects asks whether intelligence can be a native property of ALL persistent software objects, not just one agent class. NOOA does not treat persistence, relationships, experimentation, or controlled evolution as first-class primitives.
- **Lessons:** The OO-agent model is validated. Models understand it (97.9% capability test pass rate). Token efficiency is real (half the tokens of peers on SWE-bench). BUT: it is still alpha, not a runtime, not a containment boundary.
- **Threat to novelty:** HIGH. NOOA already collapses the agent into an object. If Living Objects is just "NOOA + persistence," it may not be novel.

---

## 2. LangChain / LangGraph
- **Creators:** LangChain AI (Harrison Chase et al.)
- **Date:** 2023–2026 (LangGraph 1.0 production-stable)
- **URL:** https://github.com/langchain-ai/langgraph
- **Architecture:** Graph-based stateful workflows. Nodes = prompts/sub-tasks. Edges = data flow. Checkpointed durable execution. Human-in-the-loop interrupts. Time-travel debugging. DeepAgents = opinionated harness on top.
- **What it solves:** Complex multi-step workflows with branching, error handling, production observability. 1000+ integrations. Largest ecosystem.
- **What it does not solve:** Native object-oriented agent model. Intelligence is not a property of objects; it is a property of graphs. No persistent identity semantics. No object relationships. No self-experimentation.
- **Overlap:** Both deal with stateful agents. Both have memory.
- **Differences:** LangGraph orchestrates agents. Living Objects wants agents to BE objects in a system. LangGraph is workflow-centric; Living Objects is entity-centric.
- **Threat to novelty:** LOW. Different abstraction layer entirely.

---

## 3. OpenClaw
- **Creators:** Peter Steinberger (Austrian developer)
- **Date:** November 2025 – 2026
- **URL:** https://github.com/openclaw
- **Architecture:** Local-first TypeScript agent runtime. Messaging-first UX (WhatsApp, Telegram, Discord, etc.). ReAct + composable skills. Task Brain control panel. Runs 24/7.
- **What it solves:** Privacy-first personal/team autonomous assistant. One-command setup. 50+ platform integrations.
- **What it does not solve:** Framework for building agent products. Not OO. No persistence model beyond chat history. No experimentation. No evolution.
- **Overlap:** Autonomous agent that runs continuously.
- **Differences:** OpenClaw is a personal assistant runtime. Living Objects is a programming paradigm for building systems.
- **Threat to novelty:** LOW. Different category.

---

## 4. Claude Agent SDK
- **Creators:** Anthropic
- **Date:** September 2025 (renamed from Claude Code SDK)
- **URL:** https://www.anthropic.com
- **Architecture:** Library exposing Claude Code harness. Tool-use chain with subagents. Hooks lifecycle. MCP native. File/shell access built-in. Session management.
- **What it solves:** Production coding agents, research agents, OS-level access. Deepest MCP integration.
- **What it does not solve:** Model-agnostic. No OO model. No persistent identity. No object relationships. No self-experimentation.
- **Overlap:** Agent loop, tool use, memory.
- **Differences:** Locked to Claude models. Not a programming paradigm.
- **Threat to novelty:** LOW.

---

## 5. CrewAI
- **Creators:** João Moura et al.
- **Date:** 2024–2026 (v1.14.6, ~2B executions in 12 months)
- **URL:** https://github.com/joaomdmoura/crewAI
- **Architecture:** Role-based multi-agent crews. Process types. Event-driven flows. Unified Memory. A2A protocol support.
- **What it solves:** Fast prototyping of multi-agent collaboration. Intuitive role-based DSL.
- **What it does not solve:** OO model. Persistent identity. No experimentation/evolution primitives.
- **Overlap:** Multi-agent systems.
- **Differences:** CrewAI is about agent teams. Living Objects is about intelligent object graphs.
- **Threat to novelty:** LOW.

---

## 6. Self-Evolving Software Agents (AAMAS 2026)
- **Creators:** University of Trento
- **Date:** April 2026 (AAMAS '26, Paphos, Cyprus)
- **URL:** https://arxiv.org/html/2604.27264v1
- **Architecture:** BDI–LLM architecture. Automated evolution module operates alongside reasoning loop. Elicits new requirements from experience. Synthesizes design and code updates. Agents autonomously discover new goals and generate executable behaviors.
- **What it solves:** Genuine software evolution beyond adaptation. Goals, reasoning, and code can evolve autonomously.
- **What it does not solve:** OO model. Persistence. Object relationships. Controlled experimentation framework. Security/sandboxing.
- **Overlap:** Self-evolution, autonomous improvement.
- **Differences:** BDI-based, not OO. Focus is on evolution of behavior, not on persistent intelligent objects as a programming model.
- **Threat to novelty:** MEDIUM. Shows that self-evolution is feasible. Living Objects must differentiate by being a programming model, not just an evolving agent.

---

## 7. EvoHarness-RL (Meta, 2026)
- **Creators:** Meta AI
- **Date:** August 2026
- **URL:** https://arxiv.org/html/2608.05446v1
- **Architecture:** Trainable coordination layer for learning how agents construct and use external harness state. BPE workspace: Belief, Progress, Experience. Harness meta-actions: query belief, commit progress, recall experience, write insights. Two-stage training: SFT harness fine-tuning + cost-aware GRPO.
- **What it solves:** Learning WHEN to use external state, not just how. Harness annealing: policy internalizes routine behaviors, preserves harness access for high-value moments. Experience store evolves through accumulation, consolidation, forgetting.
- **What it does not solve:** OO model. Object persistence. Object relationships. Not a developer-facing programming model.
- **Overlap:** External memory evolution, experience accumulation, harness learning.
- **Differences:** EvoHarness-RL is a training method for harness state management. Living Objects is a software architecture paradigm.
- **Threat to novelty:** MEDIUM. The experience-store evolution pattern is very similar to what Living Objects proposes.

---

## 8. Mem²Evolve (Beihang University, 2026)
- **Creators:** Zihao Cheng, Zeming Liu, et al.
- **Date:** April 2026 (ACL 2026)
- **URL:** https://arxiv.org/html/2604.10923v1
- **Architecture:** Dual-Memory mechanism: Asset Memory (expert agents + tools) and Experience Memory (strategic insights from trajectories). Forward inference: reuse first, create on demand. Backward evolution: retain assets, distill lessons. Co-evolution of capabilities and experience.
- **What it solves:** Couples dynamic capability expansion with experience distillation. Breaks static toolset boundaries. Stable self-evolution across 6 task categories, 8 benchmarks.
- **What it does not solve:** OO programming model. Persistence across restarts. Object-graph relationships. Developer experience as a paradigm.
- **Overlap:** Experience memory, asset creation, evolution, backward learning.
- **Differences:** Mem²Evolve is an agent framework with evolution. Living Objects asks whether the object itself should be the persistent, intelligent, evolving entity.
- **Threat to novelty:** HIGH. Mem²Evolve already does co-evolution of capabilities and experience. Living Objects must show that the OO + persistence + relationship + security model adds something beyond this.

---

## 9. MemEvolve (Meta-Evolution of Agent Memory Systems)
- **Creators:** Unknown (2025)
- **Date:** December 2025
- **URL:** https://arxiv.org/abs/2512.18746
- **Architecture:** Splits memory into 4 evolvable parts: how experience becomes notes, where notes are stored, how they are found, how junk is removed. EvolveLab rebuilds 12 earlier memory systems in same format. Scores designs by success, token usage, latency.
- **What it solves:** Memory system itself evolves to fit task types. +17.06% improvement on strong baselines.
- **What it does not solve:** OO model. Persistence. Relationships.
- **Overlap:** Evolving memory.
- **Differences:** Focuses on memory architecture evolution, not object intelligence.
- **Threat to novelty:** LOW.

---

## 10. Actor Model + AI (Akka, 2026)
- **Creators:** Lightbend / Community
- **Date:** Ongoing (2026 blog post)
- **URL:** https://pradeepl.com/blog/agentic-ai/akka-actor-model-agentic-ai/
- **Architecture:** Actors as concurrent, stateful agents. Message passing. Supervision. Bounded mailboxes. Persistence via event sourcing (Akka Persistence). Distributed clustering.
- **What it solves:** Managing thousands of concurrent stateful agents. Fault tolerance. Location transparency.
- **What it does not solve:** LLM integration is manual. No native reasoning. No memory consolidation. No experimentation.
- **Overlap:** Stateful objects, message passing, persistence, concurrency.
- **Differences:** Actor model is about concurrency and distribution. Living Objects is about intelligence and evolution. But the concurrency model is highly relevant.
- **Threat to novelty:** LOW for the core thesis, HIGH for implementation. Actor model may be the right runtime substrate.

---

## 11. Object Databases / AI-Native Databases
- **Creators:** Various (Tiger Data, ZeroDB, Fastio, Mem0, Weaviate)
- **Date:** 2025–2026
- **Architecture:** Unified storage for episodic events, semantic knowledge, procedural state. PostgreSQL + pgvector + hypertables. MCP tool integration. Self-provisioning.
- **What it solves:** Persistent memory for agents. Vector + relational + time-series in one system.
- **What it does not solve:** OO programming model. Object intelligence. Relationships with permissions.
- **Overlap:** Persistence, memory.
- **Differences:** Storage layer only.
- **Threat to novelty:** LOW.

---

## 12. Object-Oriented AI (Historical)
- **Creators:** Various (1990s–2000s)
- **Date:** 1990s–2010s
- **Architecture:** AI techniques embedded in OO languages. Knowledge representation via objects. Rule engines as objects.
- **What it solved:** Structured knowledge representation. Reusable AI components.
- **What it did not solve:** LLM integration. Persistent intelligent objects. Self-evolution.
- **Overlap:** OO + AI.
- **Differences:** Pre-LLM. No generative reasoning.
- **Threat to novelty:** LOW. Historical precedent, not current competition.

---

## 13. Digital Twins
- **Creators:** Various (industrial IoT, manufacturing)
- **Date:** 2010s–2026
- **Architecture:** Virtual representation of physical assets. Real-time data synchronization. Simulation. Predictive maintenance.
- **What it solves:** Monitoring and simulating physical systems.
- **What it does not solve:** Autonomous reasoning. Self-experimentation. Evolution. General software objects.
- **Overlap:** Persistent stateful representation of an entity.
- **Differences:** Digital twins mirror physical reality. Living Objects create intelligence in software entities that may have no physical counterpart.
- **Threat to novelty:** LOW.

---

## 14. Self-Modifying Software / Genetic Programming
- **Creators:** John Koza, others
- **Date:** 1990s–present
- **Architecture:** Programs that evolve their own code via evolutionary algorithms.
- **What it solves:** Automatic program synthesis. Optimization.
- **What it does not solve:** LLM reasoning. Persistent identity. Object model. Security.
- **Overlap:** Self-evolution.
- **Differences:** Genetic programming evolves code structure. Living Objects evolves behavior through experience while keeping execution layer stable.
- **Threat to novelty:** LOW. Different mechanism.

---

## 15. Cybernetics / Artificial Life
- **Creators:** Norbert Wiener, Christopher Langton, others
- **Date:** 1940s–present
- **Architecture:** Feedback loops. Homeostasis. Emergent behavior. Autopoiesis.
- **What it solves:** Theoretical framework for self-regulating systems.
- **What it does not solve:** Concrete software architecture. Programming model.
- **Overlap:** Self-regulation, adaptation, feedback.
- **Differences:** Theoretical inspiration, not engineering substrate.
- **Threat to novelty:** LOW.

---

## Summary Threat Assessment

| Threat Level | Source | Why |
|--------------|--------|-----|
| **HIGH** | NVIDIA NOOA | Already has agent-as-object. If Living Objects = NOOA + persistence, it is incremental. |
| **HIGH** | Mem²Evolve | Already has co-evolution of capabilities and experience. |
| **MEDIUM** | EvoHarness-RL | Experience store evolution + harness learning is adjacent. |
| **MEDIUM** | Self-Evolving Software Agents (AAMAS) | BDI+LLM autonomous evolution is close to controlled evolution. |
| **LOW** | LangGraph, CrewAI, OpenClaw, Claude SDK | Different abstraction layers. |
| **LOW** | Actor Model | Good runtime substrate, not competing paradigm. |
| **LOW** | Object Databases | Storage layer, not programming model. |
| **LOW** | Digital Twins, Genetic Programming, Cybernetics | Different domains or historical. |

## Critical Question
If we combine: NOOA (OO agent) + Mem²Evolve (dual memory evolution) + Actor Model (concurrency/persistence) + Object Databases (storage), do we get Living Objects? Or is there a genuine new abstraction that emerges only when these are unified?

The project MUST answer this in Months 1–3 or pivot.
