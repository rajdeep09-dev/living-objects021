"""Task metadata only: local scoring contracts, never arbitrary strategy execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LocalTaskDescriptor:
    task_id: str
    title: str
    goal_hint: str
    acceptance_checks: tuple[str, ...]
    fixed_inputs: Mapping[str, str | int | float]

