from .common import LocalTaskDescriptor

TASK = LocalTaskDescriptor(
    "primes", "Prime-number research profile", "evolve a prime number algorithm",
    ("deterministic integer inputs", "known prime/non-prime cases", "no network"),
    {"upper_bound": 10_000, "cases": 256},
)
