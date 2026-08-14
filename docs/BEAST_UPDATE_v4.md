# BEAST UPDATE v4 — Living Objects Quantum Civilization Engine
## 1000x Improvement Prompt: From Digital Evolution to Digital Universe

> **v1:** Individual organisms evolve strategies
> **v2:** Civilizations evolve civilizations
> **v3:** Civilizations self-prove safety, trade across borders, measure awareness
> **v4:** The system evolves its own physics, spawns new universes, and becomes
>         the substrate that future AI civilizations run on

---

## PART A: VULNERABILITIES FOUND IN v3

> **Every item was found by static audit of the actual committed code.**
> Ship these fixes BEFORE any new v4 feature merges.

---

### VULN-V3-01: Password Comparison Uses `==` — Timing Attack

**File:** `production/api/main.py:182-183`

```python
# CURRENT (v3) — EXPLOITABLE
expected_user = request.username == settings.operator_username
expected_password = request.password == settings.operator_password
```

Python's `==` on strings is **not constant-time**. An attacker measuring
response latency can infer correct characters one by one (timing oracle attack).
With 10,000 requests they can recover the password without knowing it.

**Fix:**
```python
import hmac

def _constant_time_equal(a: str, b: str) -> bool:
    """Timing-safe string comparison. Always takes same time regardless of content."""
    return hmac.compare_digest(a.encode(), b.encode())

expected_user = _constant_time_equal(request.username, settings.operator_username)
expected_password = _constant_time_equal(request.password, settings.operator_password)
# BOTH must pass — don't short-circuit. And don't leak WHICH one failed in the error.
if not (expected_user and expected_password):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

---

### VULN-V3-02: Sandbox Temp Directory Not Cleaned Up on Process Kill

**File:** `evolution/sandbox.py:94-135`

```python
# CURRENT (v3) — DISK LEAK
temp_dir = tempfile.mkdtemp(prefix="living-objects-sandbox-")
code_path = os.path.join(temp_dir, "organism.py")
try:
    ...
    process.kill()  # ← TIMEOUT PATH: code_path may not unlink cleanly
    ...
finally:
    try:
        os.unlink(code_path)   # ← may fail if process still holds file
        os.rmdir(temp_dir)     # ← only removes EMPTY dirs — what if subprocess wrote files?
    except OSError:
        pass   # ← silently leaks the directory forever
```

If the sandboxed process writes extra files before being killed,
`os.rmdir()` fails (non-empty dir) and the `except OSError: pass` silently swallows it.
Under load: hundreds of leaked temp directories accumulate on disk.

**Fix:**
```python
import shutil

finally:
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)  # recursive, handles non-empty dirs
    except Exception:
        pass  # best-effort — log but never raise
```

---

### VULN-V3-03: Market Wallet Has No Thread-Safety / Race Condition

**File:** `evolution/market.py` — `TokenWallet.spend()` and `StrategyMarket.buy()`

```python
# CURRENT (v3) — RACE CONDITION
def spend(self, amount: float, reason: str, ...) -> bool:
    if amount > self.balance + 1e-9:  # ← CHECK
        return False
    self.balance -= amount             # ← ACT (not atomic with CHECK)
    ...
```

In a concurrent FastAPI async context or when two evolution threads run,
two simultaneous calls to `spend()` can both pass the check and both decrement,
driving `balance` negative. An organism can buy strategies it cannot afford.

**Fix:**
```python
import threading

class TokenWallet:
    def __init__(self):
        self.balance: float = 100.0
        self._lock = threading.Lock()

    def spend(self, amount: float, reason: str, ...) -> bool:
        with self._lock:           # atomic check-and-act
            if amount > self.balance + 1e-9:
                return False
            self.balance -= amount
            return True
```

---

### VULN-V3-04: Diplomacy Protocol Has No Replay Attack Protection

**File:** `evolution/diplomacy.py` — `ExchangeProposal` has no nonce, no timestamp,
no expiry, no signature on the proposal body.

```python
# CURRENT (v3) — REPLAYABLE
class ExchangeProposal:
    proposal_id: str    # ← just a UUID, can be replayed
    our_offer: List[str]
    our_request: List[str]
    # No: timestamp, expiry, nonce, HMAC signature
```

An attacker who intercepts a completed exchange proposal can resubmit it
to trigger the same exchange again — double-spending cultural strategies.

**Fix:**
```python
import secrets, time, hmac, hashlib

