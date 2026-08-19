"""A bounded local model smoke experiment for AGNES-BRAIN research.

This is a byte-bigram statistical model, not a transformer or an LLM. It exists
only to prove that the checked-in dataset can be split deterministically,
trained on CPU, checkpointed without pickle, reloaded, evaluated on held-out
records, and used for deterministic byte generation under explicit boundaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = REPOSITORY_ROOT / "agnes_brain" / "training_data" / "dataset.jsonl"
DEFAULT_OUTPUT_DIRECTORY = REPOSITORY_ROOT / "reports" / "v13" / "beast-brain-cpu-smoke-20260819"
VOCAB_SIZE = 256
MODEL_VERSION = "beast-brain-byte-bigram-v1"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: str | Path) -> str:
    """Use a repository-relative path when possible, otherwise preserve the absolute path."""

    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPOSITORY_ROOT))
    except ValueError:
        return str(resolved)


def canonical_record_text(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_instruction_records(path: str | Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    source = Path(path)
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("record_id"), str):
            raise ValueError(f"{source}:{line_number} must be an instruction object with a record_id")
        rows.append(row)
    if not rows:
        raise ValueError("dataset contains no instruction records")
    return tuple(rows)


def split_records(records: Iterable[dict[str, Any]]) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    """Assign each content-identified record to an 80/20 stable split."""

    train: list[dict[str, Any]] = []
    holdout: list[dict[str, Any]] = []
    for record in records:
        bucket = int(hashlib.sha256(record["record_id"].encode("utf-8")).hexdigest()[:8], 16) % 5
        (holdout if bucket == 0 else train).append(record)
    if not train or not holdout:
        raise ValueError("stable dataset split must contain at least one train and one holdout record")
    return tuple(train), tuple(holdout)


@dataclass(frozen=True)
class ByteBigramModel:
    """Smoothed byte-to-byte transition model with a fixed 256-byte vocabulary."""

    counts: np.ndarray
    alpha: float = 0.5

    def __post_init__(self) -> None:
        if self.counts.shape != (VOCAB_SIZE, VOCAB_SIZE):
            raise ValueError(f"counts must have shape ({VOCAB_SIZE}, {VOCAB_SIZE})")
        if self.alpha <= 0.0:
            raise ValueError("alpha must be positive")

    @classmethod
    def train(cls, texts: Iterable[str], *, alpha: float = 0.5) -> "ByteBigramModel":
        counts = np.zeros((VOCAB_SIZE, VOCAB_SIZE), dtype=np.int64)
        observed_pairs = 0
        for text in texts:
            payload = text.encode("utf-8")
            previous = 0
            for current in payload:
                counts[previous, current] += 1
                previous = current
                observed_pairs += 1
        if observed_pairs == 0:
            raise ValueError("cannot train a byte-bigram model on empty text")
        return cls(counts=counts, alpha=alpha)

    def probabilities(self, previous_byte: int) -> np.ndarray:
        if not 0 <= previous_byte < VOCAB_SIZE:
            raise ValueError("previous byte must be in [0, 255]")
        row = self.counts[previous_byte].astype(np.float64) + self.alpha
        return row / row.sum()

    def negative_log_likelihood(self, texts: Iterable[str]) -> tuple[float, int]:
        total_loss = 0.0
        total_tokens = 0
        for text in texts:
            previous = 0
            for current in text.encode("utf-8"):
                probability = float(self.probabilities(previous)[current])
                total_loss -= math.log(probability)
                total_tokens += 1
                previous = current
        if total_tokens == 0:
            raise ValueError("cannot measure negative log likelihood on empty text")
        return total_loss / total_tokens, total_tokens

    def generate(self, prompt: str, *, max_new_bytes: int = 96, seed: int = 0) -> str:
        if max_new_bytes < 0:
            raise ValueError("max_new_bytes must not be negative")
        encoded_prompt = prompt.encode("utf-8")
        previous = encoded_prompt[-1] if encoded_prompt else 0
        rng = np.random.default_rng(seed)
        generated = bytearray()
        for _ in range(max_new_bytes):
            next_byte = int(rng.choice(VOCAB_SIZE, p=self.probabilities(previous)))
            generated.append(next_byte)
            previous = next_byte
        return (encoded_prompt + bytes(generated)).decode("utf-8", errors="replace")

    def save(self, path: str | Path) -> Path:
        checkpoint = Path(path)
        if checkpoint.exists():
            raise FileExistsError(f"refusing to overwrite checkpoint: {checkpoint}")
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        with checkpoint.open("xb") as handle:
            np.savez_compressed(
                handle,
                counts=self.counts,
                alpha=np.asarray([self.alpha], dtype=np.float64),
                model_version=np.asarray([MODEL_VERSION]),
            )
        checkpoint.chmod(0o600)
        return checkpoint

    @classmethod
    def load(cls, path: str | Path) -> "ByteBigramModel":
        with np.load(Path(path), allow_pickle=False) as checkpoint:
            version = str(checkpoint["model_version"][0])
            if version != MODEL_VERSION:
                raise ValueError(f"unsupported checkpoint version: {version}")
            return cls(counts=checkpoint["counts"], alpha=float(checkpoint["alpha"][0]))


def run_cpu_smoke_experiment(
    dataset_path: str | Path = DEFAULT_DATASET,
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
    *,
    alpha: float = 0.5,
    generation_seed: int = 20260819,
) -> dict[str, Any]:
    """Train, checkpoint, reload, and measure the bounded local model once."""

    dataset = Path(dataset_path)
    output = Path(output_directory)
    artifact_path = output / "experiment.json"
    checkpoint_path = output / "byte_bigram_model.npz"
    if artifact_path.exists() or checkpoint_path.exists():
        existing = artifact_path if artifact_path.exists() else checkpoint_path
        raise FileExistsError(f"refusing to overwrite CPU smoke output: {existing}")
    records = load_instruction_records(dataset)
    train_records, holdout_records = split_records(records)
    train_texts = tuple(canonical_record_text(record) for record in train_records)
    holdout_texts = tuple(canonical_record_text(record) for record in holdout_records)
    model = ByteBigramModel.train(train_texts, alpha=alpha)
    train_nll, train_tokens = model.negative_log_likelihood(train_texts)
    holdout_nll, holdout_tokens = model.negative_log_likelihood(holdout_texts)
    checkpoint = model.save(checkpoint_path)
    reloaded = ByteBigramModel.load(checkpoint)
    reloaded_holdout_nll, _ = reloaded.negative_log_likelihood(holdout_texts)
    if not math.isclose(holdout_nll, reloaded_holdout_nll, rel_tol=0.0, abs_tol=1e-12):
        raise RuntimeError("checkpoint reload changed held-out likelihood")
    output.mkdir(parents=True, exist_ok=True)
    artifact = {
        "schema_version": "beast-brain-cpu-smoke-experiment-v1",
        "status": "completed_local_cpu_smoke",
        "dataset": {
            "path": display_path(dataset),
            "sha256": sha256_file(dataset),
            "records": len(records),
            "train_records": len(train_records),
            "holdout_records": len(holdout_records),
        },
        "model": {
            "type": "smoothed_byte_bigram",
            "model_version": MODEL_VERSION,
            "vocabulary_size": VOCAB_SIZE,
            "alpha": alpha,
            "checkpoint_path": display_path(checkpoint),
            "checkpoint_sha256": sha256_file(checkpoint),
            "checkpoint_format": "numpy_npz_allow_pickle_false",
        },
        "metrics": {
            "uniform_byte_baseline_nll": math.log(VOCAB_SIZE),
            "train_nll": train_nll,
            "train_tokens": train_tokens,
            "heldout_nll": holdout_nll,
            "heldout_tokens": holdout_tokens,
            "reload_heldout_nll": reloaded_holdout_nll,
        },
        "generated_preview": {
            "prompt": '{"instruction":',
            "seed": generation_seed,
            "max_new_bytes": 96,
            "text": reloaded.generate('{"instruction":', max_new_bytes=96, seed=generation_seed),
            "interpretation": "Unconstrained byte continuation for serialization testing only; it is not a valid instruction answer or a BEAST candidate.",
        },
        "execution_boundary": {
            "network_calls": 0,
            "llm_calls": 0,
            "generated_source_executed": False,
            "persistent_worker_started": False,
            "runtime": "local NumPy CPU byte-bigram only",
        },
        "claim_boundary": {
            "is_llm": False,
            "is_fine_tuned_model": False,
            "is_ollama_model": False,
            "benchmark_claim": "none",
            "meaning": "The experiment verifies bounded data/model/checkpoint plumbing, not language reasoning, primitive discovery, benchmark superiority, or autonomous improvement.",
        },
    }
    with artifact_path.open("x", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    artifact_path.chmod(0o600)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the bounded local AGNES-BRAIN CPU smoke experiment.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--generation-seed", type=int, default=20260819)
    args = parser.parse_args()
    artifact = run_cpu_smoke_experiment(
        args.dataset,
        args.output_directory,
        alpha=args.alpha,
        generation_seed=args.generation_seed,
    )
    metrics = artifact["metrics"]
    print(
        f"Local CPU smoke complete: held-out NLL {metrics['heldout_nll']:.6f} "
        f"versus uniform-byte baseline {metrics['uniform_byte_baseline_nll']:.6f}; "
        "no LLM, network, generated-source execution, or worker was used."
    )


if __name__ == "__main__":
    main()
