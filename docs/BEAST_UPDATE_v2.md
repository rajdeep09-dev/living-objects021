# BEAST UPDATE — Living Objects v2.0
## The Prompt That Makes This the Future of Software

> **This document is a complete engineering prompt for the next major version.**
> Every section is a hard technical requirement, not a wish list.
> The target: an autonomous digital civilization that outperforms every AI agent,
> coding assistant, and autonomous system on every benchmark that matters.

---

## The Problem With Everything Else

| System | Limitation |
|---|---|
| GPT / Claude | Stateless. Reasons from scratch every call. Costs tokens forever. |
| AI Agents (Hermes, SWE-agent, Devin) | One-shot task execution. No memory across runs. No self-improvement. |
| Genetic Algorithms | Blind random search. No cultural knowledge. No self-modification. |
| Our v1 (Lamarckian) | Fitness is flat. Memome is in-RAM. No real-world interface. No goal synthesis. |

**v2 fixes all of this. Here's how.**

---

## PHASE 1: CONSTITUTIONAL HYPER-META-EVOLUTION

### What it is
In v1, `mutation_rate` evolves. In v2, **the laws of evolution themselves evolve**.
An organism can rewrite the selection function, the crossover operator,
the cultural adoption rules — the entire constitution of the ecosystem.

### Hard Requirements

```python
class EvolutionConstitution:
    """
    The evolving rulebook of an ecosystem.
    Every field is itself a mutable, heritable gene.
    """
    selection_pressure: float = 0.5         # How strongly fit organisms dominate
    crossover_strategy: str = "uniform"     # uniform | one_point | two_point | blend
    cultural_adoption_rate: float = 0.3     # How fast memes spread
    novelty_weight: float = 0.3             # Weight of novelty in total fitness
    extinction_threshold: float = 0.1      # Fitness below which organism dies
    generation_overlap: float = 0.5        # Fraction of old generation that survives
    mutation_distribution: str = "gaussian" # gaussian | cauchy | levy | uniform

    def mutate(self, rng) -> "EvolutionConstitution":
        """The constitution mutates like a genome."""
        ...

    def to_code(self) -> str:
        """Generate actual Python code for the selection function from this constitution."""
        ...
```

**Proof required:** Over 100 generations, the ecosystem's constitution diverges from
the initial one. Two ecosystems seeded identically but with different random seeds
should converge to different constitutional regimes. Show it with a diff.

---

## PHASE 2: MORPHOGENETIC CODE GROWTH

### What it is
v1 organisms patch *existing* methods. v2 organisms **grow new code modules**
from scratch — new classes, new APIs, new abstractions that did not exist before.
This is the software equivalent of biological morphogenesis: cells becoming organs.

### Hard Requirements

```python
class Morphogenome:
    """
    A genome that encodes how to grow code, not just float traits.
    Inspired by Lindenmeyer Systems (L-systems) for code generation.
    """

    def grow_module(self, seed: str, complexity: int) -> str:
        """
        Produce a complete, syntactically valid Python module as a string.
        The module is a function of the seed (organism's ID) and
        the complexity level (evolves via meta-evolution).
        Uses template expansion + mutation, not LLM.
        """
        ...

    def graft(self, other: "Morphogenome") -> "Morphogenome":
        """
        Sexual recombination of two code-growing genomes.
        Child inherits code templates from both parents.
        """
        ...
```

**Proof required:**
1. Organism A grows `module_A.py` with function `solve_A(x)`.
2. Organism B grows `module_B.py` with function `solve_B(x)`.
3. Their child grows `module_AB.py` that IMPORTS and CALLS both parent functions.
4. Grandchild grows further on top. Show 4 generations of cumulative code growth.
5. All grown modules are importable Python (`importlib.import_module` must work).

---

## PHASE 3: ADVERSARIAL RED-TEAM ECOSYSTEM

### What it is
Right now organisms cooperate (cultural adoption). v2 adds **predator organisms**
that try to *break*, corrupt, or exploit other organisms' strategies.
This forces the prey organisms to become more robust. Evolution accelerates.

### Hard Requirements

