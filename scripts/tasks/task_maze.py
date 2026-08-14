from .common import LocalTaskDescriptor

TASK = LocalTaskDescriptor(
    "maze", "Pathfinding research profile", "evolve a maze pathfinding strategy",
    ("fixed seeded grid mazes", "path validity checks", "no network"),
    {"grid_size": 32, "mazes": 64},
)
