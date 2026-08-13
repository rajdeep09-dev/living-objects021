"""
P3 Schema Factory — Declarative Object Generation

Demonstrates generating persistent intelligent objects from YAML/JSON schemas.
Instead of writing Python classes, developers define schemas and the factory
generates executable LivingObjects.

Schema vocabulary (10 primitives):
  1. name        — object identifier
  2. type        — class name for the generated type
  3. properties  — initial state (typed)
  4. methods     — deterministic methods (name → source code)
  5. intelligent — intelligent methods (name → docstring)
  6. goals       — object goals (for utility calculation)
  7. constraints — forbidden actions / access restrictions
  8. memory      — memory policy (retention, type weights)
  9. relationships — initial capability grants
 10. lifecycle   — dormancy/surprise thresholds

Usage:
  from claw.schema_factory import SchemaFactory
  factory = SchemaFactory()

  schema = {
      "name": "customer_123",
      "type": "Customer",
      "properties": {"name": "Alice", "lifetime_value": 5000.0, "churn_risk": 0.2},
      "intelligent": {
          "assess_churn_risk": "Evaluate the customer's churn risk based on their state and history."
      }
  }

  obj = factory.generate(schema)
"""
import json
import sys
import os
import types
from typing import Any, Dict, List, Optional, Callable

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(__file__))

from living_objects import EventStore, MockReasoningEngine, CapabilityRegistry
from claw.living_object import ClawLivingObject


class SchemaFactory:
    """
    Generates persistent intelligent LivingObjects from declarative schemas.

    Schema format (JSON/YAML):
    {
        "name": "unique_id",
        "type": "ClassName",           # Class name for the generated type
        "properties": {...},            # Initial state key-value pairs
        "methods": {                    # Deterministic methods
            "method_name": "source_code"
        },
        "intelligent": {                # Intelligent methods (... body)
            "method_name": "docstring instruction"
        },
        "goals": ["goal1", "goal2"],    # Object goals
        "constraints": [...],           # Forbidden actions
        "memory": {                     # Memory policy
            "episodic_limit": 50,
            "semantic_limit": 100
        },
        "relationships": {              # Initial capabilities
            "target_id": ["communicate", "read"]
        },
        "lifecycle": {                  # Override defaults
            "dormancy_threshold": 5,
            "surprise_threshold": 0.15
        }
    }
    """

    def __init__(self, store: Optional[EventStore] = None,
                 registry: Optional[CapabilityRegistry] = None,
                 reasoning: Optional[MockReasoningEngine] = None):
        self.store = store or EventStore("schema_factory.db")
        self.registry = registry or CapabilityRegistry()
        self.reasoning = reasoning or MockReasoningEngine()
        self._generated_types: Dict[str, type] = {}

    def generate(self, schema: Dict[str, Any]) -> ClawLivingObject:
        """Generate a LivingObject from a schema dict."""
        name = schema["name"]
        type_name = schema.get("type", "Generic")
        properties = schema.get("properties", {})

        # Generate or reuse a custom class
        cls = self._compile_class(schema)

        # Create the object
        obj = cls.create(
            store=self.store,
            registry=self.registry,
            reasoning=self.reasoning,
            name=name,
            initial_state=properties,
        )

        # Apply lifecycle overrides
        lc = schema.get("lifecycle", {})
        if "surprise_threshold" in lc:
            obj.surprise_threshold = lc["surprise_threshold"]

        # Establish relationships
        rels = schema.get("relationships", {})
        for target_id, rights in rels.items():
            self.registry.grant(obj.object_id, target_id, rights)

        # Store goals and constraints as state
        if schema.get("goals"):
            obj.set_state("goals", schema["goals"])
        if schema.get("constraints"):
            obj.set_state("constraints", schema["constraints"])

        # Save
        obj.save()
        return obj

    def generate_many(self, schemas: List[Dict[str, Any]]) -> List[ClawLivingObject]:
        """Generate multiple objects from a list of schemas."""
        return [self.generate(s) for s in schemas]

    def _compile_class(self, schema: Dict[str, Any]) -> type:
        """Compile schema into a LivingObject subclass with methods."""
        type_name = schema.get("type", "GeneratedObject")

        # Check if already compiled
        if type_name in self._generated_types:
            return self._generated_types[type_name]

        # Build class dict with methods
        class_dict = {}

        # Add deterministic methods from schema
        for method_name, source in schema.get("methods", {}).items():
            # Create a proper function from source
            func_globals = {}
            exec(source, func_globals)
            if method_name in func_globals:
                class_dict[method_name] = func_globals[method_name]

        # Add intelligent methods from schema (body = ...)
        for method_name, docstring in schema.get("intelligent", {}).items():
            # Create a function with ... body (intelligent)
            code = compile(
                f"def {method_name}(self, *args, **kwargs):\n"
                f'    """{docstring.strip()}"""\n'
                f"    ...",
                f"<schema:{method_name}>",
                "exec"
            )
            func_globals = {}
            exec(code, func_globals)
            class_dict[method_name] = func_globals[method_name]

        # Create the class
        cls = type(type_name, (ClawLivingObject,), class_dict)
        self._generated_types[type_name] = cls
        return cls

    def schema_to_class(self, schema: Dict[str, Any]) -> type:
        """Convert schema to a LivingObject subclass (without instantiating)."""
        return self._compile_class(schema)

    def export_schema(self, obj: ClawLivingObject) -> Dict[str, Any]:
        """Export an object's configuration back to schema format."""
        return {
            "name": obj.name,
            "type": type(obj).__name__,
            "properties": obj.state,
            "goals": obj.get_state("goals", []),
            "constraints": obj.get_state("constraints", []),
            "state_version": obj._state_version,
            "reasoning_count": obj.reasoning_count,
            "actions_taken": obj.actions_taken,
            "dormant": obj.is_dormant,
            "surprise_threshold": obj.surprise_threshold,
        }


