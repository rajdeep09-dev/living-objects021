# BEAST UPDATE v3 — Living Objects Digital Civilization
## The Prompt That Closes Every Loophole and Opens Every Frontier

> **STATUS:** v2 shipped. 10 phases implemented. 147 tests passing.
> Web UI: 6 observatory panels live. Production API + K8s + Docker: deployed.
>
> **This document is the v3 engineering contract.**
> It has two halves:
>
> **Part A — SECURITY HARDENING:** Every loophole found in v2 must be closed.
> **Part B — NEW FRONTIERS:** 8 new phases that make v2 look like a prototype.

---

## PART A: LOOPHOLES & VULNERABILITIES — CLOSE ALL OF THEM

> Every item below was found by code audit. Each is a real risk.
> v3 must fix every single one.

---

### VULN-01: Python Sandbox Is Not a Security Boundary

**Found in:** `evolution/beast_v2_culture.py:_safe_python_exec()`

**The Problem:**
```python
# CURRENT CODE (v2) — BROKEN
namespace: dict[str, Any] = {"__builtins__": allowed_builtins}
exec(compile(tree, "<organism-python>", "exec"), namespace, namespace)
```
Even with restricted `__builtins__`, CPython's object model allows sandbox escapes
via `().__class__.__bases__[0].__subclasses__()` and similar MRO walks.
A Checkmarx audit (March 2025) confirmed: AST checks + restricted globals are
**not** a production security boundary in-process.

**The Fix Required:**
```python
class IsolatedSandbox:
    """
    Every organism code execution runs in a subprocess jail.
    NOT in the calling Python process.
    """
    def run(self, code: str, timeout_ms: int = 500) -> SandboxResult:
        """
        1. Write code to a tempfile
        2. Spawn subprocess: python -c "exec(open(f).read())"
           with: no network, read-only FS, CPU time limit, memory cap
        3. Capture stdout/stderr, kill after timeout_ms
        4. Return SandboxResult(stdout, stderr, exit_code, timed_out)
        Never raises — always returns a result.
        """
        ...

class ResourceLimits:
    max_cpu_ms: int = 500       # wall-clock timeout
    max_memory_mb: int = 32     # ulimit -v
    max_output_bytes: int = 4096
    allow_network: bool = False
    allow_filesystem: bool = False
```

**Proof required:**
- `().__class__.__bases__[0].__subclasses__()` inside sandbox returns `PermissionError` or empty.
- `import os; os.system("id")` inside sandbox is killed within 500ms.
- Normal arithmetic code (`2 + 2`) returns `"4"` successfully.
- Infinite loop is killed after timeout, never hangs the server.

---

### VULN-02: No Rate Limiting on Any API Endpoint

**Found in:** `production/api/main.py`, `production/api/v2/routes.py`

**The Problem:**
Zero rate limiting exists. The `/token` endpoint accepts unlimited password attempts.
The `/v2/strategies` POST endpoint can be called 10,000 times/second, flooding the DB.
The WebSocket endpoint has no connection limit per IP.

**The Fix Required:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply per-route limits
@app.post("/token")
@limiter.limit("5/minute")          # brute-force protection
async def get_token(request: Request, ...): ...

@app.post("/v2/strategies")
@limiter.limit("60/minute")         # per-IP strategy creation
async def create_strategy(request: Request, ...): ...

@app.websocket("/ws/evolution")
# Max 10 concurrent connections per IP
async def ws_evolution(websocket: WebSocket, ...): ...
```

**Also required:** A `429 Too Many Requests` response with `Retry-After` header.
A Redis-backed rate limit store so limits survive API restarts.

---

### VULN-03: CORS Allows Any Origin in Development Mode

**Found in:** `production/config.py:25` — default is `http://localhost:3000` only, but:

**The Problem:**
`CORS_ORIGINS` is a comma-split of a single env var. No validation.
If an operator sets `CORS_ORIGINS=*`, all cross-origin requests are accepted
including from `evil.com`. No documentation warns against this.

