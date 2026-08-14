"""Tissue-scale collective behaviour built from adaptive BEAST cells.

There is no central scheduler assigning a cell a target.  Cells act from their
local sensor vector and learned policy.  Tissue adds only two bounded channels:
directional local signals and energy transfer between adjacent cells.  A signal
generates delayed credit only when another cell later obtains the *actual*
resource or repair outcome it identified; an empty broadcast earns no credit.
"""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, Optional, Sequence

from evolution.cellular import (
    BASE_ACTIONS,
    ActionOutcome,
    AdaptiveCell,
    CellAction,
    CellSensors,
    CellWorld,
    MOVEMENT,
    Position,
)


TISSUE_ACTIONS: tuple[CellAction, ...] = BASE_ACTIONS + (
    CellAction.BROADCAST,
    CellAction.SHARE,
)


@dataclass(frozen=True)
class TissueSignal:
    """A short-lived local observation published by a single cell."""

    source_id: str
    position: Position
    kind: str
    strength: int
    expires_at: int


@dataclass(frozen=True)
class TissueMetrics:
    """Externally observable collective outcomes from one bounded tissue run."""

    ticks: int
    survivors: int
    total_energy: float
    resources_delivered: int
    repairs_completed: int
    broadcasts_used: int
    energy_shared: float
    cooperation_credit: float

    @property
    def collective_score(self) -> float:
        return round(
            1.75 * self.resources_delivered
            + 0.80 * self.repairs_completed
            + 0.08 * self.survivors
            + 0.015 * self.total_energy,
            6,
        )


