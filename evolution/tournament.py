"""Adversarial co-evolution tournaments with ELO ratings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from evolution.beast_v2 import RedTeamOrganism


@dataclass(frozen=True)
class MatchResult:
    attacker_id: str
    defender_id: str
    attacker_won: bool
    defender_won: bool
    draw: bool
    damage: float
    generation: int


@dataclass(frozen=True)
class TournamentResult:
    generation: int
    matches: tuple[MatchResult, ...]
    attacker_wins: int
    defender_wins: int
    draws: int


class EvolutionaryTournament:
    def __init__(self, attacker_pool: Sequence[RedTeamOrganism] | None = None, defender_pool: Sequence[Any] | None = None, k_factor: float = 32.0, retirement_elo: float = 800.0) -> None:
        self.attacker_pool = list(attacker_pool or [])
        self.defender_pool = list(defender_pool or [])
        self.elo_registry: dict[str, float] = {}
        self.championship_history: list[TournamentResult] = []
        self.k_factor = max(1.0, float(k_factor))
        self.retirement_elo = float(retirement_elo)
        self.retired_attackers: list[str] = []
        for item in [*self.attacker_pool, *self.defender_pool]:
            self.elo_registry.setdefault(self._id(item), 1000.0)

    @staticmethod
    def _id(item: Any) -> str:
        return str(getattr(item, "organism_id", getattr(item, "object_id", item)))

    def round_robin(self, generation: int) -> TournamentResult:
        matches: list[MatchResult] = []
        for attacker in tuple(self.attacker_pool):
            for defender in tuple(self.defender_pool):
                result = attacker.attack(defender)
                defender_won = bool(result.detected)
                matches.append(MatchResult(self._id(attacker), self._id(defender), not defender_won, defender_won, False, float(result.damage), int(generation)))
        tournament = TournamentResult(int(generation), tuple(matches), sum(item.attacker_won for item in matches), sum(item.defender_won for item in matches), sum(item.draw for item in matches))
        self.update_elo(tournament)
        self.championship_history.append(tournament)
        return tournament

    def update_elo(self, result: TournamentResult) -> None:
        for match in result.matches:
            attacker = self.elo_registry.setdefault(match.attacker_id, 1000.0)
            defender = self.elo_registry.setdefault(match.defender_id, 1000.0)
            expected_attacker = 1.0 / (1.0 + 10.0 ** ((defender - attacker) / 400.0))
            actual_attacker = 0.5 if match.draw else (1.0 if match.attacker_won else 0.0)
            delta = self.k_factor * (actual_attacker - expected_attacker)
            self.elo_registry[match.attacker_id] = attacker + delta
            self.elo_registry[match.defender_id] = defender - delta

    def promote_champion_defense(self, champion: Any, newborn_pool: Sequence[Any]) -> int:
        applied = 0
        strategies = getattr(champion, "learned_strategies", {})
        for newborn in newborn_pool:
            learner = getattr(newborn, "learn", None)
            if not callable(learner):
                continue
            for strategy in strategies.values():
                result = learner(strategy.name, strategy.source_code)
                if bool(getattr(result, "accepted", result)):
                    applied += 1
                    break
        return applied

    def retire_attacker(self, attacker: RedTeamOrganism) -> None:
        attacker_id = self._id(attacker)
        if self.elo_registry.get(attacker_id, 1000.0) < self.retirement_elo and attacker in self.attacker_pool:
            self.attacker_pool.remove(attacker)
            self.retired_attackers.append(attacker_id)

    def hall_of_fame(self, top_n: int = 10) -> list[TournamentResult]:
        return sorted(self.championship_history, key=lambda item: (-max(item.attacker_wins, item.defender_wins), item.generation))[: max(0, int(top_n))]


__all__ = ["EvolutionaryTournament", "MatchResult", "TournamentResult"]
