"""
AGY Agnes AI Integration Tests — Tests for real LLM engine + fallback.
"""
import os
import sys
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

from living_objects import EventStore, MockReasoningEngine, CapabilityRegistry
from prototypes.agy.p1_enhanced.agy_living_object import AGYLivingObject
from prototypes.agy.p1_enhanced.agnes_reasoning_engine import (
    AgnesReasoningEngine,
    TieredAgnesEngine,
)


@pytest.fixture
def rt(tmp_path):
    store = EventStore(str(tmp_path / "agnes_test.db"))
    registry = CapabilityRegistry()
    engine = TieredAgnesEngine(fallback=True)
    yield store, registry, engine


# ===========================================================================
# AgnesReasoningEngine — Fallback (API key may be invalid)
# ===========================================================================

def test_agnes_engine_init():
    """Engine initializes with config."""
    engine = AgnesReasoningEngine(fallback=True)
    assert engine.model == "agnes-2.0-flash"
    assert engine.fallback is True
    assert engine.call_count == 0


def test_agnes_engine_no_api_key_falls_back():
    """Without API key, falls back to MockReasoningEngine."""
    engine = AgnesReasoningEngine(api_key="", fallback=True)
    result = engine.reason("test", {"return_type": "str"}, {})
    assert result is not None
    assert "result" in result


def test_agnes_engine_reason_structure():
    """Reason returns structured dict with required keys."""
    engine = AgnesReasoningEngine(fallback=True)
    result = engine.reason("hello", {"return_type": "str"}, {})
    assert "result" in result
    assert "confidence" in result
    assert "tier" in result


def test_agnes_engine_stats():
    """Stats track calls and failures."""
    engine = AgnesReasoningEngine(fallback=True)
    for _ in range(3):
        engine.reason("test", {"return_type": "str"}, {})
    stats = engine.stats()
    assert stats["calls"] == 3
    assert "model" in stats


def test_tiered_agnes_engine():
    """Tiered engine routes to correct tier and tracks stats."""
    engine = TieredAgnesEngine(fallback=True)
    # Simple prompt → tier 0 (mock)
    r1 = engine.reason("hi", {"return_type": "str"}, {"state": {}})
    assert r1["tier"] == "mock-local"
    # Complex prompt → higher tier
    r2 = engine.reason(
        "x" * 2000,
        {"return_type": "dict"},
        {"state": {f"k{i}": i for i in range(50)},
         "memory_summary": "x" * 600, "anomaly_count": 10}
    )
    assert r2["tier"] in ("agnes-2.0-flash", "agnes-2.5-flash", "agnes-2.5-pro")
    stats = engine.stats()
    assert stats["total"] == 2
    assert stats["cost_usd"] >= 0


def test_tiered_agnes_stats():
    """Tiered stats show breakdown by tier."""
    engine = TieredAgnesEngine(fallback=True)
    engine.reason("a", {"return_type": "str"}, {"state": {}})
    engine.reason("b", {"return_type": "str"}, {"state": {}})
    stats = engine.stats()
    assert stats["by_tier"]["mock-local"] >= 1


# ===========================================================================
# Integration: AGYLivingObject with Agnes engine
# ===========================================================================

def test_agy_with_agnes_engine(rt):
    """AGYLivingObject works with TieredAgnesEngine."""
    store, registry, engine = rt
    obj = AGYLivingObject.create(store, registry, engine, name="AgnesTest",
                                  initial_state={"x": 42})
    assert obj.get_state("x") == 42
    # Intelligent method auto-routed
    class Sensor(AGYLivingObject):
        def diagnose(self, issue: str) -> str:
            """Diagnose the issue."""
            ...
    s = Sensor.create(store, registry, engine, name="S1", initial_state={})
    result = s.diagnose("overheating")
    assert result is not None


def test_agnes_integration_demo_runs():
    """Full demo runs without crashing (fallback mode)."""
    from prototypes.agy.p1_enhanced.agnes_reasoning_engine import demo_agnes_integration
    # Just verify it doesn't crash
    demo_agnes_integration()
