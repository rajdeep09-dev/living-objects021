"""Finite native-checkpoint instruction tuning for BEAST-BRAIN JSON suggestions.

This module operates only on the local 28.9M byte-transformer checkpoint and
the checked-in-source structured JSON corpus.  It never downloads a model or
data, calls a service, starts a worker, overwrites the base checkpoint, or
executes generated text.  Generated candidates are treated strictly as
untrusted controller input.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agnes_brain.controller import resolve_guidance
from agnes_brain.cpu_smoke import display_path, sha256_file
from agnes_brain.json_instruction_data import DEFAULT_OUTPUT_DIRECTORY as DEFAULT_JSON_DATA_DIRECTORY
from agnes_brain.train_transformer_28m import (
    DEFAULT_OUTPUT_DIRECTORY as DEFAULT_BASE_RUN_DIRECTORY,
    TrainingRunConfig,
    _heldout_loss,
    _make_batch,
    _set_deterministic_seed,
    atomic_torch_save,
    load_local_checkpoint,
)
from agnes_brain.transformer_28m import ByteTransformer28M, Transformer28MConfig, parameter_count


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_CHECKPOINT = DEFAULT_BASE_RUN_DIRECTORY / "checkpoint-latest.pt"
DEFAULT_TUNING_DIRECTORY = REPOSITORY_ROOT / "reports" / "v16" / "prompt-conditioned-json-instruction-tuning-28m-local"
TUNING_SCHEMA_VERSION = "beast-brain-json-instruction-tuning-v2"
LEGACY_TUNING_SCHEMA_VERSION = "beast-brain-json-instruction-tuning-v1"
JSON_DATA_SCHEMA_VERSION = "beast-brain-json-instruction-v1"
MAX_GENERATION_BYTES = 768
TARGET_IGNORE_INDEX = -100
PROMPT_CONTEXT_BYTES = 32


@dataclass(frozen=True)
class InstructionTuningConfig:
    """Finite local budget for one instruction-tuning attempt."""

    max_wall_seconds: int = 1_800
    max_steps: int = 6_000
    batch_size: int = 2
    learning_rate: float = 8e-5
    weight_decay: float = 0.01
    checkpoint_interval_steps: int = 25
    evaluation_batches: int = 10
    cpu_threads: int = 3
    seed: int = 20260820
    generation_max_bytes: int = 512

    def validate(self) -> None:
        if not 1 <= self.max_wall_seconds <= 3_600:
            raise ValueError("max_wall_seconds must be in [1, 3600] for a finite local tuning attempt")
        if not 0 <= self.max_steps <= 100_000:
            raise ValueError("max_steps must be in [0, 100000]")
        if not 1 <= self.batch_size <= 8 or not 1 <= self.cpu_threads <= 6:
            raise ValueError("batch_size and cpu_threads exceed the audited local CPU boundary")
        if self.learning_rate <= 0.0 or self.weight_decay < 0.0:
            raise ValueError("learning rate must be positive and weight decay non-negative")
        if self.checkpoint_interval_steps < 1 or self.evaluation_batches < 1:
            raise ValueError("checkpoint and evaluation intervals must be positive")
        if not 8 <= self.generation_max_bytes <= MAX_GENERATION_BYTES:
            raise ValueError("generation_max_bytes must be within the bounded local output budget")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JsonDataManifest:
    """Digest-bound source-disjoint bytes used for JSON syntax tuning."""

    train_path: str
    holdout_path: str
    train_sha256: str
    holdout_sha256: str
    train_record_digest: str
    holdout_record_digest: str
    train_records: int
    holdout_records: int
    train_bytes: int
    holdout_bytes: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptTargetExample:
    """One approved prompt and controller-JSON target used without text execution."""

    source_record_id: str
    prompt: bytes
    target: bytes

    @property
    def sequence(self) -> bytes:
        return self.prompt + self.target + b"\n"


def _canonical_row_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    chunks: list[bytes] = []
    for row in rows:
        if row.get("schema_version") != JSON_DATA_SCHEMA_VERSION:
            raise ValueError("JSON tuning row does not match the checked-in corpus schema")
        if not isinstance(row.get("source_record_id"), str) or not isinstance(row.get("input"), str):
            raise ValueError("JSON tuning row lacks source identity or input")
        if not isinstance(row.get("output"), str):
            raise ValueError("JSON tuning row lacks exact controller target")
        source = row.get("source")
        if not isinstance(source, dict) or source.get("model_generated") is not False:
            raise ValueError("JSON tuning row is not approved local source material")
        # The separator is part of the declared local sequence format, not a model prompt injection.
        sequence = f"{row['instruction']}\n{row['input']}\ncontroller_json:\n{row['output']}\n"
        chunks.append(sequence.encode("utf-8"))
    if not chunks:
        raise ValueError("cannot tune on an empty JSON instruction partition")
    return b"".join(chunks)


def _prompt_target_example(row: dict[str, Any]) -> PromptTargetExample:
    """Validate and serialize one local row into a declared prompt/target pair."""

    _canonical_row_bytes((row,))
    source_record_id = row["source_record_id"]
    prompt = f"{row['instruction']}\n{row['input']}\ncontroller_json:\n".encode("utf-8")
    target = row["output"].encode("utf-8")
    if not target.startswith(b"{"):
        raise ValueError("controller JSON target must begin with an opening brace")
    if len(prompt) < PROMPT_CONTEXT_BYTES:
        raise ValueError("declared instruction prompt is unexpectedly short")
    return PromptTargetExample(source_record_id=source_record_id, prompt=prompt, target=target)


def _load_jsonl(path: str | Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON instruction line {line_number}") from error
            if not isinstance(row, dict):
                raise ValueError("JSON instruction rows must be objects")
            rows.append(row)
    return tuple(rows)


def build_json_data_manifest(
    data_directory: str | Path = DEFAULT_JSON_DATA_DIRECTORY,
) -> tuple[JsonDataManifest, bytes, bytes, tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    """Load only the materialized local JSON instruction train/holdout split."""

    directory = Path(data_directory)
    train_path = directory / "train.jsonl"
    holdout_path = directory / "holdout.jsonl"
    train_rows = _load_jsonl(train_path)
    holdout_rows = _load_jsonl(holdout_path)
    train_names = {json.loads(row["output"])["name"] for row in train_rows}
    holdout_names = {json.loads(row["output"])["name"] for row in holdout_rows}
    if train_names & holdout_names:
        raise ValueError("JSON tuning train and held-out primitive names must be disjoint")
    train_bytes = _canonical_row_bytes(train_rows)
    holdout_bytes = _canonical_row_bytes(holdout_rows)
    digest = lambda rows: hashlib.sha256(
        "\n".join(sorted(str(row["source_record_id"]) for row in rows)).encode("utf-8")
    ).hexdigest()
    manifest = JsonDataManifest(
        train_path=display_path(train_path),
        holdout_path=display_path(holdout_path),
        train_sha256=sha256_file(train_path),
        holdout_sha256=sha256_file(holdout_path),
        train_record_digest=digest(train_rows),
        holdout_record_digest=digest(holdout_rows),
        train_records=len(train_rows),
        holdout_records=len(holdout_rows),
        train_bytes=len(train_bytes),
        holdout_bytes=len(holdout_bytes),
    )
    return manifest, train_bytes, holdout_bytes, train_rows, holdout_rows


def _load_base_model(base_checkpoint: str | Path) -> tuple[ByteTransformer28M, Transformer28MConfig]:
    try:
        base = load_local_checkpoint(base_checkpoint)
    except ValueError:
        # A previously completed local instruction-tuning checkpoint remains a
        # native project artifact.  It is accepted only through its own strict
        # schema loader, never as an arbitrary Torch dictionary.
        base = load_instruction_tuning_checkpoint(base_checkpoint)
    config = Transformer28MConfig(**base["model_config"])
    config.validate()
    model = ByteTransformer28M(config)
    if int(base["model_parameter_count"]) != parameter_count(model):
        raise ValueError("base checkpoint architecture is not the exact local 28.9M model")
    model.load_state_dict(base["model_state"])
    del base
    gc.collect()
    return model, config


def _make_target_only_batch(
    rows: tuple[dict[str, Any], ...],
    *,
    block_size: int,
    batch_size: int,
    rng: random.Random,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample fixed windows whose loss labels cover only declared JSON target bytes."""

    if not rows:
        raise ValueError("cannot create a target-only batch from empty rows")
    token_rows: list[list[int]] = []
    target_rows: list[list[int]] = []
    for _ in range(batch_size):
        example = _prompt_target_example(rows[rng.randrange(len(rows))])
        sequence = example.sequence
        target_start = len(example.prompt)
        max_start = len(sequence) - block_size - 1
        if max_start < 0:
            raise ValueError("instruction prompt/target sequence is shorter than one local window")
        offset = rng.randrange(len(example.target))
        start = min(max_start, max(0, target_start - PROMPT_CONTEXT_BYTES + offset))
        window = sequence[start : start + block_size + 1]
        if len(window) != block_size + 1:
            raise RuntimeError("target-only batch window length drifted")
        token_rows.append(list(window[:-1]))
        labels: list[int] = []
        for relative_index, byte in enumerate(window[1:], start=1):
            source_index = start + relative_index
            is_target_byte = target_start <= source_index < target_start + len(example.target)
            labels.append(byte if is_target_byte else TARGET_IGNORE_INDEX)
        if all(label == TARGET_IGNORE_INDEX for label in labels):
            raise RuntimeError("target-only batch contains no supervised controller bytes")
        target_rows.append(labels)
    return torch.tensor(token_rows, dtype=torch.long), torch.tensor(target_rows, dtype=torch.long)


