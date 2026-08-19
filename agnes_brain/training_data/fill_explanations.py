"""Create a local human-review handoff for unfinished champion explanations.

Provider-assisted filling remains disabled. This command never reads a provider
credential, makes a request, or mutates the source corpus. A reviewer may use
the resulting handoff as a checklist and then submit individually reviewed
explanations through a future provenance-preserving review workflow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SOURCE = Path(__file__).resolve().parent / "explanations" / "from_champions.jsonl"
DEFAULT_HANDOFF = Path(__file__).resolve().parent / "explanations" / "manual_review_handoff.jsonl"


def _read_jsonl(path: str | Path) -> tuple[dict[str, Any], ...]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"champion explanation corpus does not exist: {source}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"line {line_number} is not an object")
        records.append(payload)
    return tuple(records)


def pending_records(source: str | Path = DEFAULT_SOURCE) -> tuple[dict[str, Any], ...]:
    """Return only records still visibly marked as incomplete."""

    return tuple(record for record in _read_jsonl(source) if record.get("explanation") == "FILL")


def review_handoff(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Reduce source records to a reviewer checklist without inventing an answer."""

    handoff: list[dict[str, Any]] = []
    for record in records:
        record_id = record.get("record_id")
        source = record.get("source")
        if not isinstance(record_id, str) or not isinstance(source, dict):
            raise ValueError("incomplete champion record lacks its stable ID or provenance source")
        handoff.append(
            {
                "record_id": record_id,
                "task": record.get("task"),
                "source": source,
                "review_instruction": "A qualified reviewer must write an explanation from the artifact-backed source code; do not infer a score or claim external validation.",
                "status": "pending_human_review",
            }
        )
    return tuple(handoff)


def write_handoff(
    destination: str | Path = DEFAULT_HANDOFF,
    *,
    source: str | Path = DEFAULT_SOURCE,
) -> Path:
    """Write a new review checklist and never overwrite existing work."""

    output = Path(destination)
    if output.exists():
        raise FileExistsError(f"manual review handoff already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = review_handoff(pending_records(source))
    with output.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    output.chmod(0o600)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a local human-review explanation handoff.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--handoff", type=Path, default=DEFAULT_HANDOFF)
    args = parser.parse_args()
    pending = pending_records(args.source)
    print(
        "Provider-assisted explanation filling is disabled pending separate authorization. "
        f"{len(pending)} artifact-backed records remain marked FILL."
    )
    output = write_handoff(args.handoff, source=args.source)
    print(f"Wrote local human-review handoff to {output}; the source corpus was not modified.")


if __name__ == "__main__":
    main()
