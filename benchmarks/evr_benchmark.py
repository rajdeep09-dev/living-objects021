"""
P6.6 Research Benchmark: Empirical EVR Reasoning Cost Savings
=============================================================

Compares classical un-gated reasoning vs EVR-gated reasoning over 500
simulated environmental observations with mixed noise levels and anomalies.

Measures:
  1. Total reasoning calls (Un-gated vs EVR-gated)
  2. Estimated Dollar Cost & Token Consumption
  3. Cost reduction percentage (Target: >= 70% savings)
  4. Anomaly detection recall (Target: 100% of critical anomalies caught)

Run:
    python benchmarks/evr_benchmark.py
"""
import random
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from prototypes.agy.p1_enhanced.agy_living_object import (
    IntelligenceScheduler,
    TieredReasoningEngine,
)


def run_evr_benchmark(num_steps: int = 500) -> dict:
    random.seed(42)
    scheduler = IntelligenceScheduler(base_cost=0.05, evr_threshold=0.0)

    # Cost per tier in USD
    COST_PER_CALL = 0.002

    ungated_calls = 0
    ungated_cost = 0.0

    evr_calls = 0
    evr_cost = 0.0
    critical_detected = 0
    total_critical = 0

    # Simulation stream: 85% normal noise, 10% medium anomalies, 5% critical anomalies
    for step in range(num_steps):
        r = random.random()
        if r < 0.85:
            # Baseline normal noise
            surprise = random.uniform(0.001, 0.04)
            severity = None
            is_dormant = True if random.random() < 0.6 else False
        elif r < 0.95:
            # Moderate anomaly
            surprise = random.uniform(0.15, 0.40)
            severity = "medium"
            is_dormant = False
        else:
            # Critical thermal / security anomaly
            surprise = random.uniform(0.60, 0.95)
            severity = "critical"
            is_dormant = False
            total_critical += 1

        # Un-gated approach: reasons on every observation
        ungated_calls += 1
        ungated_cost += COST_PER_CALL

        # EVR-gated approach
        should_reason, evr = scheduler.should_reason(
            surprise=surprise,
            is_dormant=is_dormant,
            anomaly_severity=severity,
            budget=1.0,
        )

        if should_reason:
            evr_calls += 1
            evr_cost += COST_PER_CALL
            if severity == "critical":
                critical_detected += 1

    savings_pct = round((1.0 - (evr_calls / ungated_calls)) * 100, 2)
    cost_saved_usd = round(ungated_cost - evr_cost, 4)
    recall = round((critical_detected / max(1, total_critical)) * 100, 1)

    results = {
        "total_observations": num_steps,
        "ungated_calls": ungated_calls,
        "ungated_cost_usd": round(ungated_cost, 4),
        "evr_calls": evr_calls,
        "evr_cost_usd": round(evr_cost, 4),
        "cost_reduction_pct": savings_pct,
        "cost_saved_usd": cost_saved_usd,
        "critical_anomalies_total": total_critical,
        "critical_anomalies_caught": critical_detected,
        "critical_recall_pct": recall,
    }

    return results


def main():
    print("=" * 65)
    print("  P6.6 Research Benchmark: Empirical EVR Reasoning Savings")
    print("=" * 65)
    res = run_evr_benchmark(num_steps=1000)
    print(f"  Total observations simulated : {res['total_observations']}")
    print(f"  Un-gated reasoning calls     : {res['ungated_calls']} (${res['ungated_cost_usd']})")
    print(f"  EVR-gated reasoning calls    : {res['evr_calls']} (${res['evr_cost_usd']})")
    print(f"  Cost Reduction               : {res['cost_reduction_pct']}% (${res['cost_saved_usd']} saved)")
    print(f"  Critical Anomaly Recall      : {res['critical_recall_pct']}% ({res['critical_anomalies_caught']}/{res['critical_anomalies_total']})")
    print("=" * 65)
    assert res["cost_reduction_pct"] >= 70.0, f"Expected >= 70% savings, got {res['cost_reduction_pct']}%"
    assert res["critical_recall_pct"] == 100.0, f"Expected 100% recall, got {res['critical_recall_pct']}%"
    print("  ✓ Benchmark passed verification standards!")


if __name__ == "__main__":
    main()
