"""Capability-bounded, contamination-free sorting task profiles for BEAST v8.

The curriculum intentionally exposes only generic list construction, arithmetic,
comparison, conditional selection, and list concatenation.  It contains no
complete sorting, ranking, partitioning, map/filter, unique, or reverse
operation.  This module creates a new benchmark profile and never rewrites the
historical v7 sorting artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

from evolution.fitness import SortingEvaluator
from evolution.gp_engine import ARITHMETIC_PRIMITIVES, BOOLEAN_PRIMITIVES, GENERIC_LIST_CONTROL_PRIMITIVES, LIST_PRIMITIVES, Primitive

_BY_NAME = {
    primitive.name: primitive
    for primitive in (*ARITHMETIC_PRIMITIVES, *BOOLEAN_PRIMITIVES, *LIST_PRIMITIVES)
}

STRUCTURAL_PRIMITIVES: tuple[Primitive, ...] = tuple(
    _BY_NAME[name] for name in ("head", "tail", "cons", "length")
)
ORDERING_PRIMITIVES: tuple[Primitive, ...] = tuple(
    _BY_NAME[name] for name in ("add", "sub", "neg", "min2", "max2", "gt", "lt", "eq")
) + tuple(primitive for primitive in GENERIC_LIST_CONTROL_PRIMITIVES if primitive.name == "choose_list")
COMPOSITION_PRIMITIVES: tuple[Primitive, ...] = tuple(
    primitive for primitive in GENERIC_LIST_CONTROL_PRIMITIVES if primitive.name == "concat_lists"
)


@dataclass(frozen=True)
class CurriculumPhase:
    name: str
    starts_at_generation: int
    primitives: tuple[Primitive, ...]
    purpose: str


PHASES: tuple[CurriculumPhase, ...] = (
    CurriculumPhase(
        "structural", 0, STRUCTURAL_PRIMITIVES,
        "Expose list decomposition and reconstruction only.",
    ),
    CurriculumPhase(
        "ordering", 200, STRUCTURAL_PRIMITIVES + ORDERING_PRIMITIVES,
        "Add arithmetic comparisons and generic conditional list selection.",
    ),
    CurriculumPhase(
        "composition", 1_000, STRUCTURAL_PRIMITIVES + ORDERING_PRIMITIVES + COMPOSITION_PRIMITIVES,
        "Add generic list concatenation for larger compositional programs.",
    ),
)

CURRICULUM_LENGTHS = (2, 3, 5, 10)
CURRICULUM_MASTERY = 0.95


class CleanSortingEvaluator(SortingEvaluator):
    """Sorting objective with an explicit, stateful curriculum-length boundary."""

    task_profile = "clean-sorting-v1"

    def __init__(self, stage_index: int = 0) -> None:
        self.set_stage(stage_index)

    @property
    def stage_length(self) -> int:
        return CURRICULUM_LENGTHS[self.stage_index]

    def set_stage(self, stage_index: int) -> None:
        if not 0 <= stage_index < len(CURRICULUM_LENGTHS):
            raise ValueError("clean sorting stage index is out of range")
        self.stage_index = stage_index

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[list[int], list[int]]]:
        rng = random.Random(seed)
        return [
            (values := [rng.randint(-50, 50) for _ in range(self.stage_length)], sorted(values))
            for _ in range(n)
        ]


class CleanSortingCurriculum:
    """Select and apply a fixed, reproducible capability phase by generation."""

    @staticmethod
    def phase_for_generation(generation: int) -> CurriculumPhase:
        if generation < 0:
            raise ValueError("generation must be non-negative")
        return max((phase for phase in PHASES if phase.starts_at_generation <= generation), key=lambda phase: phase.starts_at_generation)

    @classmethod
    def apply_to_population(cls, population) -> CurriculumPhase:
        phase = cls.phase_for_generation(population.generation)
        population.set_primitive_profile(phase.primitives)
        return phase

    @classmethod
    def advance_if_mastered(cls, population, *, cases: int = 100, seed: int | None = None) -> dict[str, object]:
        """Advance one task stage only on evaluator-owned 95% mastery evidence."""
        evaluator = population.evaluator
        if not isinstance(evaluator, CleanSortingEvaluator):
            raise TypeError("clean curriculum requires CleanSortingEvaluator")
        evaluated_seed = population.generation + 70_000 if seed is None else seed
        champion = population.champion
        result = evaluator.batch_evaluate([champion.genome], seed=evaluated_seed, n=cases)[0]
        advanced = result.correctness >= CURRICULUM_MASTERY and evaluator.stage_index < len(CURRICULUM_LENGTHS) - 1
        if advanced:
            evaluator.set_stage(evaluator.stage_index + 1)
        return {
            "generation": population.generation,
            "seed": evaluated_seed,
            "cases": cases,
            "mastery": result.correctness,
            "stage_index_before": evaluator.stage_index - 1 if advanced else evaluator.stage_index,
            "stage_index_after": evaluator.stage_index,
            "advanced": advanced,
        }


def clean_primitive_manifest() -> dict[str, object]:
    all_primitives = tuple(dict.fromkeys(primitive.name for phase in PHASES for primitive in phase.primitives))
    prohibited = ("sort1", "map_sq", "filter_pos", "unique", "reverse1", "sum1")
    return {
        "profile": CleanSortingEvaluator.task_profile,
        "phases": [
            {
                "name": phase.name,
                "starts_at_generation": phase.starts_at_generation,
                "primitive_names": [primitive.name for primitive in phase.primitives],
                "purpose": phase.purpose,
            }
            for phase in PHASES
        ],
        "all_primitive_names": list(all_primitives),
        "explicitly_prohibited_names": list(prohibited),
    }