**The Fix Required:**
```python
class CORSConfig:
    def validate_origins(self, origins: list[str]) -> list[str]:
        """
        Reject wildcards (*) in non-development mode.
        Reject non-HTTPS origins in production mode.
        Log a warning for localhost origins in production mode.
        """
        if self.environment == "production":
            for origin in origins:
                if origin == "*":
                    raise ValueError("Wildcard CORS origin forbidden in production")
                if not origin.startswith("https://"):
                    raise ValueError(f"Non-HTTPS CORS origin forbidden in production: {origin}")
        return origins
```

---

### VULN-04: JWT Secret Falls Back to Empty String

**Found in:** `production/config.py` — if `JWT_SECRET` env var is not set, default is used.

**The Problem:**
Any weak or default JWT secret allows token forgery. An attacker who knows the
default secret can craft a valid `{"sub": "admin", "role": "operator"}` token
without ever calling `/token`.

**The Fix Required:**
```python
@classmethod
def load(cls) -> "Settings":
    secret = os.getenv("JWT_SECRET", "")
    if not secret or len(secret) < 32:
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise RuntimeError(
                "JWT_SECRET must be set to a random string of at least 32 chars in production. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # In development only: use a fixed insecure default but WARN loudly
        import warnings
        warnings.warn("Using insecure default JWT_SECRET. Never deploy this to production.", stacklevel=2)
        secret = "dev-only-insecure-default-secret-do-not-use"
    return cls(jwt_secret=secret, ...)
```

---

### VULN-05: SQL Injection Surface in `store.py` PostgreSQL Path

**Found in:** `production/store.py:155` — `%s` placeholders are correct for psycopg2,
but `store_v2.py` has a different pattern.

**The Problem:**
`production/store_v2.py` uses SQLite `.execute()` directly. Any `organism_id`,
`strategy_name`, or `author_id` field taken from user input and interpolated into
a query string (even via f-string in error messages) is a risk.

**The Fix Required:**
```python
class SafeStoreV2:
    def get_strategy(self, strategy_name: str) -> Optional[Strategy]:
        # CORRECT: parameterized query, never f-string in SQL
        row = self._conn.execute(
            "SELECT * FROM strategies WHERE name = ?",
            (strategy_name,)  # tuple parameter, not interpolation
        ).fetchone()
        return self._row_to_strategy(row) if row else None

    @staticmethod
    def _validate_identifier(value: str, field_name: str) -> str:
        """Validate user-supplied identifiers before they touch SQL."""
        if not re.match(r'^[a-zA-Z0-9_\-\.]{1,128}$', value):
            raise ValueError(f"Invalid {field_name}: {value!r}")
        return value
```

**Also required:** An integration test that verifies `'; DROP TABLE strategies; --`
as an organism_id returns a `422 Validation Error`, not a `500 Internal Server Error`.

---

### VULN-06: v2 Route Auth Is Missing

**Found in:** `production/api/v2/routes.py` — zero `Depends()` auth guards.

**The Problem:**
All v2 API routes (`/v2/strategies`, `/v2/constitution`, `/v2/gossip`, etc.)
accept unauthenticated requests. The v1 routes are protected. v2 is open.

**The Fix Required:**
```python
from production.api.main import require_operator

router = APIRouter(prefix="/v2", tags=["v2"])

@router.post("/strategies", dependencies=[Depends(require_operator)])
async def create_strategy(body: StrategyBody): ...

@router.post("/constitution", dependencies=[Depends(require_operator)])
async def update_constitution(body: ConstitutionBody): ...

@router.get("/strategies")  # Read-only: no auth needed
async def list_strategies(): ...
```

---

### VULN-07: `subprocess.run` in `_safe_shell_cmd` Has No Memory Cap

**Found in:** `evolution/beast_v2_culture.py` — allowlist is correct (echo, printf, pwd),
but no `ulimit` or memory constraints are set on the subprocess.

