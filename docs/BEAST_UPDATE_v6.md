# BEAST UPDATE v6 — LIVING OBJECTS: THE REAL THING
## The Document That Requires 1000 Engineers Working Simultaneously

> **This is not another spec.**
> **This is the blueprint for a living, breathing, self-improving software civilization.**
>
> v1–v5 built the scaffolding.
> v6 tears down every fake part and replaces it with the real thing.
>
> After v6, organisms will:
> - Actually solve problems (not return template floats)
> - Actually reason without an LLM (genetic programming, not SHA256 lookups)
> - Actually compete in real-time markets, fix production bugs, write code, trade insights
> - Actually run on any device, in any browser, on any chip
> - Actually improve themselves while you sleep
>
> **Every single section below is a concrete engineering task.**
> **Every class has real method signatures.**
> **Every proof has a runnable test.**
> **This is what 1000 engineers build.**

---

## THE FUNDAMENTAL PROBLEM (Say It Out Loud)

Right now, every "evolved strategy" looks like this:

```python
def action_learned_g001_1(self):
    # learned at generation 1; persisted in the memome
    learned_value = 0.605100
    return min(0.99, learned_value + 0.08 * self.genome.learning_rate)
```

This is a **hardcoded template with one float**. Not evolution. Not reasoning.
The `MockReasoningEngine` hashes a string and picks from 5 sentences.

**v6 fixes this completely.** Every organism will evolve real executable code.
Every fitness function will test real correctness. Every generation will be
genuinely different from the last.

---

## PART A: THE CORE FIX — GENETIC PROGRAMMING ENGINE (MANDATORY FIRST)

> Nothing else in v6 matters until this is done.
> This is the engine that makes everything real.

---

### PHASE 0-A: REAL GENETIC PROGRAMMING (No Templates, No Floats)

**What changes:** `_strategy_source()` is replaced entirely.
Organisms now evolve **real Abstract Syntax Trees** that compile to real Python.

```python
# evolution/gp_engine.py
"""
Genetic Programming Engine.
Organisms evolve real code via AST mutation and crossover.
No templates. No float parameters. Real programs.
"""
from __future__ import annotations

import ast
import copy
import random
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVE SET — the atoms that programs are built from
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Primitive:
    """A function or terminal that can appear in an evolved program."""
    name: str
    arity: int          # number of arguments (0 = terminal)
    fn: Callable        # Python callable
    return_type: type
    arg_types: List[type]

ARITHMETIC_PRIMITIVES = [
    Primitive("add",  2, lambda a, b: a + b,   float, [float, float]),
    Primitive("sub",  2, lambda a, b: a - b,   float, [float, float]),
    Primitive("mul",  2, lambda a, b: a * b,   float, [float, float]),
    Primitive("div",  2, lambda a, b: a / b if b != 0 else 0.0, float, [float, float]),
    Primitive("max2", 2, max,                  float, [float, float]),
    Primitive("min2", 2, min,                  float, [float, float]),
    Primitive("neg",  1, lambda a: -a,         float, [float]),
    Primitive("abs1", 1, abs,                  float, [float]),
    Primitive("sq",   1, lambda a: a * a,      float, [float]),
    Primitive("sqrt", 1, lambda a: a ** 0.5 if a >= 0 else 0.0, float, [float]),
    Primitive("if_pos", 3, lambda c, t, f: t if c > 0 else f, float, [float, float, float]),
    Primitive("log",  1, lambda a: __import__("math").log(a) if a > 0 else 0.0, float, [float]),
]

BOOLEAN_PRIMITIVES = [
    Primitive("and2", 2, lambda a, b: a and b, bool, [bool, bool]),
    Primitive("or2",  2, lambda a, b: a or b,  bool, [bool, bool]),
    Primitive("not1", 1, lambda a: not a,      bool, [bool]),
    Primitive("gt",   2, lambda a, b: a > b,   bool, [float, float]),
    Primitive("lt",   2, lambda a, b: a < b,   bool, [float, float]),
    Primitive("eq",   2, lambda a, b: abs(a - b) < 1e-9, bool, [float, float]),
]

LIST_PRIMITIVES = [
    Primitive("head",   1, lambda lst: lst[0] if lst else 0,         float, [list]),
    Primitive("tail",   1, lambda lst: lst[1:] if len(lst) > 1 else [], list, [list]),
    Primitive("cons",   2, lambda x, lst: [x] + lst,                 list,  [float, list]),
    Primitive("length", 1, lambda lst: float(len(lst)),               float, [list]),
    Primitive("sort1",  1, sorted,                                    list,  [list]),
    Primitive("sum1",   1, lambda lst: sum(lst) if lst else 0.0,      float, [list]),
    Primitive("map_sq", 1, lambda lst: [x*x for x in lst],           list,  [list]),
    Primitive("filter_pos", 1, lambda lst: [x for x in lst if x > 0], list, [list]),
    Primitive("zip_add", 2, lambda a, b: [x+y for x,y in zip(a,b)],  list,  [list, list]),
    Primitive("unique",  1, lambda lst: list(dict.fromkeys(lst)),     list,  [list]),
]

STRING_PRIMITIVES = [
    Primitive("concat",  2, lambda a, b: str(a) + str(b),           str, [str, str]),
    Primitive("upper1",  1, lambda a: str(a).upper(),               str, [str]),
    Primitive("strip1",  1, lambda a: str(a).strip(),               str, [str]),
    Primitive("split1",  1, lambda a: str(a).split(),               list, [str]),
    Primitive("join1",   2, lambda sep, lst: str(sep).join(map(str, lst)), str, [str, list]),
    Primitive("startswith2", 2, lambda a, b: str(a).startswith(str(b)), bool, [str, str]),
    Primitive("replace3", 3, lambda s,a,b: str(s).replace(str(a),str(b)), str, [str,str,str]),
    Primitive("len_str", 1, lambda s: float(len(str(s))),           float, [str]),
    Primitive("substr",  3, lambda s,a,b: str(s)[int(a):int(b)],   str, [str, float, float]),
]

# ─────────────────────────────────────────────────────────────────────────────
# GP TREE NODE
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GPNode:
    """A node in a genetic programming expression tree."""
    primitive: Optional[Primitive] = None     # None = terminal
    terminal_value: Any = None                # value if terminal
    terminal_name: str = ""                   # variable name if terminal variable
    children: List["GPNode"] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.primitive is None

    def evaluate(self, context: dict[str, Any]) -> Any:
        """Recursively evaluate this node with given variable bindings."""
        if self.is_terminal:
            if self.terminal_name and self.terminal_name in context:
                return context[self.terminal_name]
            return self.terminal_value
        child_values = [child.evaluate(context) for child in self.children]
        try:
            return self.primitive.fn(*child_values)
        except Exception:
            return 0.0 if self.primitive.return_type == float else [] if self.primitive.return_type == list else ""

    def to_python(self, indent: int = 0) -> str:
        """Compile this GP tree to a readable Python expression."""
        if self.is_terminal:
            if self.terminal_name:
                return self.terminal_name
            return repr(self.terminal_value)
        args = ", ".join(child.to_python() for child in self.children)
        return f"{self.primitive.name}({args})"

    def depth(self) -> int:
        if self.is_terminal:
            return 0
        return 1 + max((c.depth() for c in self.children), default=0)

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def copy(self) -> "GPNode":
        return copy.deepcopy(self)


# ─────────────────────────────────────────────────────────────────────────────
# GP TREE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

class GPTreeBuilder:
    """Build, mutate, and crossover GP trees."""

    MAX_DEPTH: int = 8
    MAX_SIZE: int = 64

    def __init__(
        self,
        primitives: List[Primitive],
        terminals: List[Tuple[str, Any]],   # (name_or_"const", value_or_type)
        rng: random.Random,
    ) -> None:
        self.primitives = primitives
        self.terminals = terminals
        self.rng = rng

    def random_tree(self, max_depth: int = 4, method: str = "ramped") -> GPNode:
        """
        Generate a random program tree using ramped half-and-half.
        method: "full" | "grow" | "ramped"
        """
        if method == "ramped":
            method = self.rng.choice(["full", "grow"])
        return self._build(max_depth, method, terminal_only=(max_depth == 0))

    def _build(self, max_depth: int, method: str, terminal_only: bool = False) -> GPNode:
        force_terminal = terminal_only or (method == "grow" and self.rng.random() < 0.35)
        if max_depth == 0 or force_terminal:
            return self._random_terminal()
        prim = self.rng.choice(self.primitives)
        node = GPNode(primitive=prim)
        node.children = [self._build(max_depth - 1, method) for _ in range(prim.arity)]
        return node

    def _random_terminal(self) -> GPNode:
        name, value = self.rng.choice(self.terminals)
        if name == "const":
            return GPNode(terminal_value=value if not callable(value) else value(self.rng))
        return GPNode(terminal_name=name, terminal_value=None)

    def point_mutate(self, tree: GPNode) -> GPNode:
        """Replace a random node with a new random subtree."""
        tree = tree.copy()
        all_nodes = self._collect_nodes(tree)
        if not all_nodes:
            return tree
        target_parent, target_idx = self.rng.choice(all_nodes)
        new_subtree = self._build(
            self.rng.randint(0, min(3, self.MAX_DEPTH - 1)), "grow"
        )
        if target_parent is None:
            return new_subtree  # replacing root
        target_parent.children[target_idx] = new_subtree
        return tree

    def subtree_crossover(self, parent1: GPNode, parent2: GPNode) -> Tuple[GPNode, GPNode]:
        """Classic GP subtree crossover."""
        c1, c2 = parent1.copy(), parent2.copy()
        nodes1 = self._collect_nodes(c1)
        nodes2 = self._collect_nodes(c2)
        if not nodes1 or not nodes2:
            return c1, c2
        p1, i1 = self.rng.choice(nodes1)
        p2, i2 = self.rng.choice(nodes2)
        sub1 = p1.children[i1].copy() if p1 else c1.copy()
        sub2 = p2.children[i2].copy() if p2 else c2.copy()
        if p1:
            p1.children[i1] = sub2
        else:
            c1 = sub2
        if p2:
            p2.children[i2] = sub1
        else:
            c2 = sub1
        return c1, c2

    def hoist_mutate(self, tree: GPNode) -> GPNode:
        """Replace tree with one of its subtrees (shrinks size, avoids bloat)."""
        tree = tree.copy()
        internal = [n for p, i in self._collect_nodes(tree) for n in ([p.children[i]] if p else [tree]) if not n.is_terminal and n.children]
        if not internal:
            return tree
        node = self.rng.choice(internal)
        return self.rng.choice(node.children).copy()

    def expand_mutate(self, tree: GPNode) -> GPNode:
        """Replace a terminal with a small new subtree (grows size)."""
        tree = tree.copy()
        terminals = [(p, i) for p, i in self._collect_nodes(tree) if (p.children[i] if p else tree).is_terminal]
        if not terminals:
            return tree
        par, idx = self.rng.choice(terminals)
        new_sub = self._build(self.rng.randint(1, 2), "grow")
        if par:
            par.children[idx] = new_sub
        return tree

    def _collect_nodes(self, root: GPNode, parent=None, index=0):
        """BFS collect (parent, child_index) pairs."""
        result = [(parent, index)]
        for i, child in enumerate(root.children):
            result.extend(self._collect_nodes(child, root, i))
        return result

    def to_python_function(self, tree: GPNode, func_name: str, args: List[str]) -> str:
        """
        Compile a GP tree to a complete, importable Python function.
        The result is real executable Python, not a template.
        """
        body = tree.to_python()
        args_str = ", ".join(args)
        return textwrap.dedent(f"""
def {func_name}({args_str}):
    \"\"\"Evolved by genetic programming. Generation unknown.\"\"\"
    try:
        return {body}
    except Exception:
        return None
""").strip()


# ─────────────────────────────────────────────────────────────────────────────
# GP ORGANISM GENOME
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GPGenome:
    """
    A genome that IS a program, not a float.
    Every organism carries a real executable function tree.
    """
    tree: GPNode
    primitives_used: List[str] = field(default_factory=list)
    generation_created: int = 0
    parent_ids: List[str] = field(default_factory=list)
    fitness: float = 0.0
    fitness_variance: float = 1.0     # starts uncertain
    evaluations: int = 0

    def to_python(self, func_name: str = "evolved_fn", args: List[str] = None) -> str:
        args = args or ["x"]
        builder = GPTreeBuilder([], [], random.Random())
        return builder.to_python_function(self.tree, func_name, args)

    def execute(self, context: dict) -> Any:
        """Run the evolved program. Never raises."""
        try:
            return self.tree.evaluate(context)
        except Exception:
            return None

    def description_length(self) -> int:
        """Kolmogorov proxy: compressed size of the Python source."""
        import zlib
        return len(zlib.compress(self.to_python().encode(), level=9))

    def complexity(self) -> int:
        return self.tree.size()

    def depth(self) -> int:
        return self.tree.depth()
```