def _heldout_target_nll(
    model: ByteTransformer28M,
    rows: tuple[dict[str, Any], ...],
    *,
    block_size: int,
) -> float:
    """Compute deterministic source-disjoint NLL on the first prompt-conditioned target window per row."""

    losses: list[float] = []
    model.eval()
    with torch.no_grad():
        for row in rows:
            example = _prompt_target_example(row)
            sequence = example.sequence
            target_start = len(example.prompt)
            max_start = len(sequence) - block_size - 1
            if max_start < 0:
                raise ValueError("held-out prompt/target sequence is shorter than one local window")
            start = min(max_start, max(0, target_start - PROMPT_CONTEXT_BYTES))
            window = sequence[start : start + block_size + 1]
            token_ids = torch.tensor([list(window[:-1])], dtype=torch.long)
            labels = torch.tensor(
                [[
                    byte
                    if target_start <= start + relative_index < target_start + len(example.target)
                    else TARGET_IGNORE_INDEX
                    for relative_index, byte in enumerate(window[1:], start=1)
                ]],
                dtype=torch.long,
            )
            _, loss = model(token_ids, labels)
            if loss is None:
                raise RuntimeError("held-out target-only evaluation did not produce loss")
            losses.append(float(loss))
    if not losses:
        raise ValueError("cannot evaluate an empty held-out partition")
    return float(sum(losses) / len(losses))