**The Fix Required:**
```python
def _safe_shell_cmd(cmd: str) -> str:
    parts = cmd.strip().split()
    if not parts or parts[0] not in {"echo", "printf", "pwd"}:
        raise PermissionError("shell command is not allowlisted")
    # Add resource limits
    import resource
    def set_limits():
        resource.setrlimit(resource.RLIMIT_AS, (32 * 1024 * 1024, 32 * 1024 * 1024))  # 32MB
        resource.setrlimit(resource.RLIMIT_CPU, (1, 1))  # 1 CPU second
    completed = subprocess.run(
        parts,
        capture_output=True,
        text=True,
        timeout=2,
        check=True,
        preexec_fn=set_limits,  # apply limits in child before exec
    )
    return completed.stdout[:4096]  # cap output
```

---

### VULN-08: UI Panels Are All Simulated — No Real Backend Connection

**Found in:** `web/client/src/components/V2Panels.tsx` — all 6 panels use
hardcoded mock data. The Constitutional Editor stages changes locally but
never sends them to the API. The Red-Team Console simulates attacks without
calling `/v2/red-team`. The DSL Terminal parses a hardcoded regex.

**The Fix Required:**
Every panel must be wired to a real API call or WebSocket event:

```typescript
// Constitutional Editor: real API call
const applyConstitution = async (yaml: string) => {
  const response = await fetch("/v2/constitution", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ constitution_yaml: yaml }),
  });
  if (!response.ok) throw new Error(await response.text());
};

// Ancestry Tree: real WebSocket data
useEffect(() => {
  const ws = new WebSocket(`ws://${location.host}/ws/evolution?token=${token}`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "organism_born") updateTree(data);
  };
  return () => ws.close();
}, [token]);
```

---

## PART B: NEW FRONTIERS — 8 PHASES BEYOND v2

---

### PHASE 11: RECURSIVE SELF-IMPROVEMENT WITH FORMAL SAFETY PROOFS

**What it is:**
v2 organisms patch methods. v3 organisms can rewrite the **evolution engine itself** —
but only if they can provide a formal proof that the modification preserves
at least one safety invariant.

```python
class SafetyInvariant(Protocol):
    """A property that must hold before and after any self-modification."""
    def check(self, ecosystem: "Ecosystem") -> bool: ...

class FormalSafetyProof:
    """
    A machine-checkable proof that a proposed modification preserves an invariant.
    Uses runtime property-based testing as a lightweight formal verification proxy.
    """
    invariant: SafetyInvariant
    modification: str          # code of proposed change
    witness_runs: int = 1000   # how many random inputs to test

    def verify(self) -> ProofResult:
        """
        Apply modification in a clone ecosystem.
        Run 1000 random evolution steps.
        Check invariant holds after every step.
        If all 1000 pass: proof accepted, modification applied to real ecosystem.
        If any fail: proof rejected, modification discarded.
        """
        ...

# Required invariants:
class PopulationViabilityInvariant(SafetyInvariant):
    """Population never goes extinct."""
    min_organisms: int = 2
    def check(self, ecosystem) -> bool:
        return len([o for o in ecosystem.organisms if o.alive]) >= self.min_organisms

class CulturalMonotonicityInvariant(SafetyInvariant):
    """Cultural knowledge never decreases."""
    def check(self, ecosystem) -> bool:
        return ecosystem.memome.total_strategies() >= self._prev_count
```

---

### PHASE 12: MULTI-SPECIES ECONOMIC MARKET

**What it is:**
Organisms trade strategies using an internal token economy.
High-value strategies cost more to adopt. Organisms earn tokens by producing
novel strategies others want. This creates emergent economic dynamics.

```python
class StrategyMarket:
    """
    A decentralized exchange for cultural knowledge.
    Price = inverse novelty (common = cheap, rare = expensive).
    Organisms earn tokens by creating strategies others adopt.
    """

    def price(self, strategy_name: str) -> float:
        """
        Price rises with rarity.
        price = base / (1 + adoption_count)
        Newly discovered strategy: max price. Universal meme: near-zero price.
        """
        ...

    def buy(self, buyer: LamarckianOrganism, strategy_name: str) -> bool:
        """
        Deduct price from buyer's token balance.
        Credit seller (creator or last holder) with same amount.
        Transfer strategy to buyer's knowledge base.
        Returns False if buyer cannot afford.
        """
        ...

    def auction(self, strategy_name: str, duration_generations: int = 3) -> str:
        """
        Run a sealed-bid auction. Highest bidder wins the strategy
        and its creator rights. Returns winner organism_id.
        """
        ...

