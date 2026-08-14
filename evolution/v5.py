"""Local-first autonomous evolution primitives for the BEAST v5 workspace.

The worker evolves only against a fixed, local task registry.  A user-supplied
goal selects a task profile but is never evaluated as source code.  Progress is
checkpointed on disk at a coarse interval, so generation steps make no network
requests and a later process can safely resume the same run.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from evolution.lamarckian import CheckpointManager, LamarckianEcosystem, LamarckianOrganism, ParallelEcosystem


class WorkerStateError(RuntimeError):
    """Raised when a lifecycle operation violates the bounded worker state machine."""


@dataclass(frozen=True)
class EvolutionTask:
    """Local objective profile; no network or generated-code execution is involved."""

    task_id: str
    title: str
    keywords: tuple[str, ...]
    trait_targets: Mapping[str, float]
    description: str

    def score(self, organism: LamarckianOrganism, generation: int) -> float:
        genome = organism.genome
        distances = [
            abs(float(getattr(genome, trait)) - target)
            for trait, target in self.trait_targets.items()
        ]
        trait_score = 1.0 - sum(distances) / max(1, len(distances))
        culture_score = min(1.0, organism.complexity / 12.0)
        maturity = min(1.0, generation / 25_000.0)
        return max(0.0, min(1.0, 0.68 * trait_score + 0.22 * culture_score + 0.10 * maturity))


TASKS: tuple[EvolutionTask, ...] = (
    EvolutionTask(
        "primes",
        "Prime number strategy evolution",
        ("prime", "number", "math", "mathematics"),
        {"learning_rate": 0.78, "curiosity": 0.82, "mutation_rate": 0.09, "inheritance_rate": 0.98},
        "Evolves a local computational-mathematics research profile for prime-number strategy studies.",
    ),
    EvolutionTask(
        "sort",
        "Sorting strategy evolution",
        ("sort", "algorithm", "array", "order"),
        {"learning_rate": 0.74, "curiosity": 0.70, "cooperation": 0.56, "mutation_rate": 0.07},
        "Evolves an algorithm-design profile using deterministic local fitness signals.",
    ),
    EvolutionTask(
        "denoise",
        "Signal denoising strategy evolution",
        ("signal", "denoise", "filter", "noise", "audio"),
        {"learning_rate": 0.67, "curiosity": 0.72, "cultural_receptivity": 0.84, "mutation_rate": 0.06},
        "Evolves a local signal-processing research profile with cultural reuse.",
    ),
    EvolutionTask(
        "compress",
        "Compression strategy evolution",
        ("compress", "compression", "corpus", "encoding", "text"),
        {"learning_rate": 0.75, "curiosity": 0.68, "cultural_receptivity": 0.76, "mutation_rate": 0.07},
        "Evolves a deterministic local compression-research profile against a fixed public-domain corpus.",
    ),
    EvolutionTask(
        "maze",
        "Maze pathfinding strategy evolution",
        ("maze", "path", "pathfinding", "route", "grid"),
        {"learning_rate": 0.76, "curiosity": 0.80, "cooperation": 0.48, "mutation_rate": 0.08},
        "Evolves a bounded local pathfinding-research profile against deterministic grid constraints.",
    ),
    EvolutionTask(
        "cooperation",
        "Cooperative tournament evolution",
        ("cooperate", "cooperation", "game", "tournament", "prisoner"),
        {"cooperation": 0.82, "cultural_receptivity": 0.90, "inheritance_rate": 0.97, "mutation_rate": 0.05},
        "Evolves a game-theoretic cooperation profile against a deterministic local objective.",
    ),
    EvolutionTask(
        "general_research",
        "General local research evolution",
        ("research", "learn", "improve", "strategy", "goal"),
        {"learning_rate": 0.70, "curiosity": 0.74, "cooperation": 0.64, "cultural_receptivity": 0.82, "mutation_rate": 0.08},
        "Evolves a bounded, local multi-trait research profile when no narrower benchmark matches.",
    ),
)


def resolve_task(goal: str) -> EvolutionTask:
    """Select a registered local objective from an untrusted natural-language goal."""
    words = set(re.findall(r"[a-z0-9_]+", goal.lower()))
    scored = [
        (sum(keyword in words for keyword in task.keywords), -index, task)
        for index, task in enumerate(TASKS)
    ]
    best = max(scored, key=lambda item: (item[0], item[1]))
    return best[2] if best[0] else TASKS[-1]


class GoalEcosystem(ParallelEcosystem):
    """Canonical Lamarckian ecosystem with one declared, local task objective."""

    def __init__(self, *args: Any, task: EvolutionTask, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.task = task

    def _adaptive_score(self, organism: LamarckianOrganism, environment: Mapping[str, float | str]) -> float:
        baseline = super()._adaptive_score(organism, environment)
        objective = self.task.score(organism, self.generation)
        return max(0.0, min(0.99, 0.40 * baseline + 0.60 * objective))


@dataclass(frozen=True)
class WorkerConfig:
    organism_id: str
    goal: str
    task_id: str
    target_generations: int = 100_000
    population_size: int = 12
    workers: int = 4
    checkpoint_interval: int = 1_000
    seed: int = 42


@dataclass
class WorkerSnapshot:
    organism_id: str
    goal: str
    task_id: str
    status: str
    generation: int
    target_generations: int
    population_size: int
    peak_fitness: float
    average_fitness: float
    cultural_complexity: float
    novelty_count: int
    archive_size: int
    checkpoint_path: str | None
    updated_at: float
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class AutonomousEvolutionWorker:
    """A checkpointed local worker with explicit, durable lifecycle transitions.

    This object is intentionally pull-driven: a CLI, scheduled callback, or
    persistent-worker host calls :meth:`run_batch`.  It never starts an in-process
    timer, never silently spawns unbounded work, and makes no network request per
    generation.  The maximum target remains a resource policy, not a claim that
    arbitrary goals can safely run forever.
    """

    MAX_GENERATIONS = 1_000_000
    ALLOWED_STATUSES = frozenset({"created", "running", "paused", "completed", "cancelled", "failed"})

    def __init__(
        self,
        goal: str,
        workspace: os.PathLike[str] | str,
        *,
        target_generations: int = 100_000,
        population_size: int = 12,
        workers: int = 4,
        checkpoint_interval: int = 1_000,
        seed: int = 42,
        organism_id: str | None = None,
    ) -> None:
        if not goal or len(goal.strip()) < 3:
            raise ValueError("goal must contain at least three non-space characters")
        if not 2 <= population_size <= 256:
            raise ValueError("population_size must be between 2 and 256")
        if not 1 <= workers <= 32:
            raise ValueError("workers must be between 1 and 32")
        if not 1 <= target_generations <= self.MAX_GENERATIONS:
            raise ValueError(f"target_generations must be between 1 and {self.MAX_GENERATIONS}")
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.task = resolve_task(goal)
        self.config = WorkerConfig(
            organism_id=organism_id or f"org-{uuid.uuid4().hex[:12]}",
            goal=goal.strip(),
            task_id=self.task.task_id,
            target_generations=int(target_generations),
            population_size=int(population_size),
            workers=int(workers),
            checkpoint_interval=int(checkpoint_interval),
            seed=int(seed),
        )
        self.checkpoints = CheckpointManager(self.workspace / "checkpoints", interval=checkpoint_interval)
        self.ecosystem = GoalEcosystem(
            archive_path=self.workspace / "memome.sqlite",
            seed=seed,
            population_size=population_size,
            workers=workers,
            task=self.task,
        )
        self._lock = threading.RLock()
        self.status = "created"
        self.error: str | None = None
        self.events: list[dict[str, Any]] = []
        self._write_metadata()

    @property
    def metadata_path(self) -> Path:
        return self.workspace / "worker.json"

    def _record_event(self, event_type: str, **details: Any) -> None:
        self.events.append({"type": event_type, "generation": self.ecosystem.generation, "at": time.time(), **details})
        self.events = self.events[-100:]

    def _write_metadata(self) -> None:
        payload = {"config": asdict(self.config), "status": self.status, "error": self.error, "events": self.events}
        temporary = self.metadata_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.metadata_path)

    @classmethod
    def resume_from_workspace(cls, workspace: os.PathLike[str] | str) -> "AutonomousEvolutionWorker":
        root = Path(workspace)
        payload = json.loads((root / "worker.json").read_text(encoding="utf-8"))
        config = WorkerConfig(**payload["config"])
        worker = cls(
            config.goal,
            root,
            target_generations=config.target_generations,
            population_size=config.population_size,
            workers=config.workers,
            checkpoint_interval=config.checkpoint_interval,
            seed=config.seed,
            organism_id=config.organism_id,
        )
        worker.status = str(payload.get("status", "paused"))
        worker.error = payload.get("error")
        worker.events = list(payload.get("events", []))[-100:]
        worker.checkpoints.restore(worker.ecosystem)
        if worker.status == "running":
            worker.status = "paused"
            worker._record_event("recovered_after_process_exit")
            worker._write_metadata()
        return worker

    def snapshot(self) -> WorkerSnapshot:
        with self._lock:
            stats = self.ecosystem.get_statistics() if self.ecosystem.population else {
                "average_fitness": 0.0,
                "cultural_complexity": 0.0,
                "novelty_count": 0,
                "archive_size": 0,
            }
            latest = self.checkpoints.latest_path()
            return WorkerSnapshot(
                organism_id=self.config.organism_id,
                goal=self.config.goal,
                task_id=self.task.task_id,
                status=self.status,
                generation=self.ecosystem.generation,
                target_generations=self.config.target_generations,
                population_size=self.config.population_size,
                peak_fitness=max((metric.average_fitness for metric in self.ecosystem.history), default=0.0),
                average_fitness=float(stats.get("average_fitness", 0.0)),
                cultural_complexity=float(stats.get("cultural_complexity", 0.0)),
                novelty_count=int(stats.get("novelty_count", 0)),
                archive_size=int(stats.get("archive_size", 0)),
                checkpoint_path=str(latest) if latest else None,
                updated_at=time.time(),
                error=self.error,
                events=list(self.events),
            )

    def request_pause(self) -> WorkerSnapshot:
        with self._lock:
            if self.status == "running":
                self.status = "paused"
                self._record_event("pause_requested")
                self._write_metadata()
            return self.snapshot()

    def request_cancel(self) -> WorkerSnapshot:
        with self._lock:
            if self.status not in {"completed", "cancelled"}:
                self.status = "cancelled"
                self._record_event("cancel_requested")
                self.checkpoints.save(self.ecosystem)
                self._write_metadata()
            return self.snapshot()

    def run_batch(self, generations: int = 1_000) -> WorkerSnapshot:
        """Advance a finite batch locally; checkpoint only at declared boundaries."""
        if generations < 1:
            raise ValueError("generations must be positive")
        with self._lock:
            if self.status in {"completed", "cancelled"}:
                return self.snapshot()
            self.status = "running"
            self.error = None
            self._record_event("batch_started", requested_generations=int(generations))
            self._write_metadata()
        try:
            target = min(self.config.target_generations, self.ecosystem.generation + int(generations))
            if not self.ecosystem.population:
                self.ecosystem.spawn_population()
            while self.ecosystem.generation < target:
                with self._lock:
                    if self.status in {"paused", "cancelled"}:
                        break
                self.ecosystem.step()
                if self.ecosystem.generation % self.checkpoints.interval == 0:
                    self.checkpoints.save(self.ecosystem)
                    self._record_event("checkpoint_saved")
                    self._write_metadata()
            with self._lock:
                if self.ecosystem.generation >= self.config.target_generations:
                    self.status = "completed"
                    self._record_event("completed")
                elif self.status == "running":
                    self.status = "paused"
                    self._record_event("batch_complete")
                self.checkpoints.save(self.ecosystem)
                self._write_metadata()
                return self.snapshot()
        except Exception as error:
            with self._lock:
                self.status = "failed"
                self.error = f"{type(error).__name__}: {error}"
                self._record_event("failed", error=self.error)
                self._write_metadata()
            raise

    def close(self) -> None:
        self.ecosystem.close()


__all__ = [
    "AutonomousEvolutionWorker",
    "EvolutionTask",
    "GoalEcosystem",
    "TASKS",
    "WorkerConfig",
    "WorkerSnapshot",
    "WorkerStateError",
    "resolve_task",
]
