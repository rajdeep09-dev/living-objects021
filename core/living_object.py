"""
LivingObject - The smallest possible persistent intelligent object.

Core properties:
  - Persistent identity (UUID, survives restart)
  - Persistent state (versioned, event-sourced)
  - Hierarchical memory (episodic, semantic, procedural)
  - Deterministic methods (normal Python code)
  - Intelligent methods (LLM-driven via docstring + type annotations)
  - Event logging (complete audit trail)
  - Capability-based relationships (minimal)

Usage:
    from living_objects import LivingObject, EventStore, MockReasoningEngine
    from living_objects.security import CapabilityRegistry

    store = EventStore("objects.db")
    registry = CapabilityRegistry()
    reasoning = MockReasoningEngine()

    obj = LivingObject.create(store, registry, reasoning, name="SensorAlpha")
    obj.set_state("location", "lab_7")
    obj.save()

    # Later, in a new process:
    obj2 = LivingObject.load(obj.object_id, store, registry, reasoning)
    print(obj2.get_state("location"))  # "lab_7"
"""

import ast
import hashlib
import inspect
import json
import textwrap
import uuid
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone

from living_objects.core.event_store import EventStore, Event
from living_objects.core.reasoning import ReasoningEngine
from living_objects.memory.manager import MemoryManager
from living_objects.security.capability import CapabilityRegistry


class LivingObject:
    """
    The smallest possible persistent intelligent object.

    Subclass this to create concrete intelligent objects:

        class Customer(LivingObject):
            def get_status(self) -> dict:
                return {"name": self.name, "state": self.state}

            def recommend_action(self, context: str) -> dict:
                # Intelligent method - body is ... to trigger LLM.
                ...
    """

    def __init__(self, object_id: Optional[str] = None, name: str = "Unnamed"):
        # Identity
        self.object_id = object_id or str(uuid.uuid4())
        self.name = name
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.identity_signature = hashlib.sha256(
            self.object_id.encode()
        ).hexdigest()[:64]

        # State
        self._state: Dict[str, Any] = {}
        self._state_version = 0

        # Memory (attached after rehydration)
        self.memory: Optional[MemoryManager] = None

        # Runtime (attached after rehydration)
        self._store: Optional[EventStore] = None
        self._registry: Optional[CapabilityRegistry] = None
        self._reasoning: Optional[ReasoningEngine] = None
        self._last_event_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Runtime attachment
    # ------------------------------------------------------------------

    def attach(
        self,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: ReasoningEngine,
    ) -> None:
        """Attach runtime infrastructure. Called after rehydration."""
        self._store = store
        self._registry = registry
        self._reasoning = reasoning
        self.memory = MemoryManager(self.object_id, store)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist current state."""
        if self._store:
            self._store.update_state(
                self.object_id, self._state, self._state_version
            )

    def emit(self, event_type: str, payload: dict) -> None:
        """Emit a signed event to the audit trail."""
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
    # State management
    # ------------------------------------------------------------------

    def set_state(self, key: str, value: Any) -> None:
        """Update state with event logging."""
        old_value = self._state.get(key)
        self._state[key] = value
        self._state_version += 1
        self.emit(
            "state_change",
            {
                "key": key,
                "old_value": old_value,
                "new_value": value,
                "version": self._state_version,
            },
        )

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    @property
    def state(self) -> dict:
        return dict(self._state)

    # ------------------------------------------------------------------
    # Method execution
    # ------------------------------------------------------------------

    def _is_intelligent_method(self, method: Callable) -> bool:
        """Detect if a method body is `...`, `pass`, or `raise NotImplementedError`."""
        try:
            src = inspect.getsource(method)
            src = textwrap.dedent(src)
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
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is ...
                ):
                    return True
                if isinstance(stmt, ast.Pass):
                    return True
                if isinstance(stmt, ast.Raise):
                    return True
            return False
        except (OSError, TypeError, SyntaxError):
            return False

    def _execute_intelligent(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute an intelligent method via the reasoning engine."""
        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or "No instructions provided."

        context = {
            "object_id": self.object_id,
            "name": self.name,
            "state": self._state,
            "memory_summary": (
                self.memory.summarize_experiences()
                if self.memory
                else "No memory."
            ),
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
- "result": the return value (matching the method's return type annotation)
- "confidence": a float 0.0–1.0
- "reasoning": a brief explanation of your decision
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
            result = {
                "result": None,
                "confidence": 0.0,
                "reasoning": "No reasoning engine attached.",
            }

        self.emit(
            "reasoning",
            {
                "method": method.__name__,
                "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                "result": result.get("result"),
                "confidence": result.get("confidence"),
                "reasoning": result.get("reasoning"),
            },
        )
        return result.get("result")

    def _call_method(self, method: Callable, *args: Any, **kwargs: Any) -> Any:
        """Route to deterministic or intelligent execution."""
        if self._is_intelligent_method(method):
            return self._execute_intelligent(method, *args, **kwargs)

        result = method(self, *args, **kwargs)
        self.emit(
            "action",
            {
                "method": method.__name__,
                "args": str(args),
                "kwargs": str(kwargs),
                "result": str(result)[:200],
                "type": "deterministic",
            },
        )
        return result

    # ------------------------------------------------------------------
    # Lifecycle
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
    ) -> "LivingObject":
        """Create a new living object and persist it."""
        obj = cls(object_id=object_id, name=name)
        obj._state = dict(initial_state) if initial_state else {}
        obj.attach(store, registry, reasoning)

        store.create_object(
            obj.object_id, obj.name, obj.identity_signature, obj._state
        )
        obj.emit("created", {"name": name, "initial_state": obj._state})
        obj.save()
        return obj

    @classmethod
    def load(
        cls,
        object_id: str,
        store: EventStore,
        registry: CapabilityRegistry,
        reasoning: ReasoningEngine,
    ) -> Optional["LivingObject"]:
        """Rehydrate a living object from persistent storage."""
        row = store.get_object(object_id)
        if not row:
            return None

        obj = cls(object_id=row["object_id"], name=row["name"])
        obj.created_at = row["created_at"]
        obj.identity_signature = row["identity_signature"]
        obj._state = json.loads(row["current_state"])
        obj._state_version = row["state_version"]
        obj.attach(store, registry, reasoning)

        events = store.get_events(object_id)
        if events:
            obj._last_event_id = events[-1].event_id

        obj.emit(
            "loaded",
            {"state_version": obj._state_version, "event_count": len(events)},
        )
        obj.save()
        return obj

    def __repr__(self) -> str:
        return (
            f"<LivingObject {self.name} "
            f"id={self.object_id[:8]}... state_v={self._state_version}>"
        )