```python
class RedTeamOrganism(LamarckianOrganism):
    """
    An adversarial organism that attacks others.
    Its fitness = how badly it degrades victim's fitness.
    """

    def attack(self, target: LamarckianOrganism) -> AttackResult:
        """
        Try to:
        1. Inject a malformed strategy into target's memome
        2. Corrupt target's genome (adversarial noise)
        3. Steal target's best strategy
        The target must detect and repel the attack or die.
        """
        ...

class DefenseLayer:
    """
    Every organism has an immune system that detects strategy corruption.
    Strong immune systems evolve in response to attack pressure.
    """

    def validate_strategy(self, strategy_code: str) -> ValidationResult:
        """
        Check incoming strategy for:
        - Semantic consistency with organism's existing knowledge
        - Behavioral fingerprint divergence (novelty vs. corruption)
        - Compile + sandbox execution test
        """
        ...
```

**Proof required:**
1. Spawn 10 normal organisms + 3 red-team attackers.
2. Show that attacked organisms develop stronger `DefenseLayer` over generations.
3. Show that red-teamers force prey fitness variance UP (diversity under pressure).
4. Show that removing red-teamers causes premature convergence (monoculture).

---

## PHASE 4: GOAL SYNTHESIS ENGINE

### What it is
v1 organisms evolve strategies for a fixed goal. v2 organisms **synthesize their own goals**.
No human specifies what they should optimize. They discover what is worth optimizing.

```
Human → defines environment
Organisms → discover what "good" means in that environment
          → synthesize their own fitness function
          → evolve strategies for that self-discovered goal
```

### Hard Requirements

```python
class GoalSynthesizer:
    """
    Discovers what matters in an environment through exploration.
    No hand-coded fitness function.
    """

    def observe(self, state: EnvironmentState) -> None:
        """Record an observation from the environment."""
        ...

    def synthesize_goal(self) -> Callable[[EnvironmentState], float]:
        """
        After N observations, return a fitness function that:
        1. Rewards states that are SURPRISING (high information gain)
        2. Rewards states where the organism has LEVERAGE (can influence outcomes)
        3. Penalizes states it has already fully explored
        This is intrinsic motivation, not extrinsic reward.
        """
        ...

    def evolve_goal(self, child_synthesizer: "GoalSynthesizer") -> "GoalSynthesizer":
        """Lamarckian: synthesized goals are inherited by offspring."""
        ...
```

**Proof required:**
1. Give organisms a grid environment with NO specified reward.
2. Over 50 generations, they should discover "exploration coverage" as a goal.
3. Their strategies should maximize area visited, not any human-defined metric.
4. Show that offspring inherit goal parameters from parents.

---

## PHASE 5: DISTRIBUTED CONSCIOUSNESS / HIVE MEMOME

### What it is
v1 memome is a single SQLite file. v2 memome is a **federated distributed store**
where multiple organisms on different machines share knowledge via gossip protocol.
Strategies propagate like memes through a population — by influence, not by copying.

### Hard Requirements

```python
class FederatedMemome:
    """
    A peer-to-peer cultural knowledge store.
    Organisms on different nodes share strategies via gossip.
    No central server. No single point of failure.
    """

    def gossip(self, peer: "FederatedMemome") -> int:
        """
        Exchange strategies with a peer.
        - Send strategies peer doesn't have
        - Receive strategies we don't have
        - Merge with conflict resolution (fitness-weighted)
        Returns: number of strategies exchanged
        """
        ...

    def influence_score(self, strategy_name: str) -> float:
        """
        How widely has this strategy spread across the federation?
        0.0 = only on one node
        1.0 = on all nodes (universal meme)
        """
        ...

    def lineage_graph(self) -> nx.DiGraph:
        """
        Return a directed graph: strategy A → strategy B
        where B is a descendant/mutation of A.
        This is the cultural phylogenetic tree.
        """
        ...
```

**Proof required:**
1. Spawn 3 independent in-process FederatedMemome nodes.
2. Organism on node 1 learns `strategy_alpha`.
3. After 5 gossip rounds, `strategy_alpha` appears on nodes 2 and 3.
4. Show `influence_score("strategy_alpha")` rises from 0.33 to 1.0.
5. Show the lineage graph as a real `networkx` visualization or DOT file.

