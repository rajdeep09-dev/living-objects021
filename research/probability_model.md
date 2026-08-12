# Probability Model

## Uncertainty as a Native Primitive

Traditional software assumes certainty:
```python
customer.is_churning = True  # Certain, but often wrong
```

Intelligent objects should represent uncertainty:
```python
customer.churn_probability = 0.73  # Uncertain, honest
# with confidence_interval = [0.61, 0.84]
# based_on = [list_of_evidence]
```

## Bayesian Object Beliefs

### Prior, Evidence, Posterior

```
P(belief | evidence) = P(evidence | belief) × P(belief) / P(evidence)
```

### Object Belief State

```
B(t) = { (proposition, probability, confidence, evidence_list, timestamp) }
```

### Belief Update Rules

1. **New evidence supports belief:**
   ```
   P(belief) ← P(belief) + α × (1 - P(belief))
   confidence ← confidence + β
   ```

2. **New evidence contradicts belief:**
   ```
   P(belief) ← P(belief) - α × P(belief)
   confidence ← confidence - β
   ```

3. **Conflicting evidence:**
   ```
   Store both beliefs with provenance
   Flag for human review if confidence difference > threshold
   ```

4. **Evidence ages:**
   ```
   confidence ← confidence × decay_factor^{age}
   ```

## Probabilistic State

### Instead of Point Values

| Traditional | Probabilistic |
|-------------|---------------|
| `revenue = 1000000` | `revenue ~ N(1000000, 50000)` |
| `churn = False` | `churn_probability = 0.23` |
| `segment = "high_value"` | `P(high_value) = 0.7, P(at_risk) = 0.2, P(new) = 0.1` |

### Benefits

1. **Honest uncertainty:** No false confidence
2. **Better decisions:** Decision theory uses probabilities
3. **Natural Bayesian updating:** New evidence updates beliefs
4. **Risk awareness:** Low-confidence beliefs trigger caution

### Costs

1. **Complexity:** Probabilistic reasoning is harder
2. **LLM compatibility:** LLMs struggle with explicit probabilities
3. **Performance:** Maintaining distributions is expensive
4. **Debugging:** Harder to inspect than point values

## Practical Compromise: Confidence Scores

Instead of full probability distributions, use confidence scores:

```python
@dataclass
class Belief:
    value: Any           # Point estimate
    confidence: float    # 0.0 to 1.0
    evidence_count: int  # Number of supporting observations
    last_updated: datetime
    source: str          # Provenance
```

### Decision Rules

```
confidence > 0.9:   Act decisively
confidence 0.7-0.9: Act with caution, gather more evidence
confidence 0.5-0.7: Defer decision, request human input
confidence < 0.5:   Do not act, flag for investigation
```

## Causal Beliefs

### Beyond Correlation

Objects should distinguish:
- **Observation:** "A and B occur together" (correlation)
- **Intervention:** "If I do A, B happens" (causation)
- **Counterfactual:** "If I had done A, would B have happened?" (causal inference)

### Causal Graph

```
Object maintains partial causal graph:
  A → B (A causes B, confidence = 0.8)
  C → B (C causes B, confidence = 0.6)
  D ↔ E (D correlates with E, not causal)
```

### Experimentation for Causal Discovery

```
To test if A causes B:
  1. do(A = a1) → observe B
  2. do(A = a2) → observe B
  3. If B changes significantly: A likely causes B
  4. Update causal graph
```

**Note:** Full causal inference is expensive. Start with simple correlation + confidence. Add causal experimentation in Phase 4+.

## Prediction Error as Learning Signal

### Definition

```
PredictionError(t) = |predicted_outcome(t) - actual_outcome(t)|
```

### Uses

1. **Surprise detection:** High error → high surprise → more attention
2. **Model validation:** Consistent high error → model is wrong
3. **Learning rate:** High error → increase learning rate for this situation
4. **Utility estimation:** Accurate predictions → high utility object

### Prediction Quality Metric

```
PredictionQuality = 1 - mean(PredictionError) / mean(|actual_outcome|)
```

Objects with PredictionQuality < threshold should:
- Increase reasoning budget
- Run more experiments
- Request human assistance

## Information Gain for Experiment Selection

### Definition

```
IG(experiment) = H(belief_before) - E[H(belief_after)]
```

Where H is entropy.

### Practical Approximation

```
IG(experiment) ≈ novelty_of_situation × expected_confidence_change / cost
```

### Experiment Selection

```
choose_experiment = argmax_{e} [IG(e) / C(e)]
```

Select the experiment that is expected to reduce uncertainty the most per unit cost.

## Conclusion

**Probabilistic beliefs are valuable but expensive.**

**Phase 3 recommendation:** Use confidence scores (0.0–1.0) as a lightweight uncertainty primitive. Full Bayesian beliefs and causal graphs are Phase 4+ extensions.

**The critical insight:** Even a simple confidence score prevents overconfidence and enables better decision-making than certainty assumptions.
