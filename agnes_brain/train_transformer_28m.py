"""Resumable, bounded CPU training for the local 28.9M BEAST-BRAIN transformer.

The runner operates only on the approved checked-in byte corpus. It does not
download models or data, call a network endpoint, start a worker, execute
generated text, or permit a training deadline greater than one hour.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agnes_brain.cpu_smoke import DEFAULT_DATASET, display_path, sha256_file
from agnes_brain.transformer_28m import (
    DEFAULT_CONFIG,
    MODEL_VERSION,
    ByteTransformer28M,
    LocalDataManifest,
    Transformer28MConfig,
    build_local_data_manifest,
    parameter_count,
    write_training_contract,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v14" / "beast-brain-28m-local-attempt-20260819"
RUN_SCHEMA_VERSION = "beast-brain-transformer-local-run-v1"


@dataclass(frozen=True)
class TrainingRunConfig:
    """Finite resource budget for a local attempt, not a background service."""

    max_wall_seconds: int = 3_000
    max_steps: int = 10_000
    batch_size: int = 2
    learning_rate: float = 3e-4
    weight_decay: float = 0.01
    checkpoint_interval_steps: int = 20
    evaluation_batches: int = 12
    cpu_threads: int = 3
    seed: int = 20260819

    def validate(self) -> None:
        if not 1 <= self.max_wall_seconds <= 3_600:
            raise ValueError("max_wall_seconds must be in [1, 3600] for a finite local attempt")
        if not 0 <= self.max_steps <= 100_000:
            raise ValueError("max_steps must be in [0, 100000]")
        if not 1 <= self.batch_size <= 8:
            raise ValueError("batch_size must be in [1, 8] for the documented CPU memory budget")
        if self.learning_rate <= 0.0 or self.weight_decay < 0.0:
            raise ValueError("learning_rate and weight_decay must be non-negative with a positive rate")
        if self.checkpoint_interval_steps < 1 or self.evaluation_batches < 1:
            raise ValueError("checkpoint and evaluation intervals must be positive")
        if not 1 <= self.cpu_threads <= 6:
            raise ValueError("cpu_threads must be within the audited six-logical-CPU bound")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _set_deterministic_seed(seed: int, threads: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _make_batch(payload: bytes, block_size: int, batch_size: int, rng: random.Random) -> tuple[torch.Tensor, torch.Tensor]:
    if len(payload) <= block_size:
        raise ValueError("local byte payload must exceed the configured block_size")
    starts = [rng.randrange(0, len(payload) - block_size) for _ in range(batch_size)]
    inputs = [list(payload[start : start + block_size]) for start in starts]
    targets = [list(payload[start + 1 : start + block_size + 1]) for start in starts]
    return torch.tensor(inputs, dtype=torch.long), torch.tensor(targets, dtype=torch.long)


def _heldout_loss(
    model: ByteTransformer28M,
    payload: bytes,
    config: Transformer28MConfig,
    batches: int,
) -> float:
    if len(payload) <= config.block_size:
        raise ValueError("held-out payload must exceed the configured context window")
    starts = np.linspace(0, len(payload) - config.block_size - 1, num=batches, dtype=int)
    losses: list[float] = []
    model.eval()
    with torch.no_grad():
        for start in starts:
            token_ids = torch.tensor([list(payload[start : start + config.block_size])], dtype=torch.long)
            targets = torch.tensor(
                [list(payload[start + 1 : start + config.block_size + 1])], dtype=torch.long
            )
            _, loss = model(token_ids, targets)
            if loss is None:
                raise RuntimeError("held-out evaluation did not produce loss")
            losses.append(float(loss.detach()))
    return sum(losses) / len(losses)


def atomic_torch_save(payload: dict[str, Any], destination: str | Path) -> Path:
    """Atomically replace only a runner-created local checkpoint."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        torch.save(payload, temporary)
        temporary.chmod(0o600)
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        if temporary.exists():
            temporary.unlink()
    return path


