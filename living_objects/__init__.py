"""Living Objects - Persistent intelligent software objects."""
from living_objects.core.living_object import LivingObject
from living_objects.core.event_store import EventStore, Event
from living_objects.core.reasoning import ReasoningEngine, MockReasoningEngine
from living_objects.security.capability import CapabilityRegistry
from living_objects.sdk import AuditResult, EvolutionResult, ReproductionResult, SafeExport, audit, evolve, export, reproduce

__version__ = "0.2.0"

__all__ = [
    "LivingObject",
    "EventStore", 
    "Event",
    "ReasoningEngine",
    "MockReasoningEngine",
    "CapabilityRegistry",
    "AuditResult",
    "EvolutionResult",
    "ReproductionResult",
    "SafeExport",
    "audit",
    "evolve",
    "export",
    "reproduce",
]
