"""Bounded substrate-export worker that accepts metadata only."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse
from evolution.substrate import SubstrateExporter


def handle(request: dict[str, object]) -> dict[str, object]:
    organism_id = str(request.get("organism_id", "substrate-worker"))[:96]
    substrate = str(request.get("substrate", "wasm"))
    if substrate not in {"wasm", "container", "circuit"}:
        raise ValueError("substrate must be wasm, container, or circuit")
    organism = SimpleNamespace(object_id=organism_id, learned_strategies={})
    organism.spiking_genome = SpikingStrategyGenome([LIFNeuron(0), LIFNeuron(1)], [Synapse(0, 1, 0.25)])
    exporter = SubstrateExporter()
    if substrate == "wasm":
        artifact = exporter.export_wasm(organism)
        return {"substrate": substrate, "bytes": len(artifact), "magic": artifact[:4].hex(), "verified": artifact[:4] == b"\x00asm"}
    if substrate == "container":
        value = exporter.export_container(organism)
        return {"substrate": substrate, "image": value.image, "dockerfile": value.dockerfile, "security": value.security}
    value = exporter.export_circuit(organism)
    return {"substrate": substrate, "language": value.language, "source": value.source, "neurons": value.neuron_count, "synapses": value.synapse_count}


def main() -> None:
    for line in sys.stdin:
        if len(line) > 16_384:
            print(json.dumps({"error": "request too large"}), flush=True)
            continue
        try:
            print(json.dumps(handle(json.loads(line))), flush=True)
        except Exception as exc:  # pragma: no cover - worker boundary
            print(json.dumps({"error": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
