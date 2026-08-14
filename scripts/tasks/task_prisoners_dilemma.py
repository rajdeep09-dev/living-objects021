from .common import LocalTaskDescriptor

TASK = LocalTaskDescriptor(
    "cooperation", "Prisoner's Dilemma research profile", "evolve a cooperative tournament strategy",
    ("fixed opponent registry", "deterministic payoff matrix", "no network"),
    {"rounds": 200, "opponents": 8},
)