def _tuning_checkpoint_payload(
    model: ByteTransformer28M,
    optimizer: torch.optim.Optimizer,
    model_config: Transformer28MConfig,
    data: JsonDataManifest,
    config: InstructionTuningConfig,
    base_checkpoint_sha256: str,
    step: int,
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "schema_version": TUNING_SCHEMA_VERSION,
        "base_checkpoint_sha256": base_checkpoint_sha256,
        "model_config": model_config.as_dict(),
        "model_parameter_count": parameter_count(model),
        "json_data_manifest": data.as_dict(),
        "tuning_config": config.as_dict(),
        "step": step,
        "elapsed_seconds": elapsed_seconds,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
    }


def load_instruction_tuning_checkpoint(path: str | Path) -> dict[str, Any]:
    """Load only a checkpoint produced by this local tuning schema."""

    checkpoint = Path(path)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or payload.get("schema_version") not in {
        LEGACY_TUNING_SCHEMA_VERSION,
        TUNING_SCHEMA_VERSION,
    }:
        raise ValueError("checkpoint is not a BEAST-BRAIN JSON instruction-tuning checkpoint")
    return payload


def _next_greedy_byte(model: ByteTransformer28M, context: bytes) -> int:
    if not context:
        raise ValueError("generation context cannot be empty")
    token_ids = torch.tensor([list(context[-model.config.block_size :])], dtype=torch.long)
    model.eval()
    with torch.no_grad():
        logits, _ = model(token_ids)
    return int(torch.argmax(logits[0, -1]).item())