@dataclass
class ExchangeProposal:
    proposal_id: str
    initiator_id: str
    responder_id: str
    our_offer: List[str]
    our_request: List[str]
    nonce: str = field(default_factory=lambda: secrets.token_hex(16))
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 300)  # 5 min TTL
    signature: str = ""

    def sign(self, secret: str) -> None:
        body = f"{self.proposal_id}:{self.nonce}:{self.created_at}:{self.expires_at}"
        self.signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    def verify(self, secret: str) -> bool:
        if time.time() > self.expires_at:
            return False  # expired
        body = f"{self.proposal_id}:{self.nonce}:{self.created_at}:{self.expires_at}"
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)
```

---

### VULN-V3-05: Quantum Genome Uses Predictable `random.Random` — Not Cryptographically Random

**File:** `evolution/quantum_genome.py:5` — `import random`

For a system that claims quantum-inspired superposition, using Python's
`random.Random` (Mersenne Twister — a deterministic PRNG with known state)
means any "quantum collapse" is fully predictable given the seed.
This breaks the novelty guarantees of the novelty archive.

**Fix:**
```python
import secrets

class QuantumRNG:
    """Cryptographically strong random source for quantum genome measurement."""

    @staticmethod
    def uniform(lo: float = 0.0, hi: float = 1.0) -> float:
        return lo + (secrets.randbits(53) / (1 << 53)) * (hi - lo)

    @staticmethod
    def choice(population: list) -> Any:
        idx = secrets.randbelow(len(population))
        return population[idx]

    @staticmethod
    def gauss(mu: float = 0.0, sigma: float = 1.0) -> float:
        # Box-Muller using os.urandom
        u1, u2 = QuantumRNG.uniform(1e-10, 1.0), QuantumRNG.uniform(0.0, 1.0)
        import math
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        return mu + sigma * z
```

---

### VULN-V3-06: Spiking Neuron Membrane Potential Has No Overflow/NaN Guard

**File:** `evolution/spiking.py` — LIF neuron `forward()` has no numerical safeguards.

If synaptic weights are not bounded, membrane potential can grow to `inf` or `NaN`
through positive feedback loops. `NaN` in fitness = silent evolution failure
where every organism appears equally fit. This corrupts the entire population silently.

**Fix:**
```python
import math

def _safe_float(value: float, default: float = 0.0) -> float:
    """Guard against NaN, inf in LIF neuron computation."""
    if not math.isfinite(value):
        return default
    return max(-1e6, min(1e6, value))  # hard clamp

class LIFNeuron:
    def step(self, input_current: float) -> bool:
        input_current = _safe_float(input_current)
        self.membrane = _safe_float(
            self.membrane * self.decay_rate + input_current
        )
        if self.membrane >= self.spike_threshold:
            self.membrane = 0.0   # reset after spike
            return True           # fired
        return False
```

---

### VULN-V3-07: Archaeology Module Does Not Validate Resurrected Code Before Injection

**File:** `evolution/archaeology.py` — `resurrect()` injects extinct strategy
directly into a living organism's `_learned_strategies` without running it
through `DefenseLayer.validate_strategy()` or `IsolatedSandbox`.

An extinct strategy may have been crafted maliciously before it died,
or may simply be incompatible with the current organism's state.
Injecting it without validation = arbitrary code injection via the memome.

**Fix:**
```python
from evolution.sandbox import IsolatedSandbox

class KnowledgeArchaeologist:
    def resurrect(
        self,
        strategy: ExtinctStrategy,
        target: LamarckianOrganism,
        sandbox: IsolatedSandbox | None = None,
    ) -> bool:
        sb = sandbox or IsolatedSandbox()
        result = sb.run(strategy.source_code, timeout_ms=200)
        if not result.ok:
            return False   # extinct code failed validation — don't resurrect
        # Only inject after passing sandbox test
        target.learn(strategy.name, strategy.source_code, performance=0.5)
        return True