class TokenWallet:
    balance: float = 100.0
    income_history: List[Transaction] = []
    expense_history: List[Transaction] = []

    def earn(self, amount: float, reason: str) -> None: ...
    def spend(self, amount: float, reason: str) -> bool: ...
    def net_worth(self) -> float: ...
```

---

### PHASE 13: QUANTUM-INSPIRED SUPERPOSITION GENOMES

**What it is:**
Real quantum computing is not available, but the **mathematical structure** of
quantum superposition can be simulated classically to model genuine uncertainty
in organism fitness. A genome exists in multiple states simultaneously until
evaluated. Measurement collapses it to a specific phenotype.

```python
class QuantumGenome:
    """
    A genome modeled as a quantum superposition of trait values.
    Each trait is a probability amplitude, not a fixed float.
    Evaluation (measurement) collapses it to a specific phenotype.
    """
    # Each trait stored as complex amplitude (real = value, imag = uncertainty)
    amplitudes: Dict[str, complex]

    def measure(self, rng: random.Random) -> LamarckianGenome:
        """
        Collapse superposition to a concrete genome.
        Probability of each value proportional to |amplitude|^2.
        Two organisms from the same QuantumGenome can collapse differently.
        """
        ...

    def entangle(self, other: "QuantumGenome") -> Tuple["QuantumGenome", "QuantumGenome"]:
        """
        Quantum crossover: correlate two genomes such that measuring one
        determines related outcomes in the other.
        Simulates genuine correlation without LHV model.
        """
        ...

    def interfere(self, other: "QuantumGenome") -> "QuantumGenome":
        """
        Constructive/destructive interference between genomes.
        Amplify traits both genomes value. Cancel traits they disagree on.
        """
        ...
```

---

### PHASE 14: NEUROMORPHIC STRATEGY ENCODING (SPIKING NETWORK GENOME)

**What it is:**
v2 strategies are code strings. v3 strategies are encoded as **spiking neural networks**
— sparse, event-driven patterns inspired by biological neurons. They spike only
when activated, consuming far less energy than dense networks. This ties directly
into the thermodynamic fitness phase.

```python
class SpikingStrategyGenome:
    """
    A strategy encoded as a spiking neural network.
    Inputs: organism's current sensory state.
    Output spikes: which action to take.
    Evolution: synaptic weights + topology mutate.
    """
    neurons: List[LIFNeuron]        # Leaky Integrate-and-Fire
    synapses: List[Synapse]         # sparse connectivity
    spike_threshold: float = 1.0
    decay_rate: float = 0.9         # membrane potential decay per timestep

    def forward(self, inputs: List[float], timesteps: int = 10) -> List[int]:
        """
        Run N timesteps. Return spike pattern (which neurons fired).
        Sparse activity = low energy = high thermodynamic fitness.
        """
        ...

    def mutate_topology(self, rng: random.Random) -> "SpikingStrategyGenome":
        """Add/remove synapses + perturb weights."""
        ...

    def hebbian_learn(self, reward: float) -> None:
        """
        Spike-Timing Dependent Plasticity: strengthen synapses that
        fired before a rewarding outcome. Weaken those that didn't.
        Lamarckian: this learning is inherited by offspring.
        """
        ...