def load_local_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load only a path that the runner previously created in its local output directory."""

    checkpoint = Path(path)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or payload.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("checkpoint does not match the local BEAST-BRAIN run schema")
    return payload


def _checkpoint_payload(
    model: ByteTransformer28M,
    optimizer: torch.optim.Optimizer,
    model_config: Transformer28MConfig,
    manifest: LocalDataManifest,
    run_config: TrainingRunConfig,
    step: int,
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "model_config": model_config.as_dict(),
        "model_parameter_count": parameter_count(model),
        "dataset_sha256": manifest.dataset_sha256,
        "record_digest": manifest.record_digest,
        "run_config": run_config.as_dict(),
        "step": step,
        "elapsed_seconds": elapsed_seconds,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
    }


def run_local_training_attempt(
    dataset_path: str | Path = DEFAULT_DATASET,
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    *,
    model_config: Transformer28MConfig = DEFAULT_CONFIG,
    run_config: TrainingRunConfig = TrainingRunConfig(),
    resume: bool = False,
) -> dict[str, Any]:
    """Run a finite local optimization attempt and preserve its evidence artifacts."""

    model_config.validate()
    run_config.validate()
    output = Path(output_directory)
    contract_path = output / "training-contract.json"
    checkpoint_path = output / "checkpoint-latest.pt"
    metrics_path = output / "metrics.jsonl"
    artifact_path = output / "run.json"
    if artifact_path.exists():
        raise FileExistsError(f"refusing to overwrite completed local training artifact: {artifact_path}")
    if any(path.exists() for path in (contract_path, checkpoint_path, metrics_path)) and not resume:
        raise FileExistsError("existing local training state requires explicit resume=True")

    manifest, train_payload, holdout_payload = build_local_data_manifest(dataset_path)
    _set_deterministic_seed(run_config.seed, run_config.cpu_threads)
    output.mkdir(parents=True, exist_ok=True)
    if not contract_path.exists():
        write_training_contract(contract_path, model_config, manifest)

    model = ByteTransformer28M(model_config)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=run_config.learning_rate, weight_decay=run_config.weight_decay
    )
    step = 0
    prior_elapsed = 0.0
    if resume:
        checkpoint = load_local_checkpoint(checkpoint_path)
        if checkpoint["dataset_sha256"] != manifest.dataset_sha256 or checkpoint["record_digest"] != manifest.record_digest:
            raise ValueError("refusing to resume against a different local data manifest")
        if checkpoint["model_parameter_count"] != model_config.expected_parameter_count:
            raise ValueError("refusing to resume a different model architecture")
        model.load_state_dict(checkpoint["model_state"])
        optimizer.load_state_dict(checkpoint["optimizer_state"])
        step = int(checkpoint["step"])
        prior_elapsed = float(checkpoint["elapsed_seconds"])

    initial_holdout_nll = _heldout_loss(model, holdout_payload, model_config, run_config.evaluation_batches)
    rng = random.Random(run_config.seed + step)
    started = time.monotonic()
    last_train_loss: float | None = None
    completed_reason = "max_steps_reached"
    metrics_mode = "a" if metrics_path.exists() else "x"
    with metrics_path.open(metrics_mode, encoding="utf-8") as metric_handle:
        while step < run_config.max_steps:
            elapsed = prior_elapsed + (time.monotonic() - started)
            if elapsed >= run_config.max_wall_seconds:
                completed_reason = "wall_clock_deadline_reached"
                break
            model.train()
            token_ids, targets = _make_batch(train_payload, model_config.block_size, run_config.batch_size, rng)
            _, loss = model(token_ids, targets)
            if loss is None:
                raise RuntimeError("training step did not produce loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            step += 1
            last_train_loss = float(loss.detach())
            elapsed = prior_elapsed + (time.monotonic() - started)
            metric_handle.write(
                json.dumps({"step": step, "elapsed_seconds": elapsed, "train_nll": last_train_loss}, sort_keys=True)
                + "\n"
            )
            metric_handle.flush()
            if step % run_config.checkpoint_interval_steps == 0:
                atomic_torch_save(
                    _checkpoint_payload(model, optimizer, model_config, manifest, run_config, step, elapsed),
                    checkpoint_path,
                )
        elapsed = prior_elapsed + (time.monotonic() - started)

    final_holdout_nll = _heldout_loss(model, holdout_payload, model_config, run_config.evaluation_batches)
    checkpoint = atomic_torch_save(
        _checkpoint_payload(model, optimizer, model_config, manifest, run_config, step, elapsed), checkpoint_path
    )
    artifact = {
        "schema_version": RUN_SCHEMA_VERSION,
        "status": "completed_finite_local_attempt",
        "completion_reason": completed_reason,
        "dataset": manifest.as_dict(),
        "model": {
            "model_version": MODEL_VERSION,
            "parameter_count": parameter_count(model),
            "architecture": "tied-embedding causal byte transformer",
        },
        "run": {
            **run_config.as_dict(),
            "steps_completed": step,
            "elapsed_seconds": elapsed,
            "resumed": resume,
            "metrics_path": display_path(metrics_path),
            "metrics_sha256": sha256_file(metrics_path),
            "checkpoint_path": display_path(checkpoint),
            "checkpoint_sha256": sha256_file(checkpoint),
            "training_contract_path": display_path(contract_path),
            "training_contract_sha256": sha256_file(contract_path),
        },
        "metrics": {
            "uniform_byte_baseline_nll": math.log(256),
            "initial_heldout_nll": initial_holdout_nll,
            "final_heldout_nll": final_holdout_nll,
            "last_train_nll": last_train_loss,
        },
        "execution_boundary": {
            "network_calls": 0,
            "model_weights_downloaded": False,
            "external_dataset_downloaded": False,
            "persistent_worker_started": False,
            "generated_text_executed": False,
            "runtime": "finite local CPU PyTorch process",
        },
        "claim_boundary": {
            "parent_model_weight_transfer": False,
            "is_ollama_service": False,
            "general_language_capability_claim": False,
            "beast_benchmark_improvement_claim": False,
            "meaning": "This records only a time-bounded local next-byte-loss attempt on a 78-record corpus.",
        },
    }
    with artifact_path.open("x", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    artifact_path.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a finite local 28.9M BEAST-BRAIN transformer attempt.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--max-wall-seconds", type=int, default=3_000)
    parser.add_argument("--max-steps", type=int, default=10_000)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--checkpoint-interval-steps", type=int, default=20)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    artifact = run_local_training_attempt(
        args.dataset,
        args.output_directory,
        run_config=TrainingRunConfig(
            max_wall_seconds=args.max_wall_seconds,
            max_steps=args.max_steps,
            batch_size=args.batch_size,
            checkpoint_interval_steps=args.checkpoint_interval_steps,
        ),
        resume=args.resume,
    )
    print(
        f"Finite 28.9M local attempt completed after {artifact['run']['steps_completed']} steps; "
        f"held-out NLL {artifact['metrics']['initial_heldout_nll']:.6f} -> "
        f"{artifact['metrics']['final_heldout_nll']:.6f}; {artifact['completion_reason']}."
    )


if __name__ == "__main__":
    main()