def constrained_json_completion(
    model: ByteTransformer28M, prompt: bytes = b"", max_new_bytes: int = 512
) -> str:
    """Greedily complete a prompt-conditioned JSON object without executing it.

    The opening brace is the sole formatting constraint.  The supplied prompt is
    a checked-in corpus instruction and input, never a hidden target answer.
    """

    if not 8 <= max_new_bytes <= MAX_GENERATION_BYTES:
        raise ValueError("generation budget is outside the local safety limit")
    candidate = bytearray(b"{")
    for _ in range(max_new_bytes):
        candidate.append(_next_greedy_byte(model, prompt + bytes(candidate)))
        try:
            decoded = candidate.decode("utf-8")
            parsed = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict):
            return decoded
    return candidate.decode("utf-8", errors="replace")


def _evaluate_schema(model: ByteTransformer28M, holdout_rows: tuple[dict[str, Any], ...], max_new_bytes: int) -> dict[str, Any]:
    """Measure every held-out prompt for strict syntax/admission; never score task correctness."""

    valid_json = 0
    exact_schema = 0
    admitted = 0
    reason_counts: Counter[str] = Counter()
    generations: list[dict[str, Any]] = []
    for row in holdout_rows:
        example = _prompt_target_example(row)
        raw = constrained_json_completion(model, prompt=example.prompt, max_new_bytes=max_new_bytes)
        decision = resolve_guidance(raw, profile_name="default")
        json_is_valid = False
        schema_is_valid = False
        try:
            parsed = json.loads(raw)
            json_is_valid = isinstance(parsed, dict)
            schema_is_valid = json_is_valid and set(parsed) == {
                "name", "description", "input_types", "output_type", "rationale"
            }
        except json.JSONDecodeError:
            pass
        valid_json += int(json_is_valid)
        exact_schema += int(schema_is_valid)
        admitted += int(decision.accepted)
        reason_counts[decision.reason] += 1
        raw_bytes = raw.encode("utf-8", errors="strict")
        generations.append(
            {
                "source_record_id": example.source_record_id,
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "bytes": len(raw_bytes),
                "controller_reason": decision.reason,
            }
        )
    count = len(holdout_rows)
    if count == 0:
        raise ValueError("cannot evaluate an empty held-out partition")
    return {
        "evaluation_examples": count,
        "decoder": {
            "method": "greedy_prompt_conditioned",
            "format_prefix": "{",
            "prompt_source": "declared held-out instruction/input plus controller_json delimiter",
            "max_new_bytes": max_new_bytes,
        },
        "valid_json_rate": valid_json / count,
        "exact_controller_schema_rate": exact_schema / count,
        "controller_admission_rate": admitted / count,
        "controller_reason_counts": dict(sorted(reason_counts.items())),
        "generation_digests": generations,
        "generated_text_persisted": False,
        "task_correctness_measured": False,
    }