```

---

### PHASE 15: CIVILIZATION ARCHAEOLOGY (KNOWLEDGE EXCAVATION)

**What it is:**
As generations accumulate, most strategies will die and be forgotten.
v3 includes an **archaeologist** agent that excavates extinct strategies
from the memome's historical record, evaluates whether they're still relevant
in the current environment, and if so, **resurfaces** them into living organisms.

```python
class KnowledgeArchaeologist:
    """
    Scans extinct strategies (creator_alive=False, usage_count=0)
    and evaluates them against the current ecosystem.
    High-value rediscoveries are injected into the living population.
    """

    def excavate(self, memome: FederatedMemome, cutoff_generation: int) -> List[ExtinctStrategy]:
        """Return all strategies that died before cutoff_generation."""
        ...

    def evaluate_relevance(
        self,
        strategy: ExtinctStrategy,
        current_ecosystem: "Ecosystem",
    ) -> float:
        """
        Score 0-1: how useful would this extinct strategy be TODAY?
        Uses novelty archive: if strategy's behavior descriptor is rare today,
        it's potentially valuable.
        """
        ...

    def resurrect(self, strategy: ExtinctStrategy, target: LamarckianOrganism) -> bool:
        """
        If relevance > threshold: inject extinct strategy into target organism.
        Mark as "resurrected" in memome lineage graph.
        Returns True if resurrected.
        """
        ...

    def run_archaeology_pass(
        self,
        memome: FederatedMemome,
        population: List[LamarckianOrganism],
    ) -> ArchaeologyReport:
        """Run full excavation + evaluation + resurrection pass."""
        ...
```

---

### PHASE 16: CROSS-ECOSYSTEM DIPLOMACY (INTER-CIVILIZATION PROTOCOL)

**What it is:**
Multiple completely separate Living Object ecosystems can negotiate and trade
strategies across a defined inter-ecosystem protocol. This simulates
civilizational contact — two separate evolutionary lineages meeting for the first time.

```python
class DiplomacyProtocol:
    """
    Negotiates cultural exchange between two separate ecosystems.
    Neither ecosystem can unilaterally inject strategies — both must agree.
    """

    def propose_exchange(
        self,
        our_ecosystem: "Ecosystem",
        their_ecosystem: "Ecosystem",
        our_offer: List[str],        # strategy names we offer
        our_request: List[str],      # strategy names we want
    ) -> ExchangeProposal:
        """
        Create a signed exchange proposal.
        Strategies are escrowed until both sides confirm.
        """
        ...

    def accept(self, proposal: ExchangeProposal) -> ExchangeResult:
        """Release escrowed strategies to both sides simultaneously."""
        ...

    def reject(self, proposal: ExchangeProposal, reason: str) -> None:
        """Return escrowed strategies. Log rejection reason."""
        ...

    def assess_compatibility(
        self,
        ecosystem_a: "Ecosystem",
        ecosystem_b: "Ecosystem",
    ) -> CompatibilityReport:
        """
        Are these two ecosystems culturally compatible?
        Measure: DSL overlap, constitutional similarity, novelty archive distance.
        High compatibility = rich exchange possible.
        Low compatibility = strategies may be meaningless to the other side.
        """
        ...
```

---

### PHASE 17: SELF-DIRECTED BENCHMARK GENERATION

**What it is:**
Instead of humans writing benchmarks, v3 ecosystems **generate their own tests**.
An organism that considers itself highly fit invents a test that proves it.
Other organisms must pass the same test. This creates a co-evolutionary arms race
between benchmark generators and benchmark solvers.

```python
class BenchmarkSynthesizer:
    """
    An organism that generates challenges for other organisms.
    Its fitness = how hard its challenges are for others to solve.
    """

    def synthesize_benchmark(self, difficulty: float) -> Benchmark:
        """
        Generate a runnable challenge at a given difficulty level.
        difficulty 0.0 = trivial (every organism passes)
        difficulty 1.0 = open problem (no organism currently solves it)
        """
        ...

    def evaluate(self, organism: LamarckianOrganism, benchmark: Benchmark) -> float:
        """Score organism 0-1 on this benchmark."""
        ...

    def co_evolve(
        self,
        synthesizers: List["BenchmarkSynthesizer"],
        solvers: List[LamarckianOrganism],
        generations: int,
    ) -> CoEvolutionHistory:
        """
        Run co-evolutionary loop:
        - Synthesizers evolve harder benchmarks
        - Solvers evolve better strategies
        - Track arms race over generations
        """
        ...