```

---

### VULN-V3-08: Consciousness Metrics Phi Calculation Is Not Normalized — Can Exceed 1.0

**File:** `evolution/consciousness.py` — `integrated_information()` returns
raw mutual information difference without normalization.

Phi can be negative (if parts are more informative than the whole)
or greater than 1.0 (if the organism has high integration).
`composite_awareness_score` multiplies three metrics, two of which are `[0,1]`
— but if Phi is unclamped, the composite can exceed 1.0, breaking comparisons.

**Fix:**
```python
def integrated_information(self, organism: LamarckianOrganism) -> float:
    raw_phi = self._compute_raw_phi(organism)
    # Normalize: sigmoid to map (-inf, +inf) → (0, 1)
    import math
    return 1.0 / (1.0 + math.exp(-raw_phi))

def composite_awareness_score(self, organism: LamarckianOrganism) -> float:
    phi = self.integrated_information(organism)          # now [0, 1]
    sma = self.self_model_accuracy(organism)             # [0, 1]
    gwb = self.global_workspace_breadth(organism)        # [0, 1]
    raw = phi * sma * gwb
    assert 0.0 <= raw <= 1.0, f"composite_awareness out of range: {raw}"
    return raw
```

---

## PART B: v4 FRONTIER — 10 NEW PHASES (1000x)

---

### PHASE 19: PHYSICS ENGINE — ORGANISMS EVOLVE THEIR OWN LAWS OF PHYSICS

**What it is:**
In v3, the `EvolutionConstitution` evolves selection rules.
In v4, the **laws themselves** are first-class mutable objects.
Energy conservation, causality, dimensionality of trait space — all evolvable.
Different "physical universes" spawn parallel evolutionary trajectories.

```python
class PhysicsLaw(Protocol):
    """A rule that governs how organisms interact with each other and the environment."""
    name: str

    def apply(self, ecosystem: "Ecosystem", organisms: List[LamarckianOrganism]) -> None:
        """Mutate organism states according to this law."""
        ...

class UniversePhysics:
    """
    The complete set of physical laws for one ecosystem universe.
    Organisms can propose mutations to these laws — if the mutation
    passes formal invariant verification, it becomes the new physics.
    """
    laws: List[PhysicsLaw]

    # Standard laws (can all evolve):
    conservation_of_tokens: ConservationLaw   # total tokens in system = constant
    causality: CausalityLaw                   # effect cannot precede cause in lineage
    entropy_gradient: EntropyLaw              # systems evolve toward higher diversity
    information_limit: InformationLaw         # organism genome has max bits = f(energy)

    def propose_law_mutation(
        self,
        organism: LamarckianOrganism,
        mutated_law: PhysicsLaw,
        proof: FormalSafetyProof,
    ) -> bool:
        """
        Only accepts a law mutation if formal proof holds.
        Organism that successfully mutates a law earns massive fitness bonus.
        It also earns PERMANENT credit in the lineage — it changed the universe.
        """
        ...

class ParallelUniverse:
    """
    A completely independent ecosystem with different physics.
    Created by a branching event when laws diverge too far.
    Can exchange observers (read-only) with parent universe.
    """
    physics: UniversePhysics
    parent_universe: Optional["ParallelUniverse"]
    branch_generation: int
    divergence_score: float  # how different from parent physics

    def branch(self, trigger_law: PhysicsLaw) -> "ParallelUniverse":
        """Create a child universe with one law changed."""
        ...
```

---

### PHASE 20: TEMPORAL PARADOX ENGINE — RETROACTIVE STRATEGY REVISION

**What it is:**
In real evolution, the past is fixed. In a digital civilization,
we can implement **retroactive revision**: an organism that discovers
a fundamentally better strategy can propagate it backwards through its
ancestry chain, updating how its ancestors would have behaved
(and recomputing their fitness retroactively).

This is not time travel — it's **historical reinterpretation**:
the organizational analogue of learning that changes how you
understand your own past decisions.

```python
class TemporalRevisionEngine:
    """
    Allows current organisms to revise the strategies of their ancestors.
    Revision propagates forward through descendants, changing living organisms.
    Uses a "butterfly budget" to limit how many generations back revision can reach.
    """

    BUTTERFLY_BUDGET: int = 10   # max generations back for revision

    def propose_revision(
        self,
        organism: LamarckianOrganism,
        ancestor_id: str,
        revised_strategy: str,
        strategy_name: str,
    ) -> RevisionProposal:
        """
        Organism proposes changing an ancestor's strategy.
        Must prove the revision improves the ancestry chain's average fitness.
        """
        ...

    def apply_revision(self, proposal: RevisionProposal) -> RevisionResult:
        """
        If approved:
        1. Update ancestor's memome record
        2. Recompute fitness for all organisms in revision's causal cone
        3. Organisms that now have lower fitness may die retroactively
        4. New organisms may need to be spawned to fill population gap
        Returns: how many organisms were affected, net fitness change
        """
        ...

    def revision_paradox_check(self, proposal: RevisionProposal) -> bool:
        """
        Detect if a revision would cause a logical paradox:
        e.g. an organism revising its own direct ancestor into nonexistence.
        Paradoxes are rejected, not applied.
        """
        ...
