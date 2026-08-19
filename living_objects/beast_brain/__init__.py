"""Evidence-first local contracts for BEAST-BRAIN research experiments.

This package deliberately contains no model runtime, HTTP client, scheduler, or
external-service integration. It defines provenance and experiment records that
must exist before those later, separately authorized research steps are assessed.
"""

from .provenance import (
    ArtifactMeasurement,
    ExperienceRecord,
    ExperimentPlan,
    ExperimentResult,
    ProvenanceError,
    SourceKind,
    SourceReference,
)
from .collectors import (
    collect_champion_card,
    collect_evaluator_case_cards,
    collect_primitive_cards,
    write_jsonl_new,
)

__all__ = [
    "ArtifactMeasurement",
    "ExperienceRecord",
    "ExperimentPlan",
    "ExperimentResult",
    "ProvenanceError",
    "SourceKind",
    "SourceReference",
    "collect_champion_card",
    "collect_evaluator_case_cards",
    "collect_primitive_cards",
    "write_jsonl_new",
]
