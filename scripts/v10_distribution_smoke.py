"""Execute a real bounded SDK run from an installed distribution wheel.

This script intentionally imports only the public package namespace.  It is
used by the v10 Python-version matrix and must not rely on the repository
being importable through the current working directory.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from living_objects import evolve


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="living-objects-wheel-") as directory:
        result = evolve(
            "manhattan",
            generations=1,
            seed=10_202_610,
            population_size=4,
            artifact_dir=Path(directory),
        )
        assert result.fitness == result.champion["training_fitness"]
        assert result.source_code == result.champion["source_audit_export"]
        assert result.artifact_path is not None
        assert Path(result.artifact_path).is_file()
        assert result.execution_boundary["runtime"] == "typed AST interpreter only"
        assert result.execution_boundary["llm_calls"] == 0
        assert result.execution_boundary["network_calls"] == 0


if __name__ == "__main__":
    main()