---

## PHASE 6: CROSS-MODAL TOOL EMBODIMENT

### What it is
v1 organisms exist only in RAM — they mutate floats and code strings.
v2 organisms can **use real tools**: execute code, call APIs, browse the web,
write files, spawn sub-processes. They are embodied in the real world.

```
LLM Agent:   Human → Prompt → LLM reasons → Tool call → Result
Living Object: Organism → evolved strategy → Tool call → Result → Fitness update → evolve
```

The key difference: **the tool-calling strategy is EVOLVED, not prompted**.

### Hard Requirements

```python
class EmbodiedOrganism(LamarckianOrganism):
    """
    An organism that can use real-world tools as part of its strategy.
    """

    TOOL_REGISTRY: ClassVar[Dict[str, Callable]] = {}

    @classmethod
    def register_tool(cls, name: str, fn: Callable, description: str) -> None:
        """Make a tool available to all organisms."""
        cls.TOOL_REGISTRY[name] = fn

    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a registered tool and record the result.
        The result updates fitness and is stored in memome.
        """
        ...

    def evolve_tool_strategy(self, tool_name: str) -> str:
        """
        Evolve the kwargs pattern for calling a given tool.
        e.g. for 'http_get', evolve which URL parameters to use.
        """
        ...
```

**Built-in tools to register (all sandboxed):**
- `python_exec(code: str) -> str` — run Python, return stdout
- `file_read(path: str) -> str` — read a file from allowed paths
- `http_get(url: str) -> str` — GET a URL, return text
- `shell_cmd(cmd: str) -> str` — run a whitelisted shell command

**Proof required:**
1. Register `python_exec` as a tool.
2. Seed population with the task: "generate the first N primes".
3. Over 30 generations, organisms should evolve a correct `python_exec` strategy
   (the code string they exec should get better over time).
4. Show fitness (correctness %) rising from ~30% to >90% across generations.
5. The evolved code must be something no human wrote.

---

## PHASE 7: TEMPORAL CREDIT ASSIGNMENT (ANCESTRY CREDIT)

### What it is
When a Gen-50 organism has high fitness, which of its 50 ancestor generations
actually *contributed*? v2 tracks this with a `credit graph`.
Ancestors whose strategies are still in use get credit — they influenced the future.

```python
class AncestryCredit:
    """
    Tracks which ancestor strategies actually mattered.
    Organisms whose memes are used by many descendants get HIGH credit.
    Organisms whose memes died unused get ZERO credit.
    """

    def attribute(
        self,
        champion: LamarckianOrganism,
        memome: FederatedMemome,
        population_history: List[GenerationSnapshot],
    ) -> Dict[str, float]:
        """
        Returns {strategy_name: credit_score} for every strategy
        in the champion's ancestry.
        Credit is proportional to:
          - How many descendant organisms used this strategy
          - How long the strategy survived (generational span)
          - The fitness boost the strategy provided when adopted
        """
        ...
```

**Proof required:**
1. Run 50 generations.
2. Pick the champion organism.
3. Show the top-5 strategies by ancestry credit.
4. Verify: each credited strategy is in the champion's genome AND was learned
   by an ancestor, not by the champion itself (truly Lamarckian).

---

## PHASE 8: ORGANISM DSL (DOMAIN-SPECIFIC LANGUAGE EMERGENCE)

### What it is
Organisms currently communicate strategies as Python code strings.
v2 organisms **evolve their own language** — a compact Domain-Specific Language (DSL)
for expressing strategies. The DSL gets richer and more expressive over generations.

```
Gen 0:  Organism expresses strategy as: "if fitness > 0.5: cooperate"
Gen 10: Organism evolves shorthand:     "fit:coop"
Gen 30: Organism evolves primitives:    "WHEN(HIGH_FIT) → COOP; ELSE → DEFECT"
Gen 50: Organism evolves full grammar:  "(cond ((fit-p self) (coop)) (t (defect)))"
```

### Hard Requirements

