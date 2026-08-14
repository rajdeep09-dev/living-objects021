"""Atomic local control state for bounded, checkpointable GP runs.

This is intentionally thread-free: a server or worker calls ``advance`` in its
own controlled loop.  It provides no network client, arbitrary code execution,
or external side effect path.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from evolution.gp_population import GPPopulation


@dataclass(frozen=True)
class GPControlSnapshot:
    state: str
    generation: int
    generation_budget: int
    best_fitness: float
    checkpoint_path: str


class GPRunController:
    VALID_STATES = {"ready", "running", "paused", "cancelled", "completed"}

    def __init__(self, population: GPPopulation, generation_budget: int, checkpoint_path: str | Path) -> None:
        if not 1 <= generation_budget <= 1_000_000:
            raise ValueError("generation_budget must be in 1..1_000_000")
        self.population = population
        self.generation_budget = generation_budget
        self.checkpoint_path = Path(checkpoint_path)
        self.state = "ready"

    @classmethod
    def resume_from_checkpoint(cls, evaluator, checkpoint_path: str | Path) -> "GPRunController":
        path = Path(checkpoint_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        control = dict(payload.get("control", {}))
        population = GPPopulation.from_checkpoint_payload(evaluator, payload)
        controller = cls(population, int(control.get("generation_budget", max(1, population.generation))), path)
        controller.state = str(control.get("state", "paused"))
        if controller.state not in cls.VALID_STATES:
            raise ValueError("invalid checkpoint control state")
        return controller

    def start(self) -> GPControlSnapshot:
        if self.state in {"cancelled", "completed"}:
            return self.snapshot()
        self.state = "running"
        return self.snapshot()

    def pause(self) -> GPControlSnapshot:
        if self.state == "running":
            self.state = "paused"
            self.checkpoint()
        return self.snapshot()

    def resume(self) -> GPControlSnapshot:
        if self.state == "paused":
            self.state = "running"
        return self.snapshot()

    def cancel(self) -> GPControlSnapshot:
        if self.state not in {"completed", "cancelled"}:
            self.state = "cancelled"
            self.checkpoint()
        return self.snapshot()

    def advance(self, generations: int = 1) -> GPControlSnapshot:
        if generations < 1:
            raise ValueError("generations must be positive")
        if self.state != "running":
            return self.snapshot()
        if not self.population.population:
            self.population.initialize()
        remaining = max(0, self.generation_budget - self.population.generation)
        for _ in range(min(generations, remaining)):
            if self.state != "running":
                break
            self.population.step()
        if self.population.generation >= self.generation_budget:
            self.state = "completed"
        self.checkpoint()
        return self.snapshot()

    def checkpoint(self) -> None:
        payload = self.population.checkpoint_payload()
        payload["control"] = {"state": self.state, "generation_budget": self.generation_budget}
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.checkpoint_path.with_suffix(self.checkpoint_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.checkpoint_path)

    def snapshot(self) -> GPControlSnapshot:
        best_fitness = self.population.champion.fitness if self.population.population else 0.0
        return GPControlSnapshot(self.state, self.population.generation, self.generation_budget, best_fitness, str(self.checkpoint_path))


__all__ = ["GPControlSnapshot", "GPRunController"]
