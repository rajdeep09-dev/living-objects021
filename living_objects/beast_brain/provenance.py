"""Strict provenance contracts for bounded BEAST-BRAIN experiments.

The records in this module prevent a common research failure mode: attaching
plausible-looking, but unmeasured, fitness values to synthetic or teacher data.
Only ``real_beast_run`` records may contain fitness measurements, and each such
measurement must be traceable to a content-hashed local BEAST artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


class ProvenanceError(ValueError):
    """Raised when a research record cannot satisfy the evidence contract."""


class SourceKind(str, Enum):
    """Permitted origins for BEAST-BRAIN training or experiment records."""

    REAL_BEAST_RUN = "real_beast_run"
    SYNTHETIC = "synthetic"
    TEACHER_GENERATED = "teacher_generated"


def _require_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError(f"{field_name} must be a non-empty string")


def _finite_score(value: float, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ProvenanceError(f"{field_name} must be a finite numeric value")
    if not 0.0 <= float(value) <= 1.0:
        raise ProvenanceError(f"{field_name} must be between 0.0 and 1.0")


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _follow_path(payload: Any, field_path: Sequence[str]) -> Any:
    current = payload
    for key in field_path:
        if not isinstance(current, Mapping) or key not in current:
            joined = ".".join(field_path)
            raise ProvenanceError(f"artifact does not contain measured field {joined!r}")
        current = current[key]
    return current


@dataclass(frozen=True)
class SourceReference:
    """Origin metadata for a record, with strict source-specific requirements."""

    kind: SourceKind
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    teacher_model: str | None = None
    teacher_version: str | None = None
    prompt_template_id: str | None = None
    note: str = ""

    def validate(self) -> None:
        if self.kind is SourceKind.REAL_BEAST_RUN:
            _require_nonempty(self.artifact_path or "", "artifact_path")
            digest = self.artifact_sha256 or ""
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ProvenanceError("artifact_sha256 must be a lower-case SHA-256 digest")
            if any(value is not None for value in (self.teacher_model, self.teacher_version, self.prompt_template_id)):
                raise ProvenanceError("real_beast_run records cannot be labelled as teacher-generated")
        elif self.kind is SourceKind.SYNTHETIC:
            if self.artifact_path is not None or self.artifact_sha256 is not None:
                raise ProvenanceError("synthetic records cannot cite a measured BEAST artifact")
            if any(value is not None for value in (self.teacher_model, self.teacher_version, self.prompt_template_id)):
                raise ProvenanceError("synthetic records cannot carry teacher metadata")
        elif self.kind is SourceKind.TEACHER_GENERATED:
            _require_nonempty(self.teacher_model or "", "teacher_model")
            _require_nonempty(self.teacher_version or "", "teacher_version")
            _require_nonempty(self.prompt_template_id or "", "prompt_template_id")
            if self.artifact_path is not None or self.artifact_sha256 is not None:
                raise ProvenanceError("teacher-generated records cannot cite a measured BEAST artifact")
        else:  # Defensive for data decoded outside type checkers.
            raise ProvenanceError(f"unsupported source kind: {self.kind!r}")

    def to_dict(self) -> dict[str, str | None]:
        self.validate()
        return {
            "kind": self.kind.value,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "teacher_model": self.teacher_model,
            "teacher_version": self.teacher_version,
            "prompt_template_id": self.prompt_template_id,
            "note": self.note,
        }


@dataclass(frozen=True)
class ArtifactMeasurement:
    """One objectively measured score bound to an immutable local artifact."""

    artifact_path: str
    artifact_sha256: str
    field_path: tuple[str, ...]
    value: float

    @classmethod
    def from_artifact(cls, artifact_path: str | Path, field_path: Sequence[str]) -> "ArtifactMeasurement":
        path = Path(artifact_path)
        raw = path.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProvenanceError(f"artifact is not valid UTF-8 JSON: {path}") from exc
        normalized_path = tuple(str(part) for part in field_path)
        if not normalized_path or any(not part for part in normalized_path):
            raise ProvenanceError("field_path must contain one or more non-empty object keys")
        value = _follow_path(payload, normalized_path)
        _finite_score(value, "artifact measurement")
        return cls(
            artifact_path=str(path),
            artifact_sha256=hashlib.sha256(raw).hexdigest(),
            field_path=normalized_path,
            value=float(value),
        )

    def verify(self) -> None:
        _require_nonempty(self.artifact_path, "artifact_path")
        if len(self.artifact_sha256) != 64 or any(char not in "0123456789abcdef" for char in self.artifact_sha256):
            raise ProvenanceError("artifact_sha256 must be a lower-case SHA-256 digest")
        if not self.field_path or any(not isinstance(part, str) or not part for part in self.field_path):
            raise ProvenanceError("field_path must contain one or more non-empty object keys")
        _finite_score(self.value, "artifact measurement")
        raw = Path(self.artifact_path).read_bytes()
        actual_digest = hashlib.sha256(raw).hexdigest()
        if actual_digest != self.artifact_sha256:
            raise ProvenanceError("artifact content no longer matches the recorded SHA-256 digest")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProvenanceError("artifact is not valid UTF-8 JSON") from exc
        actual_value = _follow_path(payload, self.field_path)
        _finite_score(actual_value, "artifact measurement")
        if float(actual_value) != float(self.value):
            raise ProvenanceError("artifact measurement value no longer matches the recorded field")

    def to_dict(self) -> dict[str, Any]:
        self.verify()
        return {
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "field_path": list(self.field_path),
            "value": self.value,
        }


@dataclass(frozen=True)
class ExperienceRecord:
    """A BEAST-BRAIN decision trajectory with source-aware fitness semantics."""

    task: str
    state: str
    available_actions: tuple[str, ...]
    action: str
    observation: str
    source: SourceReference
    success: bool | None
    fitness_before: ArtifactMeasurement | None = None
    fitness_after: ArtifactMeasurement | None = None

    def validate(self) -> None:
        _require_nonempty(self.task, "task")
        _require_nonempty(self.state, "state")
        _require_nonempty(self.action, "action")
        _require_nonempty(self.observation, "observation")
        if not self.available_actions or any(not isinstance(item, str) or not item.strip() for item in self.available_actions):
            raise ProvenanceError("available_actions must contain non-empty action labels")
        if self.action not in self.available_actions:
            raise ProvenanceError("action must be one of available_actions")
        self.source.validate()
        measurements = (self.fitness_before, self.fitness_after)
        if self.source.kind is SourceKind.REAL_BEAST_RUN:
            if any(measurement is None for measurement in measurements):
                raise ProvenanceError("real_beast_run records require both measured fitness references")
            for measurement in measurements:
                assert measurement is not None
                measurement.verify()
                if measurement.artifact_path != self.source.artifact_path:
                    raise ProvenanceError("measurement artifact_path must match the real-run source")
                if measurement.artifact_sha256 != self.source.artifact_sha256:
                    raise ProvenanceError("measurement digest must match the real-run source")
        elif any(measurement is not None for measurement in measurements):
            raise ProvenanceError("synthetic and teacher-generated records cannot contain measured fitness values")

    def record_id(self) -> str:
        self.validate()
        return hashlib.sha256(_canonical_json(self.to_dict(include_id=False))).hexdigest()

    def to_dict(self, *, include_id: bool = True) -> dict[str, Any]:
        self.validate()
        payload: dict[str, Any] = {
            "schema_version": "beast-brain-experience-v1",
            "task": self.task,
            "state": self.state,
            "available_actions": list(self.available_actions),
            "action": self.action,
            "observation": self.observation,
            "source": self.source.to_dict(),
            "success": self.success,
            "fitness_before": self.fitness_before.to_dict() if self.fitness_before else None,
            "fitness_after": self.fitness_after.to_dict() if self.fitness_after else None,
        }
        if include_id:
            payload["record_id"] = self.record_id()
        return payload


@dataclass(frozen=True)
class ExperimentPlan:
    """A preregistered local comparison budget, written before its results."""

    experiment_id: str
    task: str
    seeds: tuple[int, ...]
    generations: int
    population_size: int
    baseline_label: str = "baseline"
    assisted_label: str = "beast_brain_assisted"

    def validate(self) -> None:
        _require_nonempty(self.experiment_id, "experiment_id")
        _require_nonempty(self.task, "task")
        _require_nonempty(self.baseline_label, "baseline_label")
        _require_nonempty(self.assisted_label, "assisted_label")
        if self.baseline_label == self.assisted_label:
            raise ProvenanceError("baseline_label and assisted_label must differ")
        if not self.seeds or any(not isinstance(seed, int) or isinstance(seed, bool) or seed < 0 for seed in self.seeds):
            raise ProvenanceError("seeds must contain one or more non-negative integers")
        if len(set(self.seeds)) != len(self.seeds):
            raise ProvenanceError("seeds must be unique")
        if not isinstance(self.generations, int) or isinstance(self.generations, bool) or self.generations < 1:
            raise ProvenanceError("generations must be a positive integer")
        if not isinstance(self.population_size, int) or isinstance(self.population_size, bool) or self.population_size < 1:
            raise ProvenanceError("population_size must be a positive integer")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": "beast-brain-experiment-plan-v1",
            "experiment_id": self.experiment_id,
            "task": self.task,
            "seeds": list(self.seeds),
            "generations": self.generations,
            "population_size": self.population_size,
            "baseline_label": self.baseline_label,
            "assisted_label": self.assisted_label,
        }

    def write_new(self, path: str | Path) -> Path:
        """Create a plan once; refusing overwrite enforces preregistration order."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = _canonical_json(self.to_dict()) + b"\n"
        try:
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ProvenanceError(f"experiment plan already exists: {target}") from exc
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
        return target


@dataclass(frozen=True)
class ExperimentResult:
    """One condition/seed outcome whose primary score is a verified artifact field."""

    plan: ExperimentPlan
    condition: str
    seed: int
    score: ArtifactMeasurement

    def validate(self) -> None:
        self.plan.validate()
        if self.condition not in {self.plan.baseline_label, self.plan.assisted_label}:
            raise ProvenanceError("condition must be the plan baseline or assisted label")
        if self.seed not in self.plan.seeds:
            raise ProvenanceError("result seed must appear in the preregistered plan")
        self.score.verify()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "experiment_id": self.plan.experiment_id,
            "condition": self.condition,
            "seed": self.seed,
            "score": self.score.to_dict(),
        }
