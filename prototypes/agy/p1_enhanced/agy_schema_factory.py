"""
AGY Schema Factory — P3 Phase 3
================================

Declarative living-object generation from schema definitions.
Generates AGYLivingObject subclasses (which inherit ClawLivingObject).

10 primitive schema types: string, int, float, bool, money, list, dict,
                           timestamp, enum, ref

Features:
  - SchemaValidator catches all errors before class generation
  - Generated classes have get_X/set_X accessors per property
  - Intelligent schema methods auto-wire to LLM
  - Deterministic schema methods use provided code body
  - default_initial_state() classmethod included
  - Schema-level type, range, and enum validation
  - Developer effort comparison (schema LoC vs. hand-written LoC)

Built-in schemas: CUSTOMER_SCHEMA, ORDER_SCHEMA, SUPPORT_AGENT_SCHEMA
"""
from __future__ import annotations

import json
import re
import textwrap
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

from living_objects import EventStore, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import (
    AGYLivingObject, TieredReasoningEngine
)


# ---------------------------------------------------------------------------
# Schema vocabulary — 10 primitive types
# ---------------------------------------------------------------------------

SCHEMA_TYPES: Dict[str, dict] = {
    "string":    {"python": str,   "default": ""},
    "int":       {"python": int,   "default": 0},
    "float":     {"python": float, "default": 0.0},
    "bool":      {"python": bool,  "default": False},
    "money":     {"python": float, "default": 0.0},
    "list":      {"python": list,  "default": None},
    "dict":      {"python": dict,  "default": None},
    "timestamp": {"python": str,   "default": ""},
    "enum":      {"python": str,   "default": ""},
    "ref":       {"python": str,   "default": ""},
}

RETURN_MAP = {
    "string": str, "str": str, "int": int, "float": float,
    "bool": bool, "list": list, "dict": dict, "money": float,
}


# ---------------------------------------------------------------------------
# Schema dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PropertyDef:
    name: str
    type: str
    description: str = ""
    default: Any = None
    required: bool = True
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class MethodDef:
    name: str
    return_type: str
    description: str
    intelligent: bool = True
    implementation: Optional[str] = None   # Python code for deterministic methods


@dataclass
class ObjectSchema:
    type_name: str
    description: str
    properties: List[PropertyDef]
    goals: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    methods: List[MethodDef] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class SchemaValidationError(Exception):
    pass


class SchemaValidator:
    def validate(self, schema: ObjectSchema) -> List[str]:
        errors: List[str] = []
        if not schema.type_name:
            errors.append("type_name is required")
        elif not re.match(r'^[a-z][a-z0-9_]*$', schema.type_name):
            errors.append(f"type_name '{schema.type_name}' must be lowercase_snake_case")
        if not schema.properties:
            errors.append("At least one property is required")
        seen: set = set()
        for p in schema.properties:
            if p.name in seen:
                errors.append(f"Duplicate property: {p.name}")
            seen.add(p.name)
            if p.type not in SCHEMA_TYPES:
                errors.append(f"Unknown type '{p.type}' for '{p.name}'")
            if p.type == "enum" and not p.allowed_values:
                errors.append(f"Enum '{p.name}' needs allowed_values")
        mseen: set = set()
        for m in schema.methods:
            if m.name in mseen:
                errors.append(f"Duplicate method: {m.name}")
            mseen.add(m.name)
            if not m.description.strip():
                errors.append(f"Method '{m.name}' needs a description")
        return errors


# ---------------------------------------------------------------------------
# AGY Schema Factory
# ---------------------------------------------------------------------------

