"""Local, explicit cross-task transfer scoring; source code is never executed here."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping


class TransferLearningEngine:
    def transfer_score(
        self,
        organism: Any,
        source_task: str,
        target_task: str,
        target_fitness_fn: Callable[[str, int], float],
    ) -> float:
        if source_task == target_task:
            return 0.0
        scores = []
        for strategy in getattr(organism, "learned_strategies", {}).values():
            domain = str(getattr(strategy, "task_domain", source_task))
            if domain != source_task:
                continue
            score = float(target_fitness_fn(str(getattr(strategy, "source_code", "")), 0))
            scores.append(max(0.0, min(1.0, score)))
        return max(scores, default=0.0)

    def cross_task_fitness_bonus(
        self,
        organism: Any,
        source_task: str,
        fitness_fns: Mapping[str, Callable[[str, int], float]],
    ) -> float:
        values = [self.transfer_score(organism, source_task, task, fn) for task, fn in fitness_fns.items()]
        return round(sum(values) / max(1, len(values)), 6)


__all__ = ["TransferLearningEngine"]