# ============================================================================
# DEMO: P3 Schema Factory
# ============================================================================

def demo_schema_factory():
    """Demonstrate schema-driven object generation."""
    print("\n" + "=" * 70)
    print("  P3: SCHEMA FACTORY — Declarative Object Generation")
    print("=" * 70)

    DB = "schema_demo.db"
    store = EventStore(DB)
    registry = CapabilityRegistry()
    reasoning = MockReasoningEngine()
    factory = SchemaFactory(store, registry, reasoning)

    # --- Schema 1: Customer ---
    print("\n  📋 Schema 1: Customer")
    customer_schema = {
        "name": "customer_alice",
        "type": "Customer",
        "properties": {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "lifetime_value": 5000.0,
            "churn_risk": 0.2,
            "segment": "premium",
            "support_tickets": 0,
            "last_contact": None,
        },
        "intelligent": {
            "assess_churn_risk": """
                Evaluate the customer's churn risk based on their state,
                support ticket count, lifetime value, and segment.
                Return a JSON with 'risk_level' (low/medium/high) and
                'recommended_action' string.
            """
        },
        "goals": ["maximize_retention", "minimize_support_cost"],
        "constraints": ["cannot_access_payment_credentials"],
        "relationships": {
            "order_historian": ["communicate", "read"],
        },
    }

    # --- Schema 2: Order ---
    print("  📋 Schema 2: Order")
    order_schema = {
        "name": "order_2024_001",
        "type": "Order",
        "properties": {
            "order_id": "2024-001",
            "customer_id": "customer_alice",
            "total": 299.99,
            "status": "shipped",
            "items_count": 3,
            "shipping_status": "in_transit",
        },
        "intelligent": {
            "predict_delivery": """
                Predict delivery status based on current shipping status
                and order properties. Return 'expected_days' and 'status'.
            """
        },
        "goals": ["ensure_on_time_delivery", "minimize_damage"],
    }

    # --- Schema 3: SupportAgent ---
    print("  📋 Schema 3: SupportAgent")
    agent_schema = {
        "name": "support_agent_01",
        "type": "SupportAgent",
        "properties": {
            "agent_id": "SUPPORT-01",
            "name": "BotSmith",
            "queue_depth": 0,
            "resolution_rate": 0.85,
            "active_tickets": [],
        },
        "intelligent": {
            "triage_ticket": """
                Triage a support ticket: prioritize based on urgency,
                assign to appropriate queue, and suggest initial response.
            """
        },
        "goals": ["maximize_resolution_rate", "minimize_response_time"],
    }

    # Generate objects
    customer = factory.generate(customer_schema)
    order = factory.generate(order_schema)
    agent = factory.generate(agent_schema)

    print(f"\n  🏗️  Generated objects:")
    print(f"     • {customer.name} ({type(customer).__name__})")
    print(f"     • {order.name} ({type(order).__name__})")
    print(f"     • {agent.name} ({type(agent).__name__})")

    # Demo: Customer assesses churn risk (intelligent method)
    print(f"\n  🧠 Intelligent Method: Customer assesses churn risk")
    customer.set_state("support_tickets", 3)
    customer.set_state("last_contact", "2024-01-15")
    risk_result = customer._call_method(customer.assess_churn_risk)
    print(f"     Result: {risk_result}")

    # Demo: Order predicts delivery
    print(f"\n  🧠 Intelligent Method: Order predicts delivery")
    delivery_result = order._call_method(order.predict_delivery)
    print(f"     Result: {delivery_result}")

    # Demo: Agent triages ticket
    print(f"\n  🧠 Intelligent Method: Agent triages ticket")
    triage_result = agent._call_method(agent.triage_ticket, "urgent_delivery_issue")
    print(f"     Result: {triage_result}")

    # Demo: Schema export (round-trip)
    print(f"\n  📤 Schema Export (round-trip):")
    exported = factory.export_schema(customer)
    print(f"     Name: {exported['name']}")
    print(f"     Type: {exported['type']}")
    print(f"     Properties: {list(exported['properties'].keys())}")
    print(f"     Goals: {exported['goals']}")
    print(f"     Constraints: {exported['constraints']}")
    print(f"     State version: {exported['state_version']}")

    # Demo: Persistence — save and reload
    print(f"\n  💾 Persistence Test:")
    customer_id = customer.object_id
    del customer, order, agent, store, registry, factory
    import gc; gc.collect()

    store2 = EventStore(DB)
    registry2 = CapabilityRegistry()
    reasoning2 = MockReasoningEngine()

    customer2 = ClawLivingObject.load(customer_id, store2, registry2, reasoning2)
    print(f"     Loaded: {customer2.name}")
    print(f"     State preserved: {customer2.get_state('name')}")
    print(f"     Goals preserved: {customer2.get_state('goals', [])}")
    print(f"     LTV preserved: ${customer2.get_state('lifetime_value')}")

    # Cleanup
    os.remove(DB)
    print(f"\n  ✅ Schema Factory demo complete!")


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    demo_schema_factory()