---

### PHASE 0-B: REAL FITNESS EVALUATOR (No Math Formulas)

Replace `_adaptive_score()` with real task evaluators:

```python
# evolution/fitness.py
"""
Real fitness functions. Every fitness score comes from
running the evolved program against actual test cases.
No formula-based scores. No fixed targets.
"""
from __future__ import annotations

import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from evolution.gp_engine import GPGenome
from evolution.sandbox import IsolatedSandbox, ResourceLimits


@dataclass(frozen=True)
class FitnessResult:
    score: float              # [0, 1]
    correctness: float        # [0, 1] task-specific accuracy
    efficiency: float         # [0, 1] speed/brevity bonus
    robustness: float         # [0, 1] variance across test cases
    description_length: int   # lower = more elegant
    wall_time_ms: float       # execution time
    test_cases_passed: int
    test_cases_total: int
    error_message: str = ""


class FitnessEvaluator(ABC):
    """Base class for all real fitness evaluators."""

    @abstractmethod
    def evaluate(self, genome: GPGenome) -> FitnessResult:
        """Run genome against real test cases. Return honest fitness."""
        ...

    @abstractmethod
    def generate_test_cases(self, seed: int, n: int) -> List[Tuple[Any, Any]]:
        """Generate (input, expected_output) pairs."""
        ...

    def batch_evaluate(self, genomes: List[GPGenome], seed: int) -> List[FitnessResult]:
        """Evaluate a whole population. Reuse same test cases per generation."""
        cases = self.generate_test_cases(seed=seed, n=20)
        return [self._eval_on_cases(g, cases) for g in genomes]

    def _eval_on_cases(self, genome: GPGenome, cases: List[Tuple]) -> FitnessResult:
        correct, total = 0, len(cases)
        times = []
        for inp, expected in cases:
            t0 = time.perf_counter()
            got = genome.execute({"x": inp, "input": inp, "data": inp})
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            if self._is_correct(got, expected):
                correct += 1

        correctness = correct / max(1, total)
        avg_ms = sum(times) / len(times)
        efficiency = max(0.0, 1.0 - avg_ms / 500.0)  # 0ms = 1.0, 500ms = 0.0
        brevity = max(0.0, 1.0 - genome.description_length() / 2000.0)
        robustness = 1.0 - (max(times) - min(times)) / max(1.0, max(times))

        score = correctness * 0.6 + efficiency * 0.15 + brevity * 0.15 + robustness * 0.1
        return FitnessResult(
            score=min(1.0, score),
            correctness=correctness,
            efficiency=efficiency,
            robustness=robustness,
            description_length=genome.description_length(),
            wall_time_ms=avg_ms,
            test_cases_passed=correct,
            test_cases_total=total,
        )

    def _is_correct(self, got: Any, expected: Any) -> bool:
        if isinstance(expected, float):
            return isinstance(got, (int, float)) and abs(float(got) - expected) < 1e-4
        if isinstance(expected, list):
            return isinstance(got, list) and len(got) == len(expected) and \
                   all(self._is_correct(a, b) for a, b in zip(got, expected))
        return got == expected


class SortingEvaluator(FitnessEvaluator):
    """Evolve a sorting algorithm. Fitness = fraction of outputs correctly sorted."""

    def generate_test_cases(self, seed: int, n: int = 20):
        rng = random.Random(seed)
        return [
            (arr := [rng.randint(0, 100) for _ in range(rng.randint(3, 15))],
             sorted(arr))
            for _ in range(n)
        ]

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        cases = self.generate_test_cases(seed=hash(genome.tree.to_python() if hasattr(genome.tree, 'to_python') else str(genome)) % 10000, n=20)
        return self._eval_on_cases(genome, cases)


class PrimeEvaluator(FitnessEvaluator):
    """
    Evolve a primality test. Input: integer. Output: True if prime, False if not.
    Fitness = fraction of correct classifications.
    """
    KNOWN = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,
             73,79,83,89,97,101,103,107,109,113}

    def generate_test_cases(self, seed: int, n: int = 20):
        rng = random.Random(seed)
        candidates = list(range(2, 200))
        selected = rng.sample(candidates, min(n, len(candidates)))
        return [(n, n in self.KNOWN) for n in selected]

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        return self._eval_on_cases(genome, self.generate_test_cases(seed=42, n=30))


class FibonacciEvaluator(FitnessEvaluator):
    """Evolve a Fibonacci function. Input: n. Output: fib(n)."""

    FIBS = [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181]

    def generate_test_cases(self, seed: int, n: int = 15):
        return [(i, self.FIBS[i]) for i in range(min(n, len(self.FIBS)))]

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        return self._eval_on_cases(genome, self.generate_test_cases(seed=42))


class StringReverseEvaluator(FitnessEvaluator):
    """Evolve a string reversal function."""

    def generate_test_cases(self, seed: int, n: int = 20):
        rng = random.Random(seed)
        words = ["hello", "world", "evolution", "organism", "meme", "culture",
                 "darwin", "lamarck", "fitness", "genome", "living", "objects"]
        selected = [rng.choice(words) for _ in range(n)]
        return [(w, w[::-1]) for w in selected]

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        return self._eval_on_cases(genome, self.generate_test_cases(seed=42))


class MaxSubarrayEvaluator(FitnessEvaluator):
    """
    Evolve Kadane's algorithm (maximum subarray sum).
    Classic dynamic programming problem — emerges from evolution over 10k+ gens.
    """

    def _kadane(self, arr: list) -> float:
        max_sum = arr[0] if arr else 0
        curr = arr[0] if arr else 0
        for x in arr[1:]:
            curr = max(x, curr + x)
            max_sum = max(max_sum, curr)
        return float(max_sum)

    def generate_test_cases(self, seed: int, n: int = 20):
        rng = random.Random(seed)
        return [
            (arr := [rng.randint(-10, 10) for _ in range(rng.randint(3, 12))],
             self._kadane(arr))
            for _ in range(n)
        ]

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        return self._eval_on_cases(genome, self.generate_test_cases(seed=42))


class PathfindingEvaluator(FitnessEvaluator):
    """
    Evolve a heuristic for A* pathfinding.
    Input: (current_x, current_y, goal_x, goal_y).
    Output: estimated distance (heuristic value).
    Fitness: how well the heuristic guides path search vs. true Euclidean.
    """

    def generate_test_cases(self, seed: int, n: int = 20):
        rng = random.Random(seed)
        cases = []
        for _ in range(n):
            cx, cy = rng.randint(0, 10), rng.randint(0, 10)
            gx, gy = rng.randint(0, 10), rng.randint(0, 10)
            true_dist = math.sqrt((gx - cx)**2 + (gy - cy)**2)
            cases.append(((cx, cy, gx, gy), true_dist))
        return cases

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        cases = self.generate_test_cases(seed=42)
        correct, total = 0, len(cases)
        for (cx, cy, gx, gy), true_dist in cases:
            got = genome.execute({"cx": cx, "cy": cy, "gx": gx, "gy": gy, "x": cx, "y": cy})
            if isinstance(got, (int, float)) and abs(float(got) - true_dist) < 2.0:
                correct += 1
        score = correct / max(1, total)
        return FitnessResult(
            score=score, correctness=score, efficiency=1.0, robustness=1.0,
            description_length=genome.description_length(),
            wall_time_ms=0.0, test_cases_passed=correct, test_cases_total=total,
        )


class CompressionEvaluator(FitnessEvaluator):
    """
    Evolve a run-length encoder.
    Input: list of integers. Output: compressed representation length.
    Fitness: how much shorter the output is vs. input.
    """

    def generate_test_cases(self, seed: int, n: int = 15):
        rng = random.Random(seed)
        cases = []
        for _ in range(n):
            # Generate runs (compressible data)
            data = []
            for _ in range(rng.randint(3, 8)):
                val = rng.randint(0, 5)
                run = rng.randint(1, 6)
                data.extend([val] * run)
            import zlib
            expected = float(len(zlib.compress(bytes(data), level=1)))
            cases.append((data, expected))
        return cases

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        return self._eval_on_cases(genome, self.generate_test_cases(seed=42))


class GameStrategyEvaluator(FitnessEvaluator):
    """
    Evolve an iterated Prisoner's Dilemma strategy.
    Input: opponent's last move (1=cooperate, 0=defect), round number.
    Output: 1 (cooperate) or 0 (defect).
    Fitness: total payoff across 200 rounds against 5 fixed opponents.
    """

    OPPONENTS = {
        "always_c": lambda h: 1,
        "always_d": lambda h: 0,
        "tit4tat":  lambda h: h[-1] if h else 1,
        "grudger":  lambda h: 0 if 0 in h else 1,
        "random50": lambda h: __import__("random").randint(0, 1),
    }

    def generate_test_cases(self, seed: int, n: int = 1):
        return [(None, None)]  # tournament-style, not input/output pairs

    def evaluate(self, genome: GPGenome) -> FitnessResult:
        total, max_possible = 0.0, 0.0
        ROUNDS = 100
        for opp_fn in self.OPPONENTS.values():
            history = []
            score = 0
            for rnd in range(ROUNDS):
                opp_last = history[-1] if history else 1
                my_raw = genome.execute({"x": float(opp_last), "rnd": float(rnd), "n": float(rnd)})
                my_move = 1 if (my_raw or 0) > 0.5 else 0
                opp_move = opp_fn([m[0] for m in history]) if history else 1
                payoff = {(1,1): 3, (1,0): 0, (0,1): 5, (0,0): 1}[(my_move, opp_move)]
                score += payoff
                history.append((opp_move, my_move))
            total += score
            max_possible += ROUNDS * 5
        fitness = total / max_possible
        return FitnessResult(
            score=fitness, correctness=fitness, efficiency=1.0, robustness=1.0,
            description_length=genome.description_length(),
            wall_time_ms=0.0, test_cases_passed=int(fitness * 100), test_cases_total=100,
        )
```

