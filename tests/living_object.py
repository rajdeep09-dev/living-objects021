"""Compatibility exports for the legacy aggregate test suite.

The production implementations live in ``living_objects``.  This module keeps
older prototype tests that import ``living_object`` directly runnable without
copying or forking their runtime behavior.
"""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from living_objects.core.event_store import EventStore
from claw.living_object import ClawLivingObject as _LivingObject
from living_objects.core.reasoning import MockReasoningEngine
from living_objects.security.capability import CapabilityRegistry as _CapabilityRegistry


class CapabilityRegistry(_CapabilityRegistry):
    """Backward-compatible registry accepting the legacy optional store argument."""

    def __init__(self, _store=None):
        super().__init__()
        self.store = _store


class LivingObject(_LivingObject):
    """Legacy facade preserving the historical ``type_name`` field."""

    @classmethod
    def create(cls, *args, type_name="object", initial_state=None, **kwargs):
        state = dict(initial_state or {})
        state.setdefault("__legacy_type_name", type_name)
        obj = super().create(*args, initial_state=state, **kwargs)
        obj.type_name = type_name
        return obj

    @classmethod
    def load(cls, *args, **kwargs):
        obj = super().load(*args, **kwargs)
        if obj is not None:
            obj.type_name = obj.get_state("__legacy_type_name", "object")
        return obj


__all__ = [
    "EventStore",
    "CapabilityRegistry",
    "MockReasoningEngine",
    "LivingObject",
]
