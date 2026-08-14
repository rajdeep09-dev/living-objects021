"""Sparse leaky-integrate-and-fire strategy genomes."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field


@dataclass
class LIFNeuron:
    neuron_id: int
    potential: float = 0.0
    last_spike: int = 0


@dataclass
class Synapse:
    source: int
    target: int
    weight: float
    last_pre_spike: int = 0
    last_post_spike: int = 0


@dataclass
class SpikingStrategyGenome:
    neurons: list[LIFNeuron] = field(default_factory=list)
    synapses: list[Synapse] = field(default_factory=list)
    spike_threshold: float = 1.0
    decay_rate: float = 0.9
    last_spike_pattern: list[int] = field(default_factory=list)

    def forward(self, inputs: list[float], timesteps: int = 10) -> list[int]:
        if timesteps < 1:
            raise ValueError("timesteps must be positive")
        if not self.neurons:
            return []
        fired: list[int] = []
        for timestep in range(timesteps):
            for index, value in enumerate(inputs):
                if index < len(self.neurons):
                    self.neurons[index].potential += float(value)
            for synapse in self.synapses:
                source = self.neurons[synapse.source]
                if source.last_spike:
                    self.neurons[synapse.target].potential += synapse.weight
            for neuron in self.neurons:
                neuron.potential *= self.decay_rate
                neuron.last_spike = int(neuron.potential >= self.spike_threshold)
                if neuron.last_spike:
                    fired.append(neuron.neuron_id)
                    neuron.potential = 0.0
            for synapse in self.synapses:
                synapse.last_pre_spike = self.neurons[synapse.source].last_spike
                synapse.last_post_spike = self.neurons[synapse.target].last_spike
        self.last_spike_pattern = fired
        return fired

    def mutate_topology(self, rng: random.Random) -> "SpikingStrategyGenome":
        clone = copy.deepcopy(self)
        if clone.neurons and (not clone.synapses or rng.random() < 0.6):
            source = rng.randrange(len(clone.neurons))
            target = rng.randrange(len(clone.neurons))
            if source != target:
                clone.synapses.append(Synapse(source, target, rng.uniform(-0.5, 0.8)))
        elif clone.synapses and rng.random() < 0.4:
            clone.synapses.pop(rng.randrange(len(clone.synapses)))
        for synapse in clone.synapses:
            synapse.weight = max(-2.0, min(2.0, synapse.weight + rng.gauss(0, 0.05)))
        return clone

    def hebbian_learn(self, reward: float) -> None:
        reward = max(-1.0, min(1.0, reward))
        for synapse in self.synapses:
            correlation = synapse.last_pre_spike * synapse.last_post_spike
            synapse.weight = max(-2.0, min(2.0, synapse.weight + 0.1 * reward * correlation))

    @property
    def energy_cost(self) -> float:
        return round(len(self.last_spike_pattern) + 0.05 * len(self.synapses), 6)


__all__ = ["LIFNeuron", "SpikingStrategyGenome", "Synapse"]
