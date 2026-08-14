"""Deterministic, local benchmark task descriptors for BEAST v5."""

from .task_compress import TASK as COMPRESS_TASK
from .task_denoise import TASK as DENOISE_TASK
from .task_maze import TASK as MAZE_TASK
from .task_primes import TASK as PRIMES_TASK
from .task_prisoners_dilemma import TASK as PRISONERS_DILEMMA_TASK
from .task_sort import TASK as SORT_TASK

TASKS = {
    task.task_id: task
    for task in (PRIMES_TASK, COMPRESS_TASK, SORT_TASK, PRISONERS_DILEMMA_TASK, DENOISE_TASK, MAZE_TASK)
}

__all__ = ["TASKS"]