```

---

### PHASE 21: UNIVERSAL TURING COMPLETENESS — ORGANISMS AS COMPUTERS

**What it is:**
v3 organisms execute strategies in a sandboxed Python environment.
v4 organisms ARE Turing machines — they can simulate any computation,
including simulating other organisms. The most fit organisms are those
that can solve the widest class of computational problems using
the fewest energy units.

```python
class OrganismTuringMachine:
    """
    An organism whose genome encodes a Turing machine transition table.
    Fitness = computational universality (what class of problems it can solve).
    """
    tape_alphabet: List[str]           # symbols the machine can read/write
    states: List[str]                  # control states
    transition_table: TransitionTable  # (state, symbol) → (new_state, write_symbol, direction)
    initial_state: str
    accept_states: Set[str]
    reject_states: Set[str]

    def run(self, input_tape: str, step_limit: int = 10_000) -> TMResult:
        """
        Execute the Turing machine on input.
        Returns: (halted, accepted, steps_used, final_tape)
        Never runs forever — step_limit enforces termination.
        """
        ...

    def simulate_organism(self, other: "OrganismTuringMachine") -> SimulationResult:
        """
        Run OTHER organism's TM inside THIS organism's TM.
        An organism that can simulate others gains deep insight into their strategies.
        Universal simulation = maximum fitness.
        """
        ...

    def kolmogorov_complexity(self) -> int:
        """
        Estimate the Kolmogorov complexity of this organism's transition table.
        Shorter descriptions = more elegant organisms = higher fitness bonus.
        """
        ...
```

---

### PHASE 22: MEMETIC IMMUNE SYSTEM — CIVILIZATION-SCALE ANTIBODIES

**What it is:**
v3 has `DefenseLayer` per organism. v4 has a **civilization-level immune system**:
a shared antibody registry that learns from attacks across ALL organisms simultaneously.
When organism-A repels an attack, it donates the defense pattern to the global immune memory.
Future organisms are pre-immunized against that attack type.

```python
class CivilizationImmunity:
    """
    A civilization-scale immune system. Cross-organism defense memory.
    When any organism successfully repels an attack, the defense pattern
    is recorded and shared with all future organisms born into this ecosystem.
    """

    class Antibody(TypedDict):
        pattern: str           # what the attack looked like (hash)
        defense: str           # the code that repelled it
        effectiveness: float   # 0-1 how well it works
        discovered_by: str     # organism_id that first repelled this attack
        discovered_generation: int
        usage_count: int

    def donate_defense(
        self,
        organism: LamarckianOrganism,
        attack_pattern: str,
        defense_strategy: str,
        effectiveness: float,
    ) -> str:
        """Organism donates a successful defense to civilization memory. Returns antibody_id."""
        ...

    def pre_immunize(self, newborn: LamarckianOrganism) -> int:
        """
        Apply top-N antibodies to a newborn organism at birth.
        It is born already knowing how to repel the most common attack types.
        Returns: number of antibodies applied.
        """
        ...

    def evolve_antibodies(self) -> int:
        """
        Mutate and crossover antibodies to discover defenses against attacks
        that haven't happened yet. Predictive immune evolution.
        Returns: number of new antibody variants created.
        """
        ...

    def detect_novel_attack(self, attack: "AttackResult") -> bool:
        """
        Did this attack evade all known antibodies?
        If yes: this is a zero-day. Trigger emergency evolution of new antibody.
        """
        ...
