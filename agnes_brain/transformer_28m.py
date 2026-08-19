"""Exact local-only 28.9M transformer specification for BEAST-BRAIN research.

This module defines architecture and data contracts only.  It never downloads
weights or data, calls a remote model, starts a service, or executes generated
text.  Training is intentionally implemented by a separate, time-bounded
runner so configuration validation can be tested without a long-lived job.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from agnes_brain.cpu_smoke import (
    DEFAULT_DATASET,
    canonical_record_text,
    load_instruction_records,
    sha256_file,
    split_records,
)

try:  # Keep base package imports usable when the optional training extra is absent.
    import torch
    from torch import Tensor, nn
    from torch.nn import functional as torch_functional

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - covered by an installed-extra skip in CI.
    torch = None  # type: ignore[assignment]
    Tensor = Any  # type: ignore[assignment,misc]
    nn = None  # type: ignore[assignment]
    torch_functional = None  # type: ignore[assignment]
    TORCH_AVAILABLE = False


MODEL_VERSION = "beast-brain-transformer-28m-v1"
BYTE_VOCABULARY_SIZE = 256


def require_torch() -> None:
    """Raise a precise local setup error instead of attempting a download."""

    if not TORCH_AVAILABLE:
        raise RuntimeError(
            "The optional local training dependency is unavailable. Install the project's "
            "training extra in a reviewed environment; this module never downloads model weights."
        )


@dataclass(frozen=True)
class Transformer28MConfig:
    """A tied-embedding GPT-style configuration totaling 28,864,544 parameters."""

    vocabulary_size: int = BYTE_VOCABULARY_SIZE
    block_size: int = 128
    embedding_size: int = 512
    attention_heads: int = 8
    layer_count: int = 9
    feedforward_size: int = 2080
    seed: int = 20260819

    def validate(self) -> None:
        if self.vocabulary_size != BYTE_VOCABULARY_SIZE:
            raise ValueError("the local contract uses an exact 256-byte vocabulary")
        if self.block_size < 8:
            raise ValueError("block_size must be at least eight bytes")
        if self.embedding_size % self.attention_heads != 0:
            raise ValueError("embedding_size must divide evenly across attention_heads")
        if self.layer_count < 1 or self.feedforward_size < self.embedding_size:
            raise ValueError("layer_count and feedforward_size are below the local model minimum")
        if not 28_800_000 <= self.expected_parameter_count <= 28_950_000:
            raise ValueError("configuration is outside the declared approximately-28.9M parameter band")

    @property
    def expected_parameter_count(self) -> int:
        """Calculate the exact trainable count with a tied input/output embedding."""

        width = self.embedding_size
        per_block = (
            4 * width * width  # query/key/value/projection matrices
            + 2 * width * self.feedforward_size  # two MLP matrices
            + self.feedforward_size  # first MLP bias
            + 9 * width  # attention biases, MLP projection bias, two LayerNorms
        )
        global_parameters = (
            self.vocabulary_size * width  # shared token embedding / output weight
            + self.block_size * width  # positional embedding
            + 2 * width  # final LayerNorm
            + self.vocabulary_size  # output bias
        )
        return self.layer_count * per_block + global_parameters

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


DEFAULT_CONFIG = Transformer28MConfig()


@dataclass(frozen=True)
class LocalDataManifest:
    """A deterministic description of the byte corpus used by a local run."""

    dataset_path: str
    dataset_sha256: str
    record_digest: str
    total_records: int
    train_records: int
    holdout_records: int
    train_bytes: int
    holdout_bytes: int
    source_policy: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def record_bytes(records: Iterable[dict[str, Any]]) -> bytes:
    """Encode canonical records with explicit separators and no hidden source data."""

    payloads = [canonical_record_text(record).encode("utf-8") for record in records]
    if not payloads:
        raise ValueError("cannot construct transformer bytes from an empty record set")
    return b"\n".join(payloads) + b"\n"


def build_local_data_manifest(
    dataset_path: str | Path = DEFAULT_DATASET,
) -> tuple[LocalDataManifest, bytes, bytes]:
    """Load the approved base corpus and return its immutable train/holdout split."""

    dataset = Path(dataset_path)
    records = load_instruction_records(dataset)
    train_records, holdout_records = split_records(records)
    train_payload = record_bytes(train_records)
    holdout_payload = record_bytes(holdout_records)
    record_digest = hashlib.sha256(
        "\n".join(sorted(str(record["record_id"]) for record in records)).encode("utf-8")
    ).hexdigest()
    manifest = LocalDataManifest(
        dataset_path=str(dataset),
        dataset_sha256=sha256_file(dataset),
        record_digest=record_digest,
        total_records=len(records),
        train_records=len(train_records),
        holdout_records=len(holdout_records),
        train_bytes=len(train_payload),
        holdout_bytes=len(holdout_payload),
        source_policy="approved local base records only; synthetic augmentation excluded",
    )
    return manifest, train_payload, holdout_payload


if TORCH_AVAILABLE:

    class CausalSelfAttention(nn.Module):  # type: ignore[misc]
        def __init__(self, config: Transformer28MConfig) -> None:
            super().__init__()
            self.heads = config.attention_heads
            self.head_width = config.embedding_size // config.attention_heads
            self.projection = nn.Linear(config.embedding_size, 3 * config.embedding_size)
            self.output = nn.Linear(config.embedding_size, config.embedding_size)

        def forward(self, values: Tensor) -> Tensor:
            batch, length, width = values.shape
            queries, keys, vectors = self.projection(values).chunk(3, dim=-1)
            shape = (batch, length, self.heads, self.head_width)
            queries = queries.view(shape).transpose(1, 2)
            keys = keys.view(shape).transpose(1, 2)
            vectors = vectors.view(shape).transpose(1, 2)
            attended = torch_functional.scaled_dot_product_attention(
                queries, keys, vectors, dropout_p=0.0, is_causal=True
            )
            return self.output(attended.transpose(1, 2).contiguous().view(batch, length, width))


    class TransformerBlock(nn.Module):  # type: ignore[misc]
        def __init__(self, config: Transformer28MConfig) -> None:
            super().__init__()
            self.norm_attention = nn.LayerNorm(config.embedding_size)
            self.attention = CausalSelfAttention(config)
            self.norm_mlp = nn.LayerNorm(config.embedding_size)
            self.mlp = nn.Sequential(
                nn.Linear(config.embedding_size, config.feedforward_size),
                nn.GELU(),
                nn.Linear(config.feedforward_size, config.embedding_size),
            )

        def forward(self, values: Tensor) -> Tensor:
            values = values + self.attention(self.norm_attention(values))
            return values + self.mlp(self.norm_mlp(values))


    class ByteTransformer28M(nn.Module):  # type: ignore[misc]
        """A local byte transformer whose only output is untrusted research data."""

        def __init__(self, config: Transformer28MConfig = DEFAULT_CONFIG) -> None:
            require_torch()
            config.validate()
            super().__init__()
            self.config = config
            self.token_embedding = nn.Embedding(config.vocabulary_size, config.embedding_size)
            self.position_embedding = nn.Embedding(config.block_size, config.embedding_size)
            self.blocks = nn.ModuleList(TransformerBlock(config) for _ in range(config.layer_count))
            self.final_norm = nn.LayerNorm(config.embedding_size)
            self.output = nn.Linear(config.embedding_size, config.vocabulary_size)
            self.output.weight = self.token_embedding.weight
            actual = parameter_count(self)
            if actual != config.expected_parameter_count:
                raise RuntimeError(
                    f"architecture count mismatch: expected {config.expected_parameter_count}, got {actual}"
                )

        def forward(self, token_ids: Tensor, targets: Tensor | None = None) -> tuple[Tensor, Tensor | None]:
            if token_ids.ndim != 2:
                raise ValueError("token_ids must have shape [batch, sequence]")
            _, length = token_ids.shape
            if length < 1 or length > self.config.block_size:
                raise ValueError("sequence length is outside the configured local context window")
            positions = torch.arange(length, device=token_ids.device)
            values = self.token_embedding(token_ids) + self.position_embedding(positions)[None, :, :]
            for block in self.blocks:
                values = block(values)
            logits = self.output(self.final_norm(values))
            loss = None
            if targets is not None:
                if targets.shape != token_ids.shape:
                    raise ValueError("targets must match token_ids shape")
                # ``-100`` is PyTorch's documented cross-entropy ignore index.  It
                # lets instruction tuning score response bytes without treating the
                # supplied prompt as a prediction target.
                loss = torch_functional.cross_entropy(
                    logits.reshape(-1, logits.size(-1)), targets.reshape(-1), ignore_index=-100
                )
            return logits, loss


else:

    class ByteTransformer28M:  # pragma: no cover - safety fallback for environments without optional deps.
        def __init__(self, config: Transformer28MConfig = DEFAULT_CONFIG) -> None:
            del config
            require_torch()


def parameter_count(model: Any) -> int:
    require_torch()
    return sum(int(parameter.numel()) for parameter in model.parameters())


def write_training_contract(path: str | Path, config: Transformer28MConfig, manifest: LocalDataManifest) -> Path:
    """Write a create-once contract that makes later training parameters auditable."""

    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite training contract: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    contract = {
        "schema_version": "beast-brain-transformer-training-contract-v1",
        "model_version": MODEL_VERSION,
        "model": {
            **config.as_dict(),
            "parameter_count": config.expected_parameter_count,
            "architecture": "tied-embedding causal byte transformer",
        },
        "dataset": manifest.as_dict(),
        "execution_boundary": {
            "network_calls": 0,
            "model_weights_downloaded": False,
            "external_dataset_downloaded": False,
            "persistent_worker_started": False,
            "generated_text_executed": False,
        },
        "claim_boundary": "A local loss measurement is not evidence of a useful LLM, parent-model transfer, general intelligence, or BEAST benchmark improvement.",
    }
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(contract, handle, sort_keys=True, indent=2)
        handle.write("\n")
    destination.chmod(0o600)
    return destination