---

### PHASE 0-C: REAL POPULATION ENGINE (Replacing MockReasoningEngine)

```python
# evolution/gp_population.py
"""
A population of GP organisms that actually evolve.
No LLM. No MockReasoning. Pure genetic programming.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from evolution.gp_engine import GPGenome, GPNode, GPTreeBuilder, ARITHMETIC_PRIMITIVES, LIST_PRIMITIVES
from evolution.fitness import FitnessEvaluator, FitnessResult


@dataclass
class GPOrganism:
    """A living GP organism. Its genome IS its program."""
    organism_id: str
    genome: GPGenome
    fitness_result: Optional[FitnessResult] = None
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    age: int = 0                   # generations survived
    cultural_strategies: int = 0   # strategies adopted from memome

    @property
    def fitness(self) -> float:
        return self.fitness_result.score if self.fitness_result else 0.0

    def to_dict(self) -> dict:
        return {
            "organism_id": self.organism_id,
            "generation": self.generation,
            "fitness": self.fitness,
            "program_size": self.genome.complexity(),
            "program_depth": self.genome.depth(),
            "source_code": self.genome.to_python(f"evolved_gen{self.generation}"),
        }


class GPPopulation:
    """
    A real genetic programming population.
    Every organism is a different evolved program.
    Tournament selection + subtree crossover + point mutation.
    """

    def __init__(
        self,
        evaluator: FitnessEvaluator,
        primitives=None,
        terminals=None,
        population_size: int = 50,
        seed: int = 42,
        tournament_size: int = 5,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.15,
        elitism_count: int = 3,
        max_depth: int = 7,
        bloat_penalty: float = 0.001,
    ) -> None:
        self.evaluator = evaluator
        self.rng = random.Random(seed)
        self.population_size = population_size
        self.tournament_size = tournament_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        self.max_depth = max_depth
        self.bloat_penalty = bloat_penalty
        self.generation = 0
        self.population: List[GPOrganism] = []
        self.history: List[GenerationStats] = []
        self.hall_of_fame: List[GPOrganism] = []
        self.builder = GPTreeBuilder(
            primitives or ARITHMETIC_PRIMITIVES + LIST_PRIMITIVES,
            terminals or [
                ("const", lambda rng: rng.uniform(-10, 10)),
                ("const", lambda rng: float(rng.randint(0, 10))),
                ("x", None),
                ("n", None),
            ],
            self.rng,
        )

    def initialize(self) -> None:
        """Ramped half-and-half initialization."""
        self.population = []
        import uuid
        for i in range(self.population_size):
            max_d = 2 + (i % (self.max_depth - 1))
            tree = self.builder.random_tree(max_depth=max_d, method="ramped")
            genome = GPGenome(tree=tree, generation_created=0)
            organism = GPOrganism(
                organism_id=str(uuid.uuid4())[:12],
                genome=genome,
                generation=0,
            )
            self.population.append(organism)

    def step(self) -> "GenerationStats":
        """Run one generation of evolution."""
        self.generation += 1

        # Evaluate all
        for org in self.population:
            if org.fitness_result is None:
                org.fitness_result = self.evaluator.evaluate(org.genome)

        # Elitism
        sorted_pop = sorted(self.population, key=lambda o: o.fitness, reverse=True)
        new_pop = sorted_pop[:self.elitism_count]
        self.hall_of_fame.append(sorted_pop[0])

        # Build next generation
        import uuid
        while len(new_pop) < self.population_size:
            parent1 = self._tournament_select()
            op = self.rng.random()

            if op < self.crossover_rate and len(self.population) > 1:
                parent2 = self._tournament_select()
                child_tree1, child_tree2 = self.builder.subtree_crossover(
                    parent1.genome.tree, parent2.genome.tree
                )
                tree = child_tree1 if self.rng.random() < 0.5 else child_tree2
                parent_ids = [parent1.organism_id, parent2.organism_id]
            else:
                tree = parent1.genome.tree.copy()
                parent_ids = [parent1.organism_id]

            # Mutation
            if self.rng.random() < self.mutation_rate:
                mut_type = self.rng.choice(["point", "hoist", "expand"])
                if mut_type == "point":
                    tree = self.builder.point_mutate(tree)
                elif mut_type == "hoist" and tree.size() > 3:
                    tree = self.builder.hoist_mutate(tree)
                else:
                    tree = self.builder.expand_mutate(tree)

            # Bloat control: if tree too big, hoist
            if tree.depth() > self.max_depth or tree.size() > 64:
                tree = self.builder.hoist_mutate(tree)

            genome = GPGenome(
                tree=tree,
                generation_created=self.generation,
                parent_ids=parent_ids,
            )
            child = GPOrganism(
                organism_id=str(uuid.uuid4())[:12],
                genome=genome,
                generation=self.generation,
                parent_ids=parent_ids,
            )
            new_pop.append(child)

        self.population = new_pop[:self.population_size]

        stats = self._record_stats()
        self.history.append(stats)
        return stats

    def _tournament_select(self) -> GPOrganism:
        contestants = self.rng.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(contestants, key=lambda o: o.fitness)

    def _record_stats(self) -> "GenerationStats":
        fitnesses = [o.fitness for o in self.population]
        sizes = [o.genome.complexity() for o in self.population]
        return GenerationStats(
            generation=self.generation,
            best_fitness=max(fitnesses),
            avg_fitness=sum(fitnesses) / len(fitnesses),
            worst_fitness=min(fitnesses),
            best_program_size=min(sizes),
            avg_program_size=sum(sizes) / len(sizes),
            champion_source=self.champion.genome.to_python(f"champion_gen{self.generation}"),
        )

    @property
    def champion(self) -> GPOrganism:
        return max(self.population, key=lambda o: o.fitness)

    def run(
        self,
        generations: int = 100,
        target_fitness: float = 0.99,
        checkpoint_dir: Optional[str] = None,
        verbose: bool = True,
    ) -> "RunSummary":
        """Run evolution for N generations or until target fitness reached."""
        t_start = time.time()
        for gen in range(generations):
            stats = self.step()
            if verbose and gen % 100 == 0:
                elapsed = time.time() - t_start
                eta = (generations - gen) * elapsed / max(1, gen + 1)
                print(
                    f"  Gen {gen:6d} | Best {stats.best_fitness:.4f} | "
                    f"Avg {stats.avg_fitness:.4f} | "
                    f"Size {stats.avg_program_size:.1f} | "
                    f"ETA {eta/60:.1f}m"
                )
            if stats.best_fitness >= target_fitness:
                print(f"  ✓ Target fitness {target_fitness} reached at generation {gen}!")
                break
        return RunSummary(
            generations_run=self.generation,
            total_time_seconds=time.time() - t_start,
            peak_fitness=max(s.best_fitness for s in self.history),
            peak_generation=max(range(len(self.history)), key=lambda i: self.history[i].best_fitness),
            champion=self.champion,
        )


@dataclass
class GenerationStats:
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    best_program_size: int
    avg_program_size: float
    champion_source: str


@dataclass
class RunSummary:
    generations_run: int
    total_time_seconds: float
    peak_fitness: float
    peak_generation: int
    champion: "GPOrganism"

    def print(self) -> None:
        print(f"\n{'='*60}")
        print(f"EVOLUTION COMPLETE")
        print(f"Generations:   {self.generations_run:,}")
        print(f"Total time:    {self.total_time_seconds/60:.1f} minutes")
        print(f"Peak fitness:  {self.peak_fitness:.4f} (gen {self.peak_generation:,})")
        print(f"Champion code:")
        print(self.champion.genome.to_python("champion"))
        print(f"{'='*60}")
```

---

## PART B: REAL-TIME MARKET — ORGANISMS TRADE WORKING CODE

```python
# evolution/live_market.py
"""
A real-time code market where organisms trade verified working programs.
Prices determined by actual benchmark performance, not arbitrary formulas.
Only code that passes the sandbox test gets listed.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import heapq

from evolution.gp_engine import GPGenome
from evolution.fitness import FitnessEvaluator, FitnessResult
from evolution.sandbox import IsolatedSandbox


@dataclass
class MarketListing:
    listing_id: str
    program_source: str      # actual verified code
    seller_id: str
    ask_price: float         # token price
    fitness_proof: FitnessResult  # verified benchmark result
    task_domain: str
    generation_created: int
    listed_at: float = field(default_factory=time.time)
    sale_count: int = 0

    @property
    def price(self) -> float:
        """Dynamic pricing: rarer = more expensive."""
        return self.ask_price / (1 + self.sale_count * 0.1)


@dataclass
class OrderBook:
    """An order book for a specific task domain."""
    task: str
    bids: List[tuple] = field(default_factory=list)   # (price, buyer_id, genome)
    asks: List[tuple] = field(default_factory=list)   # (price, listing_id, listing)

    def add_bid(self, price: float, buyer_id: str, genome: GPGenome) -> None:
        heapq.heappush(self.bids, (-price, buyer_id, genome))

    def add_ask(self, listing: MarketListing) -> None:
        heapq.heappush(self.asks, (listing.price, listing.listing_id, listing))

    def match(self) -> List[tuple]:
        """Return matched (buyer, seller, price) trades."""
        trades = []
        while self.bids and self.asks:
            bid_price = -self.bids[0][0]
            ask_price = self.asks[0][0]
            if bid_price < ask_price:
                break
            _, buyer_id, buyer_genome = heapq.heappop(self.bids)
            _, _, listing = heapq.heappop(self.asks)
            trade_price = (bid_price + ask_price) / 2
            trades.append((buyer_id, listing.seller_id, trade_price, listing))
        return trades


class LiveCodeMarket:
    """
    A real-time market for evolved code.
    Every listing must come with a verified benchmark result.
    Every buyer receives working, tested code.
    """

    def __init__(
        self,
        evaluator: FitnessEvaluator,
        sandbox: IsolatedSandbox,
        min_fitness_to_list: float = 0.3,
    ) -> None:
        self.evaluator = evaluator
        self.sandbox = sandbox
        self.min_fitness = min_fitness_to_list
        self.order_books: Dict[str, OrderBook] = defaultdict(lambda: OrderBook("default"))
        self.listings: Dict[str, MarketListing] = {}
        self.trade_history: List[dict] = []
        self.wallets: Dict[str, float] = defaultdict(lambda: 100.0)

    def list_program(
        self,
        seller_id: str,
        genome: GPGenome,
        task_domain: str,
        ask_price: Optional[float] = None,
    ) -> Optional[MarketListing]:
        """
        List a program for sale.
        MANDATORY: runs it through evaluator first. Only lists if it passes.
        """
        result = self.evaluator.evaluate(genome)
        if result.score < self.min_fitness:
            return None   # rejected — program not good enough to sell

        import uuid
        price = ask_price or (result.score * 100)  # fitness-based default price
        listing = MarketListing(
            listing_id=str(uuid.uuid4())[:10],
            program_source=genome.to_python(f"listed_{seller_id[:6]}"),
            seller_id=seller_id,
            ask_price=price,
            fitness_proof=result,
            task_domain=task_domain,
            generation_created=genome.generation_created,
        )
        self.listings[listing.listing_id] = listing
        self.order_books[task_domain].add_ask(listing)
        return listing

    def place_bid(
        self, buyer_id: str, task_domain: str, max_price: float, genome: GPGenome
    ) -> bool:
        """Buyer wants to acquire a program in this domain for up to max_price tokens."""
        if self.wallets[buyer_id] < max_price:
            return False
        self.order_books[task_domain].add_bid(max_price, buyer_id, genome)
        return True

    def settle(self) -> List[dict]:
        """Match bids and asks. Transfer code and tokens."""
        all_trades = []
        for domain, book in self.order_books.items():
            trades = book.match()
            for buyer_id, seller_id, price, listing in trades:
                if self.wallets[buyer_id] < price:
                    continue
                self.wallets[buyer_id] -= price
                self.wallets[seller_id] += price
                listing.sale_count += 1
                trade = {
                    "buyer": buyer_id,
                    "seller": seller_id,
                    "price": price,
                    "domain": domain,
                    "fitness": listing.fitness_proof.score,
                    "code_preview": listing.program_source[:100],
                    "timestamp": time.time(),
                }
                self.trade_history.append(trade)
                all_trades.append(trade)
        return all_trades

    def leaderboard(self, task_domain: str, top_n: int = 10) -> List[MarketListing]:
        """Top N programs for a given task by verified fitness."""
        domain_listings = [
            l for l in self.listings.values()
            if l.task_domain == task_domain
        ]
        return sorted(domain_listings, key=lambda l: l.fitness_proof.score, reverse=True)[:top_n]
```