```python
class DSLGenome:
    """
    A genome that encodes a mini-language.
    Tokens, grammar rules, and semantics all evolve.
    """
    vocabulary: List[str]        # evolves: new words appear
    grammar_rules: List[Rule]    # evolves: new syntax patterns
    semantics: Dict[str, Callable]  # evolves: word meanings change

    def express(self, strategy_intent: Dict) -> str:
        """Encode a strategy intent as DSL source."""
        ...

    def parse(self, dsl_source: str) -> Dict:
        """Decode a DSL string back to an executable strategy."""
        ...

    def crossover(self, other: "DSLGenome") -> "DSLGenome":
        """
        Two languages crossover → a new language with words from both.
        Meaning conflicts resolved by fitness-weighted voting.
        """
        ...
```

**Proof required:**
1. DSL vocabulary size starts at 5 tokens.
2. After 50 generations, vocabulary has grown to >20 tokens.
3. New tokens encode COMPOUND strategies (combining 2+ primitive strategies).
4. Show a token that Gen-0 organisms don't have that Gen-50 organisms use daily.

---

## PHASE 9: THERMODYNAMIC FITNESS (ENERGY-BASED SELECTION)

### What it is
Real biological fitness isn't a number — it's about energy efficiency.
Organisms that achieve their goals with LESS computation survive longer.
This makes efficiency itself evolve.

```python
class ThermodynamicFitness:
    """
    Fitness = achievement / cost.
    A strategy that gets 0.8 fitness using 10 operations
    beats one that gets 0.9 fitness using 1000 operations.
    """

    def measure(
        self,
        organism: LamarckianOrganism,
        task: Callable,
        budget: int = 1000,  # max operations
    ) -> ThermodynamicScore:
        """
        Run organism on task.
        Track: result quality, operations used, memory allocated.
        Return: efficiency-adjusted fitness score.
        """
        ...

class EnergyBudget:
    """Each organism has a finite energy budget per generation."""
    initial: float = 100.0
    cost_per_strategy_call: float = 1.0
    cost_per_memome_query: float = 0.5
    cost_per_mutation: float = 2.0
    income_per_fitness_point: float = 5.0

    def can_afford(self, action: str) -> bool: ...
    def spend(self, action: str) -> None: ...
    def earn(self, fitness: float) -> None: ...
```

**Proof required:**
1. Start with organisms that use many strategy calls per task.
2. After 50 generations under energy budget, show:
   - Average operations-per-task has DECREASED.
   - Average fitness-per-operation has INCREASED.
   - The `EnergyBudget` is binding — some organisms die from budget exhaustion.

---

## PHASE 10: REAL-TIME OBSERVATORY v2

### What it is
The current Web UI shows static charts. v2 is a **live, interactive command interface**
that lets any human directly intervene in evolution as it happens.

### Features Required

**1. Species Inspector**: Click any organism → see its full genome, memome contributions,
ancestry tree, and all current method patches in real-time.

**2. Strategy Marketplace**: Organisms publicly list strategies they'll "sell" for cultural credit.
Humans can inject strategies directly into the marketplace.

**3. Constitutional Editor**: Live YAML editor where you can edit the `EvolutionConstitution`
while evolution is running. Changes take effect at the next generation boundary.

**4. Red-Team Console**: Spawn an adversarial organism from the UI with custom attack code.
Watch how the population responds in real-time.

**5. Ancestry Visualization**: A live phylogenetic tree (D3.js force-directed graph)
showing every organism, its parents, and which strategies flowed between them.
Color-code nodes by species. Highlight the champion lineage.

**6. DSL Terminal**: A REPL where you type in the organisms' evolving DSL
and see what strategies it maps to in real Python. Watch the DSL change live.

**Backend changes required:**
```python
# WebSocket events needed:
{
    "type": "organism_born",
    "organism_id": "...",
    "genome_snapshot": {...},
    "parent_ids": [...],
    "inherited_strategies": [...]
}

{
    "type": "strategy_adopted",
    "adopter_id": "...",
    "strategy_name": "...",
    "creator_id": "...",  # may be dead
    "creator_generation": 12,
    "adopter_generation": 34
}

{
    "type": "constitution_mutated",
    "before": {...},
    "after": {...},
    "organism_id": "..."
}

{
    "type": "red_team_attack",
    "attacker_id": "...",
    "target_id": "...",
    "result": "repelled | success | partial"
}
```