@dataclass
class Tissue:
    """A finite cell population communicating only with adjacent/local signals."""

    world: CellWorld
    cells: list[AdaptiveCell]
    signals: list[TissueSignal] = field(default_factory=list)
    tick_count: int = 0
    enable_communication: bool = True
    signal_radius: int = 6
    signal_ttl: int = 7
    max_signals: int = 128
    _pending_credit: Dict[str, float] = field(default_factory=dict, init=False)
    _broadcasts_used: int = field(default=0, init=False)
    _energy_shared: float = field(default=0.0, init=False)
    _cooperation_credit: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if not self.cells:
            raise ValueError("a tissue needs at least one cell")
        if self.signal_radius <= 0 or self.signal_ttl <= 0 or self.max_signals <= 0:
            raise ValueError("signal limits must be positive")
        positions = [cell.position for cell in self.cells]
        if any(not self.world.in_bounds(position) for position in positions):
            raise ValueError("all cells must begin inside the world")

    @property
    def alive_cells(self) -> list[AdaptiveCell]:
        return [cell for cell in self.cells if cell.alive]

    def _direction(self, origin: Position, target: Position) -> int:
        dx = target[0] - origin[0]
        dy = target[1] - origin[1]
        if abs(dx) >= abs(dy) and dx:
            return 4 if dx > 0 else 3
        if dy:
            return 2 if dy > 0 else 1
        return 0

    def _nearest_signal(self, cell: AdaptiveCell) -> Optional[TissueSignal]:
        active = [
            signal
            for signal in self.signals
            if signal.expires_at >= self.tick_count
            and signal.source_id != cell.cell_id
            and self.world.manhattan(cell.position, signal.position) <= self.signal_radius
        ]
        if not active:
            return None
        return min(
            active,
            key=lambda signal: (
                self.world.manhattan(cell.position, signal.position),
                signal.source_id,
                signal.kind,
            ),
        )

    def sense(self, cell: AdaptiveCell) -> CellSensors:
        """Add a bounded tissue signal to the cell's ordinary environmental sensing."""

        base = self.world.sense(cell)
        if not self.enable_communication:
            return base
        signal = self._nearest_signal(cell)
        if signal is None:
            return base
        kind_bucket = 1 if signal.kind == "resource" else 2
        return replace(
            base,
            signal_bucket=kind_bucket,
            signal_direction=self._direction(cell.position, signal.position),
        )

    def _publish(self, cell: AdaptiveCell) -> bool:
        resource = self.world.resource_map.get(cell.position, 0)
        hazard = self.world.hazard_map.get(cell.position, 0)
        if resource:
            kind, strength = "resource", resource
        elif hazard:
            kind, strength = "hazard", hazard
        else:
            return False
        signal = TissueSignal(
            source_id=cell.cell_id,
            position=cell.position,
            kind=kind,
            strength=strength,
            expires_at=self.tick_count + self.signal_ttl,
        )
        self.signals.append(signal)
        if len(self.signals) > self.max_signals:
            del self.signals[: len(self.signals) - self.max_signals]
        return True

    def _nearest_share_recipient(self, source: AdaptiveCell) -> Optional[AdaptiveCell]:
        candidates = [
            cell
            for cell in self.alive_cells
            if cell.cell_id != source.cell_id
            and self.world.manhattan(source.position, cell.position) == 1
            and cell.energy < source.energy - 2.0
        ]
        return min(candidates, key=lambda cell: (cell.energy, cell.cell_id)) if candidates else None

    def _share_energy(self, source: AdaptiveCell) -> float:
        recipient = self._nearest_share_recipient(source)
        if recipient is None:
            return 0.0
        amount = min(2.0, source.energy - 2.0, recipient.max_energy - recipient.energy)
        if amount <= 0.0:
            return 0.0
        source.energy -= amount
        recipient.energy += amount
        self._energy_shared += amount
        return amount

    def _signal_source_for_outcome(self, actor: AdaptiveCell, outcome: ActionOutcome) -> Optional[str]:
        if not (outcome.harvested or outcome.repaired):
            return None
        kind = "resource" if outcome.harvested else "hazard"
        candidates = [
            signal
            for signal in self.signals
            if signal.position == actor.position
            and signal.kind == kind
            and signal.source_id != actor.cell_id
            and signal.expires_at >= self.tick_count
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda signal: (signal.source_id, signal.expires_at)).source_id

    def _credit_signal_source(self, actor: AdaptiveCell, outcome: ActionOutcome) -> None:
        source_id = self._signal_source_for_outcome(actor, outcome)
        if source_id is None:
            return
        # Credit is proportional to the measured environmental event, not an
        # arbitrary reward for pressing the broadcast action.
        value = 0.45 * outcome.harvested + 0.55 * outcome.repaired
        self._pending_credit[source_id] = self._pending_credit.get(source_id, 0.0) + value
        self._broadcasts_used += 1

    def _step_cell(self, cell: AdaptiveCell, rng: random.Random) -> ActionOutcome:
        sensors = self.sense(cell)
        allowed = TISSUE_ACTIONS if self.enable_communication else BASE_ACTIONS
        action = cell.reason(sensors, rng, allowed_actions=allowed)
        pending = self._pending_credit.pop(cell.cell_id, 0.0)
        outcome = self.world.apply(cell, action)
        if self.enable_communication and action == CellAction.BROADCAST:
            if self._publish(cell):
                outcome = replace(outcome, accepted=True, note="signal_published")
            else:
                outcome = replace(outcome, accepted=False, reward=outcome.reward - 0.20, note="no_local_signal")
        elif self.enable_communication and action == CellAction.SHARE:
            amount = self._share_energy(cell)
            if amount:
                outcome = replace(outcome, accepted=True, note=f"shared:{amount:.2f}")
            else:
                outcome = replace(outcome, accepted=False, reward=outcome.reward - 0.18, note="no_share_recipient")

        self._credit_signal_source(cell, outcome)
        total_reward = outcome.reward + pending
        after = self.sense(cell)
        cell.policy.learn(sensors.key(), action, total_reward, after.key(), cell.genome)
        cell.outcome_memory.append(replace(outcome, reward=round(total_reward, 6)))
        if len(cell.outcome_memory) > cell.max_outcomes:
            del cell.outcome_memory[: len(cell.outcome_memory) - cell.max_outcomes]
        cell.repairs_completed += outcome.repaired
        self._cooperation_credit += pending
        return outcome

    def tick(self, rng: random.Random) -> list[ActionOutcome]:
        """Advance every living cell exactly once under bounded local interaction."""

        self.tick_count += 1
        self.signals = [signal for signal in self.signals if signal.expires_at >= self.tick_count]
        outcomes: list[ActionOutcome] = []
        for cell in sorted(self.alive_cells, key=lambda current: current.cell_id):
            outcomes.append(self._step_cell(cell, rng))
        return outcomes

    def run(self, *, ticks: int, seed: int) -> TissueMetrics:
        if ticks <= 0:
            raise ValueError("ticks must be positive")
        rng = random.Random(seed)
        for _ in range(ticks):
            if not self.alive_cells:
                break
            self.tick(rng)
        return self.metrics()

    def metrics(self) -> TissueMetrics:
        return TissueMetrics(
            ticks=self.tick_count,
            survivors=len(self.alive_cells),
            total_energy=round(sum(cell.energy for cell in self.alive_cells), 6),
            resources_delivered=sum(cell.delivered_resource for cell in self.cells),
            repairs_completed=sum(cell.repairs_completed for cell in self.cells),
            broadcasts_used=self._broadcasts_used,
            energy_shared=round(self._energy_shared, 6),
            cooperation_credit=round(self._cooperation_credit, 6),
        )

    def clone(self, *, communication: Optional[bool] = None) -> "Tissue":
        """Clone world and cells for a fair communication-enabled comparison."""

        copied_cells = [AdaptiveCell.from_state(cell.to_state()) for cell in self.cells]
        return Tissue(
            world=self.world.clone(),
            cells=copied_cells,
            enable_communication=self.enable_communication if communication is None else communication,
            signal_radius=self.signal_radius,
            signal_ttl=self.signal_ttl,
            max_signals=self.max_signals,
        )


@dataclass(frozen=True)
class TissueComparison:
    """Fair paired evaluation with identical initial tissue and world state."""

    enabled: TissueMetrics
    disabled: TissueMetrics

    @property
    def score_delta(self) -> float:
        return round(self.enabled.collective_score - self.disabled.collective_score, 6)


def compare_communication(tissue: Tissue, *, ticks: int, seed: int) -> TissueComparison:
    """Run communication-enabled and disabled conditions from identical state."""

    enabled = tissue.clone(communication=True).run(ticks=ticks, seed=seed)
    disabled = tissue.clone(communication=False).run(ticks=ticks, seed=seed)
    return TissueComparison(enabled=enabled, disabled=disabled)