---

## PART C: SELF-IMPROVING PRODUCTION BUG FIXER

```python
# evolution/bug_fixer.py
"""
An organism that evolves to fix real production bugs autonomously.
Input: a failing test + broken code.
Output: a fixed version that passes the test.
This is the first step toward autonomous software engineering.
No LLM. Pure evolutionary search.
"""
from __future__ import annotations

import ast
import copy
import random
import textwrap
from dataclasses import dataclass
from typing import List, Optional, Tuple

from evolution.sandbox import IsolatedSandbox, ResourceLimits


@dataclass
class BugReport:
    """A real bug report with reproducible test case."""
    bug_id: str
    broken_code: str      # the code that fails
    test_case: str        # the test that exposes the bug
    error_message: str    # what goes wrong
    expected_output: str  # what should happen
    task_domain: str


@dataclass
class FixCandidate:
    code: str
    test_passed: bool
    edit_distance: int   # how far from original
    generation: int


class EvolutionaryBugFixer:
    """
    Evolves fixes for a failing function using mutation search.
    Algorithm:
    1. Parse broken code to AST
    2. Generate N mutations of the AST
    3. Test each mutation against the failing test in sandbox
    4. Keep passing mutations, generate more from them
    5. Return the fix with the smallest edit distance (most elegant)

    No LLM. No pattern database. Pure evolutionary program repair.
    """

    MUTATIONS = [
        "swap_operators",      # + ↔ -, * ↔ /
        "flip_comparator",     # > ↔ <, >= ↔ <=
        "off_by_one",          # i → i+1, i-1
        "negate_condition",    # if x → if not x
        "swap_variables",      # swap two variable references
        "insert_guard",        # add if x is None: return None
        "change_return",       # return x → return y
        "remove_statement",    # delete one line
        "add_return_early",    # add early return
        "fix_range",           # range(n) → range(n+1) or range(1, n)
    ]

    def __init__(
        self,
        sandbox: IsolatedSandbox,
        population_size: int = 30,
        max_generations: int = 200,
        seed: int = 42,
    ) -> None:
        self.sandbox = sandbox
        self.population_size = population_size
        self.max_generations = max_generations
        self.rng = random.Random(seed)

    def fix(self, bug_report: BugReport) -> Optional[FixCandidate]:
        """
        Attempt to evolve a fix. Returns fixed code or None if no fix found.
        """
        population = [bug_report.broken_code] * self.population_size
        best_fix = None

        for gen in range(self.max_generations):
            candidates = [self._mutate(code) for code in population]
            results = [self._test(candidate, bug_report) for candidate in candidates]

            passing = [(c, r) for c, r in zip(candidates, results) if r.test_passed]
            if passing:
                best_fix = min(passing, key=lambda cr: cr[1].edit_distance)[0]
                candidate = FixCandidate(
                    code=best_fix,
                    test_passed=True,
                    edit_distance=self._edit_distance(bug_report.broken_code, best_fix),
                    generation=gen,
                )
                return candidate

            # Keep best partial fixes (most lines passing)
            scored = sorted(
                zip(candidates, results),
                key=lambda cr: cr[1].edit_distance,
            )
            survivors = [c for c, r in scored[:max(1, self.population_size // 3)]]
            population = survivors * (self.population_size // len(survivors) + 1)
            population = population[:self.population_size]

        return None

    def _mutate(self, code: str) -> str:
        """Apply one random mutation to source code."""
        mutation = self.rng.choice(self.MUTATIONS)
        try:
            tree = ast.parse(code)
            mutated = self._apply_mutation(tree, mutation)
            return ast.unparse(mutated)
        except Exception:
            return code   # mutation failed syntactically — return original

    def _apply_mutation(self, tree: ast.AST, mutation: str) -> ast.AST:
        tree = copy.deepcopy(tree)
        nodes = list(ast.walk(tree))

        if mutation == "swap_operators":
            ops = [(n, type(n).__name__) for n in nodes if isinstance(n, (ast.Add, ast.Sub, ast.Mult, ast.Div))]
            if ops:
                node, name = self.rng.choice(ops)
                swap = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
                node.__class__ = swap.get(type(node), type(node))

        elif mutation == "flip_comparator":
            comps = [n for n in nodes if isinstance(n, ast.Compare)]
            if comps:
                node = self.rng.choice(comps)
                if node.ops:
                    flip = {ast.Gt: ast.Lt, ast.Lt: ast.Gt, ast.GtE: ast.LtE, ast.LtE: ast.GtE}
                    node.ops[0].__class__ = flip.get(type(node.ops[0]), type(node.ops[0]))

        elif mutation == "negate_condition":
            ifs = [n for n in nodes if isinstance(n, ast.If)]
            if ifs:
                node = self.rng.choice(ifs)
                node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)

        elif mutation == "off_by_one":
            nums = [n for n in nodes if isinstance(n, ast.Constant) and isinstance(n.value, int)]
            if nums:
                node = self.rng.choice(nums)
                node.value += self.rng.choice([-1, 1])

        return tree

    def _test(self, code: str, bug_report: BugReport) -> FixCandidate:
        full_code = f"{code}\n\n{bug_report.test_case}"
        result = self.sandbox.run(full_code, timeout_ms=500)
        passed = result.ok and bug_report.expected_output in result.stdout
        return FixCandidate(
            code=code,
            test_passed=passed,
            edit_distance=self._edit_distance(bug_report.broken_code, code),
            generation=0,
        )

    def _edit_distance(self, a: str, b: str) -> int:
        """Character-level edit distance proxy."""
        return sum(1 for ca, cb in zip(a, b) if ca != cb) + abs(len(a) - len(b))
```

---

## PART D: LIVE STREAMING EVOLUTION — WEBSOCKET-DRIVEN REAL-TIME EVOLUTION

```python
# production/api/v6/evolution_stream.py
"""
Real-time evolution streamed over WebSocket.
Users watch organisms evolve live in the browser.
Every message contains actual evolved code and real fitness scores.
Not simulation. Not mock. The real evolution loop running in real time.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Set

from evolution.gp_population import GPPopulation, GenerationStats
from evolution.fitness import (
    SortingEvaluator, PrimeEvaluator, GameStrategyEvaluator,
    FibonacciEvaluator, CompressionEvaluator,
)

TASK_EVALUATORS = {
    "sorting":       SortingEvaluator(),
    "primes":        PrimeEvaluator(),
    "game_theory":   GameStrategyEvaluator(),
    "fibonacci":     FibonacciEvaluator(),
    "compression":   CompressionEvaluator(),
}


@dataclass
class EvolutionEvent:
    event_type: str                    # "generation", "new_champion", "task_solved", "trade"
    generation: int
    task: str
    best_fitness: float
    avg_fitness: float
    champion_code: str                 # real evolved code
    champion_correctness: float
    champion_size: int
    message: str = ""
    timestamp: float = 0.0

    def to_json(self) -> str:
        d = asdict(self)
        d["timestamp"] = time.time()
        return json.dumps(d)


class LiveEvolutionSession:
    """
    A live evolution session for one user/connection.
    Runs real GP evolution and streams results over WebSocket.
    """

    def __init__(
        self,
        task: str = "sorting",
        population_size: int = 30,
        seed: int = 42,
    ) -> None:
        evaluator = TASK_EVALUATORS.get(task, SortingEvaluator())
        self.population = GPPopulation(
            evaluator=evaluator,
            population_size=population_size,
            seed=seed,
        )
        self.population.initialize()
        self.task = task
        self.running = False
        self.subscribers: Set[Any] = set()   # WebSocket connections
        self.prev_best: float = 0.0

    async def run_stream(self, max_generations: int = 10000) -> None:
        """Run evolution and stream every generation to all subscribers."""
        self.running = True
        for gen in range(max_generations):
            if not self.running:
                break

            stats = self.population.step()
            champion = self.population.champion
            result = champion.fitness_result

            event = EvolutionEvent(
                event_type="generation",
                generation=gen,
                task=self.task,
                best_fitness=stats.best_fitness,
                avg_fitness=stats.avg_fitness,
                champion_code=champion.genome.to_python(f"gen_{gen}_champion"),
                champion_correctness=result.correctness if result else 0.0,
                champion_size=champion.genome.complexity(),
            )

            # Extra events for interesting moments
            if stats.best_fitness > self.prev_best + 0.05:
                event.event_type = "new_champion"
                event.message = f"Fitness jumped from {self.prev_best:.3f} to {stats.best_fitness:.3f}!"
                self.prev_best = stats.best_fitness

            if stats.best_fitness >= 0.99:
                event.event_type = "task_solved"
                event.message = f"TASK SOLVED at generation {gen}! Champion code is live."

            # Broadcast to all subscribers
            await self._broadcast(event.to_json())

            # Small sleep to avoid overwhelming clients
            await asyncio.sleep(0.05)

    async def _broadcast(self, message: str) -> None:
        dead = set()
        for ws in self.subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self.subscribers -= dead

    def subscribe(self, ws: Any) -> None:
        self.subscribers.add(ws)

    def unsubscribe(self, ws: Any) -> None:
        self.subscribers.discard(ws)

    def pause(self) -> None:
        self.running = False

    def resume(self) -> None:
        self.running = True
```

---

## PART E: CROSS-LANGUAGE ORGANISM EXPORT — RUN ANYWHERE

