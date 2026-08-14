"""Substrate export adapters for BEAST v4 research organisms."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DockerSpec:
    image: str
    dockerfile: str
    endpoints: tuple[str, ...] = ("POST /invoke", "GET /genome", "GET /memome")
    security: tuple[str, ...] = ("read-only-rootfs", "no-new-privileges", "drop-all-capabilities")


@dataclass(frozen=True)
class HardwareCircuit:
    language: str
    source: str
    neuron_count: int
    synapse_count: int


class ExportError(ValueError):
    """Raised when a substrate artifact exceeds a declared safe export budget."""


class WasmExportResult(bytes):
    """Byte-compatible WASM export carrying bounded strategy metadata."""

    def __new__(cls, binary: bytes, strategy_count: int) -> "WasmExportResult":
        result = bytes.__new__(cls, binary)
        result.binary = bytes(binary)
        result.strategy_count = int(strategy_count)
        return result


class SubstrateExporter:
    _MINIMAL_WASM = bytes.fromhex("0061736d01000000" "0105016000017f" "03020100" "0707010372756e0000" "0a0601040041010b")
    MAX_WASM_STRATEGIES = 20
    MAX_WASM_SIZE_BYTES = 512_000

    def _compile_to_wasm(self, strategies: list[Any]) -> bytes:
        """Emit the bounded research-mode module; strategy source is never executed here."""
        del strategies
        return self._MINIMAL_WASM

    def export_wasm(self, organism: Any) -> WasmExportResult:
        strategies = list(getattr(organism, "learned_strategies", {}).values())
        top_strategies = sorted(
            strategies,
            key=lambda strategy: float(getattr(strategy, "effectiveness", 0.0)),
            reverse=True,
        )[: self.MAX_WASM_STRATEGIES]
        wasm_bytes = self._compile_to_wasm(top_strategies)
        if len(wasm_bytes) > self.MAX_WASM_SIZE_BYTES:
            raise ExportError(
                f"WASM export size {len(wasm_bytes)} exceeds limit {self.MAX_WASM_SIZE_BYTES}"
            )
        return WasmExportResult(wasm_bytes, len(top_strategies))

    def export_container(self, organism: Any) -> DockerSpec:
        organism_id = re.sub(r"[^a-z0-9-]", "-", str(getattr(organism, "object_id", "organism")).lower()).strip("-") or "organism"
        metadata = json.dumps({"organism_id": organism_id, "strategies": len(getattr(organism, "learned_strategies", {}))}, sort_keys=True)
        dockerfile = "\n".join(["FROM python:3.12-slim", "WORKDIR /app", "COPY . /app", "USER 65532:65532", "ENTRYPOINT [\"python\", \"-m\", \"organism_service\"]", f"# metadata {metadata}"])
        return DockerSpec(f"living-objects/{organism_id}:v4", dockerfile)

    def export_circuit(self, organism: Any) -> HardwareCircuit:
        genome = getattr(organism, "spiking_genome", None)
        neurons = list(getattr(genome, "neurons", []))
        synapses = list(getattr(genome, "synapses", []))
        assigns = [f"assign spike_{neuron.neuron_id} = (potential_{neuron.neuron_id} >= 32'sd1);" for neuron in neurons]
        source = "module living_object(input logic clk);\n" + "\n".join(assigns) + "\nendmodule\n"
        return HardwareCircuit("SystemVerilog", source, len(neurons), len(synapses))

    def fitness_substrate_breadth(self, organism: Any) -> float:
        available = [self.export_wasm, self.export_container, self.export_circuit]
        successful = 0
        for exporter in available:
            try:
                exporter(organism)
                successful += 1
            except Exception:
                continue
        return round(successful / len(available), 6)


__all__ = ["DockerSpec", "ExportError", "HardwareCircuit", "SubstrateExporter", "WasmExportResult"]