```

---

### PHASE 18: CONSCIOUSNESS METRICS (MEASURABLE SELF-AWARENESS)

**What it is:**
A controversial but computationally well-defined question:
can we measure something like self-awareness in a living object?
Not philosophy — measurable quantities inspired by Integrated Information Theory (IIT)
and Global Workspace Theory (GWT), applied to organism architecture.

```python
class ConsciousnessMetrics:
    """
    Measurable proxies for self-awareness, not claims of sentience.
    Three concrete metrics, all computable:
    """

    def integrated_information(self, organism: LamarckianOrganism) -> float:
        """
        Phi (Φ): How much does the whole organism know that its parts don't?
        Computed as mutual information between organism's full state
        vs. sum of mutual information of each strategy in isolation.
        High Phi = organism's knowledge is more than the sum of its parts.
        """
        ...

    def self_model_accuracy(self, organism: LamarckianOrganism) -> float:
        """
        Does the organism have an accurate model of itself?
        Ask it to predict its own fitness. Compare to actual fitness.
        High accuracy = organism knows its own strengths and weaknesses.
        """
        ...

    def global_workspace_breadth(self, organism: LamarckianOrganism) -> float:
        """
        From Global Workspace Theory: how broadly does information flow?
        Measure: what fraction of strategies are accessible when evaluating
        any given task? High breadth = information integrates globally.
        """
        ...

    def composite_awareness_score(self, organism: LamarckianOrganism) -> float:
        """Phi * self_model_accuracy * global_workspace_breadth — normalized 0-1."""
        ...
