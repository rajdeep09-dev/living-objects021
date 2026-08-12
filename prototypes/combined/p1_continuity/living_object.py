"""Mimo's Enhanced LivingObject — adds dormancy, communication, surprise."""
import json, hashlib, uuid, inspect, textwrap, ast
from datetime import datetime, timezone
from typing import Any, Optional, Dict, Callable
from living_objects.core.event_store import EventStore, Event
from living_objects.memory.manager import MemoryManager
from living_objects.security.capability import CapabilityRegistry
from living_objects.core.reasoning import ReasoningEngine

DEFAULT_DORMANCY_THRESHOLD = 5
DEFAULT_SURPRISE_THRESHOLD = 0.15

class EnhancedLivingObject:
    """LivingObject with dormancy, surprise, and communication."""
    _store = None; _registry = None; _reasoning = None

    def __init__(self, object_id=None, name="Unnamed", oid=None):
        self.object_id = oid or object_id or str(uuid.uuid4())
        self.name = name
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.identity_signature = hashlib.sha256(self.object_id.encode()).hexdigest()[:64]
        self._state = {}; self._state_version = 0; self.memory = None
        self.is_alive = True; self.is_dormant = False; self.idle_steps = 0
        self.surprise_score = 0.0; self.surprise_threshold = DEFAULT_SURPRISE_THRESHOLD
        self.surprise_history = []; self.expected_state = {}
        self.reasoning_count = 0; self.total_tokens_used = 0; self.actions_taken = 0
        self.prediction_errors = []; self._last_event_id = None

    def attach(self, store, registry, reasoning):
        self._store = store; self._registry = registry; self._reasoning = reasoning
        self.memory = MemoryManager(self.object_id, store)

    def save(self):
        if self._store:
            self._store.update_state(self.object_id, self._state, self._state_version)

    def emit(self, etype, payload):
        if not self._store: return
        eid = str(uuid.uuid4())
        self._store.append_event(Event(eid, self.object_id, datetime.now(timezone.utc).isoformat(), etype, payload, self._last_event_id))
        self._last_event_id = eid

    def set_state(self, key, value):
        old = self._state.get(key); self._state[key] = value; self._state_version += 1
        self.emit("state_change", {"key":key,"old":old,"new":value,"ver":self._state_version})

    def get_state(self, key, default=None): return self._state.get(key, default)

    @property
    def state(self): return dict(self._state)

    def observe(self, observation):
        self._apply_observation(observation)
        surprise = self._compute_surprise(self.expected_state, self._state)
        self.surprise_score = surprise; self.surprise_history.append(surprise)
        if len(self.surprise_history) > 5:
            avg = sum(self.surprise_history[-5:])/5
            if avg < 0.05: self.surprise_threshold = max(0.02, self.surprise_threshold*0.9)
            elif avg > 0.5: self.surprise_threshold = min(0.5, self.surprise_threshold*1.1)
        self.emit("observation", {"data":observation,"surprise":surprise})
        if self.is_dormant and surprise > 0.2: self.wake()
        if surprise > self.surprise_threshold: self.idle_steps = 0
        return {"surprise":surprise,"object_id":self.object_id}

    def should_reason(self):
        return not self.is_dormant and self.is_alive and self.surprise_score > self.surprise_threshold

    def tick(self):
        self.idle_steps += 1
        if self.idle_steps > DEFAULT_DORMANCY_THRESHOLD and not self.is_dormant: self.hibernate()

    def communicate(self, target_id, message):
        if not self._registry: return {"success":False,"reason":"no_registry"}
        if not self._registry.check(self.object_id, target_id, "communicate"):
            return {"success":False,"reason":"no_relationship"}
        return {"success":True,"from":self.object_id,"to":target_id,"message":message}

    def receive_message(self, message):
        if self.memory: self.memory.record_fact(f"Received message from {message.get('from','?')}: {json.dumps(message)[:100]}", 0.8, "communication")
        self.surprise_score = max(self.surprise_score, 0.3); self.idle_steps = 0
        if self.is_dormant: self.wake()

    def hibernate(self):
        self.is_dormant = True; self.emit("lifecycle",{"event":"hibernated"}); self.save()

    def wake(self):
        self.is_dormant = False; self.idle_steps = 0; self.emit("lifecycle",{"event":"woken"}); self.save()

    def retire(self):
        self.is_alive = False; self.emit("lifecycle",{"event":"retired"}); self.save()

    def _apply_observation(self, obs):
        for k,v in obs.items():
            if k in ("type","target_type","object_id"): continue
            if isinstance(v,(int,float)) and k in self._state and isinstance(self._state[k],(int,float)):
                self._state[k] = max(0,min(1,self._state[k]+v))
            elif isinstance(v,(int,float)) and k.endswith("_change"):
                bk = k[:-7]
                if bk in self._state and isinstance(self._state[bk],(int,float)):
                    self._state[bk] = max(0,min(1,self._state[bk]+v))

    def _compute_surprise(self, exp, act):
        if not exp or not act: return 0.0
        td,c = 0.0,0
        for k in set(list(exp.keys())+list(act.keys())):
            p,a = exp.get(k,0),act.get(k,0)
            if isinstance(p,(int,float)) and isinstance(a,(int,float)):
                td += abs(p-a)/max(abs(a),0.01); c += 1
        return min(1.0, td/max(1,c))

    @classmethod
    def create(cls, store, registry, reasoning, oid=None, name="Unnamed", initial_state=None):
        obj = cls(oid=oid, name=name)
        obj._state = dict(initial_state) if initial_state else {}
        obj.expected_state = dict(obj._state)
        obj.attach(store, registry, reasoning)
        store.create_object(obj.object_id, obj.name, obj.identity_signature, obj._state)
        obj.emit("created",{"name":name,"state":obj._state}); obj.save()
        return obj

    @classmethod
    def load(cls, oid, store, registry, reasoning):
        row = store.get_object(oid)
        if not row: return None
        obj = cls(oid=row["object_id"], name=row["name"])
        obj.created_at = row["created_at"]; obj.identity_signature = row["identity_signature"]
        obj._state = json.loads(row["current_state"]); obj._state_version = row["state_version"]
        obj.expected_state = dict(obj._state); obj.attach(store, registry, reasoning)
        events = store.get_events(oid)
        if events: obj._last_event_id = events[-1].event_id
        obj.emit("loaded",{"ver":obj._state_version,"events":len(events)}); obj.save()
        return obj

    def _is_intelligent_method(self, method):
        """Check if method body is ... (intelligent)."""
        import inspect, textwrap, ast
        src = textwrap.dedent(inspect.getsource(method))
        try:
            tree = ast.parse(src)
            func_def = tree.body[0]
            if isinstance(func_def, ast.FunctionDef):
                non_doc = [s for s in func_def.body if not (isinstance(s,ast.Expr) and isinstance(s.value,ast.Constant) and isinstance(s.value.value,str))]
                if len(non_doc)==0: return True
                elif len(non_doc)==1:
                    s = non_doc[0]
                    if isinstance(s,ast.Expr) and isinstance(s.value,ast.Constant) and s.value.value is ...: return True
                    elif isinstance(s,ast.Pass): return True
                    elif isinstance(s,ast.Raise): return True
        except: pass
        return False