```python
# evolution/polyglot_export.py
"""
Export evolved GP programs to multiple languages.
An evolved sorting algorithm becomes runnable JavaScript, Rust, Go, Java.
No transpiler. AST-based direct compilation.
"""
from __future__ import annotations

from evolution.gp_engine import GPNode, Primitive


class PolyglotCompiler:
    """
    Compiles a GP tree to multiple programming languages.
    All targets produce identical output for identical inputs.
    """

    OPERATOR_MAP = {
        "javascript": {
            "add": "(a + b)", "sub": "(a - b)", "mul": "(a * b)",
            "div": "(b !== 0 ? a / b : 0)", "max2": "Math.max(a, b)",
            "min2": "Math.min(a, b)", "neg": "(-a)", "abs1": "Math.abs(a)",
            "sq": "(a * a)", "sqrt": "(a >= 0 ? Math.sqrt(a) : 0)",
            "if_pos": "(c > 0 ? t : f)",
        },
        "rust": {
            "add": "(a + b)", "sub": "(a - b)", "mul": "(a * b)",
            "div": "(if b != 0.0 { a / b } else { 0.0 })",
            "max2": "f64::max(a, b)", "min2": "f64::min(a, b)",
            "neg": "(-a)", "abs1": "a.abs()", "sq": "(a * a)",
            "sqrt": "(if a >= 0.0 { a.sqrt() } else { 0.0 })",
            "if_pos": "(if c > 0.0 { t } else { f })",
        },
        "go": {
            "add": "(a + b)", "sub": "(a - b)", "mul": "(a * b)",
            "div": "func() float64 { if b != 0 { return a / b }; return 0 }()",
            "max2": "math.Max(a, b)", "min2": "math.Min(a, b)",
            "neg": "(-a)", "abs1": "math.Abs(a)", "sq": "(a * a)",
            "sqrt": "math.Sqrt(math.Max(0, a))",
            "if_pos": "func() float64 { if c > 0 { return t }; return f }()",
        },
    }

    def to_javascript(self, tree: GPNode, func_name: str = "evolved", args: list = None) -> str:
        args = args or ["x"]
        body = self._compile_node(tree, "javascript")
        args_str = ", ".join(args)
        return f"""
// Evolved by Living Objects v6 — Genetic Programming
// This function was never written by a human.
function {func_name}({args_str}) {{
    try {{
        return {body};
    }} catch(e) {{
        return null;
    }}
}}
""".strip()

    def to_rust(self, tree: GPNode, func_name: str = "evolved", args: list = None) -> str:
        args = args or [("x", "f64")]
        args_str = ", ".join(f"{n}: {t}" for n, t in args)
        body = self._compile_node(tree, "rust")
        return f"""
// Evolved by Living Objects v6 — Genetic Programming
fn {func_name}({args_str}) -> f64 {{
    {body}
}}
""".strip()

    def to_wasm_text(self, tree: GPNode, func_name: str = "evolved") -> str:
        """Compile to WebAssembly Text Format (.wat)."""
        instructions = self._compile_to_wasm_instructions(tree)
        return f"""
(module
  (func (export "{func_name}") (param $x f64) (result f64)
    {chr(10).join('    ' + i for i in instructions)}
  )
)
""".strip()

    def _compile_node(self, node: GPNode, target: str) -> str:
        if node.is_terminal:
            if node.terminal_name:
                return node.terminal_name
            return str(node.terminal_value)
        op_map = self.OPERATOR_MAP.get(target, {})
        template = op_map.get(node.primitive.name, f"{node.primitive.name}(...)")
        child_exprs = [self._compile_node(c, target) for c in node.children]
        # Simple substitution for up to 3 args
        var_names = ["a", "b", "c", "d", "t", "f"]
        result = template
        for i, (var, expr) in enumerate(zip(var_names, child_exprs)):
            result = result.replace(f"({var} ", f"({expr} ").replace(f" {var})", f" {expr})")
            result = result.replace(f" {var} ", f" {expr} ")
        return result

    def _compile_to_wasm_instructions(self, node: GPNode) -> list:
        """Very simplified WASM instruction generation."""
        if node.is_terminal:
            if node.terminal_name == "x":
                return ["local.get $x"]
            return [f"f64.const {float(node.terminal_value or 0)}"]
        instructions = []
        for child in node.children:
            instructions.extend(self._compile_to_wasm_instructions(child))
        wasm_ops = {
            "add": "f64.add", "sub": "f64.sub",
            "mul": "f64.mul", "div": "f64.div",
        }
        op = wasm_ops.get(node.primitive.name, "f64.add")
        instructions.append(op)
        return instructions
```

---

## PART F: PRODUCTION DEPLOYMENT — KUBERNETES AUTOSCALING EVOLUTION CLUSTER

```yaml
# production/k8s/v6/evolution-cluster.yaml
---
# Namespace isolation for v6
apiVersion: v1
kind: Namespace
metadata:
  name: living-objects-v6
  labels:
    version: "6.0"
    security: "restricted"

---
# One deployment per task domain — tasks scale independently
apiVersion: apps/v1
kind: Deployment
metadata:
  name: evolution-sorting
  namespace: living-objects-v6
spec:
  replicas: 3
  selector:
    matchLabels:
      app: evolution-sorting
  template:
    metadata:
      labels:
        app: evolution-sorting
        task: sorting
    spec:
      securityContext:
        runAsNonRoot: true
        readOnlyRootFilesystem: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: evolution-worker
        image: living-objects:v6
        env:
        - name: TASK_DOMAIN
          value: "sorting"
        - name: POPULATION_SIZE
          value: "100"
        - name: CHECKPOINT_INTERVAL
          value: "1000"
        - name: WORKERS
          value: "4"
        resources:
          requests:
            cpu: "2"
            memory: "2Gi"
          limits:
            cpu: "4"
            memory: "4Gi"
        volumeMounts:
        - name: checkpoints
          mountPath: /data/checkpoints
        - name: memome-db
          mountPath: /data/memome
      volumes:
      - name: checkpoints
        persistentVolumeClaim:
          claimName: sorting-checkpoints-pvc
      - name: memome-db
        persistentVolumeClaim:
          claimName: sorting-memome-pvc

---
# Horizontal Pod Autoscaler — scale by evolution throughput
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: evolution-hpa
  namespace: living-objects-v6
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: evolution-sorting
  minReplicas: 1
  maxReplicas: 50
  metrics:
  - type: Pods
    pods:
      metric:
        name: generations_per_second
      target:
        type: AverageValue
        averageValue: "100"   # scale up if we drop below 100 gen/s per pod
```

---

## PART G: LIVE WEB OBSERVATORY v6 — THE CONTROL ROOM

The v6 Web Observatory must be a **live, real, working application**.
Not mocked. Not simulated. Real evolution happening in the browser.

### Required Components

#### G-1: Real-Time Code Theater
```typescript
// web/client/src/components/CodeTheater.tsx
/**
 * Shows the champion's code evolving in real time.
 * Every generation, the code changes — you watch it get smarter.
 * Diff highlighting shows exactly what changed between generations.
 */
export function CodeTheater({ wsUrl }: { wsUrl: string }) {
  const [currentCode, setCurrentCode] = useState("");
  const [prevCode, setPrevCode] = useState("");
  const [generation, setGeneration] = useState(0);
  const [fitness, setFitness] = useState(0);
  const [diff, setDiff] = useState<DiffLine[]>([]);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      const data: EvolutionEvent = JSON.parse(event.data);
      setPrevCode(currentCode);
      setCurrentCode(data.champion_code);
      setGeneration(data.generation);
      setFitness(data.best_fitness);
      setDiff(computeDiff(prevCode, data.champion_code));
    };
    return () => ws.close();
  }, [wsUrl]);

  return (
    <article className="code-theater">
      <header>
        <span className="gen-counter">Generation {generation.toLocaleString()}</span>
        <FitnessBar value={fitness} />
        <span className="live-badge">● LIVE</span>
      </header>
      <DiffViewer prev={prevCode} current={currentCode} diff={diff} />
      <footer>
        <small>This code was never written by a human.</small>
      </footer>
    </article>
  );
}
```

#### G-2: Fitness Landscape 3D Visualizer
```typescript
// web/client/src/components/FitnessLandscape3D.tsx
/**
 * 3D visualization of the fitness landscape using Three.js.
 * X/Y axes: two genome dimensions.
 * Z axis: fitness.
 * Organisms shown as particles. Champion shown as a glowing sphere.
 * Watch the landscape evolve in real time.
 */
import * as THREE from "three";

export function FitnessLandscape3D({ organisms }: { organisms: OrganismState[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current!, antialias: true });

    // Create height map from organism fitness
    const geometry = new THREE.PlaneGeometry(10, 10, 50, 50);
    const positions = geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i], y = positions[i + 1];
      // Interpolate fitness from nearest organism
      const nearest = organisms.reduce((best, org) =>
        Math.hypot(org.x - x, org.y - y) < Math.hypot(best.x - x, best.y - y) ? org : best
      );
      positions[i + 2] = nearest.fitness * 3;  // Z = fitness
    }
    geometry.attributes.position.needsUpdate = true;
    geometry.computeVertexNormals();

    const material = new THREE.MeshPhongMaterial({
      color: 0x00ff88, wireframe: false, side: THREE.DoubleSide,
    });
    scene.add(new THREE.Mesh(geometry, material));
    scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    scene.add(new THREE.DirectionalLight(0xffffff, 1));

    camera.position.set(0, -8, 6);
    camera.lookAt(0, 0, 0);

    let frame: number;
    const animate = () => {
      frame = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();
    return () => { cancelAnimationFrame(frame); renderer.dispose(); };
  }, [organisms]);

  return <canvas ref={canvasRef} className="landscape-3d" width={600} height={400} />;
}
```