class AGYSchemaFactory:
    """Generates AGYLivingObject subclasses from ObjectSchema definitions."""

    def __init__(self):
        self._validator = SchemaValidator()
        self._cache: Dict[str, Type[AGYLivingObject]] = {}

    def create_class(self, schema: ObjectSchema) -> Type[AGYLivingObject]:
        errors = self._validator.validate(schema)
        if errors:
            raise SchemaValidationError(
                f"Schema '{schema.type_name}' invalid:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
        if schema.type_name in self._cache:
            return self._cache[schema.type_name]
        cls_name = "".join(w.capitalize() for w in schema.type_name.split("_"))
        class_dict = self._build_dict(schema)
        cls = type(cls_name, (AGYLivingObject,), class_dict)
        cls.__doc__ = (f"AGY schema-generated: {schema.type_name}\n"
                       f"{schema.description}\n"
                       f"Goals: {', '.join(schema.goals)}")
        # Manually wrap intelligent methods (type() bypasses __init_subclass__)
        for attr_name, m in list(class_dict.items()):
            if callable(m) and getattr(m, "_schema_intelligent", False):
                def _wrap(orig):
                    def wrapper(self, *a, **kw):
                        return self._execute_intelligent(orig, *a, **kw)
                    wrapper.__name__ = orig.__name__
                    wrapper.__doc__ = orig.__doc__
                    wrapper._agy_intelligent = True
                    return wrapper
                setattr(cls, attr_name, _wrap(m))
        self._cache[schema.type_name] = cls
        return cls

    def _build_dict(self, schema: ObjectSchema) -> dict:
        d: dict = {"_schema": schema}

        # default_initial_state
        def _default(cls_self) -> dict:
            st = {}
            for p in cls_self._schema.properties:
                if p.default is not None:
                    st[p.name] = p.default
                elif p.type in ("list",):
                    st[p.name] = []
                elif p.type in ("dict",):
                    st[p.name] = {}
                else:
                    st[p.name] = SCHEMA_TYPES.get(p.type, {}).get("default")
            return st
        d["default_initial_state"] = classmethod(_default)

        # schema-aware create / load
        def _create(cls_self, store, registry, reasoning, object_id=None,
                    name=None, initial_state=None):
            init = cls_self.default_initial_state()
            if initial_state:
                init.update(initial_state)
            obj = AGYLivingObject.create(
                store=store, registry=registry, reasoning=reasoning,
                object_id=object_id,
                name=name or cls_self._schema.type_name,
                initial_state=init,
            )
            obj.__class__ = cls_self
            obj.expected_state = dict(init)
            return obj
        d["create"] = classmethod(_create)

        def _load(cls_self, object_id, store, registry, reasoning):
            obj = AGYLivingObject.load(object_id, store, registry, reasoning)
            if obj:
                obj.__class__ = cls_self
            return obj
        d["load"] = classmethod(_load)

        # property validation
        def _validate_prop(self, name: str, value: Any) -> Tuple[bool, str]:
            for p in self._schema.properties:
                if p.name != name:
                    continue
                pt = SCHEMA_TYPES.get(p.type, {}).get("python")
                if pt and not isinstance(value, pt):
                    return False, f"'{name}' expects {p.type}, got {type(value).__name__}"
                if p.type == "enum" and p.allowed_values and value not in p.allowed_values:
                    return False, f"'{name}' must be one of {p.allowed_values}"
                if p.min_value is not None and isinstance(value, (int, float)) and value < p.min_value:
                    return False, f"'{name}' must be >= {p.min_value}"
                if p.max_value is not None and isinstance(value, (int, float)) and value > p.max_value:
                    return False, f"'{name}' must be <= {p.max_value}"
                return True, ""
            return True, ""
        d["validate_property"] = _validate_prop

        def _set_prop(self, name: str, value: Any) -> None:
            ok, msg = self.validate_property(name, value)
            if not ok:
                raise ValueError(f"AGY schema: {msg}")
            self.set_state(name, value)
        d["set_property"] = _set_prop

        # accessors for each property
        for prop in schema.properties:
            d.update(self._make_accessors(prop))

        # methods
        for mdef in schema.methods:
            d[mdef.name] = self._make_method(mdef)

        def _repr(self):
            preview = {p.name: self.get_state(p.name)
                       for p in self._schema.properties[:3]}
            return (f"<{self.__class__.__name__} '{self.name}' "
                    f"id={self.object_id[:8]}... "
                    f"v={self._state_version} "
                    f"{json.dumps(preview, default=str)[:60]}>")
        d["__repr__"] = _repr
        return d

    def _make_accessors(self, prop: PropertyDef) -> dict:
        pdefault = prop.default
        if pdefault is None:
            if prop.type == "list":
                pdefault = []
            elif prop.type == "dict":
                pdefault = {}
            else:
                pdefault = SCHEMA_TYPES.get(prop.type, {}).get("default")

        def make_get(pname, pdef):
            def getter(self) -> Any:
                return self.get_state(pname, pdef)
            getter.__name__ = f"get_{pname}"
            getter.__doc__ = f"Get {pname}. {prop.description}"
            return getter

        def make_set(pname):
            def setter(self, value: Any) -> None:
                self.set_property(pname, value)
            setter.__name__ = f"set_{pname}"
            setter.__doc__ = f"Set {pname} with schema validation."
            return setter

        return {
            f"get_{prop.name}": make_get(prop.name, pdefault),
            f"set_{prop.name}": make_set(prop.name),
        }

    def _make_method(self, mdef: MethodDef) -> Any:
        if mdef.intelligent:
            rtype = RETURN_MAP.get(mdef.return_type, str)

            def intelligent(self, *args, **kwargs) -> rtype:
                return self._execute_intelligent(intelligent, *args, **kwargs)
            intelligent.__name__ = mdef.name
            intelligent.__doc__ = mdef.description
            intelligent._schema_intelligent = True
            return intelligent
        else:
            code = mdef.implementation or "return None"
            globs = {"json": json, "__import__": __import__}
            exec(
                f"def {mdef.name}(self, *args, **kwargs):\n"
                + textwrap.indent(code, "    "),
                globs,
            )
            fn = globs[mdef.name]
            fn.__doc__ = mdef.description
            return fn

    def generate_source(self, schema: ObjectSchema) -> str:
        """Emit equivalent hand-written Python for developer effort comparison."""
        cn = "".join(w.capitalize() for w in schema.type_name.split("_"))
        lines = [
            f'class {cn}(AGYLivingObject):',
            f'    """{schema.description}',
            f'    Goals: {", ".join(schema.goals)}',
            f'    """', "",
        ]
        for p in schema.properties:
            pt = SCHEMA_TYPES.get(p.type, {}).get("python", Any).__name__
            lines += [
                f"    def get_{p.name}(self) -> {pt}:",
                f'        """{p.description}"""',
                f"        return self.get_state('{p.name}', {repr(p.default)})", "",
                f"    def set_{p.name}(self, value: {pt}) -> None:",
                f"        self.set_state('{p.name}', value)", "",
            ]
        for m in schema.methods:
            if m.intelligent:
                lines += [
                    f"    def {m.name}(self, *args, **kwargs) -> {m.return_type}:",
                    f'        """{m.description[:80]}"""', "        ...", "",
                ]
            else:
                lines += [
                    f"    def {m.name}(self, *args, **kwargs):",
                    f'        """{m.description[:80]}"""',
                    f"        {m.implementation or 'return None'}", "",
                ]
        return "\n".join(lines)

    def measure_effort(self, schema: ObjectSchema) -> dict:
        schema_lines = (
            3
            + len(schema.properties)
            + len(schema.methods) * 2
            + 2
        )
        hand = self.generate_source(schema)
        hand_lines = len([l for l in hand.splitlines() if l.strip()])
        red = round((1 - schema_lines / max(1, hand_lines)) * 100, 1)
        return {
            "schema_type": schema.type_name,
            "schema_lines": schema_lines,
            "hand_written_lines": hand_lines,
            "reduction_pct": red,
            "properties": len(schema.properties),
            "methods": len(schema.methods),
        }


# ---------------------------------------------------------------------------
# Built-in schemas
# ---------------------------------------------------------------------------

CUSTOMER_SCHEMA = ObjectSchema(
    type_name="customer",
    description="Persistent customer that monitors its own health and predicts churn.",
    properties=[
        PropertyDef("name",              "string", "Customer full name",   default="Unknown"),
        PropertyDef("ltv",               "money",  "Lifetime value USD",   default=0.0, min_value=0.0),
        PropertyDef("churn_probability", "float",  "Churn probability 0-1", default=0.0,
                    min_value=0.0, max_value=1.0),
        PropertyDef("segment",           "enum",   "Customer segment",
                    allowed_values=["new","growth","champion","at_risk","churned"],
                    default="new"),
        PropertyDef("interactions",      "list",   "Interaction log",      default=None),
    ],
    goals=["maximize_retention", "grow_ltv"],
    constraints={"max_reasoning_cost_usd": 0.50},
    methods=[
        MethodDef("assess_churn_risk", "dict",
                  "Analyse ltv, segment, interactions and episodic memory. "
                  "Return {risk_level: low|medium|high, probability: 0-1, "
                  "key_factors: [str], intervention: str}."),
        MethodDef("predict_ltv_90_days", "float",
                  "Predict lifetime value over 90 days from segment and historical patterns. "
                  "Return float (USD)."),
        MethodDef("suggest_next_touchpoint", "string",
                  "Suggest the most effective next marketing touchpoint. "
                  "Return a concise action string."),
        MethodDef("record_interaction", "string",
                  "Record an interaction event. Deterministic.",
                  intelligent=False,
                  implementation=(
                      "interactions = self.get_state('interactions', []) or []\n"
                      "event = {'event': args[0] if args else kwargs.get('event','?'), "
                      "'ts': __import__('datetime').datetime.now("
                      "__import__('datetime').timezone.utc).isoformat()}\n"
                      "interactions.append(event)\n"
                      "self.set_state('interactions', interactions[-100:])\n"
                      "return f\"Recorded: {event['event']}\""
                  )),
    ],
    tags=["business", "crm"],
)

ORDER_SCHEMA = ObjectSchema(
    type_name="order",
    description="Persistent order that tracks fulfilment and resolves exceptions autonomously.",
    properties=[
        PropertyDef("order_id",       "string", "External order ID",      default=""),
        PropertyDef("customer_ref",   "ref",    "UUID ref to Customer",   default=""),
        PropertyDef("quantity",       "int",    "Units ordered",          default=1, min_value=1),
        PropertyDef("total_amount",   "money",  "Total USD",              default=0.0, min_value=0.0),
        PropertyDef("status",         "enum",   "Order status",
                    allowed_values=["pending","confirmed","shipped","delivered","returned","cancelled"],
                    default="pending"),
    ],
    goals=["ensure_delivery", "minimise_exceptions"],
    methods=[
        MethodDef("assess_fulfilment_risk", "dict",
                  "Assess failure probability. Consider status, quantity, and memory. "
                  "Return {risk_level, probability, likely_cause, action}."),
        MethodDef("resolve_exception", "string",
                  "Determine best resolution for the given exception. "
                  "Use memory for past resolutions."),
        MethodDef("advance_status", "string",
                  "Advance order to next valid status. Deterministic.",
                  intelligent=False,
                  implementation=(
                      "t = {'pending':'confirmed','confirmed':'shipped','shipped':'delivered'}\n"
                      "c = self.get_state('status','pending')\n"
                      "n = t.get(c)\n"
                      "if n: self.set_state('status', n); return f'Status: {c} → {n}'\n"
                      "return f'Cannot advance from {c}'"
                  )),
    ],
    tags=["ecommerce"],
)

SUPPORT_AGENT_SCHEMA = ObjectSchema(
    type_name="support_agent",
    description="Autonomous support agent that triages tickets and learns resolution strategies.",
    properties=[
        PropertyDef("agent_name",       "string", "Agent identifier",    default="BotSmith"),
        PropertyDef("tickets_resolved", "int",    "Total resolved",      default=0, min_value=0),
        PropertyDef("speciality",       "enum",   "Domain",
                    allowed_values=["billing","technical","shipping","general"],
                    default="general"),
        PropertyDef("active",           "bool",   "Agent is active",     default=True),
    ],
    goals=["maximise_resolution_rate", "minimise_escalation"],
    methods=[
        MethodDef("triage_ticket", "dict",
                  "Classify ticket by priority and category. "
                  "Return {priority: urgent|high|medium|low, category: str, "
                  "suggested_action: str, confidence: 0-1}."),
        MethodDef("draft_response", "string",
                  "Draft a concise, empathetic response for the ticket. "
                  "Use past resolution strategies from memory."),
        MethodDef("close_ticket", "string",
                  "Close ticket and increment resolved count. Deterministic.",
                  intelligent=False,
                  implementation=(
                      "count = self.get_state('tickets_resolved', 0) + 1\n"
                      "self.set_state('tickets_resolved', count)\n"
                      "tid = args[0] if args else kwargs.get('ticket_id','?')\n"
                      "return f'Ticket {tid} closed. Total: {count}'"
                  )),
    ],
    tags=["support"],
)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def run_demo() -> None:
    import os
    DB = os.path.join(os.path.dirname(__file__), "_schema_factory_agy.db")
    if os.path.exists(DB):
        os.remove(DB)

    factory = AGYSchemaFactory()
    store = EventStore(DB)
    registry = CapabilityRegistry()
    engine = TieredReasoningEngine()

    def banner(t):
        print("\n" + "═" * 54)
        print(f"  {t}")
        print("═" * 54)

    # Customer
    banner("Customer Schema")
    CustomerClass = factory.create_class(CUSTOMER_SCHEMA)
    alice = CustomerClass.create(store, registry, engine, name="Alice",
                                 initial_state={"name": "Alice", "ltv": 1250.0,
                                                "segment": "champion"})
    alice.record_interaction("Purchased premium plan")
    alice.record_interaction("Opened loyalty email")
    alice.memory.record_episode("Alice nearly churned Q1", "Sent VIP discount",
                                "Renewed", "success", "VIP works for champions")
    print(f"  Created: {alice}")
    churn = alice.assess_churn_risk()
    ltv = alice.predict_ltv_90_days()
    tp = alice.suggest_next_touchpoint()
    print(f"  Churn risk   : {churn}")
    print(f"  LTV 90d      : {ltv}")
    print(f"  Touchpoint   : {tp}")
    alice.save()
    alice_id = alice.object_id
    alice2 = CustomerClass.load(alice_id, store, registry, engine)
    assert alice2.get_name() == "Alice"
    assert alice2.get_segment() == "champion"
    print(f"  Reload check : name={alice2.get_name()} seg={alice2.get_segment()} ✓")

    # Order
    banner("Order Schema")
    OrderClass = factory.create_class(ORDER_SCHEMA)
    order = OrderClass.create(store, registry, engine, name="Ord-42",
                              initial_state={"order_id": "ORD-2026-42",
                                             "customer_ref": alice_id,
                                             "quantity": 3, "total_amount": 149.97})
    print(f"  Created : {order}")
    print(f"  Advance : {order.advance_status()}")
    print(f"  Risk    : {order.assess_fulfilment_risk()}")
    print(f"  Resolve : {order.resolve_exception('stockout')}")

    # SupportAgent
    banner("SupportAgent Schema")
    AgentClass = factory.create_class(SUPPORT_AGENT_SCHEMA)
    agent = AgentClass.create(store, registry, engine, name="BotSmith",
                              initial_state={"agent_name": "BotSmith",
                                             "speciality": "technical"})
    print(f"  Created  : {agent}")
    print(f"  Triage   : {agent.triage_ticket('My laptop wont boot after update!')}")
    print(f"  Response : {agent.draft_response('Laptop boot failure')}")
    print(f"  Close    : {agent.close_ticket('TKT-001')}")

    # Validation errors
    banner("Validation Errors")
    bad = ObjectSchema(type_name="BAD NAME", description="", properties=[])
    for e in SchemaValidator().validate(bad):
        print(f"  ✗ {e}")

    # Developer effort
    banner("Developer Effort Comparison")
    print(f"  {'Schema':<18} {'Schema LoC':>10} {'Hand-written LoC':>17} {'Reduction':>10}")
    print("  " + "-" * 58)
    for s in [CUSTOMER_SCHEMA, ORDER_SCHEMA, SUPPORT_AGENT_SCHEMA]:
        m = factory.measure_effort(s)
        print(f"  {m['schema_type']:<18} {m['schema_lines']:>10} "
              f"{m['hand_written_lines']:>17} {m['reduction_pct']:>9}%")

    print(f"\n  Engine stats: {engine.stats()}")
    if os.path.exists(DB):
        os.remove(DB)
    banner("AGY Schema Factory demo complete ✓")


if __name__ == "__main__":
    run_demo()
