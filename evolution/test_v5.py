from __future__ import annotations

from dataclasses import dataclass

import pytest

from evolution.morphogenetic_ai import MorphogeneticProgram
from evolution.physics import ParallelUniverse
from evolution.spiking import LIFNeuron
from evolution.substrate import SubstrateExporter, WasmExportResult
from evolution.temporal import RevisionError, TemporalRevisionEngine
from evolution.v5 import AutonomousEvolutionWorker, resolve_task
from evolution.writing_system import StrategyIntent, WritingSystem


def test_goal_routes_to_a_fixed_local_task_without_executing_goal_text() -> None:
    assert resolve_task("find an efficient prime number method").task_id == "primes"
    assert resolve_task("<script>bad()</script>").task_id == "general_research"


def test_worker_runs_local_batch_and_resumes_from_atomic_checkpoint(tmp_path) -> None:
    worker = AutonomousEvolutionWorker(
        "evolve a cooperative tournament strategy",
        tmp_path,
        target_generations=12,
        population_size=4,
        workers=2,
        checkpoint_interval=4,
        seed=9,
    )
    first = worker.run_batch(5)
    assert first.status == "paused"
    assert first.generation == 5
    assert first.checkpoint_path
    worker.close()

    recovered = AutonomousEvolutionWorker.resume_from_workspace(tmp_path)
    final = recovered.run_batch(10)
    assert final.status == "completed"
    assert final.generation == 12
    assert final.novelty_count > 0
    recovered.close()


def test_worker_enforces_population_and_generation_ceilings(tmp_path) -> None:
    with pytest.raises(ValueError, match="population_size"):
        AutonomousEvolutionWorker("learn algorithms", tmp_path, population_size=1)
    with pytest.raises(ValueError, match="target_generations"):
        AutonomousEvolutionWorker("learn algorithms", tmp_path, target_generations=1_000_001)


def test_worker_supports_a_100k_generation_budget_with_a_small_checkpointed_smoke_batch(tmp_path) -> None:
    worker = AutonomousEvolutionWorker(
        "evolve a text compression strategy",
        tmp_path,
        target_generations=100_000,
        population_size=2,
        workers=1,
        checkpoint_interval=2,
        seed=17,
    )
    snapshot = worker.run_batch(2)
    assert snapshot.status == "paused"
    assert snapshot.generation == 2
    assert snapshot.target_generations == 100_000
    assert snapshot.checkpoint_path
    worker.close()


def test_parallel_universe_branch_copies_memome_snapshot(tmp_path) -> None:
    archive = tmp_path / "memome.sqlite"
    archive.write_bytes(b"parent archive")
    child = ParallelUniverse(memome_path=archive).branch(type("Law", (), {"name": "test", "apply": lambda *_: None})())
    assert child.memome_path is not None
    assert child.memome_path != archive
    assert child.memome_path.read_bytes() == b"parent archive"


def test_temporal_revision_rejects_recomputation_budget_excess() -> None:
    organism = type("Organism", (), {"object_id": "child"})()
    engine = TemporalRevisionEngine(
        organisms=[organism],
        lineage={"child": "ancestor"},
        butterfly_budget=2,
        max_causal_recomputations=1,
    )
    proposal = engine.propose_revision(organism, "ancestor", "def strategy(): return 1", "safe")
    assert not engine.apply_revision(proposal).applied
    with pytest.raises(RevisionError):
        TemporalRevisionEngine(lineage={"child": "parent", "parent": "ancestor"}, butterfly_budget=1).propose_revision(
            organism, "ancestor", "x", "safe"
        )


def test_morphogenetic_development_detects_repeated_states() -> None:
    program = MorphogeneticProgram(
        [{"type": "differentiate", "condition": "always", "parameters": {"potential": 0.0}}],
        max_neurons=4,
        max_synapses=4,
    )
    genome = program.develop(LIFNeuron(0), steps=10_000)
    assert len(genome.neurons) == 1


def test_translation_falls_back_for_unknown_target_concepts_without_target_mutation() -> None:
    source = WritingSystem()
    target = WritingSystem()
    text = source.write(StrategyIntent("new_concept"))
    before = target.vocabulary_size
    translated = source.translate(text, target)
    assert str(translated) == "[?new_concept]"
    assert translated.quality == 0.0
    assert translated.unknown_token_count == 1
    assert target.vocabulary_size == before


@dataclass
class _Strategy:
    effectiveness: float


@dataclass
class _Organism:
    learned_strategies: dict[str, _Strategy]


def test_wasm_export_is_bytes_compatible_and_caps_strategy_metadata() -> None:
    organism = _Organism({str(index): _Strategy(float(index)) for index in range(40)})
    result = SubstrateExporter().export_wasm(organism)
    assert isinstance(result, bytes)
    assert isinstance(result, WasmExportResult)
    assert result.strategy_count == 20
