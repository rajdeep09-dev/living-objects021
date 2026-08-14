"""A compact, evolving writing system for civilization-scale communication."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Symbol:
    glyph: str
    phonetic: str
    semantic: str
    generation_born: int


@dataclass(frozen=True)
class MeaningShift:
    glyph: str
    old_meaning: str
    new_meaning: str
    generation: int


@dataclass(frozen=True)
class Context:
    values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyIntent:
    action: str
    parameters: dict[str, float] = field(default_factory=dict)


@dataclass
class Grammar:
    layers: tuple[str, ...] = ("phonetic", "semantic", "pragmatic")
    order: tuple[str, ...] = ("action", "parameters")


class WritingSystem:
    def __init__(self, symbols: dict[str, Symbol] | None = None, grammar: Grammar | None = None, pragmatics: dict[str, str] | None = None, etymology: list[MeaningShift] | None = None, generation: int = 0) -> None:
        self.symbols = dict(symbols or {"·": Symbol("·", "a", "observe", 0), "∿": Symbol("∿", "co", "cooperate", 0), "!": Symbol("!", "f", "defect", 0)})
        self.grammar = grammar or Grammar()
        self.pragmatics = dict(pragmatics or {})
        self.etymology = list(etymology or [])
        self.generation = int(generation)

    def _glyph_for(self, action: str) -> str:
        for glyph, symbol in self.symbols.items():
            if symbol.semantic == action:
                return glyph
        glyph = chr(0x2500 + (len(self.symbols) % 96))
        self.symbols[glyph] = Symbol(glyph, f"x{len(self.symbols)}", action, self.generation)
        return glyph

    def write(self, intent: StrategyIntent, context: Context | None = None) -> str:
        glyph = self._glyph_for(intent.action)
        suffix = "".join(f"{key}={value};" for key, value in sorted(intent.parameters.items()))
        if context and context.values.get("mood") == "urgent":
            suffix = "!" + suffix
        return glyph + suffix

    def read(self, text: str, context: Context | None = None) -> StrategyIntent:
        if not text:
            raise ValueError("text cannot be empty")
        glyph = text[1:] if text.startswith("!") else text[0]
        symbol = self.symbols.get(glyph)
        if symbol is None:
            raise ValueError("unknown glyph")
        params: dict[str, float] = {}
        for token in text[1:].split(";"):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            try:
                params[key] = float(value)
            except ValueError:
                continue
        action = self.pragmatics.get(symbol.semantic, symbol.semantic) if context else symbol.semantic
        return StrategyIntent(action, params)

    def evolve(self, rng: random.Random) -> "WritingSystem":
        child = WritingSystem(copy.deepcopy(self.symbols), copy.deepcopy(self.grammar), dict(self.pragmatics), list(self.etymology), self.generation + 1)
        if child.symbols and rng.random() < 0.7:
            glyph = rng.choice(list(child.symbols))
            symbol = child.symbols[glyph]
            if rng.random() < 0.5:
                new_meaning = f"{symbol.semantic}:context{child.generation}"
                child.etymology.append(MeaningShift(glyph, symbol.semantic, new_meaning, child.generation))
                child.symbols[glyph] = Symbol(glyph, symbol.phonetic, new_meaning, symbol.generation_born)
        if rng.random() < 0.8:
            child._glyph_for(f"concept_{child.generation}_{len(child.symbols)}")
        return child

    def mutual_intelligibility(self, other: "WritingSystem") -> float:
        left = {symbol.semantic for symbol in self.symbols.values()}
        right = {symbol.semantic for symbol in other.symbols.values()}
        if not left and not right:
            return 1.0
        return round(len(left & right) / max(1, len(left | right)), 6)

    def translate(self, text: str, target_system: "WritingSystem") -> str:
        intent = self.read(text)
        quality = self.mutual_intelligibility(target_system)
        if quality == 0.0:
            return "?"
        return target_system.write(intent)

    @property
    def vocabulary_size(self) -> int:
        return len(self.symbols)


__all__ = ["Context", "Grammar", "MeaningShift", "StrategyIntent", "Symbol", "WritingSystem"]
