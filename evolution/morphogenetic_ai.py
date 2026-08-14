"""Self-assembling spiking topologies grown from compact instructions."""

from __future__ import annotations

import copy
import random
from typing import Literal, TypedDict

from evolution.spiking import LIFNeuron, SpikingStrategyGenome, Synapse


class MorphogeneticInstruction(TypedDict):
    type: Literal["divide", "differentiate", "migrate", "connect", "apoptosis"]
    condition: str
    parameters: dict[str, float]


class MorphogeneticProgram:
    def __init__(self, instructions: list[MorphogeneticInstruction] | None = None, max_neurons: int = 1000, max_synapses: int = 10_000) -> None:
        self.instructions = list(instructions or [])
        self.max_neurons = max(1, int(max_neurons))
        self.max_synapses = max(1, int(max_synapses))

    def develop(self, seed_neuron: LIFNeuron, steps: int = 100) -> SpikingStrategyGenome:
        if steps < 0:
            raise ValueError("steps must be non-negative")
        neurons = [copy.deepcopy(seed_neuron)]
        synapses: list[Synapse] = []
        for _ in range(steps):
            for instruction in self.instructions:
                kind = instruction.get("type")
                params = instruction.get("parameters", {})
                if kind == "divide" and len(neurons) < self.max_neurons:
                    parent = neurons[-1]
                    neurons.append(LIFNeuron(len(neurons), parent.potential, parent.last_spike))
                elif kind == "differentiate" and neurons:
                    neurons[-1].potential = float(params.get("potential", neurons[-1].potential))
                elif kind == "migrate" and len(neurons) > 1:
                    neurons.append(neurons.pop(0))
                elif kind == "connect" and len(neurons) > 1 and len(synapses) < self.max_synapses:
                    source = int(params.get("source", len(neurons) - 2)) % len(neurons)
                    target = int(params.get("target", len(neurons) - 1)) % len(neurons)
                    if source != target and not any(edge.source == source and edge.target == target for edge in synapses):
                        synapses.append(Synapse(source, target, float(params.get("weight", 0.25))))
                elif kind == "apoptosis" and len(neurons) > 1:
                    doomed = int(params.get("neuron", len(neurons) - 1)) % len(neurons)
                    neurons.pop(doomed)
                    for index, neuron in enumerate(neurons):
                        neuron.neuron_id = index
                    synapses = [Synapse(edge.source, edge.target, edge.weight) for edge in synapses if edge.source != doomed and edge.target != doomed]
            if len(neurons) >= self.max_neurons and len(synapses) >= self.max_synapses:
                break
        return SpikingStrategyGenome(neurons=neurons[: self.max_neurons], synapses=synapses[: self.max_synapses])

    def mutate_instruction(self, rng: random.Random) -> "MorphogeneticProgram":
        child = MorphogeneticProgram(copy.deepcopy(self.instructions), self.max_neurons, self.max_synapses)
        if not child.instructions:
            child.instructions.append({"type": "divide", "condition": "always", "parameters": {}})
            return child
        index = rng.randrange(len(child.instructions))
        instruction = child.instructions[index]
        if rng.random() < 0.5:
            instruction["type"] = rng.choice(["divide", "differentiate", "migrate", "connect", "apoptosis"])
        instruction["parameters"]["weight"] = rng.uniform(-0.5, 0.8)
        return child

    def crossover(self, other: "MorphogeneticProgram") -> "MorphogeneticProgram":
        midpoint = len(self.instructions) // 2
        other_midpoint = len(other.instructions) // 2
        return MorphogeneticProgram(copy.deepcopy(self.instructions[:midpoint] + other.instructions[other_midpoint:]), min(self.max_neurons, other.max_neurons), min(self.max_synapses, other.max_synapses))

    def complexity(self) -> int:
        return max(1, min(10**9, (len(self.instructions) + 1) * (1 + len({item.get("type") for item in self.instructions}))))


__all__ = ["MorphogeneticInstruction", "MorphogeneticProgram"]