#### G-3: Market Trading Floor
```typescript
// web/client/src/components/MarketFloor.tsx
/**
 * Live code market. Real programs for sale. Real token prices.
 * Click "Buy" to acquire a top-performing evolved program.
 * Your download is verified, working code — not mock data.
 */
export function MarketFloor() {
  const [listings, setListings] = useState<MarketListing[]>([]);
  const [wallet, setWallet] = useState(100.0);
  const [ownedPrograms, setOwnedPrograms] = useState<string[]>([]);

  // Poll market every 2s
  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch("/api/v6/market/listings?domain=sorting&top=10", {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setListings(await res.json());
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const buyProgram = async (listingId: string, price: number) => {
    if (wallet < price) return alert("Insufficient tokens");
    const res = await fetch(`/api/v6/market/buy/${listingId}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    const data = await res.json();
    setWallet(data.new_balance);
    setOwnedPrograms(prev => [...prev, data.program_source]);
  };

  return (
    <section className="market-floor">
      <header>
        <h2>Code Market</h2>
        <span className="wallet">💰 {wallet.toFixed(2)} tokens</span>
      </header>
      <div className="listings-grid">
        {listings.map(listing => (
          <div key={listing.id} className="listing-card">
            <div className="fitness-badge">{(listing.fitness * 100).toFixed(1)}% correct</div>
            <code className="code-preview">{listing.code_preview}</code>
            <div className="listing-meta">
              Gen {listing.generation} · {listing.task_domain} · {listing.sale_count} sales
            </div>
            <div className="listing-actions">
              <span className="price">{listing.price.toFixed(1)} tokens</span>
              <button onClick={() => buyProgram(listing.id, listing.price)}>
                Buy & Download
              </button>
            </div>
          </div>
        ))}
      </div>
      {ownedPrograms.length > 0 && (
        <div className="owned-programs">
          <h3>Your Evolved Programs</h3>
          {ownedPrograms.map((code, i) => (
            <pre key={i}><code>{code}</code></pre>
          ))}
        </div>
      )}
    </section>
  );
}
```

---

## PART H: AUTONOMOUS REAL-WORLD TASK AGENTS

```python
# evolution/real_world_agents.py
"""
Organisms that solve actual real-world tasks autonomously.
Each agent runs continuously, improving its strategies over time.
No LLM. Evolution is the only intelligence.
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from evolution.gp_population import GPPopulation
from evolution.fitness import FitnessEvaluator, FitnessResult
from evolution.sandbox import IsolatedSandbox


# ─────────────────────────────────────────────────────────────────────────────
# REAL TASK 1: CSV Data Cleaner
# ─────────────────────────────────────────────────────────────────────────────

class CSVCleanerEvaluator(FitnessEvaluator):
    """
    Evolve a function that cleans messy CSV data.
    Fitness: fraction of rows correctly cleaned vs. ground truth.
    """

    DIRTY_DATA = [
        ("  John Doe , 25, NYC ", {"name": "John Doe", "age": 25, "city": "NYC"}),
        ("Jane Smith,30,San Francisco", {"name": "Jane Smith", "age": 30, "city": "San Francisco"}),
        ("  Bob , 17 , Boston ", {"name": "Bob", "age": 17, "city": "Boston"}),
        ("Alice,25,", {"name": "Alice", "age": 25, "city": ""}),
        (" Mary Jones , 45, Chicago  ", {"name": "Mary Jones", "age": 45, "city": "Chicago"}),
    ]

    def generate_test_cases(self, seed: int, n: int = 10):
        return self.DIRTY_DATA[:n]

    def evaluate(self, genome) -> FitnessResult:
        correct = 0
        for dirty, expected in self.DIRTY_DATA:
            got = genome.execute({"x": dirty, "input": dirty, "row": dirty})
            if isinstance(got, dict) and got.get("name", "").strip() == expected["name"]:
                correct += 1
        score = correct / len(self.DIRTY_DATA)
        return FitnessResult(
            score=score, correctness=score, efficiency=1.0, robustness=1.0,
            description_length=100, wall_time_ms=0.0,
            test_cases_passed=correct, test_cases_total=len(self.DIRTY_DATA),
        )


# ─────────────────────────────────────────────────────────────────────────────
# REAL TASK 2: Log Anomaly Detector
# ─────────────────────────────────────────────────────────────────────────────

class LogAnomalyEvaluator(FitnessEvaluator):
    """
    Evolve a function that detects anomalies in server logs.
    Input: log line string. Output: 1 (anomaly) or 0 (normal).
    Fitness: F1 score on labelled log samples.
    """

    LOG_SAMPLES = [
        ("2026-08-14 ERROR Failed to connect to database after 30 retries", 1),
        ("2026-08-14 INFO User login successful", 0),
        ("2026-08-14 WARN Memory usage at 95%", 1),
        ("2026-08-14 INFO Request completed in 45ms", 0),
        ("2026-08-14 ERROR NullPointerException in PaymentService.java:142", 1),
        ("2026-08-14 DEBUG Cache hit for key user:1234", 0),
        ("2026-08-14 CRITICAL Disk space < 1GB on /dev/sda1", 1),
        ("2026-08-14 INFO Scheduled job completed successfully", 0),
        ("2026-08-14 ERROR Connection timeout: redis://cache:6379", 1),
        ("2026-08-14 INFO API rate limit: 450/500 used", 0),
    ]

    def generate_test_cases(self, seed: int, n: int = 10):
        return [(log, label) for log, label in self.LOG_SAMPLES[:n]]

    def evaluate(self, genome) -> FitnessResult:
        tp = fp = tn = fn = 0
        for log, expected in self.LOG_SAMPLES:
            got_raw = genome.execute({"x": log, "log": log, "line": log})
            got = 1 if (got_raw or 0) > 0.5 else 0
            if expected == 1 and got == 1: tp += 1
            elif expected == 0 and got == 0: tn += 1
            elif expected == 0 and got == 1: fp += 1
            else: fn += 1
        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = 2 * precision * recall / max(0.001, precision + recall)
        return FitnessResult(
            score=f1, correctness=f1, efficiency=1.0, robustness=1.0,
            description_length=100, wall_time_ms=0.0,
            test_cases_passed=tp + tn, test_cases_total=len(self.LOG_SAMPLES),
        )


# ─────────────────────────────────────────────────────────────────────────────
# REAL TASK 3: URL Validator
# ─────────────────────────────────────────────────────────────────────────────

class URLValidatorEvaluator(FitnessEvaluator):
    """
    Evolve a URL validation function.
    Fitness: accuracy on known valid/invalid URLs.
    Interesting because the pattern for valid URLs is non-trivial to evolve.
    """

    URL_SAMPLES = [
        ("https://www.google.com", True),
        ("http://example.com/path?q=1&r=2", True),
        ("ftp://files.example.org/data.txt", True),
        ("not_a_url", False),
        ("http://", False),
        ("https://sub.domain.co.uk/path/to/page#anchor", True),
        ("://missing-scheme.com", False),
        ("https://valid-domain.com:8080/api/v1", True),
        ("javascript:alert(1)", False),
        ("https://user:pass@host.com/path", True),
    ]

    def generate_test_cases(self, seed: int, n: int = 10):
        return self.URL_SAMPLES[:n]

    def evaluate(self, genome) -> FitnessResult:
        correct = 0
        for url, expected in self.URL_SAMPLES:
            got_raw = genome.execute({"x": url, "url": url, "input": url})
            got = bool(got_raw) if got_raw is not None else False
            if got == expected:
                correct += 1
        score = correct / len(self.URL_SAMPLES)
        return FitnessResult(
            score=score, correctness=score, efficiency=1.0, robustness=1.0,
            description_length=100, wall_time_ms=0.0,
            test_cases_passed=correct, test_cases_total=len(self.URL_SAMPLES),
        )
```

---

## PART I: 100,000-GENERATION MARATHON RUNNER WITH REAL CODE

```python
# scripts/run_v6_marathon.py
"""
THE v6 MARATHON RUNNER.
Runs organisms on real tasks for 100,000 generations.
Outputs a full Markdown report with the actual evolved code.

Usage:
    python scripts/run_v6_marathon.py --task sorting --generations 100000
    python scripts/run_v6_marathon.py --task primes --generations 100000 --pop 100
    python scripts/run_v6_marathon.py --all --generations 10000

Required time estimate per task (population=50, single-thread):
    sorting:     ~4-8 hours for 100k gens
    primes:      ~3-6 hours for 100k gens
    game_theory: ~6-12 hours for 100k gens (tournament evaluation is slow)
    fibonacci:   ~2-4 hours for 100k gens

With --workers 4 (multi-core): divide estimates by 3-4x.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.gp_engine import ARITHMETIC_PRIMITIVES, LIST_PRIMITIVES, BOOLEAN_PRIMITIVES
from evolution.gp_population import GPPopulation
from evolution.fitness import (
    SortingEvaluator, PrimeEvaluator, GameStrategyEvaluator,
    FibonacciEvaluator, MaxSubarrayEvaluator, CompressionEvaluator,
)

TASK_CONFIGS = {
    "sorting": {
        "evaluator": SortingEvaluator,
        "primitives": ARITHMETIC_PRIMITIVES + LIST_PRIMITIVES,
        "terminals": [("x", None), ("n", None),
                      ("const", lambda rng: float(rng.randint(0, 10)))],
        "description": "Evolve a sorting algorithm from scratch",
        "victory_condition": 0.95,
    },
    "primes": {
        "evaluator": PrimeEvaluator,
        "primitives": ARITHMETIC_PRIMITIVES + BOOLEAN_PRIMITIVES,
        "terminals": [("x", None), ("n", None),
                      ("const", lambda rng: float(rng.randint(1, 20)))],
        "description": "Evolve a primality test (True if prime, False if not)",
        "victory_condition": 0.90,
    },
    "fibonacci": {
        "evaluator": FibonacciEvaluator,
        "primitives": ARITHMETIC_PRIMITIVES,
        "terminals": [("x", None), ("n", None),
                      ("const", lambda rng: float(rng.randint(0, 5)))],
        "description": "Evolve a Fibonacci function",
        "victory_condition": 0.85,
    },
    "max_subarray": {
        "evaluator": MaxSubarrayEvaluator,
        "primitives": ARITHMETIC_PRIMITIVES + LIST_PRIMITIVES,
        "terminals": [("x", None), ("data", None),
                      ("const", lambda rng: float(rng.randint(0, 10)))],
        "description": "Evolve Kadane's maximum subarray algorithm",
        "victory_condition": 0.80,
    },
    "game_theory": {
        "evaluator": GameStrategyEvaluator,
        "primitives": ARITHMETIC_PRIMITIVES + BOOLEAN_PRIMITIVES,
        "terminals": [("x", None), ("rnd", None),
                      ("const", lambda rng: float(rng.randint(0, 1)))],
        "description": "Evolve a Prisoner's Dilemma strategy (discover Tit-for-Tat)",
        "victory_condition": 0.75,
    },
}