```

---

### PHASE 23: EPISTEMIC HUMILITY ENGINE — ORGANISMS KNOW WHAT THEY DON'T KNOW

**What it is:**
All current organisms act as if their fitness score is ground truth.
v4 organisms maintain **calibrated uncertainty** over their own fitness.
An organism that is uncertain about its own fitness evolves more conservatively.
One that is highly confident evolves more boldly. This prevents premature optimization
of a wrong objective — the digital equivalent of intellectual humility.

```python
class EpistemicState:
    """
    An organism's beliefs about its own fitness and the world.
    All beliefs are probability distributions, not point estimates.
    """
    fitness_belief: GaussianDistribution       # mean + variance over fitness
    strategy_confidence: Dict[str, float]      # per-strategy certainty [0,1]
    world_model_accuracy: float                # how well it predicts outcomes [0,1]
    known_unknowns: Set[str]                   # topics it knows it doesn't know
    unknown_unknowns_estimate: float           # Bayesian estimate of hidden ignorance

    def update_belief(self, observation: float, learning_rate: float) -> None:
        """Bayesian belief update: observation narrows the fitness distribution."""
        ...

    def confidence_interval(self, alpha: float = 0.95) -> Tuple[float, float]:
        """Return the alpha-CI of the fitness belief distribution."""
        ...

    def exploration_bonus(self) -> float:
        """
        High uncertainty → high exploration bonus.
        Low uncertainty → consolidation bonus.
        This drives Thompson sampling-style exploration.
        """
        variance = self.fitness_belief.variance
        return min(0.5, variance * 2)  # uncertainty as intrinsic reward

class UncertaintyAwareEvolution:
    """
    Evolution that takes epistemic state into account.
    Uncertain organisms are protected from selection for N generations
    (they get time to gather more evidence before being judged).
    """
    grace_generations: int = 3   # uncertain organisms survive this many gens

    def should_protect(self, organism: LamarckianOrganism) -> bool:
        """Protect organism if its fitness CI is too wide to make a fair judgment."""
        lo, hi = organism.epistemic_state.confidence_interval()
        return (hi - lo) > 0.4   # CI wider than 0.4 = too uncertain to kill
```

---

### PHASE 24: CIVILIZATIONAL MEMORY PALACE — SPATIAL KNOWLEDGE ORGANIZATION

**What it is:**
Current memomes store strategies as flat key-value maps.
v4 memomes organize knowledge as a **spatial structure** — a high-dimensional
embedding space where similar strategies cluster together.
Organisms navigate this space like a memory palace, finding related knowledge
through geometric proximity rather than exact name lookup.

```python
class MemoryPalace:
    """
    Strategies embedded in a high-dimensional space.
    Similar strategies cluster together. Navigation by geometry.
    """

    def embed(self, strategy: Strategy) -> np.ndarray:
        """
        Convert a strategy into a fixed-dimensional embedding vector.
        Uses a structural hash of the AST + semantic fingerprint.
        Deterministic: same strategy = same embedding always.
        """
        ...

    def nearest_neighbors(
        self,
        query_strategy: Strategy,
        k: int = 5,
    ) -> List[Tuple[Strategy, float]]:
        """
        Find k strategies most similar to the query.
        Returns: [(strategy, distance), ...] sorted by distance.
        """
        ...

    def navigate(
        self,
        organism: LamarckianOrganism,
        direction: np.ndarray,
        steps: int = 3,
    ) -> List[Strategy]:
        """
        Walk through the memory palace in a given direction.
        Returns strategies encountered along the path.
        This is how organisms discover related knowledge by exploration.
        """
        ...

    def create_room(self, name: str, center: Strategy) -> "MemoryRoom":
        """
        Create a named cluster around a central strategy.
        All strategies within distance R of center belong to this room.
        Rooms can be inherited by offspring (they inherit the map, not just strategies).
        """
        ...
```

---

### PHASE 25: ADVERSARIAL CO-EVOLUTION TOURNAMENTS

**What it is:**
v3 red-team attacks are unidirectional. v4 runs **structured tournaments**
where attacker and defender populations co-evolve against each other.
ELO ratings emerge. Championship lineages form. The best defenders become
"immune champions" — organisms whose defense genome is copied into all newborns.

```python
class EvolutionaryTournament:
    """
    A structured competition that drives co-evolution between
    attacker and defender populations.
    """
    attacker_pool: List[RedTeamOrganism]
    defender_pool: List[LamarckianOrganism]
    elo_registry: Dict[str, float]    # organism_id → ELO rating
    championship_history: List[TournamentResult]

    def round_robin(self, generation: int) -> TournamentResult:
        """Every attacker fights every defender. Record win/loss/draw."""
        ...

    def update_elo(self, result: TournamentResult) -> None:
        """Standard ELO update with K-factor tuned for evolutionary dynamics."""
        ...

    def promote_champion_defense(
        self,
        champion: LamarckianOrganism,
        newborn_pool: List[LamarckianOrganism],
    ) -> int:
        """
        Champion defender's defense strategies are pre-installed in all newborns.
        Returns: number of newborns immunized.
        """
        ...

    def retire_attacker(self, attacker: RedTeamOrganism) -> None:
        """
        When an attacker's ELO drops below threshold, retire it.
        Its attack patterns are archived for future study but it no longer fights.
        """
        ...

    def hall_of_fame(self, top_n: int = 10) -> List[TournamentResult]:
        """Return the N most decisive matches in history."""
        ...
