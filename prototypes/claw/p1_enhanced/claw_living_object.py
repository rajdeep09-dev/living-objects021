"""
Claw Runtime — Enhanced LivingObject with dormancy, surprise, communication,
intelligent method routing, and full persistence.

Merged from: Mimo (dormancy/surprise/comms) + Kimi (audit/event sourcing) + Claw enhancements
"""
import json
import hashlib
import uuid
import inspect
import textwrap
import ast
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass

from living_objects.core.event_store import EventStore, Event
from living_objects.memory.manager import MemoryManager
from living_objects.security.capability import CapabilityRegistry
from living_objects.core.reasoning import ReasoningEngine, MockReasoningEngine

DEFAULT_DORMANCY_THRESHOLD = 5
DEFAULT_SURPRISE_THRESHOLD = 0.15


class ClawLivingObject:
    """
    Full-featured LivingObject with:
    - Persistence (SQLite event sourcing)
    - Smart memory (episodic/semantic/procedural)
    - Dormancy lifecycle (auto-sleep, wake-on-stimulus)
    - Surprise-driven cognition
    - Peer-to-peer communication
    - Intelligent method routing (AST-based)
    - Capability-based security
    """

    _store = None
    _registry = None
    _reasoning = None

    def __init__(self, object_id: Optional[str] = None, name: str = "Unnamed"):
        # Identity
        self.object_id = object_id or str(uuid.uuid4())
        self.name = name
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.identity_signature = hashlib.sha256(self.object_id.encode()).hexdigest()[:64]

        # State
        self._state: Dict[str, Any] = {}
        self._state_version = 0

        # Memory
        self.memory: Optional[MemoryManager] = None

        # Runtime (attached after rehydration)
        self._store: Optional[EventStore] = None
        self._registry: Optional[CapabilityRegistry] = None
        self._reasoning: Optional[ReasoningEngine] = None
        self._last_event_id: Optional[str] = None

        # Lifecycle (Mimo-enhanced)
        self.is_alive = True
        self.is_dormant = False
        self.idle_steps = 0
        self.surprise_score = 0.0
        self.surprise_threshold = DEFAULT_SURPRISE_THRESHOLD
        self.surprise_history: List[float] = []
        self.expected_state: Dict[str, Any] = {}
        self.reasoning_count = 0
        self.total_tokens_used = 0
        self.actions_taken = 0
        self.prediction_errors: List[float] = []

    def attach(self, store: EventStore, registry: CapabilityRegistry, reasoning: ReasoningEngine) -> None:
        self._store = store
        self._registry = registry
        self._reasoning = reasoning
        self.memory = MemoryManager(self.object_id, store)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        if self._store:
            self._store.update_state(self.object_id, self._state, self._state_version)
            self._store.update_lifecycle(
                self.object_id,
                is_alive=int(self.is_alive),
                is_dormant=int(self.is_dormant),
                idle_steps=self.idle_steps
            )

    def emit(self, event_type: str, payload: dict) -> None:
        if not self._store:
            return
        event_id = str(uuid.uuid4())
        event = Event(
            event_id=event_id,
            object_id=self.object_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            payload=payload,
            parent_event_id=self._last_event_id,
        )
        self._store.append_event(event)
        self._last_event_id = event_id

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def set_state(self, key: str, value: Any) -> None:
        old = self._state.get(key)
        self._state[key] = value
        self._state_version += 1
        self.emit("state_change", {"key": key, "old": old, "new": value, "ver": self._state_version})

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    @property
    def state(self) -> dict:
        return dict(self._state)

    # ------------------------------------------------------------------
    # Observation & Surprise
    # ------------------------------------------------------------------

    def observe(self, observation: dict) -> dict:
        self._apply_observation(observation)
        surprise = self._compute_surprise(self.expected_state, self._state)
        self.surprise_score = surprise
        self.surprise_history.append(surprise)
        if len(self.surprise_history) > 5:
            avg = sum(self.surprise_history[-5:]) / 5
            if avg < 0.05:
                self.surprise_threshold = max(0.02, self.surprise_threshold * 0.9)
            elif avg > 0.5:
                self.surprise_threshold = min(0.5, self.surprise_threshold * 1.1)
        self.emit("observation", {"data": observation, "surprise": surprise})
        if self.is_dormant and surprise > 0.2:
            self.wake()
        if surprise > self.surprise_threshold:
            self.idle_steps = 0
        return {"surprise": surprise, "object_id": self.object_id}

    def should_reason(self) -> bool:
        return not self.is_dormant and self.is_alive and self.surprise_score > self.surprise_threshold

    def tick(self) -> None:
        self.idle_steps += 1
        if self.idle_steps > DEFAULT_DORMANCY_THRESHOLD and not self.is_dormant:
            self.hibernate()

    # ------------------------------------------------------------------
    # Reasoning
    # ------------------------------------------------------------------

    def reason(self, context: Optional[dict] = None) -> dict:
        self.reasoning_count += 1
        self.idle_steps = 0
        analysis = {
            "health": 1.0 - min(1.0, self.idle_steps / 10.0),
            "surprise": self.surprise_score,
            "dormant": self.is_dormant,
        }
        action = {"name": "observe", "reason": "default"}
        prediction = {"status": "no_pred"}
        tokens = 100
        self.total_tokens_used += tokens
        self.emit("reasoning", {"analysis": analysis, "action": action, "tokens": tokens})
        return {
            "object_id": self.object_id,
            "analysis": analysis,
            "action": action,
            "prediction": prediction,
            "tokens_used": tokens,
        }

    def act(self, action: dict) -> dict:
        self.actions_taken += 1
        result = {"success": True, "action": action.get("name", "idle"), "effects": {}}
        self.emit("action", {"action": action, "result": result})
        return result

    def learn(self, outcome: dict) -> Optional[str]:
        pe = None
        if self._last_event_id is not None:
            pe = self._compute_surprise(self.expected_state, self._state)
        lesson = None
        if pe is not None and pe > 0.2 and self.memory:
            lesson = f"Prediction off by {pe:.2f}"
            self.memory.record_episode(
                json.dumps(outcome)[:200], "", json.dumps(outcome)[:200], "learned", lesson
            )
        # Update expected state with EMA
        for k in self._state:
            if k in self.expected_state and isinstance(self._state[k], (int, float)) and isinstance(self.expected_state.get(k), (int, float)):
                self.expected_state[k] = self.expected_state[k] * 0.85 + self._state[k] * 0.15
        return lesson

    # ------------------------------------------------------------------
    # Communication
    # ------------------------------------------------------------------

    def communicate(self, target_id: str, message: dict) -> dict:
        if not self._registry:
            return {"success": False, "reason": "no_registry"}
        if not self._registry.check(self.object_id, target_id, "communicate"):
            return {"success": False, "reason": "no_relationship"}
        return {"success": True, "from": self.object_id, "to": target_id, "message": message}

    def receive_message(self, message: dict) -> None:
        if self.memory:
            self.memory.record_fact(
                f"Received from {message.get('from', '?')}: {json.dumps(message)[:100]}",
                0.8, "communication"
            )
        self.surprise_score = max(self.surprise_score, 0.3)
        self.idle_steps = 0
        if self.is_dormant:
            self.wake()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def hibernate(self) -> None:
        self.is_dormant = True
        self.emit("lifecycle", {"event": "hibernated"})
        self.save()

    def wake(self) -> None:
        self.is_dormant = False
        self.idle_steps = 0
        self.emit("lifecycle", {"event": "woken"})
        self.save()

    def retire(self) -> None:
        self.is_alive = False
        self.emit("lifecycle", {"event": "retired"})
        self.save()

    def get_utility(self) -> float:
        rec = 1.0 / (1 + self.idle_steps)
        act = min(1.0, self.actions_taken / 5.0)
        pq = 1.0 - (sum(self.prediction_errors[-5:]) / max(1, len(self.prediction_errors[-5:])))
        return 0.4 * rec + 0.3 * act + 0.3 * pq

    # ------------------------------------------------------------------
    # Intelligent Method Routing (AST-based)
    # ------------------------------------------------------------------

    def _is_intelligent_method(self, method: Callable) -> bool:
        """Detect if method body is `...`, `pass`, or empty (intelligent)."""
        try:
            src = textwrap.dedent(inspect.getsource(method))
            tree = ast.parse(src)
            func_def = tree.body[0]
            if not isinstance(func_def, ast.FunctionDef):
                return False

            def is_docstring(stmt: ast.stmt) -> bool:
                return (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)
                )

            body = [s for s in func_def.body if not is_docstring(s)]

            if len(body) == 0:
                return True
            if len(body) == 1:
                stmt = body[0]
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is ...:
                    return True
                if isinstance(stmt, ast.Pass):
                    return True
                if isinstance(stmt, ast.Raise):
                    return True
            return False
        except (OSError, TypeError, SyntaxError):
            return False

    def _execute_intelligent(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute intelligent method via reasoning engine."""
        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or "No instructions provided."

        context = {
            "object_id": self.object_id,
            "name": self.name,
            "state": self._state,
            "memory_summary": self.memory.summarize_experiences() if self.memory else "No memory.",
            "args": args,
            "kwargs": kwargs,
        }

        prompt = f"""You are the intelligent method `{method.__name__}` of object `{self.name}` (ID: {self.object_id}).

Instructions:
{doc}

Current object state:
{json.dumps(context["state"], indent=2, default=str)}

Recent experiences:
{context["memory_summary"]}

Method arguments: {json.dumps(context["args"], default=str)}
Method keyword arguments: {json.dumps(context["kwargs"], default=str)}

Respond with a JSON object containing:
- "result": the return value
- "confidence": a float 0.0-1.0
- "reasoning": a brief explanation
"""

        return_annotation = sig.return_annotation
        return_type = "str"
        if return_annotation == bool:
            return_type = "bool"
        elif return_annotation == int:
            return_type = "int"
        elif return_annotation == list:
            return_type = "list"
        elif return_annotation == dict:
            return_type = "dict"

        schema = {"return_type": return_type}

        if self._reasoning:
            result = self._reasoning.reason(prompt, schema, context)
        else:
            result = {"result": None, "confidence": 0.0, "reasoning": "No reasoning engine."}

        self.emit("reasoning", {
            "method": method.__name__,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
            "result": result.get("result"),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning"),
        })
        return result.get("result")

    def _call_method(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        """Route to deterministic or intelligent execution."""
        if self._is_intelligent_method(method):
            return self._execute_intelligent(method, *args, **kwargs)

        # If method is already bound (has __self__), don't pass self again
        if hasattr(method, '__self__'):
            result = method(*args, **kwargs)
        else:
            result = method(self, *args, **kwargs)
        self.emit("action", {
            "method": method.__name__,
            "args": str(args),
            "kwargs": str(kwargs),
            "result": str(result)[:200],
            "type": "deterministic",
        })
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_observation(self, obs: dict) -> None:
        for k, v in obs.items():
            if k in ("type", "target_type", "object_id"):
                continue
            if isinstance(v, (int, float)) and k in self._state and isinstance(self._state[k], (int, float)):
                self._state[k] = max(0, min(1, self._state[k] + v))
            elif isinstance(v, (int, float)) and k.endswith("_change"):
                bk = k[:-7]
                if bk in self._state and isinstance(self._state[bk], (int, float)):
                    self._state[bk] = max(0, min(1, self._state[bk] + v))

    def _compute_surprise(self, exp: dict, act: dict) -> float:
        if not exp or not act:
            return 0.0
        td, c = 0.0, 0
        for k in set(list(exp.keys()) + list(act.keys())):
            p, a = exp.get(k, 0), act.get(k, 0)
            if isinstance(p, (int, float)) and isinstance(a, (int, float)):
                td += abs(p - a) / max(abs(a), 0.01)
                c += 1
        return min(1.0, td / max(1, c))

    # ------------------------------------------------------------------
    # Factory Methods
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: ReasoningEngine,
        object_id: Optional[str] = None,
        name: str = "Unnamed",
        initial_state: Optional[dict] = None,
    ) -> "ClawLivingObject":
        obj = cls(object_id=object_id, name=name)
        obj._state = dict(initial_state) if initial_state else {}
        obj.expected_state = dict(obj._state)
        obj.attach(store, registry, reasoning)
        store.create_object(obj.object_id, obj.name, obj.identity_signature, obj._state)
        obj.emit("created", {"name": name, "state": obj._state})
        obj.save()
        return obj

    @classmethod
    def load(
        cls,
        object_id: str,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: ReasoningEngine,
    ) -> Optional["ClawLivingObject"]:
        row = store.get_object(object_id)
        if not row:
            return None
        obj = cls(object_id=row["object_id"], name=row["name"])
        obj.created_at = row["created_at"]
        obj.identity_signature = row["identity_signature"]
        obj._state = json.loads(row["current_state"])
        obj._state_version = row["state_version"]
        obj.is_alive = bool(row.get("is_alive", 1))
        obj.is_dormant = bool(row.get("is_dormant", 0))
        obj.idle_steps = int(row.get("idle_steps", 0))
        obj.expected_state = dict(obj._state)
        obj.attach(store, registry, reasoning)
        events = store.get_events(object_id)
        if events:
            obj._last_event_id = events[-1].event_id
        obj.emit("loaded", {"ver": obj._state_version, "events": len(events)})
        obj.save()
        return obj

    def __repr__(self) -> str:
        return f"<ClawObj {self.name} id={self.object_id[:8]}... dormant={self.is_dormant} v={self._state_version}>"