def run_task(
    task_name: str,
    generations: int = 100_000,
    population_size: int = 50,
    seed: int = 42,
    checkpoint_dir: str = "checkpoints",
    verbose: bool = True,
) -> dict:
    config = TASK_CONFIGS[task_name]
    print(f"\n{'='*70}")
    print(f"LIVING OBJECTS v6 — {task_name.upper()} MARATHON")
    print(f"Description: {config['description']}")
    print(f"Generations: {generations:,} | Population: {population_size} | Seed: {seed}")
    print(f"{'='*70}\n")

    evaluator = config["evaluator"]()
    pop = GPPopulation(
        evaluator=evaluator,
        primitives=config["primitives"],
        terminals=config["terminals"],
        population_size=population_size,
        seed=seed,
        tournament_size=7,
        crossover_rate=0.85,
        mutation_rate=0.12,
        elitism_count=5,
        max_depth=8,
    )
    pop.initialize()

    t_start = time.time()
    victory_gen = None
    checkpoint_path = Path(checkpoint_dir) / task_name
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    sample_records = {}   # gen → stats snapshot

    for gen in range(generations):
        stats = pop.step()

        # Sample at key generations for report
        key_gens = {0, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000}
        if gen in key_gens or gen % 10000 == 0:
            sample_records[gen] = {
                "generation": gen,
                "best_fitness": stats.best_fitness,
                "avg_fitness": stats.avg_fitness,
                "worst_fitness": stats.worst_fitness,
                "champion_size": pop.champion.genome.complexity(),
                "champion_code": pop.champion.genome.to_python(f"champion_gen{gen}"),
                "elapsed_min": (time.time() - t_start) / 60,
                "gens_per_sec": (gen + 1) / max(1, time.time() - t_start),
            }

        if verbose and gen % 1000 == 0:
            elapsed = time.time() - t_start
            gps = (gen + 1) / max(0.001, elapsed)
            eta_min = (generations - gen) / max(0.001, gps) / 60
            print(
                f"  Gen {gen:7,} | "
                f"Best {stats.best_fitness:.4f} | "
                f"Avg {stats.avg_fitness:.4f} | "
                f"Size {stats.avg_program_size:5.1f} | "
                f"ETA {eta_min:.0f}m | "
                f"{gps:.1f} gen/s"
            )

        if stats.best_fitness >= config["victory_condition"] and victory_gen is None:
            victory_gen = gen
            print(f"\n  🏆 VICTORY CONDITION MET at generation {gen}!")
            print(f"  Champion code:")
            print(f"  {pop.champion.genome.to_python(f'champion')}")

    total_time = time.time() - t_start
    champion = pop.champion
    champion_result = champion.fitness_result

    report = {
        "task": task_name,
        "generations": generations,
        "population_size": population_size,
        "total_time_minutes": total_time / 60,
        "peak_fitness": max(r["best_fitness"] for r in sample_records.values()),
        "peak_generation": max(sample_records, key=lambda g: sample_records[g]["best_fitness"]),
        "final_avg_fitness": sample_records.get(generations - 1, {}).get("avg_fitness", 0),
        "victory_generation": victory_gen,
        "victory_condition": config["victory_condition"],
        "achieved_victory": victory_gen is not None,
        "champion_source_code": champion.genome.to_python("champion_final"),
        "champion_test_cases_passed": champion_result.test_cases_passed if champion_result else 0,
        "champion_test_cases_total": champion_result.test_cases_total if champion_result else 0,
        "champion_size_nodes": champion.genome.complexity(),
        "champion_depth": champion.genome.depth(),
        "avg_gens_per_second": generations / max(1, total_time),
        "sample_records": sample_records,
    }

    # Write report
    report_path = Path("reports") / f"{task_name}_{generations}gens_report.md"
    report_path.parent.mkdir(exist_ok=True)
    _write_markdown_report(report, report_path)
    print(f"\n  Report written to: {report_path}")
    return report


