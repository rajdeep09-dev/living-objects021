# Literature

## Core Papers

### 1. NVIDIA-labs OO Agents: Native Python Object-Oriented Agents
- **Authors:** Paul Furgale, Severin Klingler, James Nolan, Matt Staats, et al.
- **Year:** 2026
- **URL:** https://arxiv.org/pdf/2607.20709
- **Key Contributions:**
  1. Agent-as-Python-object programming model.
  2. Six combined capabilities: typed I/O, pass-by-reference, code-as-action, programmable loops, explicit state, model-callable harness APIs.
  3. SWE-bench Verified 82.2%, CyberGym L1 86.8%, ARC-AGI-3 85.1%.
  4. Capability tests: 97.9% pass rate across 10 models.
  5. Memory system: SQLite-based, reflection, consolidation, ACT-R activation + graph retrieval.
- **Relevance:** Foundation substrate for Living Objects.

### 2. Self-Evolving Software Agents (AAMAS 2026)
- **Authors:** University of Trento
- **Year:** 2026
- **URL:** https://arxiv.org/html/2604.27264v1
- **Key Contributions:**
  1. BDI–LLM architecture for autonomous evolution.
  2. Evolution module elicits new requirements from experience.
  3. Synthesizes design and code updates.
  4. Agents discover new goals and generate executable behaviors.
- **Relevance:** Shows feasibility of autonomous evolution. Threat to novelty if Living Objects does not differentiate.

### 3. EvoHarness-RL: Learning Self-Evolving Runtime Harness for Long-Horizon LLM Agents
- **Authors:** Meta AI
- **Year:** 2026
- **URL:** https://arxiv.org/html/2608.05446v1
- **Key Contributions:**
  1. BPE workspace: Belief, Progress, Experience.
  2. Harness meta-actions as learned policy.
  3. Cost-aware GRPO optimization.
  4. Harness annealing: policy internalizes routine behaviors.
  5. Experience store evolves through accumulation, consolidation, forgetting.
  6. 96.9% success on ALFWorld (Qwen3-8B).
- **Relevance:** Experience evolution pattern. Adjacent to Living Objects memory model.

### 4. Mem²Evolve: Towards Self-Evolving Agents via Co-Evolutionary Capability Expansion and Experience Distillation
- **Authors:** Zihao Cheng, Zeming Liu, et al. (Beihang University)
- **Year:** 2026 (ACL 2026)
- **URL:** https://arxiv.org/html/2604.10923v1
- **Key Contributions:**
  1. Co-evolutionary paradigm: capability expansion + experience distillation.
  2. Dual-Memory: Asset Memory (tools/agents) + Experience Memory (lessons).
  3. Forward inference: reuse first, create on demand.
  4. Backward evolution: retain assets, distill lessons.
  5. +18.53% over standard LLMs, +11.80% over experience-only, +6.46% over capability-only.
- **Relevance:** Directly adjacent. Living Objects must show that OO + persistence + relationships adds value beyond this.

### 5. MemEvolve: Meta-Evolution of Agent Memory Systems
- **Authors:** Unknown
- **Year:** 2025
- **URL:** https://arxiv.org/abs/2512.18746
- **Key Contributions:**
  1. Memory system itself evolves.
  2. 4 evolvable parts: experience→notes, storage, retrieval, forgetting.
  3. +17.06% improvement.
- **Relevance:** Memory architecture evolution.

## Survey Papers

### 6. A Survey of RAG-Reasoning Systems in Large Language Models
- **Authors:** Yangning Li et al.
- **Year:** 2025 (EMNLP)
- **Relevance:** Memory and reasoning patterns.

## Books / Historical

### 7. Cybernetics: Or Control and Communication in the Animal and the Machine
- **Author:** Norbert Wiener
- **Year:** 1948
- **Relevance:** Theoretical foundation for feedback, self-regulation.

### 8. The Society of Mind
- **Author:** Marvin Minsky
- **Year:** 1986
- **Relevance:** Society of agents as mind. Relevant to object-graph intelligence.

### 9. Object-Oriented Software Construction
- **Author:** Bertrand Meyer
- **Year:** 1988/1997
- **Relevance:** Design by contract. Type systems. Persistence. Relevant to typed intelligent methods.

## Framework Documentation

### 10. LangGraph Documentation
- **URL:** https://langchain-ai.github.io/langgraph/
- **Relevance:** Stateful workflow patterns. Checkpointing. Human-in-the-loop.

### 11. NOOA GitHub Repository
- **URL:** https://github.com/NVIDIA-NeMo/labs-OO-Agents
- **Relevance:** Implementation details. Memory subsystem. Examples.

## Blog Posts / Industry Analysis

### 12. NVIDIA NOOA vs LangChain vs AutoGen (2026)
- **URL:** https://aitoolsrecap.com/Comparisons/nvidia-nooa-vs-langchain-vs-autogen-2026
- **Relevance:** Comparative analysis. Production readiness assessment.

### 13. Open-Source AI Agent Frameworks Comparison (Langfuse)
- **URL:** https://langfuse.com/blog/2025-03-19-ai-agent-comparison
- **Relevance:** Framework landscape as of July 2026.

### 14. NVIDIA NOOA Review (Wavect)
- **URL:** https://wavect.io/blog/nvidia-nooa-object-oriented-agents-review/
- **Relevance:** Production readiness critique. Security analysis.