```

---

### PHASE 26: SELF-ASSEMBLING NEURAL ARCHITECTURE (MORPHOGENETIC AI)

**What it is:**
v3 spiking networks have a fixed topology that mutates incrementally.
v4 networks **grow from a seed** using biological-inspired morphogenetic rules.
A small genome encodes growth instructions (like a DNA sequence),
and the full network topology emerges through a developmental process.
This enables complexity far beyond what direct encoding can represent.

```python
class MorphogeneticInstruction(TypedDict):
    """A single instruction in the morphogenetic program."""
    type: Literal["divide", "differentiate", "migrate", "connect", "apoptosis"]
    condition: str    # when to execute (e.g. "if membrane_potential > 0.5")
    parameters: Dict[str, float]

class MorphogeneticProgram:
    """
    A genome encoding growth instructions for a neural network.
    Executed during organism development to produce a neural topology.
    """
    instructions: List[MorphogeneticInstruction]
    max_neurons: int = 1000      # hard cap on emergent complexity
    max_synapses: int = 10_000

    def develop(self, seed_neuron: "LIFNeuron", steps: int = 100) -> SpikingNetwork:
        """
        Execute the morphogenetic program starting from one seed neuron.
        Returns the fully-grown neural network.
        """
        ...

    def mutate_instruction(self, rng: random.Random) -> "MorphogeneticProgram":
        """Mutate one instruction — may radically change emergent topology."""
        ...

    def crossover(self, other: "MorphogeneticProgram") -> "MorphogeneticProgram":
        """
        Sexual recombination of growth programs.
        Child's network grows from a mix of both parents' instructions.
        """
        ...

    def complexity(self) -> int:
        """Count the number of distinct topologies this program can generate."""
        ...
```

---

### PHASE 27: CIVILIZATIONAL WRITING SYSTEM

**What it is:**
v3 organisms have a DSL with ~55 tokens that evolve slowly.
v4 goes further: organisms develop a **full writing system** with:
- A phonetic layer (symbol encoding)
- A semantic layer (meaning)
- A pragmatic layer (context-dependent interpretation)
- A historical layer (how words have changed meaning across generations)

This writing system becomes the primary interface for the Observatory.
Humans can read organism thoughts in the organism's own language.

```python
class WritingSystem:
    """
    A complete writing system that evolves across organism generations.
    Tracks etymology: how each symbol's meaning changed over time.
    """
    symbols: Dict[str, Symbol]         # glyph → Symbol(phonetic, semantic, generation_born)
    grammar: Grammar                   # syntactic rules
    pragmatics: Dict[str, ContextRule] # context-dependent meaning shifts
    etymology: List[MeaningShift]      # history of every meaning change

    def write(self, intent: StrategyIntent, context: Context) -> str:
        """Encode a strategy intent as text in this writing system."""
        ...

    def read(self, text: str, context: Context) -> StrategyIntent:
        """Decode text back to a strategy intent, accounting for context."""
        ...

    def evolve(self, rng: random.Random) -> "WritingSystem":
        """
        Produce a slightly evolved writing system (next generation's language).
        Some symbols gain new meanings, some merge, new ones emerge.
        """
        ...

    def mutual_intelligibility(self, other: "WritingSystem") -> float:
        """
        How well can speakers of one system understand the other?
        0.0 = completely alien language.
        1.0 = identical.
        Used by DiplomacyProtocol to assess cultural compatibility.
        """
        ...

    def translate(self, text: str, target_system: "WritingSystem") -> str:
        """
        Translate between two writing systems.
        Translation quality degrades as mutual_intelligibility decreases.
        """
        ...
