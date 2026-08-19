from __future__ import annotations

import json
from pathlib import Path

import pytest

from agnes_brain.training_data.collect_primitives import build_examples, build_examples_with_ids, collect
from evolution.gp_engine import ALL_REGISTERED_PRIMITIVES
from living_objects.beast_brain import ProvenanceError


def test_primitive_collector_covers_every_registered_primitive_with_a_rule_based_rationale() -> None:
    examples = build_examples()
    by_name = {example["suggested"]["name"]: example for example in examples}

    assert len(examples) == len(ALL_REGISTERED_PRIMITIVES)
    assert set(by_name) == {primitive.name for primitive in ALL_REGISTERED_PRIMITIVES}
    assert by_name["add"]["suggested"]["rationale"] == "useful for numeric computation"
    assert by_name["head"]["suggested"]["rationale"] == "useful for list tasks"
    assert by_name["upper1"]["suggested"]["rationale"] == "useful for text extraction tasks"
    assert all(example["suggested"]["name"] not in example["existing_primitives"] for example in examples)
    assert all(example["source"]["has_side_effects"] is False for example in examples)
    assert all("fitness" not in json.dumps(example) for example in examples)


def test_primitive_collector_writes_a_complete_content_identified_jsonl_file(tmp_path: Path) -> None:
    output = tmp_path / "from_codebase.jsonl"
    written = collect(output)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert written == output
    assert len(rows) >= 30
    assert rows == list(build_examples_with_ids())
    assert all(row["schema_version"] == "agnes-brain-primitive-example-v1" for row in rows)
    assert output.stat().st_mode & 0o077 == 0
    with pytest.raises(ProvenanceError, match="already exists"):
        collect(output)