def run_instruction_tuning_attempt(
    *,
    base_checkpoint: str | Path = DEFAULT_BASE_CHECKPOINT,
    data_directory: str | Path = DEFAULT_JSON_DATA_DIRECTORY,
    output_directory: str | Path = DEFAULT_TUNING_DIRECTORY,
    tuning_config: InstructionTuningConfig = InstructionTuningConfig(),
    resume: bool = False,
) -> dict[str, Any]:
    """Run a finite, native-only JSON syntax-tuning attempt without overwriting the base run."""

    tuning_config.validate()
    base_path = Path(base_checkpoint)
    output = Path(output_directory)
    artifact_path = output / "run.json"
    checkpoint_path = output / "checkpoint-latest.pt"
    metrics_path = output / "metrics.jsonl"
    contract_path = output / "tuning-contract.json"
    if artifact_path.exists():
        raise FileExistsError(f"refusing to overwrite completed tuning artifact: {artifact_path}")
    if any(path.exists() for path in (checkpoint_path, metrics_path, contract_path)) and not resume:
        raise FileExistsError("existing tuning state requires explicit resume=True")
    if not base_path.is_file():
        raise FileNotFoundError(base_path)

    data, train_bytes, holdout_bytes, train_rows, holdout_rows = build_json_data_manifest(data_directory)
    _set_deterministic_seed(tuning_config.seed, tuning_config.cpu_threads)
    model, model_config = _load_base_model(base_path)
    optimizer = torch.optim.AdamW(model.parameters(), lr=tuning_config.learning_rate, weight_decay=tuning_config.weight_decay)
    base_digest = sha256_file(base_path)
    output.mkdir(parents=True, exist_ok=True)
    if not contract_path.exists():
        contract = {
                "schema_version": "beast-brain-json-instruction-tuning-contract-v2",
            "base_checkpoint_sha256": base_digest,
            "model_parameter_count": parameter_count(model),
            "json_data_manifest": data.as_dict(),
            "tuning_config": tuning_config.as_dict(),
            "execution_boundary": {
                "network_calls": 0,
                "model_weights_downloaded": False,
                "external_dataset_downloaded": False,
                "persistent_worker_started": False,
                "generated_text_executed": False,
            },
            "claim_boundary": "Schema validity is not evidence of reasoning, coding, general ability, or BEAST benchmark improvement.",
            "supervision": {
                "mode": "target_only",
                "prompt_loss_labels": "ignored",
                "prompt_context_bytes": PROMPT_CONTEXT_BYTES,
                "target_only_ignore_index": TARGET_IGNORE_INDEX,
            },
        }
        with contract_path.open("x", encoding="utf-8") as handle:
            json.dump(contract, handle, sort_keys=True, indent=2)
            handle.write("\n")
        contract_path.chmod(0o600)

    step = 0
    prior_elapsed = 0.0
    if resume:
        prior = load_instruction_tuning_checkpoint(checkpoint_path)
        if prior["base_checkpoint_sha256"] != base_digest or prior["json_data_manifest"] != data.as_dict():
            raise ValueError("refusing to resume against a different base checkpoint or JSON corpus")
        model.load_state_dict(prior["model_state"])
        optimizer.load_state_dict(prior["optimizer_state"])
        step = int(prior["step"])
        prior_elapsed = float(prior["elapsed_seconds"])

    initial_holdout_nll = _heldout_target_nll(model, holdout_rows, block_size=model_config.block_size)
    rng = random.Random(tuning_config.seed + step)
    started = time.monotonic()
    last_train_nll: float | None = None
    completion_reason = "max_steps_reached"
    metrics_mode = "a" if metrics_path.exists() else "x"
    with metrics_path.open(metrics_mode, encoding="utf-8") as handle:
        while step < tuning_config.max_steps:
            elapsed = prior_elapsed + (time.monotonic() - started)
            if elapsed >= tuning_config.max_wall_seconds:
                completion_reason = "wall_clock_deadline_reached"
                break
            model.train()
            token_ids, targets = _make_target_only_batch(
                train_rows,
                block_size=model_config.block_size,
                batch_size=tuning_config.batch_size,
                rng=rng,
            )
            _, loss = model(token_ids, targets)
            if loss is None:
                raise RuntimeError("JSON instruction-tuning step did not produce loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            step += 1
            last_train_nll = float(loss.detach())
            elapsed = prior_elapsed + (time.monotonic() - started)
            handle.write(json.dumps({"step": step, "elapsed_seconds": elapsed, "train_nll": last_train_nll}, sort_keys=True) + "\n")
            handle.flush()
            if step % tuning_config.checkpoint_interval_steps == 0:
                atomic_torch_save(
                    _tuning_checkpoint_payload(model, optimizer, model_config, data, tuning_config, base_digest, step, elapsed),
                    checkpoint_path,
                )
    elapsed = prior_elapsed + (time.monotonic() - started)
    final_holdout_nll = _heldout_target_nll(model, holdout_rows, block_size=model_config.block_size)
    checkpoint = atomic_torch_save(
        _tuning_checkpoint_payload(model, optimizer, model_config, data, tuning_config, base_digest, step, elapsed), checkpoint_path
    )
    artifact = {
        "schema_version": TUNING_SCHEMA_VERSION,
        "status": "completed_finite_local_instruction_tuning",
        "completion_reason": completion_reason,
        "base_checkpoint": {"path": display_path(base_path), "sha256": base_digest, "overwritten": False},
        "model": {"parameter_count": parameter_count(model), "runtime": "native PyTorch checkpoint only"},
        "json_data": data.as_dict(),
        "run": {
            **tuning_config.as_dict(),
            "steps_completed": step,
            "elapsed_seconds": elapsed,
            "resumed": resume,
            "metrics_path": display_path(metrics_path),
            "metrics_sha256": sha256_file(metrics_path),
            "checkpoint_path": display_path(checkpoint),
            "checkpoint_sha256": sha256_file(checkpoint),
            "contract_path": display_path(contract_path),
            "contract_sha256": sha256_file(contract_path),
        },
        "metrics": {
            "initial_heldout_target_nll": initial_holdout_nll,
            "final_heldout_target_nll": final_holdout_nll,
            "last_train_nll": last_train_nll,
        },
        "schema_evaluation": _evaluate_schema(model, holdout_rows, tuning_config.generation_max_bytes),
        "execution_boundary": {
            "network_calls": 0,
            "model_weights_downloaded": False,
            "external_dataset_downloaded": False,
            "persistent_worker_started": False,
            "generated_text_executed": False,
        },
        "claim_boundary": {
            "is_ollama_or_gguf": False,
            "parent_model_weight_transfer": False,
            "general_reasoning_claim": False,
            "coding_capability_claim": False,
            "beast_benchmark_improvement_claim": False,
            "meaning": "This is a finite native-checkpoint prompt-conditioned JSON-syntax measurement only.",
        },
    }
    with artifact_path.open("x", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    artifact_path.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Run finite native-checkpoint BEAST-BRAIN JSON instruction tuning.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--data-directory", type=Path, default=DEFAULT_JSON_DATA_DIRECTORY)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_TUNING_DIRECTORY)
    parser.add_argument("--max-wall-seconds", type=int, default=1_800)
    parser.add_argument("--max-steps", type=int, default=6_000)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--checkpoint-interval-steps", type=int, default=25)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    result = run_instruction_tuning_attempt(
        base_checkpoint=args.base_checkpoint,
        data_directory=args.data_directory,
        output_directory=args.output_directory,
        tuning_config=InstructionTuningConfig(
            max_wall_seconds=args.max_wall_seconds,
            max_steps=args.max_steps,
            batch_size=args.batch_size,
            checkpoint_interval_steps=args.checkpoint_interval_steps,
        ),
        resume=args.resume,
    )
    print(
        f"Finite JSON tuning completed after {result['run']['steps_completed']} steps; held-out NLL "
        f"{result['metrics']['initial_heldout_nll']:.6f} -> {result['metrics']['final_heldout_nll']:.6f}; "
        f"controller admission {result['schema_evaluation']['controller_admission_rate']:.0%}."
    )


if __name__ == "__main__":
    main()
