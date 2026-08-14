"""BEAST v2 cultural, embodiment, ancestry, language, and energy primitives."""
from __future__ import annotations

import ast
import io
import json
import math
import random
import subprocess
import urllib.parse
import urllib.request
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from evolution.beast_v2 import DefenseLayer
from evolution.lamarckian import LamarckianOrganism, Strategy


class FederatedMemome:
    """Small deterministic federated store with fitness-weighted anti-entropy."""

    _registry: set["FederatedMemome"] = set()

    def __init__(self, node_id: str, *, node_count_hint: Optional[int] = None) -> None:
        if not node_id:
            raise ValueError("node_id is required")
        self.node_id = node_id
        self.node_count_hint = node_count_hint
        self._strategies: dict[str, Strategy] = {}
        self._seen_nodes: set[str] = {node_id}
        self._registry.add(self)

    def close(self) -> None:
        self._registry.discard(self)

    def contribute(self, strategy: Strategy) -> Strategy:
        current = self._strategies.get(strategy.strategy_id)
        if current is None or strategy.effectiveness > current.effectiveness:
            self._strategies[strategy.strategy_id] = strategy
        return self._strategies[strategy.strategy_id]

    def publish(
        self,
        *,
        name: str,
        source_code: str,
        descriptor: str,
        effectiveness: float,
        author_id: str,
        generation: int,
        parent_ids: Sequence[str] = (),
    ) -> Strategy:
        import hashlib
        from datetime import datetime, timezone

        raw = f"{name}\0{descriptor}\0{source_code}".encode()
        strategy = Strategy(
            strategy_id=hashlib.sha256(raw).hexdigest()[:20],
            name=name,
            source_code=source_code,
            descriptor=descriptor,
            effectiveness=float(effectiveness),
            author_id=author_id,
            generation=int(generation),
            parent_ids=tuple(parent_ids),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return self.contribute(strategy)

    def strategies(self) -> list[Strategy]:
        return sorted(self._strategies.values(), key=lambda item: (-item.effectiveness, item.strategy_id))

    def get(self, strategy_id: str) -> Optional[Strategy]:
        return self._strategies.get(strategy_id)

    def gossip(self, peer: "FederatedMemome") -> int:
        """Exchange missing records and resolve conflicts by effectiveness."""
        if peer is self:
            return 0
        before = len(self._strategies) + len(peer._strategies)
        for strategy in tuple(self._strategies.values()):
            peer.contribute(strategy)
        for strategy in tuple(peer._strategies.values()):
            self.contribute(strategy)
        self._seen_nodes.add(peer.node_id)
        peer._seen_nodes.add(self.node_id)
        self._seen_nodes.update(peer._seen_nodes)
        peer._seen_nodes.update(self._seen_nodes)
        after = len(self._strategies) + len(peer._strategies)
        return max(0, after - before)

    def influence_score(self, strategy_name: str) -> float:
        node_ids = set(self._seen_nodes) or {self.node_id}
        node_by_id = {node.node_id: node for node in self._registry}
        total = self.node_count_hint or len(node_ids) or 1
        present = sum(
            1
            for node_id in node_ids
            if node_id in node_by_id
            and any(item.name == strategy_name for item in node_by_id[node_id]._strategies_for_influence())
        )
        return min(1.0, present / total)

    def _strategies_for_influence(self) -> Iterable[Strategy]:
        return self._strategies.values()

    def lineage_graph(self) -> Any:
        """Return a networkx graph when available, otherwise a serializable graph fallback."""
        try:
            import networkx as nx  # type: ignore

            graph = nx.DiGraph()
            for strategy in self._strategies.values():
                graph.add_node(strategy.strategy_id, name=strategy.name, generation=strategy.generation)
                for parent_id in strategy.parent_ids:
                    graph.add_edge(parent_id, strategy.strategy_id)
            return graph
        except ImportError:
            return SimpleLineageGraph.from_strategies(self._strategies.values())

    def to_dot(self) -> str:
        graph = self.lineage_graph()
        if hasattr(graph, "nodes") and hasattr(graph, "edges"):
            nodes = graph.nodes(data=True) if callable(graph.nodes) else graph.nodes
            edges = graph.edges() if callable(graph.edges) else graph.edges
            lines = ["digraph memome {"]
            for node, data in nodes:
                label = data.get("name", node) if isinstance(data, Mapping) else str(node)
                lines.append(f'  "{node}" [label="{label}"];')
            for source, target in edges:
                lines.append(f'  "{source}" -> "{target}";')
            lines.append("}")
            return "\n".join(lines)
        return graph.to_dot()


@dataclass
class SimpleLineageGraph:
    node_data: dict[str, dict[str, Any]] = field(default_factory=dict)
    edge_data: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_strategies(cls, strategies: Iterable[Strategy]) -> "SimpleLineageGraph":
        graph = cls()
        for strategy in strategies:
            graph.node_data[strategy.strategy_id] = {"name": strategy.name, "generation": strategy.generation}
            graph.edge_data.extend((parent, strategy.strategy_id) for parent in strategy.parent_ids)
        return graph

    def nodes(self, data: bool = False) -> Any:
        return list(self.node_data.items()) if data else list(self.node_data)

    def edges(self) -> list[tuple[str, str]]:
        return list(self.edge_data)

    def to_dot(self) -> str:
        lines = ["digraph memome {"]
        for node, data in self.node_data.items():
            lines.append(f'  "{node}" [label="{data.get("name", node)}"];')
        lines.extend(f'  "{source}" -> "{target}";' for source, target in self.edge_data)
        lines.append("}")
        return "\n".join(lines)


class EmbodiedOrganism(LamarckianOrganism):
    """A Lamarckian organism with an allowlisted tool registry."""

    TOOL_REGISTRY: dict[str, tuple[Callable[..., Any], str]] = {}

    def __init__(self, organism_id: str = "embodied", *, allowed_root: Optional[Path] = None) -> None:
        self.object_id = organism_id
        self.name = organism_id
        self.fitness = 0.0
        self.generation = 0
        self.dead = False
        self.allowed_root = (allowed_root or Path.cwd()).resolve()
        self.tool_history: list[dict[str, Any]] = []
        self.defense = DefenseLayer(0.5)

    @classmethod
    def register_tool(cls, name: str, fn: Callable[..., Any], description: str) -> None:
        if not name or not callable(fn):
            raise ValueError("tool name and callable are required")
        cls.TOOL_REGISTRY[name] = (fn, description)

    def use_tool(self, tool_name: str, **kwargs: Any) -> Any:
        if tool_name not in self.TOOL_REGISTRY:
            raise KeyError(f"tool is not registered: {tool_name}")
        fn, description = self.TOOL_REGISTRY[tool_name]
        result = fn(**kwargs)
        serialized = str(result)
        self.tool_history.append({"tool": tool_name, "description": description, "result": serialized[:2000]})
        self.fitness = min(1.0, self.fitness + (0.03 if result is not None else 0.0))
        return result

    def evolve_tool_strategy(self, tool_name: str) -> str:
        if tool_name not in self.TOOL_REGISTRY:
            raise KeyError(f"tool is not registered: {tool_name}")
        return f"call {tool_name} with validated arguments; record result; retry once on transient failure"

    def file_read(self, path: str) -> str:
        candidate = (self.allowed_root / path).resolve()
        if self.allowed_root not in candidate.parents and candidate != self.allowed_root:
            raise PermissionError("path is outside the organism allowlist")
        return candidate.read_text(encoding="utf-8")


def _safe_python_exec(code: str) -> str:
    result = DefenseLayer().validate_strategy(code)
    if not result.accepted:
        raise ValueError(f"python rejected: {result.reason}")
    tree = ast.parse(code)
    allowed_builtins = {
        "range": range,
        "len": len,
        "sum": sum,
        "int": int,
        "str": str,
        "list": list,
        "print": print,
    }
    namespace: dict[str, Any] = {"__builtins__": allowed_builtins}
    output = io.StringIO()
    with redirect_stdout(output):
        exec(compile(tree, "<organism-python>", "exec"), namespace, namespace)
    return output.getvalue().strip()


def _safe_shell_cmd(cmd: str) -> str:
    parts = cmd.strip().split()
    if not parts or parts[0] not in {"echo", "printf", "pwd"}:
        raise PermissionError("shell command is not allowlisted")
    completed = subprocess.run(parts, capture_output=True, text=True, timeout=2, check=True)
    return completed.stdout[:2000].strip()


def _safe_http_get(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only http(s) URLs are supported")
    allowed_hosts = {"example.com", "httpbin.org", "localhost", "127.0.0.1"}
    if parsed.hostname not in allowed_hosts:
        raise PermissionError("HTTP host is not allowlisted")
    request = urllib.request.Request(url, headers={"User-Agent": "living-objects-research/2"})
    with urllib.request.urlopen(request, timeout=2) as response:  # noqa: S310 - allowlisted host
        return response.read(2000).decode("utf-8", errors="replace")


def register_builtin_tools() -> None:
    EmbodiedOrganism.register_tool("python_exec", _safe_python_exec, "execute a restricted Python expression")
    EmbodiedOrganism.register_tool("file_read", lambda path: EmbodiedOrganism("tool").file_read(path), "read an allowlisted file")
    EmbodiedOrganism.register_tool("http_get", _safe_http_get, "fetch text from an allowlisted HTTP host")
    EmbodiedOrganism.register_tool("shell_cmd", _safe_shell_cmd, "run an allowlisted shell command")


@dataclass(frozen=True)
class GenerationSnapshot:
    generation: int
    organisms: tuple[Mapping[str, Any], ...]


class AncestryCredit:
    """Attribute champion strategy value to ancestors that actually mattered."""

    def attribute(
        self,
        champion: Any,
        memome: Any,
        population_history: Sequence[GenerationSnapshot],
    ) -> dict[str, float]:
        champion_ids = set(getattr(champion, "learned_strategies", {}).keys())
        scores: dict[str, float] = {strategy_id: 0.0 for strategy_id in champion_ids}
        current_generation = max((snapshot.generation for snapshot in population_history), default=0)
        for strategy_id in list(scores):
            strategy = memome.get(strategy_id) if hasattr(memome, "get") else None
            if strategy is None:
                continue
            descendants = 0
            span = max(1, current_generation - int(strategy.generation) + 1)
            for snapshot in population_history:
                for organism in snapshot.organisms:
                    used = set(organism.get("strategy_ids", organism.get("learned_strategies", [])))
                    if strategy_id in used:
                        descendants += 1
            if strategy.author_id != getattr(champion, "object_id", None):
                scores[strategy_id] = descendants * span * max(0.0, strategy.effectiveness)
        return dict(sorted(scores.items(), key=lambda item: (-item[1], item[0])))


@dataclass(frozen=True)
class DSLGenome:
    """A compact, evolving language for strategy intent."""

    vocabulary: tuple[str, ...] = ("fit", "coop", "defect", "high", "else")
    grammar_rules: tuple[str, ...] = ("conditional",)
    semantics: tuple[tuple[str, str], ...] = (
        ("fit", "fitness"),
        ("coop", "cooperate"),
        ("defect", "defect"),
        ("high", "high"),
        ("else", "otherwise"),
    )

    def express(self, strategy_intent: Mapping[str, Any]) -> str:
        condition = str(strategy_intent.get("condition", "high"))
        action = str(strategy_intent.get("action", "coop"))
        fallback = str(strategy_intent.get("fallback", "defect"))
        allowed = set(self.vocabulary)
        for token in (condition, action, fallback):
            if token not in allowed:
                raise ValueError(f"token is not in vocabulary: {token}")
        return f"WHEN({condition}) -> {action}; ELSE -> {fallback}"

    def parse(self, dsl_source: str) -> dict[str, str]:
        normalized = dsl_source.replace(" ", "")
        if not normalized.startswith("WHEN(") or ")- >" in normalized:
            normalized = dsl_source.replace(" ", "")
        try:
            left, right = normalized.split(";ELSE->")
            condition, action = left.removeprefix("WHEN(").split(")->")
            fallback = right
        except ValueError as exc:
            raise ValueError("invalid DSL; expected WHEN(condition) -> action; ELSE -> fallback") from exc
        tokens = set(self.vocabulary)
        if not {condition, action, fallback}.issubset(tokens):
            raise ValueError("DSL uses a token outside this genome vocabulary")
        return {"condition": condition, "action": action, "fallback": fallback}

    def mutate(self, rng: random.Random) -> "DSLGenome":
        vocabulary = list(self.vocabulary)
        index = len(vocabulary)
        vocabulary.append(f"compound_{index}")
        semantics = list(self.semantics)
        semantics.append((vocabulary[-1], f"compose:{vocabulary[index % len(vocabulary)]}"))
        rules = list(self.grammar_rules)
        if len(vocabulary) > 8 and "compound" not in rules:
            rules.append("compound")
        return DSLGenome(tuple(vocabulary), tuple(rules), tuple(semantics))

    def crossover(self, other: "DSLGenome") -> "DSLGenome":
        merged_vocab = tuple(dict.fromkeys(self.vocabulary + other.vocabulary))
        merged_rules = tuple(dict.fromkeys(self.grammar_rules + other.grammar_rules))
        merged_semantics = tuple(dict.fromkeys(self.semantics + other.semantics))
        return DSLGenome(merged_vocab, merged_rules, merged_semantics)


@dataclass(frozen=True)
class ThermodynamicScore:
    result_quality: float
    operations: int
    memory_allocated: int
    efficiency: float
    affordable: bool


class EnergyBudget:
    def __init__(self, initial: float = 100.0) -> None:
        self.initial = float(initial)
        self.remaining = float(initial)
        self.costs = {"strategy_call": 1.0, "memome_query": 0.5, "mutation": 2.0}
        self.income_per_fitness_point = 5.0

    def can_afford(self, action: str) -> bool:
        return self.remaining >= self.costs.get(action, 0.0)

    def spend(self, action: str) -> None:
        cost = self.costs.get(action)
        if cost is None:
            raise KeyError(action)
        if self.remaining < cost:
            raise RuntimeError("energy budget exhausted")
        self.remaining -= cost

    def earn(self, fitness: float) -> None:
        self.remaining += max(0.0, float(fitness)) * self.income_per_fitness_point


class ThermodynamicFitness:
    def measure(self, organism: Any, task: Callable[..., Any], budget: int = 1000) -> ThermodynamicScore:
        """Measure quality per operation; tasks may return quality or a 3-tuple."""
        try:
            raw = task(organism)
        except TypeError:
            raw = task()
        if isinstance(raw, tuple):
            quality = float(raw[0])
            operations = int(raw[1])
            memory = int(raw[2]) if len(raw) > 2 else 0
        else:
            quality, operations, memory = float(raw), 1, 0
        operations = max(1, operations)
        affordable = operations <= budget
        efficiency = max(0.0, quality) / operations if affordable else 0.0
        if hasattr(organism, "energy"):
            organism.energy = max(0.0, float(organism.energy) - operations / max(1, budget) * 10.0)
            if organism.energy <= 0.0:
                setattr(organism, "dead", True)
        return ThermodynamicScore(max(0.0, quality), operations, max(0, memory), efficiency, affordable)
