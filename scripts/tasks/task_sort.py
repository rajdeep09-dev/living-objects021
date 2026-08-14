from .common import LocalTaskDescriptor

TASK = LocalTaskDescriptor(
    "sort", "Sorting research profile", "evolve a sorting algorithm",
    ("fixed seeded arrays", "stable ordering checks", "no network"),
    {"array_count": 200, "max_length": 256},
)