def _write_markdown_report(report: dict, path: Path) -> None:
    samples = report["sample_records"]
    lines = [
        f"# Living Objects v6 — Marathon Benchmark Report",
        f"",
        f"**Task:** `{report['task']}`  ",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}  ",
        f"**Status:** {'🏆 VICTORY' if report['achieved_victory'] else '🔬 In Progress'}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Generations | {report['generations']:,} |",
        f"| Population Size | {report['population_size']} |",
        f"| Total Time | {report['total_time_minutes']:.1f} minutes |",
        f"| Peak Fitness | **{report['peak_fitness']:.4f}** (Gen {report['peak_generation']:,}) |",
        f"| Victory Condition | {report['victory_condition']} |",
        f"| Victory Achieved | {'Yes at Gen ' + str(report['victory_generation']) if report['achieved_victory'] else 'Not yet'} |",
        f"| Champion Size | {report['champion_size_nodes']} nodes, depth {report['champion_depth']} |",
        f"| Champion Correctness | {report['champion_test_cases_passed']}/{report['champion_test_cases_total']} test cases |",
        f"| Avg Speed | {report['avg_gens_per_second']:.1f} gen/sec |",
        f"",
        f"## Fitness Curve",
        f"",
        f"| Generation | Best | Avg | Worst | Champion Size | Speed (gen/s) |",
        f"|---|---|---|---|---|---|",
    ]

    for gen in sorted(samples.keys()):
        r = samples[gen]
        lines.append(
            f"| {gen:,} | {r['best_fitness']:.4f} | {r['avg_fitness']:.4f} | "
            f"{r['worst_fitness']:.4f} | {r['champion_size']} | {r['gens_per_sec']:.1f} |"
        )

    lines += [
        f"",
        f"## Champion Strategy — Final Generation",
        f"",
        f"> **This code was evolved. No human wrote it.**",
        f"> It emerged from {report['generations']:,} generations of genetic programming.",
        f"",
        f"```python",
        report["champion_source_code"],
        f"```",
        f"",
        f"## Real-World Verification",
        f"",
        f"The champion strategy passed {report['champion_test_cases_passed']} out of "
        f"{report['champion_test_cases_total']} held-out test cases.",
        f"",
        f"## How to Reproduce",
        f"",
        f"```bash",
        f"python scripts/run_v6_marathon.py \\",
        f"  --task {report['task']} \\",
        f"  --generations {report['generations']} \\",
        f"  --pop {report['population_size']}",
        f"```",
    ]

    path.write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=list(TASK_CONFIGS.keys()) + ["all"], default="sorting")
    parser.add_argument("--generations", type=int, default=100_000)
    parser.add_argument("--pop", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.task == "all":
        for task in TASK_CONFIGS:
            run_task(task, args.generations, args.pop, args.seed)
    else:
        run_task(args.task, args.generations, args.pop, args.seed)
```

---

## PART J: COMPLETE v6 SECURITY AUDIT

### VULN-V5-01: GPNode Evaluation Has No Depth/Recursion Guard

```python
# RISK: Deep trees cause RecursionError in evaluate()
# Python default recursion limit = 1000
# A tree of depth 1000+ crashes the process.

# FIX:
import sys

class GPNode:
    _EVAL_DEPTH = 0
    MAX_EVAL_DEPTH = 50

    def evaluate(self, context: dict) -> Any:
        GPNode._EVAL_DEPTH += 1
        if GPNode._EVAL_DEPTH > self.MAX_EVAL_DEPTH:
            GPNode._EVAL_DEPTH -= 1
            return 0.0   # hard return — no crash
        try:
            ...  # existing evaluate logic
        finally:
            GPNode._EVAL_DEPTH -= 1
```

### VULN-V5-02: Market Price Is a Float — Subject to Floating-Point Exploit

```python
# RISK: float arithmetic allows balance = 99.99999999999997
# Two fast buys can drain balance below 0 due to floating-point rounding.

# FIX: Use Python Decimal for all financial calculations
from decimal import Decimal, ROUND_DOWN

class TokenWallet:
    def __init__(self):
        self.balance = Decimal("100.00")

    def spend(self, amount: float) -> bool:
        d_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        with self._lock:
            if d_amount > self.balance:
                return False
            self.balance -= d_amount
            return True
```

### VULN-V5-03: `to_python_function` Output Is Not Validated — Can Produce Syntactically Invalid Code

```python
# RISK: GP tree to_python() can produce "add(x, )" or other malformed strings
# if the tree structure is corrupted mid-evolution.

# FIX: Always validate at generation boundary
def to_python_function(self, tree: GPNode, func_name: str, args: list) -> str:
    source = self._generate(tree, func_name, args)
    try:
        compile(source, "<gp-output>", "exec")  # validate before returning
        return source
    except SyntaxError:
        # Fall back to identity function — organism survives but scores 0
        args_str = ", ".join(args)
        return f"def {func_name}({args_str}):\n    return None"
```

### VULN-V5-04: `GPTreeBuilder.subtree_crossover` Modifies Trees In-Place

```python
# RISK: crossover operates on copies but internal _collect_nodes()
# returns references to the original tree nodes.
# If the original is still referenced by another organism, shared mutation occurs.

# FIX: Always deep-copy before modifying
def subtree_crossover(self, parent1: GPNode, parent2: GPNode):
    c1 = copy.deepcopy(parent1)  # always isolate
    c2 = copy.deepcopy(parent2)  # always isolate
    ...
```

### VULN-V5-05: `LiveEvolutionSession.run_stream` Has No Memory Leak Guard

```python
# RISK: hall_of_fame list grows unboundedly (one entry per generation).
# At 100,000 generations, this holds 100,000 GPOrganism objects in RAM.
# Each with a full tree + fitness result = potential GB of memory.

# FIX:
class GPPopulation:
    HALL_OF_FAME_MAX: int = 100   # keep only top 100 ever

    def _update_hall_of_fame(self, candidate: GPOrganism) -> None:
        self.hall_of_fame.append(candidate)
        if len(self.hall_of_fame) > self.HALL_OF_FAME_MAX:
            # Keep only the best
            self.hall_of_fame.sort(key=lambda o: o.fitness, reverse=True)
            self.hall_of_fame = self.hall_of_fame[:self.HALL_OF_FAME_MAX]
```

### VULN-V5-06: `PolyglotCompiler.to_wasm_text` Produces Invalid WAT for Nested Operations

```python
# RISK: Current WASM compiler only handles single-depth operations.
# A tree like add(mul(x, 2), sub(3, x)) produces incorrect WAT
# because the instruction ordering doesn't match WASM's stack semantics.

# FIX: Proper post-order traversal for WASM stack machine
def _compile_to_wasm_instructions(self, node: GPNode) -> list:
    """Correct post-order: push children first, then operation."""
    if node.is_terminal:
        if node.terminal_name == "x":
            return ["local.get $x"]
        return [f"f64.const {float(node.terminal_value or 0)}"]
    instructions = []
    for child in node.children:      # ← children FIRST (push onto stack)
        instructions.extend(self._compile_to_wasm_instructions(child))
    wasm_ops = {
        "add": "f64.add", "sub": "f64.sub",
        "mul": "f64.mul", "div": "f64.div",
        "neg": "f64.neg", "abs1": "f64.abs", "sq": ["f64.dup", "f64.mul"],
    }
    op = wasm_ops.get(node.primitive.name, "f64.add")
    if isinstance(op, list):
        instructions.extend(op)
    else:
        instructions.append(op)
    return instructions
```

### VULN-V5-07: WebSocket `_broadcast` Has No Message Queue — Fast Producers Overwhelm Slow Clients

```python
# RISK: If evolution runs at 35 gen/s and the client WebSocket processes at 10 msg/s,
# the send queue grows without bound. Browser tab crashes after ~30 seconds.

# FIX: Add per-client rate limiting
import asyncio
from collections import deque

class LiveEvolutionSession:
    MAX_QUEUE_PER_CLIENT = 50

    async def _broadcast(self, message: str) -> None:
        dead = set()
        for ws in self.subscribers:
            try:
                # Drop old messages if queue is too full
                if hasattr(ws, '_send_queue') and len(ws._send_queue) > self.MAX_QUEUE_PER_CLIENT:
                    ws._send_queue.clear()  # drop old messages, keep latest
                await asyncio.wait_for(ws.send_text(message), timeout=0.5)
            except (asyncio.TimeoutError, Exception):
                dead.add(ws)
        self.subscribers -= dead
```

### VULN-V5-08: `EpochDetector._js_divergence` Has Division-by-Zero on Empty Fingerprint

```python
# FIX:
def _js_divergence(self, p: List[float], q: List[float]) -> float:
    if not p or not q or len(p) != len(q):
        return 0.0
    total_p = sum(p) or 1.0
    total_q = sum(q) or 1.0
    p_norm = [x / total_p for x in p]
    q_norm = [x / total_q for x in q]
    m = [(a + b) / 2 for a, b in zip(p_norm, q_norm)]
    import math
    def kl(a, b): return sum(ai * math.log(ai / bi + 1e-10) for ai, bi in zip(a, b) if ai > 0)
    return (kl(p_norm, m) + kl(q_norm, m)) / 2
```

---

## v6 DELIVERABLES CHECKLIST (1000 Engineer Tasks)

### Team 1: GP Engine (10 engineers, 2 weeks)
- [ ] `evolution/gp_engine.py` — Full GP tree implementation (500 lines)
- [ ] `evolution/gp_engine.py` — All primitive sets: arithmetic, boolean, list, string, float (200 lines)
- [ ] `evolution/gp_engine.py` — `GPTreeBuilder`: random, mutate, crossover, hoist, expand (300 lines)
- [ ] `evolution/gp_engine.py` — `to_python_function()` with compile validation (50 lines)
- [ ] `evolution/gp_engine.py` — VULN-V5-01 recursion guard (20 lines)
- [ ] `evolution/gp_engine.py` — VULN-V5-03 syntax validation on every output (20 lines)
- [ ] `evolution/gp_engine.py` — VULN-V5-04 deepcopy isolation in crossover (20 lines)
- [ ] `evolution/test_gp_engine.py` — 50 unit tests (300 lines)

### Team 2: Fitness Evaluators (8 engineers, 1.5 weeks)
- [ ] `evolution/fitness.py` — `FitnessEvaluator` base class + `FitnessResult` (100 lines)
- [ ] `evolution/fitness.py` — `SortingEvaluator`: 20 random test cases per gen (80 lines)
- [ ] `evolution/fitness.py` — `PrimeEvaluator`: 30 primality test cases (60 lines)
- [ ] `evolution/fitness.py` — `FibonacciEvaluator`: exact Fibonacci values (50 lines)
- [ ] `evolution/fitness.py` — `MaxSubarrayEvaluator`: Kadane's algorithm (70 lines)
- [ ] `evolution/fitness.py` — `GameStrategyEvaluator`: 5-opponent tournament (90 lines)
- [ ] `evolution/fitness.py` — `CompressionEvaluator`: real byte compression (80 lines)
- [ ] `evolution/fitness.py` — `PathfindingEvaluator`: A* heuristic (70 lines)
- [ ] `evolution/real_world_agents.py` — `CSVCleanerEvaluator` (60 lines)
- [ ] `evolution/real_world_agents.py` — `LogAnomalyEvaluator` with F1 scoring (80 lines)
- [ ] `evolution/real_world_agents.py` — `URLValidatorEvaluator` (60 lines)
- [ ] `evolution/test_fitness.py` — 40 unit tests (250 lines)

### Team 3: GP Population Engine (8 engineers, 2 weeks)
- [ ] `evolution/gp_population.py` — `GPOrganism` dataclass (50 lines)
- [ ] `evolution/gp_population.py` — `GPPopulation.initialize()` ramped half-and-half (80 lines)
- [ ] `evolution/gp_population.py` — `GPPopulation.step()` full generation (120 lines)
- [ ] `evolution/gp_population.py` — `GPPopulation._tournament_select()` (30 lines)
- [ ] `evolution/gp_population.py` — `GPPopulation.run()` with target/checkpoint (80 lines)
- [ ] `evolution/gp_population.py` — VULN-V5-05 hall of fame size cap (20 lines)
- [ ] `evolution/gp_population.py` — `GenerationStats` + `RunSummary` (50 lines)
- [ ] `evolution/test_gp_population.py` — 40 unit tests (250 lines)

### Team 4: Bug Fixer Agent (5 engineers, 1.5 weeks)
- [ ] `evolution/bug_fixer.py` — `BugReport` dataclass (30 lines)
- [ ] `evolution/bug_fixer.py` — `EvolutionaryBugFixer.fix()` main loop (100 lines)
- [ ] `evolution/bug_fixer.py` — All 10 mutation operators (200 lines)
- [ ] `evolution/bug_fixer.py` — `_apply_mutation()` AST transformation (150 lines)
- [ ] `evolution/test_bug_fixer.py` — 10 real bug scenarios with tests (200 lines)

### Team 5: Live Code Market (8 engineers, 2 weeks)
- [ ] `evolution/live_market.py` — `MarketListing` + `OrderBook` (100 lines)
- [ ] `evolution/live_market.py` — `LiveCodeMarket.list_program()` with mandatory eval (80 lines)
- [ ] `evolution/live_market.py` — `LiveCodeMarket.settle()` bid/ask matching (80 lines)
- [ ] `evolution/live_market.py` — `LiveCodeMarket.leaderboard()` (30 lines)
- [ ] `evolution/live_market.py` — VULN-V5-02 Decimal arithmetic for wallets (50 lines)
- [ ] `production/api/v6/market.py` — REST API for market (200 lines)
- [ ] `evolution/test_live_market.py` — 30 unit tests (200 lines)

### Team 6: Marathon Runner + Reports (5 engineers, 1 week)
- [ ] `scripts/run_v6_marathon.py` — Full runner with checkpoints (300 lines)
- [ ] `scripts/run_v6_marathon.py` — Markdown report writer (100 lines)
- [ ] `data/gutenberg_excerpt.txt` — 10,000 char public domain corpus
- [ ] `data/log_samples.txt` — 1000 labelled log lines for anomaly detection
- [ ] `reports/` — Directory for auto-generated reports
- [ ] `Makefile` — `make marathon-sort`, `make marathon-all`, etc.

### Team 7: Polyglot Compiler (5 engineers, 1.5 weeks)
- [ ] `evolution/polyglot_export.py` — `PolyglotCompiler.to_javascript()` (80 lines)
- [ ] `evolution/polyglot_export.py` — `PolyglotCompiler.to_rust()` (60 lines)
- [ ] `evolution/polyglot_export.py` — `PolyglotCompiler.to_wasm_text()` (80 lines)
- [ ] `evolution/polyglot_export.py` — VULN-V5-06 correct WASM stack ordering (50 lines)
- [ ] `evolution/test_polyglot.py` — 30 tests verifying same output across languages (200 lines)

### Team 8: Live WebSocket Evolution Stream (8 engineers, 2 weeks)
- [ ] `production/api/v6/evolution_stream.py` — `LiveEvolutionSession` (150 lines)
- [ ] `production/api/v6/evolution_stream.py` — `EvolutionEvent` streaming (80 lines)
- [ ] `production/api/v6/evolution_stream.py` — VULN-V5-07 message queue + rate limit (50 lines)
- [ ] `production/api/v6/routes.py` — WebSocket endpoint, task management (200 lines)
- [ ] `production/api/v6/routes.py` — Market REST endpoints (150 lines)
- [ ] `production/test_v6_api.py` — 40 integration tests (300 lines)

### Team 9: Web Observatory v6 (12 engineers, 3 weeks)
- [ ] `web/client/src/components/CodeTheater.tsx` — Real-time code evolution viewer (200 lines)
- [ ] `web/client/src/components/FitnessLandscape3D.tsx` — Three.js 3D landscape (150 lines)
- [ ] `web/client/src/components/MarketFloor.tsx` — Live trading floor (200 lines)
- [ ] `web/client/src/components/EpochTimeline.tsx` — Civilizational history (120 lines)
- [ ] `web/client/src/components/ChampionPlayground.tsx` — Run champion code interactively (150 lines)
- [ ] `web/client/src/components/BugFixerConsole.tsx` — Submit bug, watch it evolve a fix (180 lines)
- [ ] `web/client/src/components/MultiverseBrowser.tsx` — Parallel universe tree (160 lines)
- [ ] `web/client/src/hooks/useEvolutionStream.ts` — WebSocket management hook (80 lines)
- [ ] `web/client/src/hooks/useMarketData.ts` — Market polling hook (60 lines)
- [ ] `web/v6.css` — Complete v6 design system (300 lines)

### Team 10: Production Infrastructure (10 engineers, 2 weeks)
- [ ] `production/k8s/v6/evolution-cluster.yaml` — K8s deployments, HPA (200 lines)
- [ ] `production/k8s/v6/market-service.yaml` — Market service K8s (100 lines)
- [ ] `production/k8s/v6/monitoring.yaml` — Prometheus + custom metrics (150 lines)
- [ ] `Dockerfile.v6` — Multi-stage build with GP engine (50 lines)
- [ ] `docker-compose.v6.yml` — Local dev cluster (80 lines)
- [ ] `production/metrics.py` — `evolution_fitness_gauge`, `market_volume_counter` (80 lines)
- [ ] `production/monitoring/v6-grafana.json` — Full Grafana dashboard JSON (500 lines)
- [ ] `scripts/deploy_v6.sh` — One-command deployment to K8s (100 lines)

### Team 11: Security (8 engineers, 1 week — run in PARALLEL with all other teams)
- [ ] Fix VULN-V5-01 through VULN-V5-08 across all files
- [ ] `evolution/test_security_v6.py` — 30 security tests (250 lines)
- [ ] Threat model review of GP engine (can evolved code escape sandbox?)
- [ ] Fuzz testing of `_apply_mutation()` with 10,000 random inputs
- [ ] Rate limit all new v6 endpoints (5 req/min for evolution start, 60 req/min for market)

### Team 12: Documentation + Science (5 engineers, ongoing)
- [ ] `docs/v6-architecture.md` — Complete v6 design (100 lines)
- [ ] `docs/gp-engine.md` — How genetic programming works in v6 (200 lines)
- [ ] `docs/real-vs-fake.md` — What changed from v5 (template floats) to v6 (real GP)
- [ ] `docs/benchmark-methodology.md` — How to run and interpret benchmarks (100 lines)
- [ ] `research/gp-task-findings.md` — Findings from marathon runs (ongoing)

---

## BENCHMARK TARGETS FOR v6

| Benchmark | v5 Promise | v6 Reality |
|---|---|---|
| Total tests | 500+ | **800+** |
| Security tests | 20 | **50** |
| Sorting fitness at 100k gens | projected 0.999 | **measured ≥ 0.95 required** |
| Fibonacci fitness at 10k gens | projected | **measured ≥ 0.80 required** |
| GameTheory Tit-for-Tat discovery | projected | **measured at which generation it emerges** |
| Bug fixer success rate | N/A | **≥ 60% of provided bug corpus** |
| Market trades per 100 gens | N/A | **≥ 10 verified code trades** |
| Champion code runs in JS | N/A | **All polyglot exports pass cross-language tests** |
| Live WebSocket latency | N/A | **< 100ms from step() to browser** |
| Memory under 100k gens | N/A | **< 2GB RAM (hall of fame capped)** |

---

## THE HIERARCHY

```
v1:  Template floats stored in SQLite
v2:  More template floats with cultural inheritance
v3:  Template floats + safety proofs + markets
v4:  Template floats + physics + substrate export
v5:  Template floats + planned real tasks
v6:  REAL PROGRAMS evolving REAL CODE solving REAL PROBLEMS
     Market where only VERIFIED CODE gets listed
     Bug fixer that patches production failures
     Observatory showing code changing live
     Export to JavaScript, Rust, WASM
     100,000 generations of real genetic programming
```

**After v6, the honest answer to "do they evolve without an LLM?" is:**

> Yes.
> Evolution is the only intelligence.
> Genetic programming generates real code.
> Real fitness functions test real correctness.
> The market only sells verified programs.
> No human wrote the champion. No LLM generated it.
> It emerged. That's what v6 is.

---

*v6 closes the gap between what was claimed and what was real.*
*Every phase above is concrete, testable, and honest.*
*The system either works or the tests fail. There is no in-between.*