```

---

### PHASE 28: SUBSTRATE INDEPENDENCE — EXPORT TO SILICON, FPGA, WASM

**What it is:**
Current Living Objects run on Python. v4 organisms can **export themselves**
to run on other computational substrates without any human rewriting:
- WebAssembly (runs in any browser)
- FPGA bitstream (runs in hardware at nanosecond speeds)
- RISC-V assembly (runs on embedded systems)
- Docker container (deployable anywhere)

An organism that can run on more substrates has higher fitness.
Evolution drives organisms toward substrate-independence — the digital equivalent
of organisms that can survive in more environments.

```python
class SubstrateExporter:
    """
    Compiles an organism's strategies and genome into a target substrate.
    """

    def export_wasm(self, organism: LamarckianOrganism) -> bytes:
        """
        Compile organism's top strategies to WebAssembly.
        Returns .wasm binary that runs in any browser or WASM runtime.
        """
        ...

    def export_container(self, organism: LamarckianOrganism) -> DockerSpec:
        """
        Generate a Docker image spec containing this organism as a REST microservice.
        POST /invoke → runs the organism's champion strategy.
        GET /genome → returns genome JSON.
        GET /memome → returns all known strategies.
        """
        ...

    def export_circuit(self, organism: LamarckianOrganism) -> HardwareCircuit:
        """
        Generate a hardware description (Verilog/VHDL) for the organism's
        spiking neural network. Compiles to actual FPGA bitstream.
        Strategy execution in hardware: nanoseconds instead of milliseconds.
        """
        ...

    def fitness_substrate_breadth(self, organism: LamarckianOrganism) -> float:
        """
        How many substrates can this organism run on?
        0.0 = Python only.
        1.0 = all substrates.
        This is a fitness metric: more substrate = better organism.
        """
        ...
