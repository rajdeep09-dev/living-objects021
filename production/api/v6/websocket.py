"""Real bounded GP-generation events and an in-memory WebSocket broadcaster.

The broadcaster owns interpreter-only :class:`GPPopulation` instances keyed by
named task domain.  It accepts no source code and emits an event only after an
actual ``population.step()`` has completed.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from pydantic import BaseModel, Field

from evolution.fitness import FitnessEvaluator
from evolution.gp_population import GPPopulation


class ProgramEvolvedEvent(BaseModel):
    event_type: str = "gp_generation_completed"
    run_id: str = Field(min_length=8, max_length=96)
    task_domain: str = Field(min_length=1, max_length=64)
    generation: int = Field(ge=1)
    best_fitness: float = Field(ge=0.0, le=1.0)
    avg_fitness: float = Field(ge=0.0, le=1.0)
    champion_code: str = Field(min_length=1, max_length=16_384)
    champion_size_nodes: int = Field(ge=1, le=64)


class ProgramRejectedEvent(BaseModel):
    event_type: str = "program_rejected"
    run_id: str = Field(min_length=8, max_length=96)
    reason: str = Field(min_length=1, max_length=160)


class LiveGPPopulationBroadcaster:
    """Keep one real, bounded population per task and fan out real step events."""

    def __init__(self, *, max_events: int = 500, client_queue_size: int = 50) -> None:
        self.max_events = max_events
        self.client_queue_size = client_queue_size
        self.populations: dict[str, GPPopulation] = {}
        self.run_ids: dict[str, str] = {}
        self._configurations: dict[str, tuple[int, int]] = {}
        self.history: list[dict[str, Any]] = []
        self.clients: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()
        self._step_lock = asyncio.Lock()

    async def advance(
        self,
        *,
        task_domain: str,
        evaluator: FitnessEvaluator,
        population_size: int,
        seed: int,
        steps: int,
    ) -> list[dict[str, Any]]:
        """Advance the task-owned population and publish one event per real step."""

        if steps <= 0:
            raise ValueError("steps must be positive")
        configuration = (population_size, seed)
        async with self._step_lock:
            population = self.populations.get(task_domain)
            if population is None:
                population = GPPopulation(evaluator=evaluator, population_size=population_size, seed=seed)
                population.initialize()
                self.populations[task_domain] = population
                self.run_ids[task_domain] = f"v7-{uuid.uuid4().hex[:20]}"
                self._configurations[task_domain] = configuration
            elif self._configurations[task_domain] != configuration:
                raise ValueError(
                    "task domain already has a live population; retain its population_size and seed"
                )

            emitted: list[dict[str, Any]] = []
            for _ in range(steps):
                stats = population.step()
                champion = population.champion
                event = ProgramEvolvedEvent(
                    run_id=self.run_ids[task_domain],
                    task_domain=task_domain,
                    generation=stats.generation,
                    best_fitness=stats.best_fitness,
                    avg_fitness=stats.average_fitness,
                    champion_code=champion.genome.to_python(
                        f"evolved_{task_domain}_generation_{stats.generation}"
                    ),
                    champion_size_nodes=champion.genome.complexity(),
                ).model_dump()
                await self.publish(event)
                emitted.append(event)
            return emitted

    def population_for(self, task_domain: str) -> GPPopulation:
        try:
            return self.populations[task_domain]
        except KeyError as exc:
            raise RuntimeError("task domain has no initialized live population") from exc

    async def publish(self, event: dict[str, Any]) -> None:
        async with self._lock:
            self.history.append(event)
            self.history = self.history[-self.max_events :]
            for client in list(self.clients):
                if client.full():
                    try:
                        client.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                client.put_nowait(event)

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.client_queue_size)
        async with self._lock:
            self.clients.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self.clients.discard(queue)
