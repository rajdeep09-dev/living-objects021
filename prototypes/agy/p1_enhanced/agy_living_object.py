"""
AGY Living Object v2 — Full Agnes AI integration + persistent budget + object discovery
========================================================================================

Improvements over v1 (based on Claw's Agnes AI commit 6ac4a9e):

  AGY-9   Agnes AI integration — TieredAgnesEngine used by default when AGNES_API_KEY set
  AGY-10  Persistent reasoning budget — daily_budget + reasoning_spend saved to DB
  AGY-11  Object Discovery Registry — find peers by type / tag / goal
  AGY-12  YAML schema round-trip — ObjectSchema ↔ YAML (used by AGYSchemaFactory)
  AGY-13  Prompt engineering — richer system prompt with object identity context
  AGY-14  Reasoning result caching — identical prompts reuse last result (1-call cache)
  AGY-15  Improved utility — incorporates budget health + memory richness

Inherits all of AGY v1:
  AGY-1  AnomalyRecord (z-score + severity)
  AGY-2  Adaptive EMA surprise threshold
  AGY-3  EVR IntelligenceScheduler
  AGY-4  TieredReasoningEngine
  AGY-5  __init_subclass__ auto-routing
  AGY-6  Dual-gate anomaly detection
  AGY-7  Cross-restart anomaly pattern learning
  AGY-8  Schema Factory (see agy_schema_factory.py)
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import os
import textwrap
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from claw.living_object import ClawLivingObject
from living_objects.core.event_store import EventStore
from living_objects.core.reasoning import ReasoningEngine, MockReasoningEngine
from living_objects.security.capability import CapabilityRegistry


# ---------------------------------------------------------------------------
# AGY-1  AnomalyRecord
# ---------------------------------------------------------------------------

@dataclass
class AnomalyRecord:
    anomaly_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metric: str = ""
    observed: float = 0.0
    expected: float = 0.0
    z_score: float = 0.0
    deviation: float = 0.0
    severity: str = "medium"
    cause: str = ""
    resolution: str = ""
    resolved: bool = False
    context: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def resolve(self, resolution: str) -> None:
        self.resolution = resolution
        self.resolved = True

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def __repr__(self) -> str:
        st = "✓" if self.resolved else "!"
        return (f"[{st}] {self.metric}: obs={self.observed:.2f} "
                f"exp={self.expected:.2f} z={self.z_score:.2f} sev={self.severity}")


# ---------------------------------------------------------------------------
# AGY-3  EVR IntelligenceScheduler
# ---------------------------------------------------------------------------

class IntelligenceScheduler:
    def __init__(self, base_cost: float = 0.05, evr_threshold: float = 0.0):
        self.base_cost = base_cost
        self.evr_threshold = evr_threshold

    def compute_evr(self, surprise: float, anomaly_severity: Optional[str],
                    goal_urgency: float = 0.5, budget: float = 1.0) -> float:
        boost = {"low": 0.0, "medium": 0.2, "high": 0.5, "critical": 1.0}.get(
            anomaly_severity or "low", 0.0)
        p_improve = min(1.0, surprise + boost)
        value = p_improve * goal_urgency * budget
        cost = self.base_cost * (1.0 - budget * 0.5)
        return value - cost

    def should_reason(self, surprise: float, is_dormant: bool = False,
                      anomaly_severity: Optional[str] = None,
                      budget: float = 1.0, goal_urgency: float = 0.5) -> Tuple[bool, float]:
        if anomaly_severity == "critical":
            return True, 999.0
        if is_dormant and surprise < 0.3:
            return False, -1.0
        evr = self.compute_evr(surprise, anomaly_severity, goal_urgency, budget)
        return evr > self.evr_threshold, evr


# ---------------------------------------------------------------------------
# AGY-4  TieredReasoningEngine (now wraps Agnes when available)
# ---------------------------------------------------------------------------

class TieredReasoningEngine(ReasoningEngine):
    """
    Selects model tier based on task complexity.
    Uses Agnes AI engines when available (AGNES_API_KEY set), else Mock.
    """
    TIERS = {0: "local-8b", 1: "gpt-4o-mini", 2: "claude-3-5-sonnet", 3: "o3"}
    COSTS = {0: 0.000, 1: 0.001, 2: 0.005, 3: 0.015}

    def __init__(self, mock: Optional[MockReasoningEngine] = None,
                 use_agnes: bool = True):
        self._mock = mock or MockReasoningEngine()
        self._agnes_engine = None
        self.calls: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self.total_cost: float = 0.0
        # Auto-detect Agnes AI
        if use_agnes and os.environ.get("AGNES_API_KEY"):
            try:
                from prototypes.agy.p1_enhanced.agnes_reasoning_engine import TieredAgnesEngine
                self._agnes_engine = TieredAgnesEngine(
                    api_key=os.environ.get("AGNES_API_KEY"), fallback=True
                )
            except ImportError:
                pass

    def _complexity(self, prompt: str, ctx: dict) -> float:
        raw = (
            len(prompt) / 2000
            + len(json.dumps(ctx.get("state", {}))) / 500
            + len(ctx.get("memory_summary", "")) / 1000
            + ctx.get("anomaly_count", 0) * 0.1
        )
        return min(1.0, raw)

    def _tier(self, complexity: float, budget: float) -> int:
        if complexity < 0.25 or budget < 0.1:
            return 0
        if complexity < 0.50:
            return 1
        if complexity < 0.75:
            return 2
        return 3

    def reason(self, prompt: str, schema: dict, context: dict) -> dict:
        # Delegate to Agnes tiered engine if available
        if self._agnes_engine:
            r = self._agnes_engine.reason(prompt, schema, context)
            # Sync cost tracking
            c = self._complexity(prompt, context)
            t = self._tier(c, context.get("budget_remaining", 1.0))
            self.calls[t] = self.calls.get(t, 0) + 1
            self.total_cost += self.COSTS.get(t, 0.001)
            return r

        c = self._complexity(prompt, context)
        t = self._tier(c, context.get("budget_remaining", 1.0))
        self.calls[t] += 1
        self.total_cost += self.COSTS[t]
        r = self._mock.reason(prompt, schema, context)
        r["tier"] = self.TIERS[t]
        r["complexity"] = c
        return r

    def stats(self) -> dict:
        return {
            "total": sum(self.calls.values()),
            "by_tier": {self.TIERS[k]: v for k, v in self.calls.items()},
            "cost_usd": round(self.total_cost, 6),
            "backend": "agnes" if self._agnes_engine else "mock",
        }


# ---------------------------------------------------------------------------
# AGY-11  Object Discovery Registry
# ---------------------------------------------------------------------------

class ObjectDiscoveryRegistry:
    """
    In-memory registry for finding peers by type, tag, or goal.
    Objects self-register on create/load; deregister on retire.
    """
    _global: Dict[str, dict] = {}   # object_id → metadata

    @classmethod
    def register(cls, object_id: str, name: str,
                 type_name: str = "", tags: List[str] = None,
                 goals: List[str] = None) -> None:
        cls._global[object_id] = {
            "name": name, "type_name": type_name,
            "tags": tags or [], "goals": goals or [],
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def deregister(cls, object_id: str) -> None:
        cls._global.pop(object_id, None)

    @classmethod
    def find_by_type(cls, type_name: str) -> List[str]:
        return [oid for oid, m in cls._global.items()
                if m["type_name"] == type_name]

    @classmethod
    def find_by_tag(cls, tag: str) -> List[str]:
        return [oid for oid, m in cls._global.items()
                if tag in m["tags"]]

    @classmethod
    def find_by_goal(cls, goal: str) -> List[str]:
        return [oid for oid, m in cls._global.items()
                if any(goal in g for g in m["goals"])]

    @classmethod
    def all(cls) -> Dict[str, dict]:
        return dict(cls._global)

    @classmethod
    def clear(cls) -> None:
        cls._global.clear()


# ---------------------------------------------------------------------------
# AGY Living Object v2
# ---------------------------------------------------------------------------

class AGYLivingObject(ClawLivingObject):
    """
    AGY-enhanced LivingObject v2 — full Agnes AI integration.
    Extends Claw with all AGY innovations (v1) + v2 improvements.
    """

    # -----------------------------------------------------------------
    # AGY-5  __init_subclass__ auto-route ... methods
    # -----------------------------------------------------------------

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for attr_name, method in list(cls.__dict__.items()):
            if not callable(method) or attr_name.startswith("_"):
                continue
            try:
                src = textwrap.dedent(inspect.getsource(method))
                tree = ast.parse(src)
                func_def = tree.body[0]
                if not isinstance(func_def, ast.FunctionDef):
                    continue
                non_doc = [
                    s for s in func_def.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant)
                            and isinstance(s.value.value, str))
                ]
                is_intelligent = (
                    len(non_doc) == 0
                    or (len(non_doc) == 1 and (
                        (isinstance(non_doc[0], ast.Expr)
                         and isinstance(non_doc[0].value, ast.Constant)
                         and non_doc[0].value.value is ...)
                        or isinstance(non_doc[0], ast.Pass)
                        or isinstance(non_doc[0], ast.Raise)
                    ))
                )
                if is_intelligent:
                    def _wrap(orig: Callable) -> Callable:
                        def wrapper(self: "AGYLivingObject", *a: Any, **kw: Any) -> Any:
                            return self._execute_intelligent(orig, *a, **kw)
                        wrapper.__name__ = orig.__name__
                        wrapper.__doc__ = orig.__doc__
                        wrapper._agy_intelligent = True
                        return wrapper
                    setattr(cls, attr_name, _wrap(method))
            except (OSError, TypeError, SyntaxError, IndentationError):
                pass

    # -----------------------------------------------------------------
    # __init__
    # -----------------------------------------------------------------

    def __init__(self, object_id: Optional[str] = None, name: str = "Unnamed"):
        super().__init__(object_id=object_id, name=name)

        # AGY-2  Adaptive EMA
        self._ema_alpha: float = 0.3
        self._surprise_ema: float = 0.0

        # AGY-3  EVR scheduler
        self.scheduler = IntelligenceScheduler()

        # AGY-10  Persistent budget (loaded/saved to DB)
        self.daily_budget: float = 1.0
        self.reasoning_spend: float = 0.0

        # AGY-1  Anomaly tracking
        self._anomaly_history: List[AnomalyRecord] = []
        self._anomaly_patterns: Dict[str, int] = {}
        self._metric_window: Dict[str, List[float]] = {}

        # AGY-14  Result cache (prompt_hash → result)
        self._reasoning_cache: Dict[str, Any] = {}
        self._cache_hits: int = 0

        # Discovery metadata
        self._type_name: str = self.__class__.__name__.lower()
        self._tags: List[str] = []
        self._goals: List[str] = []

    # -----------------------------------------------------------------
    # AGY-9 + AGY-13  Enhanced _execute_intelligent with Agnes + prompt
    # -----------------------------------------------------------------

    def _execute_intelligent(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        """Route to reasoning engine with: Agnes AI, richer prompt, caching, budget tracking."""
        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or "No instructions provided."

        mem_summary = self.memory.summarize_experiences() if self.memory else ""
        context: dict = {
            "object_id": self.object_id,
            "name": self.name,
            "type": self._type_name,
            "goals": self._goals,
            "state": self._state,
            "memory_summary": mem_summary,
            "anomaly_count": len(self._anomaly_history),
            "recent_anomalies": [a.to_dict() for a in self._anomaly_history[-3:]],
            "anomaly_patterns": self._anomaly_patterns,
            "args": list(args),
            "kwargs": kwargs,
            "budget_remaining": self.daily_budget,
            "dormant": self.is_dormant,
            "version": self._state_version,
        }

        # AGY-13  Richer system prompt with identity context
        prompt = (
            f"You are the intelligent method `{method.__name__}` of a Living Object.\n\n"
            f"Object identity:\n"
            f"  name={self.name}  id={self.object_id[:12]}  type={self._type_name}\n"
            f"  goals={self._goals or 'none'}  version={self._state_version}\n\n"
            f"Method instructions:\n{doc}\n\n"
            f"Current state:\n{json.dumps(self._state, indent=2, default=str)}\n\n"
            f"Recent memory:\n{mem_summary[:800]}\n\n"
            f"Anomaly patterns: {json.dumps(self._anomaly_patterns)}\n"
            f"Recent anomalies: {json.dumps([a.to_dict() for a in self._anomaly_history[-2:]], default=str)}\n\n"
            f"Method args: {json.dumps(list(args), default=str)}\n"
            f"Method kwargs: {json.dumps(kwargs, default=str)}\n\n"
            f"Respond with JSON: {{\"result\": <value>, \"confidence\": <0-1>, \"reasoning\": <str>}}"
        )

        # AGY-14  Cache check
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        if prompt_hash in self._reasoning_cache:
            self._cache_hits += 1
            cached = self._reasoning_cache[prompt_hash]
            self.emit("reasoning_cached", {
                "method": method.__name__, "hash": prompt_hash, "hits": self._cache_hits
            })
            return cached

        return_annotation = sig.return_annotation
        return_type = "str"
        if return_annotation == bool: return_type = "bool"
        elif return_annotation == int: return_type = "int"
        elif return_annotation == list: return_type = "list"
        elif return_annotation == dict: return_type = "dict"
        elif return_annotation == float: return_type = "float"
        schema = {"return_type": return_type}

        if self._reasoning:
            raw = self._reasoning.reason(prompt, schema, context)
        else:
            raw = {"result": None, "confidence": 0.0, "reasoning": "No engine."}

        result_val = raw.get("result")

        # Cache the result
        self._reasoning_cache[prompt_hash] = result_val

        # AGY-10  Track spend
        cost = raw.get("cost", 0.005)
        self.reasoning_spend += cost
        self.daily_budget = max(0.0, self.daily_budget - 0.04)

        self.emit("reasoning", {
            "method": method.__name__,
            "prompt_hash": prompt_hash,
            "result": result_val,
            "confidence": raw.get("confidence"),
            "reasoning": raw.get("reasoning", "")[:200],
            "tier": raw.get("tier", "unknown"),
            "budget_left": self.daily_budget,
        })
        return result_val

    # -----------------------------------------------------------------
    # AGY-2  Adaptive EMA observe (overrides Claw)
    # -----------------------------------------------------------------

    def _update_ema(self, surprise: float) -> None:
        self._surprise_ema = self._ema_alpha * surprise + (1 - self._ema_alpha) * self._surprise_ema
        self.surprise_history.append(surprise)
        if len(self.surprise_history) >= 10:
            recent = sum(self.surprise_history[-10:]) / 10
            if recent < 0.05:
                self.surprise_threshold = max(0.08, self.surprise_threshold * 0.92)
            elif recent > 0.5:
                self.surprise_threshold = min(0.5, self.surprise_threshold * 1.08)

    def observe(self, observation: dict) -> dict:
        result = super().observe(observation)
        surprise = result["surprise"]
        self._update_ema(surprise)
        last_sev = self._anomaly_history[-1].severity if self._anomaly_history else None
        should, evr = self.scheduler.should_reason(
            surprise=surprise, is_dormant=self.is_dormant,
            anomaly_severity=last_sev, budget=self.daily_budget,
        )
        result["ema"] = self._surprise_ema
        result["evr"] = evr
        result["should_reason"] = should
        return result

    # -----------------------------------------------------------------
    # AGY-6  Z-score dual-gate anomaly detection
    # -----------------------------------------------------------------

    def detect_anomaly(self, metric: str, observed: float, expected: float,
                       context: Optional[dict] = None, z_threshold: float = 2.0,
                       window: int = 20) -> Optional[AnomalyRecord]:
        history = self._metric_window.setdefault(metric, [])
        history.append(observed)
        if len(history) > window:
            history.pop(0)

        z = 0.0
        if len(history) >= 3:
            mean = sum(history) / len(history)
            var = sum((x - mean) ** 2 for x in history) / len(history)
            std = math.sqrt(var) if var > 0 else 0.0
            z = abs(observed - mean) / std if std > 0 else 0.0

        deviation = abs(observed - expected)
        relative = deviation / max(abs(expected), 0.01)

        if z < z_threshold and relative < 0.10:
            return None

        if relative < 0.25 and z < 3.0:
            severity = "low"
        elif relative < 0.50 and z < 4.0:
            severity = "medium"
        elif relative < 1.00 and z < 6.0:
            severity = "high"
        else:
            severity = "critical"

        self._anomaly_patterns[metric] = self._anomaly_patterns.get(metric, 0) + 1
        recurrence = self._anomaly_patterns[metric]

        rec = AnomalyRecord(
            metric=metric, observed=observed, expected=expected,
            z_score=round(z, 3), deviation=round(deviation, 4),
            severity=severity,
            cause=f"Recurrence #{recurrence}" if recurrence > 1 else "",
            context=context or {},
        )
        self._anomaly_history.append(rec)

        if self.memory:
            self.memory.record_episode(
                observation=(f"Anomaly on '{metric}': obs={observed:.3f} "
                             f"exp={expected:.3f} z={z:.2f} sev={severity} "
                             f"recurrence=#{recurrence}"),
                action="anomaly_detected",
                result=f"severity={severity}",
                outcome="detected",
                lesson=f"'{metric}' anomalised {recurrence}× (z={z:.2f}).",
            )

        self.emit("anomaly", {
            "id": rec.anomaly_id, "metric": metric, "observed": observed,
            "expected": expected, "z": z, "severity": severity, "recurrence": recurrence,
        })
        return rec

    def resolve_anomaly(self, anomaly_id: str, resolution: str) -> bool:
        for rec in self._anomaly_history:
            if rec.anomaly_id == anomaly_id:
                rec.resolve(resolution)
                if self.memory:
                    self.memory.record_fact(
                        f"Anomaly {anomaly_id} ('{rec.metric}') resolved: {resolution}",
                        confidence=0.95, source="resolution",
                    )
                self.emit("anomaly_resolved", {"id": anomaly_id, "resolution": resolution})
                return True
        return False

    def anomaly_summary(self) -> str:
        if not self._anomaly_history:
            return "No anomalies detected."
        lines = [f"Anomaly History ({len(self._anomaly_history)} total):"]
        for r in self._anomaly_history[-5:]:
            lines.append(f"  {r}")
        if self._anomaly_patterns:
            lines.append("Recurring: " + ", ".join(
                f"{m}(×{c})" for m, c in
                sorted(self._anomaly_patterns.items(), key=lambda x: -x[1])
            ))
        return "\n".join(lines)

    # -----------------------------------------------------------------
    # AGY-7  Cross-restart pattern learning
    # -----------------------------------------------------------------

    def load_anomaly_patterns_from_memory(self) -> int:
        if not self.memory:
            return 0
        count = 0
        for ep in self.memory.recall_episodes(limit=500):
            try:
                content = json.loads(ep["content"])
                obs = content.get("observation", "")
                if "Anomaly on '" in obs and "recurrence=#" in obs:
                    metric = obs.split("Anomaly on '")[1].split("'")[0].strip()
                    rec_str = obs.split("recurrence=#")[1].split(" ")[0].strip()
                    recurrence = int(rec_str)
                    self._anomaly_patterns[metric] = max(
                        self._anomaly_patterns.get(metric, 0), recurrence
                    )
                    count += 1
            except Exception:
                pass
        return count

    # -----------------------------------------------------------------
    # AGY-10  Persistent budget — save/load overrides
    # -----------------------------------------------------------------

    def save(self) -> None:
        """Persist state, lifecycle, AND budget to memory (as a semantic fact)."""
        super().save()
        # Persist budget as a fact so it survives restarts
        if self.memory:
            # Remove old budget fact, add fresh one
            budget_key = f"__budget__{self.object_id}"
            try:
                self.memory.record_fact(
                    f"daily_budget={self.daily_budget:.4f} "
                    f"reasoning_spend={self.reasoning_spend:.4f} "
                    f"cache_hits={self._cache_hits}",
                    confidence=1.0, source="__budget__"
                )
            except Exception:
                pass

    def _load_budget_from_memory(self) -> None:
        """Restore daily_budget and reasoning_spend from the LAST saved fact."""
        if not self.memory:
            return
        # get_memories returns newest first (ORDER BY timestamp DESC), so use first match
        for fact in self.memory.recall_facts(limit=100):
            try:
                content = json.loads(fact["content"])
                text = content.get("fact", "")
                if text.startswith("daily_budget="):
                    parts = dict(p.split("=") for p in text.split())
                    self.daily_budget = float(parts.get("daily_budget", 1.0))
                    self.reasoning_spend = float(parts.get("reasoning_spend", 0.0))
                    self._cache_hits = int(parts.get("cache_hits", 0))
                    return
            except Exception:
                pass

    # -----------------------------------------------------------------
    # AGY-11  Discovery: register on create/load, deregister on retire
    # -----------------------------------------------------------------

    def _register(self) -> None:
        ObjectDiscoveryRegistry.register(
            self.object_id, self.name,
            type_name=self._type_name,
            tags=self._tags,
            goals=self._goals,
        )

    def retire(self) -> None:
        ObjectDiscoveryRegistry.deregister(self.object_id)
        super().retire()

    def find_peers_by_type(self, type_name: str) -> List[str]:
        """Find all registered objects of the given type."""
        return [oid for oid in ObjectDiscoveryRegistry.find_by_type(type_name)
                if oid != self.object_id]

    def find_peers_by_goal(self, goal: str) -> List[str]:
        return [oid for oid in ObjectDiscoveryRegistry.find_by_goal(goal)
                if oid != self.object_id]

    def find_peers_by_tag(self, tag: str) -> List[str]:
        return [oid for oid in ObjectDiscoveryRegistry.find_by_tag(tag)
                if oid != self.object_id]

    # -----------------------------------------------------------------
    # Improved utility (AGY-15)
    # -----------------------------------------------------------------

    def get_utility(self) -> float:
        base = super().get_utility()
        total_a = max(1, len(self._anomaly_history))
        resolved_a = sum(1 for a in self._anomaly_history if a.resolved)
        resolution_bonus = (resolved_a / total_a) * 0.10
        budget_health = self.daily_budget * 0.05
        mem_richness = min(0.05, len(self.memory.recall_episodes(limit=5)) * 0.01
                          if self.memory else 0)
        cache_bonus = min(0.05, self._cache_hits * 0.005)
        return round(min(1.0, base * 0.80 + resolution_bonus + budget_health
                         + mem_richness + cache_bonus), 3)

    # -----------------------------------------------------------------
    # Factory Methods
    # -----------------------------------------------------------------

    @classmethod
    def create(cls, store: EventStore, registry: CapabilityRegistry,
               reasoning: ReasoningEngine, object_id: Optional[str] = None,
               name: str = "Unnamed", initial_state: Optional[dict] = None,
               tags: Optional[List[str]] = None,
               goals: Optional[List[str]] = None) -> "AGYLivingObject":
        obj: AGYLivingObject = super().create(
            store=store, registry=registry, reasoning=reasoning,
            object_id=object_id, name=name, initial_state=initial_state,
        )
        obj._tags = tags or []
        obj._goals = goals or []
        obj._type_name = cls.__name__.lower()
        obj._register()
        return obj

    @classmethod
    def load(cls, object_id: str, store: EventStore,
             registry: CapabilityRegistry,
             reasoning: ReasoningEngine) -> Optional["AGYLivingObject"]:
        # AGY-10: Pre-load budget BEFORE super().load() calls save()
        # (which would overwrite with default values)
        temp_obj = AGYLivingObject(object_id=object_id)
        temp_obj.attach(store, registry, reasoning)
        temp_obj._load_budget_from_memory()
        budget = temp_obj.daily_budget
        spend = temp_obj.reasoning_spend
        cache_hits = temp_obj._cache_hits
        del temp_obj

        obj: Optional[AGYLivingObject] = super().load(object_id, store, registry, reasoning)
        if obj is None:
            return None
        obj._type_name = cls.__name__.lower()
        # Restore budget (saved before super().load() overwrote it)
        obj.daily_budget = budget
        obj.reasoning_spend = spend
        obj._cache_hits = cache_hits
        # AGY-7: replay anomaly patterns
        loaded = obj.load_anomaly_patterns_from_memory()
        if loaded:
            obj.emit("agy_patterns_loaded", {"patterns": obj._anomaly_patterns})
        # AGY-11: re-register
        obj._register()
        return obj

    def __repr__(self) -> str:
        dormant = " [dormant]" if self.is_dormant else ""
        return (
            f"<AGYLivingObject '{self.name}' id={self.object_id[:8]}... "
            f"v={self._state_version} anomalies={len(self._anomaly_history)} "
            f"budget={self.daily_budget:.2f} cache={self._cache_hits}×"
            f"{dormant}>"
        )
