# BEAST v7 Bounded Sorting Run — Final Report (Generation 1,000)

> This is the final report for the completed **bounded execution stated below**. It is not the v7 guide's 100,000-generation public-marathon claim, and it must not be represented as one.

## Measured result

| Measurement | Value |
|---|---:|
| Completed generations | 1,000 |
| Target generations for this execution | 1,000 |
| Training champion fitness | 1.000000 |
| Fresh-sort correctness | 1.000000 (100/100) |
| Fresh inputs | 100 at seed 901000 |
| Champion program nodes | 2 |
| Elapsed seconds in this invocation | 19.318 |
| Git commit | `be7d22c2dd94d115bdede0678ff602417cf3cd3f` |

## Champion audit source

```python
import math

def sorting_champion_generation_1000(x):
    try:
        input = x
        return sorted(list(input))
    except Exception:
        return None
```

## Fitness curve

The complete machine-readable curve is `fitness_curve.json`; this rendering is sampled from it.

| Generation | Best fitness | Average fitness | Best nodes |
|---:|---:|---:|---:|
| 0 | 1.000000 | 0.024000 | 5 |
| 43 | 1.000000 | 0.760000 | 2 |
| 86 | 1.000000 | 0.700000 | 2 |
| 129 | 1.000000 | 0.689000 | 2 |
| 172 | 1.000000 | 0.660000 | 2 |
| 215 | 1.000000 | 0.720000 | 2 |
| 258 | 1.000000 | 0.810000 | 2 |
| 301 | 1.000000 | 0.700000 | 2 |
| 344 | 1.000000 | 0.800000 | 2 |
| 387 | 1.000000 | 0.740000 | 2 |
| 430 | 1.000000 | 0.823000 | 2 |
| 473 | 1.000000 | 0.741000 | 2 |
| 516 | 1.000000 | 0.620000 | 2 |
| 559 | 1.000000 | 0.820000 | 2 |
| 602 | 1.000000 | 0.720000 | 2 |
| 645 | 1.000000 | 0.660000 | 2 |
| 688 | 1.000000 | 0.620000 | 2 |
| 731 | 1.000000 | 0.720000 | 2 |
| 774 | 1.000000 | 0.700000 | 2 |
| 817 | 1.000000 | 0.661000 | 2 |
| 860 | 1.000000 | 0.720000 | 2 |
| 903 | 1.000000 | 0.660000 | 2 |
| 946 | 1.000000 | 0.780000 | 2 |
| 989 | 1.000000 | 0.700000 | 2 |
| 1,000 | 1.000000 | 0.780000 | 2 |

## Reproduction boundary

```bash
APP_ENV=dev JWT_SECRET='v7-local-test-secret' python scripts/run_v7_sorting_marathon.py --generations 1000 --seed 42 --population-size 50 --report-dir reports/sorting_marathon --checkpoint-path checkpoints/sorting_marathon/population.json
```

All scoring is performed by the bounded typed-AST interpreter. The audit-source block is not executed by this runner. Training cases rotate by generation; the fresh suite is evaluator-owned and uses a distinct seed.