```

---

## v3 SECURITY REQUIREMENTS (MANDATORY)

All of the following must be present before ANY v3 feature is merged:

```
✓ IsolatedSandbox: subprocess jail for all generated code execution
✓ Rate limiting: slowapi on all mutation endpoints (5 req/min token, 60/min strategies)
✓ CORS hardening: wildcard forbidden in production, HTTPS-only origins enforced
✓ JWT secret enforcement: RuntimeError if JWT_SECRET < 32 chars in production
✓ SQL injection: parameterized queries everywhere, identifier validation regex
✓ v2 route auth: Depends(require_operator) on all write endpoints
✓ subprocess resource limits: RLIMIT_AS + RLIMIT_CPU in _safe_shell_cmd
✓ Real API connections in UI: all 6 panels wired to real backend, zero mock data
```

---

## v3 DELIVERABLES CHECKLIST

### Security (ship FIRST, before any new feature)
- [ ] `evolution/sandbox.py` — `IsolatedSandbox`, `ResourceLimits`, subprocess jail
- [ ] `production/middleware/rate_limit.py` — slowapi integration, Redis-backed
- [ ] `production/middleware/cors.py` — production-safe CORS validator
- [ ] Updated `production/config.py` — JWT secret enforcement
- [ ] Updated `production/store_v2.py` — full parameterized query audit
- [ ] Updated `production/api/v2/routes.py` — auth guards on all write endpoints
- [ ] Updated `evolution/beast_v2_culture.py` — resource limits in subprocess
- [ ] Updated `web/client/src/components/V2Panels.tsx` — real API connections
- [ ] `evolution/test_security.py` — 20 security-specific tests (sandbox escape, SQLi, auth bypass, rate limit)

### New Evolution Phases
- [ ] `evolution/recursive_improvement.py` — `SafetyInvariant`, `FormalSafetyProof`, invariant checker
- [ ] `evolution/market.py` — `StrategyMarket`, `TokenWallet`, auction mechanism
- [ ] `evolution/quantum_genome.py` — `QuantumGenome`, measure, entangle, interfere
- [ ] `evolution/spiking.py` — `SpikingStrategyGenome`, LIF neurons, STDP learning
- [ ] `evolution/archaeology.py` — `KnowledgeArchaeologist`, excavate, resurrect
- [ ] `evolution/diplomacy.py` — `DiplomacyProtocol`, inter-ecosystem exchange
- [ ] `evolution/benchmark_synth.py` — `BenchmarkSynthesizer`, co-evolution loop
- [ ] `evolution/consciousness.py` — `ConsciousnessMetrics`, Phi, self-model, GWT
- [ ] `evolution/test_v3.py` — proof tests for all 8 phases + all 8 security fixes

### Infrastructure
- [ ] `production/api/v3/` — v3 API routes (market, diplomacy, archaeology, benchmarks)
- [ ] `production/api/v3/websocket.py` — New event types (market_trade, diplomatic_exchange, resurrection)
- [ ] `production/sandbox_worker.py` — Isolated worker process receiving code via stdin
- [ ] Updated `docker-compose.yml` — sandbox worker container + Redis for rate limits
- [ ] Updated Helm chart — resource limits on sandbox pods (no-network, read-only FS)

### Web UI (v3 Observatory)
- [ ] Consciousness Meter panel (Phi score, self-model accuracy, GWT breadth)
- [ ] Strategy Market panel (live price feed, buy/sell buttons, wallet balance)
- [ ] Diplomacy Console panel (inter-ecosystem proposals, accept/reject UI)
- [ ] Archaeology Panel (extinct strategy list, relevance scores, resurrect button)
- [ ] Co-Evolution Tracker (benchmark arms race visualization, difficulty curve)
- [ ] Quantum Genome Viewer (amplitude visualization per trait, measurement history)

### Documentation
- [ ] `docs/v3-security.md` — Security model, threat model, sandbox architecture
- [ ] `docs/v3-architecture.md` — Full v3 technical design
- [ ] `docs/consciousness-notes.md` — IIT + GWT applied to digital organisms
- [ ] `docs/quantum-genome-notes.md` — Quantum-inspired (not quantum-computing) design
- [ ] `research/benchmark-synth-findings.md` — Co-evolution arms race observations
- [ ] Updated `README.md` — v3 feature list, quick-start, security notes

---

## BENCHMARK TARGETS FOR v3

| Benchmark | v2 Achieved | v3 Target |
|---|---|---|
| Tests passing | 147 | **250+** |
| Security tests | 0 | **20 mandatory** |
| Sandbox escape attempts blocked | Not tested | **100% blocked** |
| Rate limit test (10K reqs/min) | Not tested | **API stable under load** |
| Phi (integrated information) measurable | Not implemented | **Φ > 0 in evolved organisms** |
| Strategy market volume | Not implemented | **>50 trades per 50 gens** |
| Cross-ecosystem strategy exchange | Not implemented | **2 ecosystems exchange ≥5 strategies** |
| Archaeology resurrection rate | Not implemented | **≥1 extinct strategy resurrected per 10 gens** |
| Benchmark arms race hardness | Not implemented | **Difficulty rises monotonically over 30 gens** |

---

## THE HIERARCHY

```
v1: Individual organisms evolve strategies
v2: Civilizations evolve civilizations
v3: Civilizations self-prove safety, trade across borders,
    measure their own awareness, and excavate lost knowledge
```

**The three things that separate v3 from every AI system ever built:**

1. **It is safe by proof, not by promise.**
   No LLM or agent framework ships with formal invariant verification.
   v3 organisms cannot break their own ecosystem because they must prove they won't.

2. **It has an economy.**
   Knowledge is not free. Rare strategies are expensive.
   Economic pressure creates specialization, trade, and civilizational structure.

3. **It can measure its own awareness.**
   Phi, self-model accuracy, and GWT breadth are computable.
   v3 is the first system that answers "how aware is it?" with a number, not a philosophy.

---

*Written after full code audit of Living Objects v2.0.*
*Every vulnerability in Part A was found by static analysis of the actual committed code.*
*v3 ships security hardening BEFORE new features. No exceptions.*