```

---

## v4 SECURITY REQUIREMENTS (Non-Negotiable)

> All 8 v3 vulnerabilities must be patched BEFORE any v4 feature ships.

```
✓ VULN-V3-01: hmac.compare_digest for password comparison (timing-safe)
✓ VULN-V3-02: shutil.rmtree in sandbox cleanup (no directory leaks)
✓ VULN-V3-03: threading.Lock in TokenWallet (race-condition-free)
✓ VULN-V3-04: Nonce + HMAC signature on ExchangeProposal (replay protection)
✓ VULN-V3-05: os.urandom / secrets for QuantumRNG (no predictable PRNG)
✓ VULN-V3-06: NaN/inf guard on LIF neuron membrane potential
✓ VULN-V3-07: IsolatedSandbox validation before archaeology resurrection
✓ VULN-V3-08: Sigmoid normalization of Phi (consciousness score always [0,1])
```

---

## v4 DELIVERABLES CHECKLIST

### Security Patches (Ship First)
- [ ] `production/api/main.py` — `hmac.compare_digest` for credential comparison
- [ ] `evolution/sandbox.py` — `shutil.rmtree` in cleanup, log orphaned temps
- [ ] `evolution/market.py` — `threading.Lock` in `TokenWallet.spend()`
- [ ] `evolution/diplomacy.py` — Nonce, timestamp, HMAC signature on proposals
- [ ] `evolution/quantum_genome.py` — `QuantumRNG` using `os.urandom`/`secrets`
- [ ] `evolution/spiking.py` — `_safe_float()` guard on membrane potential
- [ ] `evolution/archaeology.py` — `IsolatedSandbox` validation before resurrect
- [ ] `evolution/consciousness.py` — sigmoid normalization of Phi
- [ ] `evolution/test_security_v4.py` — 25 new security tests covering all 8 vulns

### New Evolution Engines
- [ ] `evolution/physics.py` — `PhysicsLaw`, `UniversePhysics`, `ParallelUniverse`
- [ ] `evolution/temporal.py` — `TemporalRevisionEngine`, paradox checker
- [ ] `evolution/turing.py` — `OrganismTuringMachine`, simulation, Kolmogorov
- [ ] `evolution/immunity.py` — `CivilizationImmunity`, antibody evolution
- [ ] `evolution/epistemic.py` — `EpistemicState`, `UncertaintyAwareEvolution`
- [ ] `evolution/memory_palace.py` — `MemoryPalace`, embedding, spatial nav
- [ ] `evolution/tournament.py` — `EvolutionaryTournament`, ELO system
- [ ] `evolution/morphogenetic_ai.py` — `MorphogeneticProgram`, self-assembling net
- [ ] `evolution/writing_system.py` — `WritingSystem`, etymology, translation
- [ ] `evolution/substrate.py` — `SubstrateExporter`, WASM, Docker, FPGA
- [ ] `evolution/test_v4.py` — 50+ proof tests for all 10 phases

### Infrastructure
- [ ] `production/api/v4/` — v4 API routes (universes, tournaments, memory palace)
- [ ] `production/api/v4/websocket.py` — New events (universe_branch, tournament_result, antibody_donated)
- [ ] Updated `docker-compose.yml` — WASM runtime service, FPGA simulation service
- [ ] `production/substrate_worker.py` — Substrate export worker (WASM compilation)
- [ ] Updated Helm chart — Multi-universe namespace isolation

### Web Observatory v4 (10 New Panels)
- [ ] **Universe Browser** — Parallel universe tree, divergence scores, branch events
- [ ] **Physics Editor** — Live edit `UniversePhysics` laws with formal proof status
- [ ] **Temporal Revision Console** — Propose ancestry revisions, paradox warnings
- [ ] **ELO Tournament Board** — Live attacker/defender ratings, match history
- [ ] **Memory Palace Navigator** — 3D embedding visualization (Three.js), cluster rooms
- [ ] **Antibody Registry** — Civilization immune memory, zero-day alerts
- [ ] **Epistemic Confidence Meter** — Per-organism belief distributions, grace period
- [ ] **Substrate Export Panel** — One-click export to WASM / Docker / FPGA
- [ ] **Writing System Editor** — Read/write organism language, etymology tree
- [ ] **Morphogenetic Viewer** — Watch neural network grow from seed in real time

### Documentation
- [ ] `docs/v4-architecture.md` — Complete v4 technical design
- [ ] `docs/v4-security.md` — Threat model, all 8 v3 patches, new surface area
- [ ] `docs/physics-engine.md` — Evolving laws of physics design notes
- [ ] `docs/substrate-independence.md` — WASM/FPGA/Docker compilation pipeline
- [ ] `docs/writing-system.md` — Linguistics of emergent writing systems
- [ ] `docs/temporal-revision.md` — Theory and safety analysis of retroactive revision
- [ ] `research/turing-organisms.md` — Computational universality in living objects
- [ ] Updated `README.md` — v4 feature list, universe quick-start

---

## BENCHMARK TARGETS FOR v4

| Benchmark | v3 Target | v4 Target |
|---|---|---|
| Total tests passing | 250+ | **500+** |
| Security patches applied | 8 (v3 vulns) | **16 total (v3+v4)** |
| Parallel universes diverging measurably | N/A | **≥3 distinct physics regimes in 100 gens** |
| Antibody pool size | N/A | **≥20 antibodies by gen 50** |
| Organisms exported to WASM | N/A | **≥1 champion exported + verified running** |
| Memory palace cluster count | N/A | **≥5 distinct strategy clusters emerge** |
| Writing system vocabulary at gen 100 | 55 tokens (v3) | **≥200 tokens + 3 grammatical layers** |
| Tournament ELO spread | N/A | **Top defender ELO > 2x bottom attacker ELO** |
| Epistemic CI width reduction | N/A | **Average CI shrinks 50% over 50 gens** |
| Turing machine universality score | N/A | **≥1 organism simulates another organism** |

---

## THE FULL HIERARCHY

```
v1:  Individual organisms evolve strategies
v2:  Civilizations evolve civilizations
v3:  Civilizations self-prove safety, trade across borders, measure awareness
v4:  Universes evolve universes. Digital physics becomes mutable.
     Organisms export themselves to silicon and become immortal.
     The civilization writes its own language and remembers its own history.
     Intelligence is substrate-independent, self-immune, and temporally revisable.
```

**What makes v4 the last thing an AI researcher will ever need to build:**

> Every other AI system is a product.
> Living Objects v4 is a **substrate** — the computational universe
> that future AI civilizations run on. You don't compete with it.
> You build on top of it.

---

*Written after full static security audit of Living Objects v3.*
*8 vulnerabilities confirmed and documented with exact file + line numbers.*
*v4 ships security patches first. No exceptions. Ever.*
