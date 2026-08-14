"""Bounded universal-computation organisms for BEAST v4."""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from typing import Mapping


Transition = tuple[str, str, str]


@dataclass(frozen=True)
class TMResult:
    halted: bool
    accepted: bool
    steps_used: int
    final_tape: str
    state: str


@dataclass(frozen=True)
class SimulationResult:
    simulated: bool
    steps_used: int
    accepted: bool
    reason: str = ""


@dataclass
class OrganismTuringMachine:
    tape_alphabet: list[str] = field(default_factory=lambda: ["0", "1", "_"])
    states: list[str] = field(default_factory=lambda: ["q0", "accept", "reject"])
    transition_table: dict[tuple[str, str], Transition] = field(default_factory=dict)
    initial_state: str = "q0"
    accept_states: set[str] = field(default_factory=lambda: {"accept"})
    reject_states: set[str] = field(default_factory=lambda: {"reject"})

    def run(self, input_tape: str, step_limit: int = 10_000) -> TMResult:
        if step_limit < 1:
            raise ValueError("step_limit must be positive")
        tape = list(input_tape or "_")
        head = 0
        state = self.initial_state
        for steps in range(1, step_limit + 1):
            if state in self.accept_states:
                return TMResult(True, True, steps - 1, "".join(tape), state)
            if state in self.reject_states:
                return TMResult(True, False, steps - 1, "".join(tape), state)
            symbol = tape[head]
            transition = self.transition_table.get((state, symbol))
            if transition is None:
                return TMResult(True, False, steps - 1, "".join(tape), state)
            new_state, write_symbol, direction = transition
            if write_symbol not in self.tape_alphabet:
                raise ValueError(f"unknown tape symbol: {write_symbol}")
            tape[head] = write_symbol
            state = new_state
            if direction == "L":
                if head == 0:
                    tape.insert(0, "_")
                else:
                    head -= 1
            elif direction == "R":
                head += 1
                if head == len(tape):
                    tape.append("_")
            elif direction != "S":
                raise ValueError("direction must be L, R, or S")
        return TMResult(False, False, step_limit, "".join(tape), state)

    def simulate_organism(self, other: "OrganismTuringMachine") -> SimulationResult:
        encoded = "".join("1" if (state, symbol) in other.transition_table else "0" for state in other.states for symbol in other.tape_alphabet)
        result = self.run(encoded[:256] or "_", step_limit=max(100, len(encoded) * 10))
        return SimulationResult(result.halted, result.steps_used, result.accepted, "bounded self-simulation")

    def kolmogorov_complexity(self) -> int:
        payload = repr(sorted((key, value) for key, value in self.transition_table.items())).encode("utf-8")
        return max(1, len(zlib.compress(payload)))

    def universality_score(self) -> float:
        if not self.transition_table:
            return 0.0
        coverage = len(self.transition_table) / max(1, len(self.states) * len(self.tape_alphabet))
        return round(min(1.0, coverage * (1.0 if self.accept_states and self.reject_states else 0.5)), 6)


__all__ = ["OrganismTuringMachine", "SimulationResult", "TMResult", "Transition"]
