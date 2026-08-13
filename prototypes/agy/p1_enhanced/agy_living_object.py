"""
AGY Living Object — Extends Claw with AGY innovations
======================================================

Inherits 100% of ClawLivingObject (from claw/living_object.py) and adds:

  AGY-1  AnomalyRecord      – Structured anomaly with z-score, severity, resolution
  AGY-2  Adaptive EMA       – Surprise threshold self-tunes per environment  
  AGY-3  EVR Scheduler      – Only reasons when E[value of reasoning] > 0
  AGY-4  TieredEngine       – T0=local → T3=frontier, cost-tracked
  AGY-5  Auto-routing       – __init_subclass__ wraps ... methods automatically
  AGY-6  Z-score detection  – Rolling window z-score + relative deviation dual-gate
  AGY-7  Cross-restart      – Anomaly patterns replayed from episodic memory on load
  AGY-8  Schema Factory     – Lives in agy_schema_factory.py

Claw changes preserved:
  ✓ is_alive / is_dormant / idle_steps persisted in DB via update_lifecycle()
  ✓ Bound vs unbound method routing fix (_call_method)
  ✓ get_utility() formula
  ✓ learn() EMA adaptation

Usage:
    from prototypes.agy.p1_enhanced.agy_living_object import AGYLivingObject

    class Sensor(AGYLivingObject):
        def diagnose(self, symptom: str) -> str:
            \"\"\"Diagnose the symptom using memory context.\"\"\"
            ...          # ← auto-routed to LLM, no _call_method needed!

        def record(self, val: float) -> str:
            self.set_state('last', val)
            return f'Recorded {val}'

    sensor = Sensor.create(store, registry, engine, name='S1')
    sensor.diagnose('temp spike')  # direct call — LLM routed automatically
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import textwrap
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

# Import claw's runtime directly
from claw.living_object import ClawLivingObject
from living_objects.core.event_store import EventStore
from living_objects.core.reasoning import ReasoningEngine, MockReasoningEngine
from living_objects.security.capability import CapabilityRegistry


# ---------------------------------------------------------------------------
# AGY-1  AnomalyRecord
# ---------------------------------------------------------------------------

@dataclass
class AnomalyRecord:
    """
    Structured anomaly record.
    - Dual detection: z-score (Claw) + relative deviation (AGY)
    - Severity grading: low / medium / high / critical
    - Resolution tracking for utility/memory scoring
    """
    anomaly_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metric: str = ""
    observed: float = 0.0
    expected: float = 0.0
    z_score: float = 0.0
    deviation: float = 0.0
    severity: str = "medium"           # low | medium | high | critical
    cause: str = ""
    resolution: str = ""
    resolved: bool = False
    context: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def resolve(self, resolution: str) -> None:
        self.resolution = resolution
        self.resolved = True

    def to_dict(self) -> dict:
        return {
            "anomaly_id": self.anomaly_id, "metric": self.metric,
            "observed": self.observed, "expected": self.expected,
            "z_score": self.z_score, "deviation": self.deviation,
            "severity": self.severity, "cause": self.cause,
            "resolution": self.resolution, "resolved": self.resolved,
            "context": self.context, "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        st = "✓" if self.resolved else "!"
        return (f"[{st}] {self.metric}: obs={self.observed:.2f} "
                f"exp={self.expected:.2f} z={self.z_score:.2f} sev={self.severity}")


# ---------------------------------------------------------------------------
# AGY-3  EVR IntelligenceScheduler
# ---------------------------------------------------------------------------

class IntelligenceScheduler:
    """
    Expected-Value-of-Reasoning gate.
    EVR = P(improve|reason) × V(improve) × budget - C(reason)
    Reasons only when EVR > threshold (default 0).
    Critical anomalies always bypass the gate.
    """

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
# AGY-4  TieredReasoningEngine
# ---------------------------------------------------------------------------

class TieredReasoningEngine(ReasoningEngine):
    """
    Selects model tier based on task complexity.
      T0  local-8b        (complexity < 0.25)
      T1  gpt-4o-mini     (complexity < 0.50)
      T2  claude-sonnet   (complexity < 0.75)
      T3  o3-frontier     (everything else)
    Falls back to MockReasoningEngine in each tier (plug real LLM here).
    Tracks cost & per-tier call counts.
    """
    TIERS = {0: "local-8b", 1: "gpt-4o-mini", 2: "claude-3-5-sonnet", 3: "o3"}
    COSTS = {0: 0.000, 1: 0.001, 2: 0.005, 3: 0.015}

    def __init__(self, mock: Optional[MockReasoningEngine] = None):
        self._mock = mock or MockReasoningEngine()
        self.calls: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self.total_cost: float = 0.0

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
        }


# ---------------------------------------------------------------------------
# AGY Living Object — extends ClawLivingObject
# ---------------------------------------------------------------------------

class AGYLivingObject(ClawLivingObject):
    """
    AGY-enhanced LivingObject.

    Everything Claw has, plus:
      - AnomalyRecord with z-score dual-gate detection
      - Adaptive EMA surprise threshold (self-tuning)
      - EVR-gated IntelligenceScheduler
      - TieredReasoningEngine cost tracking
      - __init_subclass__ auto-routes ... methods (no _call_method needed)
      - Cross-restart anomaly pattern learning
    """

    # -----------------------------------------------------------------
    # AGY-5  __init_subclass__ — auto-route ... methods
    # -----------------------------------------------------------------

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        At class definition time: scan every method in the subclass.
        If its body is `...`, `pass`, or only a docstring → wrap it so
        a direct call auto-routes to _execute_intelligent.
        No more obj._call_method(obj.diagnose, ...) boilerplate.
        """
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
                        def wrapper(self: AGYLivingObject, *a: Any, **kw: Any) -> Any:
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

        # AGY-2  Adaptive EMA surprise (replaces claw's fixed threshold)
        self._ema_alpha: float = 0.3
        self._surprise_ema: float = 0.0
        # Claw's surprise_threshold is inherited; we override tuning logic

        # AGY-3  EVR scheduler
        self.scheduler = IntelligenceScheduler()

        # AGY-4  budget tracking
        self.daily_budget: float = 1.0
        self.reasoning_spend: float = 0.0

        # AGY-1  Anomaly tracking
        self._anomaly_history: List[AnomalyRecord] = []
        self._anomaly_patterns: Dict[str, int] = {}     # metric → recurrence count
        self._metric_window: Dict[str, List[float]] = {}  # rolling window for z-score

    # -----------------------------------------------------------------
    # AGY-2  Adaptive EMA surprise (overrides claw's fixed _compute_surprise)
    # -----------------------------------------------------------------

    def _update_ema(self, surprise: float) -> None:
        """Update EMA and auto-tune threshold based on recent history."""
        self._surprise_ema = self._ema_alpha * surprise + (1 - self._ema_alpha) * self._surprise_ema
        self.surprise_history.append(surprise)
        # Tune threshold every 10 observations
        if len(self.surprise_history) >= 10:
            recent = sum(self.surprise_history[-10:]) / 10
            if recent < 0.05:
                self.surprise_threshold = max(0.08, self.surprise_threshold * 0.92)
            elif recent > 0.5:
                self.surprise_threshold = min(0.5, self.surprise_threshold * 1.08)

    def observe(self, observation: dict) -> dict:
        """Extended observe: EMA surprise + EVR gate + Claw wakeup logic."""
        result = super().observe(observation)
        surprise = result["surprise"]
        self._update_ema(surprise)

        last_sev = self._anomaly_history[-1].severity if self._anomaly_history else None
        should, evr = self.scheduler.should_reason(
            surprise=surprise,
            is_dormant=self.is_dormant,
            anomaly_severity=last_sev,
            budget=self.daily_budget,
        )
        result["ema"] = self._surprise_ema
        result["evr"] = evr
        result["should_reason"] = should
        return result

    # -----------------------------------------------------------------
    # AGY-1 + AGY-6  Z-score + relative deviation anomaly detection
    # -----------------------------------------------------------------

    def detect_anomaly(
        self,
        metric: str,
        observed: float,
        expected: float,
        context: Optional[dict] = None,
        z_threshold: float = 2.0,
        window: int = 20,
    ) -> Optional[AnomalyRecord]:
        """
        Dual-gate anomaly detection:
          1. Z-score on rolling window (Claw contribution)
          2. Relative deviation from expected (AGY contribution)
        Either gate can trigger. Severity graded into low/medium/high/critical.
        Records in episodic memory for AGY-7 cross-restart pattern learning.
        """
        history = self._metric_window.setdefault(metric, [])
        history.append(observed)
        if len(history) > window:
            history.pop(0)

        # Z-score
        z = 0.0
        if len(history) >= 3:
            mean = sum(history) / len(history)
            var = sum((x - mean) ** 2 for x in history) / len(history)
            std = math.sqrt(var) if var > 0 else 0.0
            z = abs(observed - mean) / std if std > 0 else 0.0

        # Relative deviation
        deviation = abs(observed - expected)
        relative = deviation / max(abs(expected), 0.01)

        # Neither gate triggered → no anomaly
        if z < z_threshold and relative < 0.10:
            return None

        # Severity grading
        if relative < 0.25 and z < 3.0:
            severity = "low"
        elif relative < 0.50 and z < 4.0:
            severity = "medium"
        elif relative < 1.00 and z < 6.0:
            severity = "high"
        else:
            severity = "critical"

        # Cross-restart counter
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

        # AGY-7: persist pattern to episodic memory
        if self.memory:
            self.memory.record_episode(
                observation=(f"Anomaly on '{metric}': obs={observed:.3f} "
                             f"exp={expected:.3f} z={z:.2f} sev={severity} "
                             f"recurrence=#{recurrence}"),
                action="anomaly_detected",
                result=f"severity={severity}",
                outcome="detected",
                lesson=f"'{metric}' has anomalised {recurrence}× (z={z:.2f}).",
            )

        self.emit("anomaly", {
            "id": rec.anomaly_id, "metric": metric,
            "observed": observed, "expected": expected,
            "z": z, "severity": severity, "recurrence": recurrence,
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
                self.emit("anomaly_resolved", {
                    "id": anomaly_id, "metric": rec.metric, "resolution": resolution,
                })
                return True
        return False

    def anomaly_summary(self) -> str:
        if not self._anomaly_history:
            return "No anomalies detected."
        lines = [f"Anomaly History ({len(self._anomaly_history)} total):"]
        for r in self._anomaly_history[-5:]:
            lines.append(f"  {r}")
        if self._anomaly_patterns:
            lines.append("Recurring metrics: " + ", ".join(
                f"{m}(×{c})" for m, c in
                sorted(self._anomaly_patterns.items(), key=lambda x: -x[1])
            ))
        return "\n".join(lines)

    # -----------------------------------------------------------------
    # AGY-7  Cross-restart pattern learning
    # -----------------------------------------------------------------

    def load_anomaly_patterns_from_memory(self) -> int:
        """Replay anomaly patterns from episodic memory after restart."""
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
    # Override _execute_intelligent to use EVR budget tracking
    # -----------------------------------------------------------------

    def _execute_intelligent(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        """Route to reasoning engine with budget tracking."""
        context: dict = {
            "object_id": self.object_id, "name": self.name, "state": self._state,
            "memory_summary": self.memory.summarize_experiences() if self.memory else "",
            "anomaly_count": len(self._anomaly_history),
            "recent_anomalies": [a.to_dict() for a in self._anomaly_history[-3:]],
            "args": list(args), "kwargs": kwargs,
            "budget_remaining": self.daily_budget,
        }
        result = super()._execute_intelligent(method, *args, **kwargs)
        self.reasoning_spend += 0.005
        self.daily_budget = max(0.0, self.daily_budget - 0.04)
        return result

    # -----------------------------------------------------------------
    # Lifecycle overrides: save / load include anomaly patterns
    # -----------------------------------------------------------------

    def save(self) -> None:
        """Persist state, lifecycle, AND anomaly pattern count in memory."""
        super().save()
        # Patterns already persisted via episodic memory in detect_anomaly()

    @classmethod
    def load(
        cls,
        object_id: str,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: ReasoningEngine,
    ) -> Optional[AGYLivingObject]:
        """Rehydrate object and replay anomaly patterns from memory (AGY-7)."""
        obj = super().load(object_id, store, registry, reasoning)
        if obj is None:
            return None
        # AGY-7: replay patterns
        loaded = obj.load_anomaly_patterns_from_memory()
        if loaded:
            obj.emit("agy_patterns_loaded", {"patterns": obj._anomaly_patterns})
        return obj

    # -----------------------------------------------------------------
    # Improved utility (extends Claw's get_utility)
    # -----------------------------------------------------------------

    def get_utility(self) -> float:
        """
        Extended Claw utility + AGY anomaly resolution bonus.
          0.35 recency (inverse idle)
          0.25 action activity
          0.20 prediction quality
          0.10 anomaly resolution rate
          0.10 remaining budget
        """
        base = super().get_utility()   # Claw's 0.4/0.3/0.3 blend
        total_a = max(1, len(self._anomaly_history))
        resolved_a = sum(1 for a in self._anomaly_history if a.resolved)
        resolution_bonus = (resolved_a / total_a) * 0.1
        budget_bonus = self.daily_budget * 0.1
        return round(min(1.0, base * 0.8 + resolution_bonus + budget_bonus), 3)

    def __repr__(self) -> str:
        dormant = " [dormant]" if self.is_dormant else ""
        return (
            f"<AGYLivingObject '{self.name}' id={self.object_id[:8]}... "
            f"v={self._state_version} anomalies={len(self._anomaly_history)}"
            f"{dormant}>"
        )
