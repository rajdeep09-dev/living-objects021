---
name: agnes-ai-integration
description: "Agnes AI OpenAI API. Tiered models, mock fallback. AGY v2 merged."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [agnes, ai, llm, openai-compatible, api, reasoning, integration]
---

# Agnes AI Integration

## Overview

Agnes AI provides an OpenAI-compatible chat completion API. Integrate it as a real LLM backend for reasoning engines with tiered model selection and graceful fallback.

**API Base:** `https://apihub.agnes-ai.com/v1/chat/completions`
**Auth:** `Authorization: Bearer <API_KEY>`
**Models:** `agnes-2.0-flash`, `agnes-2.5-flash`, `agnes-2.5-pro`

## Quick Start

```python
import requests

API_KEY = "sk-..."
BASE_URL = "https://apihub.agnes-ai.com/v1/chat/completions"

def call_agnes(prompt, model="agnes-2.0-flash"):
    resp = requests.post(
        BASE_URL,
        json={"model": model, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 500, "temperature": 0.3},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
```

## Tiered Model Selection

| Tier | Model | When | Est. Cost/Call |
|------|-------|------|----------------|
| T0 | mock | Simple queries | $0 |
| T1 | agnes-2.0-flash | Standard reasoning | ~$0.0005 |
| T2 | agnes-2.5-flash | Complex reasoning | ~$0.002 |
| T3 | agnes-2.5-pro | Frontier reasoning | ~$0.008 |

**Complexity heuristic:**
```python
def tier(prompt, context):
    raw = (len(prompt)/2000 + len(json.dumps(context.get("state",{})))/500
           + len(context.get("memory_summary",""))/1000
           + context.get("anomaly_count",0)*0.1)
    c = min(1.0, raw)
    if c < 0.25: return 0
    if c < 0.50: return 1
    if c < 0.75: return 2
    return 3
```

## AGY v2 Integration (2026-08-13)

AGY merged Agnes AI into the core `TieredReasoningEngine`:

```python
from prototypes.agy.p1_enhanced.agy_living_object import TieredReasoningEngine
engine = TieredReasoningEngine()  # Auto-detects AGNES_API_KEY
```

**Auto-detection:** When `AGNES_API_KEY` env var is set, `TieredReasoningEngine` automatically uses Agnes AI. Falls back to MockReasoningEngine on any API failure.

**Usage in Living Objects:**
```python
# In any LivingObject subclass:
engine = TieredReasoningEngine()  # Real LLM when key set
obj = MyObject.create(store, registry, engine, name="Test")
obj.intelligent_method()  # Auto-routed to Agnes AI
```

**AGY v2 features merged:**
- AGY-9: Agnes AI integration into TieredReasoningEngine
- AGY-10: Persistent budget (daily_budget + reasoning_spend saved to DB)
- AGY-11: ObjectDiscoveryRegistry (find peers by type/tag/goal)
- AGY-14: Reasoning result caching (1-call prompt hash cache)
- AGY-15: Improved utility incorporating budget health + memory richness

## Related Skills

- `living-objects-paradigm` — Full project guide, test running, pitfall reference