---

## BENCHMARK TARGETS

When v2 is complete, it must beat these published benchmarks:

| Benchmark | Target | Current SOTA |
|---|---|---|
| Novelty search diversity (archive size / generations) | >5 novel behaviors/gen | ~2 (Lehman & Stanley 2011) |
| Cultural strategy survival rate | >80% strategies outlive creator | Not measured in literature |
| Meta-evolution convergence speed | Constitution stabilizes in <20 gens | N/A |
| Thermodynamic efficiency gain | >3x operations reduction over 50 gens | N/A |
| DSL vocabulary growth | >4x expansion in 50 gens | N/A |
| Red-team robustness | Population survives 30% adversarial pressure | N/A |

---

## DELIVERABLES CHECKLIST

### Code
- [ ] `evolution/constitution.py` — `EvolutionConstitution` with full mutation + code generation
- [ ] `evolution/morphogenome.py` — `Morphogenome`, code growth, `graft()`
- [ ] `evolution/red_team.py` — `RedTeamOrganism`, `DefenseLayer`, `AttackResult`
- [ ] `evolution/goal_synthesis.py` — `GoalSynthesizer`, intrinsic motivation loop
- [ ] `evolution/federated_memome.py` — `FederatedMemome`, gossip protocol, lineage graph
- [ ] `evolution/embodied.py` — `EmbodiedOrganism`, tool registry, tool strategy evolution
- [ ] `evolution/ancestry_credit.py` — `AncestryCredit`, attribution algorithm
- [ ] `evolution/dsl.py` — `DSLGenome`, `Rule`, parser, crossover
- [ ] `evolution/thermodynamic.py` — `ThermodynamicFitness`, `EnergyBudget`
- [ ] `evolution/test_v2.py` — Full test suite, all proofs above, 100% passing

### Infrastructure
- [ ] `production/api/v2/` — New API endpoints for all v2 features
- [ ] `production/api/v2/websocket.py` — All 4 new WebSocket event types
- [ ] `production/store_v2.py` — Federated memome SQLite schema
- [ ] Updated `docker-compose.yml` — Add gossip port exposure
- [ ] Updated Helm chart — HPA for organism count

### Web UI
- [ ] Species Inspector panel
- [ ] Strategy Marketplace UI
- [ ] Constitutional Editor (live YAML)
- [ ] Red-Team Console
- [ ] D3.js ancestry phylogenetic tree
- [ ] DSL Terminal REPL

### Documentation
- [ ] `docs/v2-architecture.md` — Complete technical architecture
- [ ] `docs/api-v2-reference.md` — Full OpenAPI spec
- [ ] `docs/benchmark-results.md` — Benchmark runs vs. SOTA
- [ ] `research/dsl-emergence-notes.md` — Theoretical notes on DSL evolution
- [ ] Updated `README.md` — v2 feature list + quick-start

---

## THE BIG PICTURE

```
v1 (current):  Individual organisms evolve strategies
v2 (this prompt): Civilizations evolve civilizations

           [Constitution evolves]
                    ↓
    [Organisms evolve code modules]    ←→   [Red-team forces robustness]
                    ↓
    [Organisms synthesize their own goals]
                    ↓
    [DSL emerges — organisms get a language]
                    ↓
    [Federated memome — knowledge becomes civilization-scale]
                    ↓
    [Embodied organisms act in the real world]
                    ↓
    [Ancestry credit — history matters]
                    ↓
    [Thermodynamic pressure — efficiency is survival]
```

**This is not a better AI agent.**
**This is a new class of system: a digital civilization engine.**

The difference:
- AI agents answer questions. This **builds civilizations that answer questions better over time**.
- LLMs consume tokens. This **compounds knowledge across generations**.
- Coding assistants write code. This **evolves code that writes itself**.

---

*Written by the Living Objects Research team.*
*Target delivery: v2.0 milestone.*
*Priority: MAXIMUM.*
