"""Five-stage, contamination-free sorting curriculum for BEAST v9.

The curriculum is a benchmark controller, not a claim that sorting was solved.
It keeps the v8 primitive prohibition intact, measures population-level stage
mastery on evaluator-owned cases, and persists every transition plus optional
cultural seed as JSON data attached to the GP checkpoint.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from dataclasses import dataclass
from statistics import fmean
from typing import Any, Mapping

from evolution.clean_sorting import COMPOSITION_PRIMITIVES, ORDERING_PRIMITIVES, STRUCTURAL_PRIMITIVES
from evolution.fitness import SortingEvaluator
from evolution.gp_engine import GPGenome, Primitive
from evolution.gp_population import GPOrganism, GPPopulation


MASTERY_INDIVIDUAL_CORRECTNESS = 0.95
MASTERY_POPULATION_FRACTION = 0.95
MASTERY_MEAN_CORRECTNESS = 0.90
CHECKPOINT_NAMESPACE = "beast_v9_sorting_curriculum"


@dataclass(frozen=True)
class SortingStage:
    index: int
    identifier: str
    title: str
    primitives: tuple[Primitive, ...]
    length_min: int
    length_max: int
    purpose: str


STAGES: tuple[SortingStage, ...] = (
    SortingStage(0, "pairs", "Pair ordering", STRUCTURAL_PRIMITIVES, 2, 2, "Learn list decomposition and pair reconstruction without comparison primitives."),
    SortingStage(1, "triples", "Three-element ordering", STRUCTURAL_PRIMITIVES + ORDERING_PRIMITIVES, 3, 3, "Introduce generic numeric comparison and conditional list selection."),
    SortingStage(2, "duplicates", "Duplicate preservation", STRUCTURAL_PRIMITIVES + ORDERING_PRIMITIVES, 3, 5, "Require sorting while retaining repeated values and list cardinality."),
    SortingStage(3, "negatives", "Negative-value ordering", STRUCTURAL_PRIMITIVES + ORDERING_PRIMITIVES, 4, 6, "Require ordering across negative, zero, and positive values."),
    SortingStage(4, "up-to-16", "Lists up to sixteen elements", STRUCTURAL_PRIMITIVES + ORDERING_PRIMITIVES + COMPOSITION_PRIMITIVES, 2, 16, "Permit generic concatenation for larger compositional programs."),
)
PROHIBITED_PRIMITIVES = ("sort1", "map_sq", "filter_pos", "unique", "reverse1", "sum1")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class V9CleanSortingEvaluator(SortingEvaluator):
    """Five deterministic input domains sharing the v8 clean primitive boundary."""

    task_profile = "clean-sorting-v9-five-stage"

    def __init__(self, stage_index: int = 0) -> None:
        self.set_stage(stage_index)

    @property
    def stage(self) -> SortingStage:
        return STAGES[self.stage_index]

    def set_stage(self, stage_index: int) -> None:
        if not 0 <= stage_index < len(STAGES):
            raise ValueError("v9 clean-sorting stage index is out of range")
        self.stage_index = stage_index

    def checkpoint_state(self) -> dict[str, Any]:
        return {"profile": self.task_profile, "stage_index": self.stage_index}

    def restore_checkpoint_state(self, state: Mapping[str, Any]) -> None:
        if state.get("profile") != self.task_profile:
            raise ValueError("checkpoint evaluator profile does not match v9 clean sorting")
        self.set_stage(int(state["stage_index"]))

    def generate_test_cases(self, seed: int, n: int = 20) -> list[tuple[list[int], list[int]]]:
        rng = random.Random(seed)
        stage = self.stage
        cases: list[tuple[list[int], list[int]]] = []
        for _ in range(n):
            size = rng.randint(stage.length_min, stage.length_max)
            if stage.identifier == "duplicates":
                values = [rng.randint(-2, 2) for _ in range(size)]
            elif stage.identifier == "negatives":
                values = [rng.randint(-50, 50) for _ in range(size)]
                values[0] = -rng.randint(1, 50)
            else:
                values = [rng.randint(-50, 50) for _ in range(size)]
            cases.append((values, sorted(values)))
        return cases


class FiveStageSortingCurriculum:
    """Stateful controller with explicit mastery, culture, and resume records."""

    schema = "beast-v9-five-stage-sorting-curriculum-v1"

    def __init__(self, *, archive: list[dict[str, Any]] | None = None, events: list[dict[str, Any]] | None = None) -> None:
        self.archive = copy.deepcopy(archive or [])
        self.events = copy.deepcopy(events or [])

    @staticmethod
    def _evaluator(population: GPPopulation) -> V9CleanSortingEvaluator:
        if not isinstance(population.evaluator, V9CleanSortingEvaluator):
            raise TypeError("five-stage curriculum requires V9CleanSortingEvaluator")
        return population.evaluator

    def bind(self, population: GPPopulation) -> None:
        """Apply the evaluator's active primitive profile and checkpoint controller state."""
        evaluator = self._evaluator(population)
        population.set_primitive_profile(
            STAGES[evaluator.stage_index].primitives,
            primitive_profile_name="task-specific",
        )
        population.set_checkpoint_metadata(CHECKPOINT_NAMESPACE, self.to_state())

    def to_state(self) -> dict[str, Any]:
        return {"schema": self.schema, "archive": copy.deepcopy(self.archive), "events": copy.deepcopy(self.events)}

    @classmethod
    def from_population(cls, population: GPPopulation) -> "FiveStageSortingCurriculum":
        stored = population.checkpoint_metadata(CHECKPOINT_NAMESPACE)
        if stored is None:
            return cls()
        if stored.get("schema") != cls.schema:
            raise ValueError("unsupported v9 clean-sorting curriculum checkpoint state")
        return cls(archive=list(stored.get("archive", [])), events=list(stored.get("events", [])))

    @staticmethod
    def _mastery_measurement(population: GPPopulation, *, seed: int, cases: int) -> tuple[float, float]:
        results = population.evaluator.batch_evaluate([organism.genome for organism in population.population], seed=seed, n=cases)
        individual_mastery_fraction = sum(result.correctness >= MASTERY_INDIVIDUAL_CORRECTNESS for result in results) / len(results)
        return individual_mastery_fraction, fmean(result.correctness for result in results)

    def _archive_champion(self, population: GPPopulation, *, stage_index: int, measurement: Mapping[str, Any]) -> dict[str, Any]:
        champion = population.champion
        genome = champion.genome.to_dict()
        entry = {
            "schema": "beast-v9-cultural-seed-v1",
            "tree_sha256": _digest(genome),
            "genome": genome,
            "source_stage_index": stage_index,
            "source_stage_id": STAGES[stage_index].identifier,
            "population_generation": population.generation,
            "mastery_measurement": dict(measurement),
        }
        self.archive.append(entry)
        return entry

    def _inject_latest_verified_seed(self, population: GPPopulation) -> dict[str, Any]:
        if not self.archive:
            return {"injected": False, "reason": "no verified prior-stage culture"}
        evaluator = self._evaluator(population)
        seed = self.archive[-1]
        genome = GPGenome.from_dict(seed["genome"], primitives=population.builder.primitives)
        used = {name for name in genome.primitives_used}
        if used.intersection(PROHIBITED_PRIMITIVES):
            return {"injected": False, "reason": "prohibited primitive in archived culture"}
        if genome.tree.result_type != evaluator.output_type:
            return {"injected": False, "reason": "typed output does not match active evaluator"}
        replacement_index = min(range(len(population.population)), key=lambda index: population._selection_score(population.population[index]))
        population.population[replacement_index] = GPOrganism(
            organism_id=f"cultural-{seed['tree_sha256'][:12]}",
            genome=genome,
            generation=population.generation,
            parent_ids=[f"culture:{seed['tree_sha256']}"],
            cultural_strategies=1,
        )
        # The inherited program is re-scored exclusively by the new stage's
        # evaluator before it can influence a later selection decision.
        population._evaluate_current()
        return {
            "injected": True,
            "tree_sha256": seed["tree_sha256"],
            "source_stage_index": seed["source_stage_index"],
            "replacement_index": replacement_index,
        }

    def evaluate_and_advance(self, population: GPPopulation, *, cases: int = 100, seed: int | None = None) -> dict[str, Any]:
        """Measure the entire population and conditionally advance one stage.

        A transition requires **both** at least 95% of organisms to obtain at
        least 95% correctness and a population mean correctness of at least 0.90
        on a fresh evaluator-owned suite. It is intentionally harder than a
        single champion promotion and emits an event even on failure.
        """
        if cases < 20:
            raise ValueError("curriculum mastery cases must be at least 20")
        evaluator = self._evaluator(population)
        before = evaluator.stage_index
        measured_seed = population.generation + 770_000 if seed is None else int(seed)
        population_fraction, mean_correctness = self._mastery_measurement(population, seed=measured_seed, cases=cases)
        measurement = {
            "generation": population.generation,
            "seed": measured_seed,
            "cases": cases,
            "stage_index_before": before,
            "stage_id_before": STAGES[before].identifier,
            "individual_mastery_threshold": MASTERY_INDIVIDUAL_CORRECTNESS,
            "population_mastery_fraction": population_fraction,
            "population_mastery_required": MASTERY_POPULATION_FRACTION,
            "mean_correctness": mean_correctness,
            "mean_correctness_required": MASTERY_MEAN_CORRECTNESS,
        }
        eligible = population_fraction >= MASTERY_POPULATION_FRACTION and mean_correctness >= MASTERY_MEAN_CORRECTNESS
        at_final_stage = before == len(STAGES) - 1
        event: dict[str, Any] = measurement | {
            "advanced": bool(eligible and not at_final_stage),
            "stage_index_after": before,
            "stage_id_after": STAGES[before].identifier,
            "culture": {"injected": False, "reason": "stage not advanced"},
        }
        if eligible and not at_final_stage:
            archived = self._archive_champion(population, stage_index=before, measurement=measurement)
            evaluator.set_stage(before + 1)
            self.bind(population)
            event["stage_index_after"] = evaluator.stage_index
            event["stage_id_after"] = evaluator.stage.identifier
            event["culture"] = {"archived_tree_sha256": archived["tree_sha256"]} | self._inject_latest_verified_seed(population)
        elif at_final_stage and eligible:
            event["culture"] = {"injected": False, "reason": "final stage mastered; no further stage exists"}
        self.events.append(event)
        population.set_checkpoint_metadata(CHECKPOINT_NAMESPACE, self.to_state())
        return copy.deepcopy(event)


def primitive_manifest() -> dict[str, Any]:
    """Return the profile definition used by a v9 pre-registration or audit."""
    return {
        "profile": V9CleanSortingEvaluator.task_profile,
        "stages": [
            {
                "index": stage.index,
                "id": stage.identifier,
                "title": stage.title,
                "primitive_names": [primitive.name for primitive in stage.primitives],
                "length_range": [stage.length_min, stage.length_max],
                "purpose": stage.purpose,
            }
            for stage in STAGES
        ],
        "explicitly_prohibited_names": list(PROHIBITED_PRIMITIVES),
        "mastery_rule": {
            "individual_correctness": MASTERY_INDIVIDUAL_CORRECTNESS,
            "population_fraction": MASTERY_POPULATION_FRACTION,
            "mean_correctness": MASTERY_MEAN_CORRECTNESS,
        },
    }


__all__ = [
    "CHECKPOINT_NAMESPACE",
    "FiveStageSortingCurriculum",
    "STAGES",
    "V9CleanSortingEvaluator",
    "primitive_manifest",
]
