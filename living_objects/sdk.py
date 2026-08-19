"""Stable local SDK for bounded, evidence-first BEAST experiments.

The four public functions intentionally delegate to the typed-AST interpreter
and persisted v8 evidence.  Exported source is an audit artifact only: the SDK
never evaluates it with ``exec`` or a compiler.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from evolution.fitness import ManhattanDistanceEvaluator
from evolution.gp_engine import GPGenome
from evolution.gp_population import GPPopulation
from evolution.polyglot_export import PolyglotCompiler
from evolution.v9_sorting_curriculum import FiveStageSortingCurriculum, STAGES, V9CleanSortingEvaluator
try:
    from agnes_brain.client import AgnesBrainClient as _AgnesBrainClient
except ImportError:  # Optional local explanations must never break GP use.
    _AgnesBrainClient = None
from living_objects.ollama_explanations import ExplanationResult, request_local_explanation


SDK_VERSION = "0.3.0"
RUN_SCHEMA = "living-objects-sdk-run-v1"
_ROOT = Path(__file__).resolve().parents[1]
_TASK_ALIASES = {
    "manhattan": "manhattan-distance",
    "manhattan-distance": "manhattan-distance",
    "clean-sorting": "clean-sorting",
}
_DEFAULTS = {
    "manhattan-distance": {"population_size": 128, "mutation_rate": 0.22, "crossover_rate": 0.85, "elitism_count": 4, "max_depth": 7},
    "clean-sorting": {"population_size": 50, "mutation_rate": 0.12, "crossover_rate": 0.85, "elitism_count": 5, "max_depth": 8},
}


@dataclass(frozen=True)
class EvolutionResult:
    """A JSON-safe record for one bounded interpreter-only evolution run."""

    run_id: str
    task: str
    seed: int
    generations: int
    population_size: int
    champion: dict[str, Any]
    initial_tree_contains_final: bool
    history: list[dict[str, Any]]
    curriculum_events: list[dict[str, Any]]
    execution_boundary: dict[str, Any]
    artifact_path: str | None = None

    @property
    def fitness(self) -> float:
        """Return the champion's persisted training fitness for SDK compatibility.

        The value is an evaluator result from the bounded run, not an assertion of
        general program quality.  Fresh correctness remains available under
        ``champion[\"fresh\"]`` with its declared seed and case count.
        """
        return float(self.champion["training_fitness"])

    @property
    def source_code(self) -> str:
        """Return the champion's source-only Python audit export.

        This convenience accessor preserves the interpreter-only boundary: the SDK
        does not execute the returned text.
        """
        return str(self.champion["source_audit_export"])

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic scientific fields, excluding local file placement."""
        return {
            "run_id": self.run_id,
            "task": self.task,
            "seed": self.seed,
            "generations": self.generations,
            "population_size": self.population_size,
            "champion": self.champion,
            "initial_tree_contains_final": self.initial_tree_contains_final,
            "history": self.history,
            "curriculum_events": self.curriculum_events,
            "execution_boundary": self.execution_boundary,
        }


@dataclass(frozen=True)
class AuditResult:
    """An artifact-backed contamination classification, not a newly inferred claim."""

    task: str
    status: str
    claim_boundary: str
    evidence_path: str
    details: dict[str, Any]


@dataclass(frozen=True)
class ReproductionResult:
    """Comparison of an independently re-run bounded configuration."""

    run_id: str
    verified: bool
    mismatches: list[str]
    expected_tree_sha256: str
    reproduced_tree_sha256: str
    execution_boundary: dict[str, Any]


@dataclass(frozen=True)
class SafeExport:
    """Source text that has not been executed by this SDK."""

    target: str
    source: str
    execution_boundary: str


def _canonical_task(task: str) -> str:
    canonical = _TASK_ALIASES.get(str(task).strip().lower())
    if canonical is None:
        allowed = ", ".join(sorted(_TASK_ALIASES))
        raise ValueError(f"unsupported SDK task: {task!r}; choose one of {allowed}")
    return canonical


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _run_directory(directory: str | Path | None) -> Path:
    return Path(directory) if directory is not None else Path.cwd() / ".living-objects" / "runs"


def _build_population(task: str, *, seed: int, population_size: int) -> GPPopulation:
    settings = _DEFAULTS[task]
    if task == "manhattan-distance":
        evaluator = ManhattanDistanceEvaluator()
        return GPPopulation(
            evaluator=evaluator,
            population_size=population_size,
            seed=seed,
            mutation_rate=settings["mutation_rate"],
            crossover_rate=settings["crossover_rate"],
            elitism_count=settings["elitism_count"],
            max_depth=settings["max_depth"],
        )
    evaluator = V9CleanSortingEvaluator()
    return GPPopulation(
        evaluator=evaluator,
        primitives=STAGES[0].primitives,
        population_size=population_size,
        seed=seed,
        mutation_rate=settings["mutation_rate"],
        crossover_rate=settings["crossover_rate"],
        elitism_count=settings["elitism_count"],
        max_depth=settings["max_depth"],
    )


def _champion_record(population: GPPopulation, *, fresh_seed: int) -> dict[str, Any]:
    champion = population.champion
    fresh = population.evaluator.batch_evaluate([champion.genome], seed=fresh_seed, n=1_000)[0]
    tree = champion.genome.to_dict()
    return {
        "tree": tree,
        "tree_sha256": _digest(tree),
        "generation": population.generation,
        "training_fitness": champion.fitness,
        "fresh": {
            "seed": fresh_seed,
            "cases": 1_000,
            "correctness": fresh.correctness,
            "passed": fresh.test_cases_passed,
        },
        "nodes": champion.genome.complexity(),
        "depth": champion.genome.depth(),
        "source_audit_export": champion.genome.to_python(f"beast_{population.generation}"),
    }


def _execute(task: str, *, generations: int, seed: int, population_size: int) -> EvolutionResult:
    population = _build_population(task, seed=seed, population_size=population_size)
    population.initialize()
    initial_hashes = {_digest(organism.genome.to_dict()) for organism in population.population}
    curriculum_events: list[dict[str, Any]] = []
    curriculum = FiveStageSortingCurriculum() if task == "clean-sorting" else None
    if curriculum is not None:
        curriculum.bind(population)
    for _ in range(generations):
        population.step()
        if curriculum is not None:
            curriculum_events.append(curriculum.evaluate_and_advance(population, cases=100))
    champion = _champion_record(population, fresh_seed=990_000 + seed)
    configuration = {"task": task, "seed": seed, "generations": generations, "population_size": population_size}
    run_id = f"BEAST-SDK-V1-{_digest(configuration)[:16].upper()}"
    return EvolutionResult(
        run_id=run_id,
        task=task,
        seed=seed,
        generations=generations,
        population_size=population_size,
        champion=champion,
        initial_tree_contains_final=champion["tree_sha256"] in initial_hashes,
        history=[asdict(item) for item in population.history],
        curriculum_events=curriculum_events,
        execution_boundary={
            "runtime": "typed AST interpreter only",
            "llm_calls": 0,
            "network_calls": 0,
            "generated_source_executed": False,
        },
    )


def evolve(
    task: str,
    *,
    generations: int,
    seed: int,
    population_size: int | None = None,
    artifact_dir: str | Path | None = None,
    enable_local_explanation: bool = False,
    explanation_evidence_path: str | Path | None = None,
    explanation_model: str | None = None,
    explanation_client: Any | None = None,
) -> EvolutionResult:
    """Run one bounded local task and persist a JSON record for ``reproduce``.

    ``generations`` is deliberately limited to 10,000. Long campaigns require a
    separately pre-registered operator workflow and are not hidden behind this
    convenience function.
    """
    canonical = _canonical_task(task)
    if not 1 <= generations <= 10_000:
        raise ValueError("generations must be in 1..10000")
    selected_population = population_size or _DEFAULTS[canonical]["population_size"]
    if not 2 <= selected_population <= 512:
        raise ValueError("population_size must be in 2..512")
    result = _execute(canonical, generations=generations, seed=int(seed), population_size=selected_population)
    # This block is deliberately after selection, fitness measurement, and all
    # mutation/curriculum operations.  Text is untrusted and never re-enters GP.
    if enable_local_explanation and explanation_evidence_path is not None and explanation_model and _AgnesBrainClient is not None:
        brain = _AgnesBrainClient(evidence_path=explanation_evidence_path, model=explanation_model, client=explanation_client)
        if brain.is_available():
            explanation = brain.explain(result.source_code, canonical, result.fitness)
            result.execution_boundary["post_selection_explanation_calls"] = int(explanation.available)
            if explanation.available and explanation.text is not None:
                result.champion["brain_explanation"] = {
                    "text": explanation.text,
                    "source": "optional_local_model_untrusted_explanation",
                    "execution_boundary": explanation.execution_boundary,
                }
    target = _run_directory(artifact_dir) / f"{result.run_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": RUN_SCHEMA,
        "sdk_version": SDK_VERSION,
        "configuration": {
            "task": canonical,
            "generations": generations,
            "seed": int(seed),
            "population_size": selected_population,
        },
        "result": result.to_dict(),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Artifacts may contain program lineage and evaluation records.  The default
    # run identifier is deterministic for reproducibility, so do not leave its
    # JSON record readable by other local accounts when the filesystem supports
    # POSIX permissions.  This does not turn a caller-supplied shared directory
    # into a multi-tenant service; the production API remains operator-gated.
    if os.name == "posix":
        target.chmod(0o600)
    return EvolutionResult(**(result.to_dict() | {"artifact_path": str(target)}))


def audit(task: str) -> AuditResult:
    """Return the persisted v8 contamination status for a task.

    This function never converts a non-match into a valid discovery claim; it
    simply exposes the machine-derived ledger already published by v8.
    """
    requested = str(task).strip().lower()
    canonical = _TASK_ALIASES.get(requested, requested)
    path = _ROOT / "docs" / "v8-benchmark-ledger.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    for row in ledger["experiment_rows"]:
        if row["task"] == canonical:
            boundary = row.get("claim_boundary") or ledger["claim_boundary"]
            return AuditResult(canonical, row["benchmark_status"], boundary, str(path), dict(row))
    task_audit = ledger["task_audit"].get(canonical)
    if task_audit is not None:
        return AuditResult(
            canonical,
            task_audit["audit_status"],
            "No one-operation match observed is not a proof of an unrestricted discovery claim.",
            str(path),
            dict(task_audit),
        )
    raise ValueError(f"no persisted contamination audit for task: {task!r}")


def reproduce(run_id: str, *, artifact_dir: str | Path | None = None) -> ReproductionResult:
    """Independently rerun a persisted SDK configuration and compare deterministic fields."""
    if not re.fullmatch(r"BEAST-SDK-V1-[A-F0-9]{16}", str(run_id)):
        raise ValueError("run_id has an invalid SDK v1 format")
    path = _run_directory(artifact_dir) / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != RUN_SCHEMA or payload.get("result", {}).get("run_id") != run_id:
        raise ValueError("run artifact does not satisfy the SDK v1 schema")
    config = payload["configuration"]
    rerun = _execute(
        _canonical_task(config["task"]),
        generations=int(config["generations"]),
        seed=int(config["seed"]),
        population_size=int(config["population_size"]),
    )
    stored = payload["result"]
    fields = ("task", "seed", "generations", "population_size", "champion", "initial_tree_contains_final", "history", "curriculum_events", "execution_boundary")
    mismatches = [field for field in fields if stored.get(field) != rerun.to_dict().get(field)]
    return ReproductionResult(
        run_id=run_id,
        verified=not mismatches,
        mismatches=mismatches,
        expected_tree_sha256=str(stored["champion"]["tree_sha256"]),
        reproduced_tree_sha256=str(rerun.champion["tree_sha256"]),
        execution_boundary=rerun.execution_boundary,
    )


def export(champion: EvolutionResult | Mapping[str, Any], target: str) -> SafeExport:
    """Serialize a champion as source without executing generated source.

    The numeric JavaScript, Rust, and Go targets intentionally cover only the
    portable numeric primitive subset. Python audit source is available for
    every supported typed tree, subject to the existing source safety fallback.
    """
    if isinstance(champion, EvolutionResult):
        record = champion.champion
        task = champion.task
    else:
        record = dict(champion.get("champion", champion))
        task = str(champion.get("task", ""))
    if "tree" not in record:
        raise ValueError("champion must include a typed tree record")
    genome = GPGenome.from_dict(record["tree"])
    normalized_target = str(target).strip().lower()
    if normalized_target == "python":
        source = genome.to_python("beast_export")
    elif normalized_target in {"javascript", "rust", "go"}:
        if _canonical_task(task) != "manhattan-distance":
            raise ValueError("portable non-Python exports currently support only the numeric Manhattan task")
        compiler = PolyglotCompiler()
        args = ("x1", "y1", "x2", "y2")
        source = getattr(compiler, f"to_{normalized_target}")(genome.tree, "beast_export", args)
    else:
        raise ValueError("target must be one of python, javascript, rust, go")
    return SafeExport(
        target=normalized_target,
        source=source,
        execution_boundary="Export is source-only. The typed AST interpreter is the only SDK execution runtime; review and sandbox this text before any external use.",
    )


__all__ = [
    "SDK_VERSION",
    "EvolutionResult",
    "AuditResult",
    "ReproductionResult",
    "SafeExport",
    "ExplanationResult",
    "evolve",
    "audit",
    "reproduce",
    "export",
    "request_local_explanation",
]
