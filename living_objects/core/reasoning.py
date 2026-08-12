"""
Reasoning Engine — Pluggable intelligence layer.

The default MockReasoningEngine produces deterministic structured output
based on prompt hash — no API keys needed, fully reproducible for testing.

Swap in LiteLLMReasoningEngine for real LLM integration.
"""

import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict


class ReasoningEngine(ABC):
    """Base class for intelligent method execution."""

    @abstractmethod
    def reason(self, prompt: str, schema: dict, context: dict) -> dict:
        """
        Execute reasoning and return structured result.

        Returns a dict with keys:
            - result: the actual return value
            - confidence: float 0.0–1.0
            - reasoning: brief explanation
        """
        ...


class MockReasoningEngine(ReasoningEngine):
    """
    Deterministic mock reasoning for reproducible testing.

    Produces structured output based on prompt hash — no API keys,
    no network calls, fully deterministic.
    """

    def reason(self, prompt: str, schema: dict, context: dict) -> dict:
        h = hashlib.sha256(prompt.encode()).hexdigest()
        return_type = schema.get("return_type", "str")

        if return_type == "str":
            decisions = [
                "analyze the current state carefully before acting",
                "prioritize stability and incremental improvement",
                "seek additional information to reduce uncertainty",
                "apply learned heuristics from past experiences",
                "delegate to a specialized sub-procedure if available",
            ]
            idx = int(h[:8], 16) % len(decisions)
            conf = 0.7 + (int(h[8:12], 16) % 30) / 100
            return {"result": decisions[idx], "confidence": conf}

        if return_type == "bool":
            return {"result": int(h[:8], 16) % 2 == 0, "confidence": 0.75}

        if return_type == "int":
            return {"result": int(h[:8], 16) % 100, "confidence": 0.8}

        if return_type == "list":
            items = ["observe", "plan", "act", "reflect", "adapt"]
            mask = int(h[:8], 16)
            selected = [items[i] for i in range(len(items)) if mask & (1 << i)]
            return {"result": selected or ["observe"], "confidence": 0.72}

        if return_type == "dict":
            return {
                "result": {
                    "action": "reasoned_decision",
                    "rationale": f"Based on context hash {h[:16]}...",
                    "priority": int(h[:8], 16) % 10,
                },
                "confidence": 0.78,
            }

        return {"result": f"mock_result_{h[:8]}", "confidence": 0.7}
