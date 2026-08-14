"""Bounded adaptive cells for the BEAST cellular-foundation experiment.

This module deliberately models a *minimal* adaptive cell rather than asserting
that software is biological or conscious.  A cell has a finite sensor vector,
finite action set, energy-constrained lifetime, mutable action-value memory,
and a heritable policy snapshot.  The world, rather than the cell, applies all
action effects.  Scores are therefore derived from observed resource delivery,
repair, energy, and survival—not from self-reported success.

The evaluator-cell and tissue layers are added in neighbouring modules.  This
file provides the auditable substrate they operate on.
"""
from __future__ import annotations

import copy
import itertools
import random
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple


Position = Tuple[int, int]
StateKey = Tuple[int, int, int, int, int, int, int]


class CellAction(str, Enum):
    """The only actions a cell policy may choose.

    Actions are symbolic data, not callbacks.  ``CellWorld.apply`` is the only
    interpreter and validates liveness, boundaries, inventory, and costs.
    """

    MOVE_NORTH = "move_north"
    MOVE_SOUTH = "move_south"
    MOVE_WEST = "move_west"
    MOVE_EAST = "move_east"
    HARVEST = "harvest"
    REPAIR = "repair"
    BROADCAST = "broadcast"
    SHARE = "share"
    WAIT = "wait"
    SIGNAL_ALARM = "signal_alarm"
    COORDINATE_WITH_NEIGHBOUR = "coordinate_with_neighbour"
    CACHE_RESOURCE = "cache_resource"
    PREDICT_HAZARD = "predict_hazard"


# Action names are declarative data. A cell can evolve a subset of this finite
# universe, but cannot register a callback, load source, or gain an action that
# the world has not already implemented and bounded.
ACTION_UNIVERSE: frozenset[str] = frozenset(action.value for action in CellAction)
MIN_ACTION_CAPABILITIES = 4
DEFAULT_ACTION_CAPABILITIES: frozenset[str] = frozenset({
    CellAction.MOVE_NORTH.value,
    CellAction.MOVE_SOUTH.value,
    CellAction.MOVE_WEST.value,
    CellAction.MOVE_EAST.value,
    CellAction.HARVEST.value,
    CellAction.WAIT.value,
})
COMMUNICATION_ACTIONS: frozenset[CellAction] = frozenset({
    CellAction.BROADCAST,
    CellAction.SHARE,
    CellAction.SIGNAL_ALARM,
    CellAction.COORDINATE_WITH_NEIGHBOUR,
})


MOVEMENT: Mapping[CellAction, Position] = {
    CellAction.MOVE_NORTH: (0, -1),
    CellAction.MOVE_SOUTH: (0, 1),
    CellAction.MOVE_WEST: (-1, 0),
    CellAction.MOVE_EAST: (1, 0),
}

BASE_ACTIONS: tuple[CellAction, ...] = (
    CellAction.MOVE_NORTH,
    CellAction.MOVE_SOUTH,
    CellAction.MOVE_WEST,
    CellAction.MOVE_EAST,
    CellAction.HARVEST,
    CellAction.REPAIR,
    CellAction.WAIT,
)


@dataclass(frozen=True)
class CellGenome:
    """Heritable, bounded policy parameters for one adaptive cell."""

    learning_rate: float = 0.38
    discount: float = 0.72
    exploration_rate: float = 0.20
    mutation_rate: float = 0.10
    inheritance_rate: float = 0.90
    repair_bias: float = 0.10
    cooperation: float = 0.50
    action_capabilities: frozenset[str] = DEFAULT_ACTION_CAPABILITIES
    generation_born: int = 0

    def __post_init__(self) -> None:
        normalized = frozenset(
            item.value if isinstance(item, CellAction) else str(item)
            for item in self.action_capabilities
        )
        unknown = normalized - ACTION_UNIVERSE
        if unknown:
            raise ValueError(f"unknown action capabilities: {sorted(unknown)}")
        if not MIN_ACTION_CAPABILITIES <= len(normalized) <= len(ACTION_UNIVERSE):
            raise ValueError(
                f"action_capabilities must contain {MIN_ACTION_CAPABILITIES}..{len(ACTION_UNIVERSE)} actions"
            )
        object.__setattr__(self, "action_capabilities", normalized)

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def mutate(self, rng: random.Random, *, generation_born: Optional[int] = None) -> "CellGenome":
        """Create a child genome including one bounded structural action mutation."""

        next_mutation_rate = self._clamp(
            self.mutation_rate + rng.gauss(0.0, self.mutation_rate * 0.20 + 0.008),
            0.01,
            0.40,
        )

        def shifted(value: float, low: float, high: float, scale: float = 1.0) -> float:
            return self._clamp(value + rng.gauss(0.0, next_mutation_rate * scale), low, high)

        capabilities = set(self.action_capabilities)
        unavailable = sorted(ACTION_UNIVERSE - capabilities)
        removable = sorted(capabilities) if len(capabilities) > MIN_ACTION_CAPABILITIES else []
        if unavailable and (not removable or rng.random() < 0.5):
            capabilities.add(rng.choice(unavailable))
        elif removable:
            capabilities.remove(rng.choice(removable))

        return CellGenome(
            learning_rate=shifted(self.learning_rate, 0.05, 0.90, 0.45),
            discount=shifted(self.discount, 0.05, 0.95, 0.35),
            exploration_rate=shifted(self.exploration_rate, 0.01, 0.55, 0.45),
            mutation_rate=next_mutation_rate,
            inheritance_rate=shifted(self.inheritance_rate, 0.05, 1.0, 0.20),
            repair_bias=shifted(self.repair_bias, 0.0, 0.80, 0.35),
            cooperation=shifted(self.cooperation, 0.0, 1.0, 0.35),
            action_capabilities=frozenset(capabilities),
            generation_born=self.generation_born + 1 if generation_born is None else generation_born,
        )

    def to_state(self) -> Dict[str, object]:
        state: Dict[str, object] = asdict(self)
        state["action_capabilities"] = sorted(self.action_capabilities)
        return state

    @classmethod
    def from_state(cls, payload: Mapping[str, object]) -> "CellGenome":
        fields = cls.__dataclass_fields__
        recognized = {name: payload[name] for name in fields if name in payload}
        return cls(**recognized)  # type: ignore[arg-type]


@dataclass(frozen=True)
class CellSensors:
    """Finite local observations presented to a cell policy."""

    resource_bucket: int
    hazard_bucket: int
    home_distance_bucket: int
    energy_bucket: int
    carried_bucket: int
    signal_bucket: int = 0
    signal_direction: int = 0

    def key(self) -> StateKey:
        return (
            self.resource_bucket,
            self.hazard_bucket,
            self.home_distance_bucket,
            self.energy_bucket,
            self.carried_bucket,
            self.signal_bucket,
            self.signal_direction,
        )


@dataclass(frozen=True)
class ActionOutcome:
    """Immutable evidence emitted after the world accepts or rejects an action."""

    action: CellAction
    reward: float
    accepted: bool
    energy_delta: float
    harvested: int = 0
    repaired: int = 0
    delivered: int = 0
    damage: float = 0.0
    note: str = ""


@dataclass
class CellPolicy:
    """Finite action-value memory updated from the cell's actual outcomes.

    The policy is intentionally narrow: a table maps a quantised sensor state
    to one value per allowed action.  It cannot call arbitrary code, access the
    world outside its sensors, or manufacture reward.  It *does* alter future
    choices from prediction error, which is the concrete learning mechanism.
    """

    values: Dict[StateKey, Dict[CellAction, float]] = field(default_factory=dict)
    max_states: int = 256

    def _row(self, state: StateKey) -> Dict[CellAction, float]:
        row = self.values.get(state)
        if row is None:
            if len(self.values) >= self.max_states:
                # Remove the oldest insertion deterministically to enforce a
                # hard memory limit. Python dictionaries preserve insertion order.
                self.values.pop(next(iter(self.values)))
            row = {action: 0.0 for action in CellAction}
            self.values[state] = row
        return row

    def choose(
        self,
        state: StateKey,
        genome: CellGenome,
        rng: random.Random,
        *,
        allowed_actions: Optional[Sequence[CellAction]] = None,
    ) -> CellAction:
        """Choose an action by bounded epsilon-greedy selection.

        The repair bias changes only a tie/initialisation preference; successful
        repair must still be reinforced by outcomes from the environment.
        """

        row = self._row(state)
        actions = tuple(allowed_actions or BASE_ACTIONS)
        if not actions:
            raise ValueError("at least one action must be allowed")
        if rng.random() < genome.exploration_rate:
            return rng.choice(list(actions))
        preference = {action: row[action] for action in actions}
        if CellAction.REPAIR in preference:
            preference[CellAction.REPAIR] += genome.repair_bias * 0.02
        best_value = max(preference.values())
        best_actions = sorted(
            action for action, value in preference.items() if value == best_value
        )
        return best_actions[0]

    def learn(
        self,
        state: StateKey,
        action: CellAction,
        reward: float,
        next_state: StateKey,
        genome: CellGenome,
        *,
        allowed_actions: Optional[Sequence[CellAction]] = None,
    ) -> None:
        """Apply one temporal-difference update from observed evidence."""

        row = self._row(state)
        actions = tuple(allowed_actions or tuple(CellAction(capability) for capability in sorted(genome.action_capabilities)))
        if action not in actions:
            raise ValueError("attempted to learn an action absent from the genome capability repertoire")
        next_best = max(self._row(next_state)[candidate] for candidate in actions)
        target = float(reward) + genome.discount * next_best
        row[action] += genome.learning_rate * (target - row[action])

    def inherited_copy(self, rng: random.Random, inheritance_rate: float) -> "CellPolicy":
        """Copy a bounded subset of learned values for Lamarckian inheritance."""

        copied: Dict[StateKey, Dict[CellAction, float]] = {}
        for state, row in self.values.items():
            if rng.random() <= inheritance_rate:
                copied[state] = dict(row)
        return CellPolicy(values=copied, max_states=self.max_states)

    def to_state(self) -> Dict[str, object]:
        return {
            "max_states": self.max_states,
            "values": {
                ",".join(str(value) for value in state): {
                    action.value: value for action, value in row.items()
                }
                for state, row in self.values.items()
            },
        }

    @classmethod
    def from_state(cls, payload: Mapping[str, object]) -> "CellPolicy":
        raw_values = payload.get("values", {})
        values: Dict[StateKey, Dict[CellAction, float]] = {}
        if isinstance(raw_values, Mapping):
            for encoded_state, raw_row in raw_values.items():
                if not isinstance(encoded_state, str) or not isinstance(raw_row, Mapping):
                    continue
                try:
                    state = tuple(int(value) for value in encoded_state.split(","))
                    if len(state) != 7:
                        continue
                    row = {
                        CellAction(str(action)): float(value)
                        for action, value in raw_row.items()
                        if str(action) in {candidate.value for candidate in CellAction}
                    }
                except (TypeError, ValueError):
                    continue
                values[state] = {action: row.get(action, 0.0) for action in CellAction}  # type: ignore[assignment]
        max_states = int(payload.get("max_states", 256))
        return cls(values=values, max_states=max(1, min(1024, max_states)))


@dataclass
class CellWorld:
    """Deterministic finite world that owns all action physics and rewards."""

    seed: int
    width: int = 7
    height: int = 7
    resource_sites: int = 8
    hazard_sites: int = 5
    home: Position = (0, 0)
    resource_map: Dict[Position, int] = field(init=False, default_factory=dict)
    hazard_map: Dict[Position, int] = field(init=False, default_factory=dict)
    tick_count: int = 0

    def __post_init__(self) -> None:
        if self.width < 3 or self.height < 3:
            raise ValueError("world dimensions must be at least 3")
        if not self.in_bounds(self.home):
            raise ValueError("home must be inside the world")
        rng = random.Random(self.seed)
        candidates = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) != self.home
        ]
        rng.shuffle(candidates)
        if self.resource_sites + self.hazard_sites > len(candidates):
            raise ValueError("too many world sites for the requested dimensions")
        for position in candidates[: self.resource_sites]:
            self.resource_map[position] = rng.randint(1, 3)
        for position in candidates[self.resource_sites : self.resource_sites + self.hazard_sites]:
            self.hazard_map[position] = rng.randint(1, 2)

    def clone(self) -> "CellWorld":
        """Return an identical world state for fair policy comparisons."""

        world = CellWorld(
            seed=self.seed,
            width=self.width,
            height=self.height,
            resource_sites=self.resource_sites,
            hazard_sites=self.hazard_sites,
            home=self.home,
        )
        world.resource_map = dict(self.resource_map)
        world.hazard_map = dict(self.hazard_map)
        world.tick_count = self.tick_count
        return world

    def in_bounds(self, position: Position) -> bool:
        return 0 <= position[0] < self.width and 0 <= position[1] < self.height

    def manhattan(self, first: Position, second: Position) -> int:
        return abs(first[0] - second[0]) + abs(first[1] - second[1])

    def local_hazard(self, position: Position) -> int:
        total = self.hazard_map.get(position, 0)
        for delta in MOVEMENT.values():
            adjacent = (position[0] + delta[0], position[1] + delta[1])
            total += self.hazard_map.get(adjacent, 0)
        return total

    def sense(self, cell: "AdaptiveCell") -> CellSensors:
        resource = self.resource_map.get(cell.position, 0)
        hazard = self.local_hazard(cell.position)
        distance = self.manhattan(cell.position, self.home)
        return CellSensors(
            resource_bucket=min(2, resource),
            hazard_bucket=min(2, hazard),
            home_distance_bucket=min(3, distance // 2),
            energy_bucket=min(3, max(0, int(cell.energy // 7))),
            carried_bucket=min(2, cell.carried_resource),
        )

    def _energy_cost(self, action: CellAction) -> float:
        if action in MOVEMENT:
            return 0.75
        if action in {CellAction.HARVEST, CellAction.REPAIR}:
            return 0.90
        if action in {CellAction.CACHE_RESOURCE, CellAction.PREDICT_HAZARD}:
            return 0.55
        return 0.35

    def apply(self, cell: "AdaptiveCell", action: CellAction) -> ActionOutcome:
        """Apply a validated action and return observable environmental evidence."""

        if not cell.alive:
            return ActionOutcome(action, reward=-1.0, accepted=False, energy_delta=0.0, note="dead")
        if action.value not in cell.genome.action_capabilities:
            return ActionOutcome(action, reward=-0.5, accepted=False, energy_delta=0.0, note="capability_unavailable")

        self.tick_count += 1
        before_energy = cell.energy
        cost = self._energy_cost(action)
        reward = -0.08
        accepted = True
        harvested = repaired = delivered = 0
        damage = 0.0
        note = ""

        if action in MOVEMENT:
            delta = MOVEMENT[action]
            target = (cell.position[0] + delta[0], cell.position[1] + delta[1])
            if self.in_bounds(target):
                cell.position = target
            else:
                accepted = False
                cost += 0.25
                reward -= 0.35
                note = "boundary"
        elif action == CellAction.HARVEST:
            available = self.resource_map.get(cell.position, 0)
            if available:
                self.resource_map[cell.position] = available - 1
                if self.resource_map[cell.position] == 0:
                    del self.resource_map[cell.position]
                cell.carried_resource += 1
                harvested = 1
                reward += 1.20
            else:
                accepted = False
                reward -= 0.30
                note = "no_resource"
        elif action == CellAction.REPAIR:
            severity = self.hazard_map.get(cell.position, 0)
            if severity:
                if severity == 1:
                    del self.hazard_map[cell.position]
                else:
                    self.hazard_map[cell.position] = severity - 1
                repaired = 1
                reward += 1.45
            else:
                accepted = False
                reward -= 0.25
                note = "no_hazard"
        elif action == CellAction.CACHE_RESOURCE:
            if cell.carried_resource:
                cell.carried_resource -= 1
                self.resource_map[cell.position] = self.resource_map.get(cell.position, 0) + 1
                reward += 0.12
                note = "resource_cached"
            else:
                accepted = False
                reward -= 0.20
                note = "no_resource_to_cache"
        elif action == CellAction.PREDICT_HAZARD:
            if self.local_hazard(cell.position):
                reward += 0.16
                note = "hazard_observed"
            else:
                accepted = False
                reward -= 0.12
                note = "no_hazard_observed"
        elif action in COMMUNICATION_ACTIONS:
            accepted = False
            reward -= 0.10
            note = "requires_tissue"

        if cell.position == self.home and cell.carried_resource:
            delivered = cell.carried_resource
            cell.delivered_resource += delivered
            cell.carried_resource = 0
            reward += delivered * 2.50

        severity = self.hazard_map.get(cell.position, 0)
        if severity:
            damage = min(4.0, 1.25 * severity)
            reward -= damage * 0.65
        cell.energy = max(0.0, min(cell.max_energy, cell.energy - cost - damage))
        cell.age += 1
        if cell.energy <= 0.0 or cell.age >= cell.max_age:
            cell.alive = False
            note = note or ("depleted" if cell.energy <= 0.0 else "aged")

        return ActionOutcome(
            action=action,
            reward=round(reward, 6),
            accepted=accepted,
            energy_delta=round(cell.energy - before_energy, 6),
            harvested=harvested,
            repaired=repaired,
            delivered=delivered,
            damage=damage,
            note=note,
        )


_cell_id_sequence = itertools.count(1)


@dataclass
class AdaptiveCell:
    """A finite adaptive unit with runtime learning and inheritable policy memory."""

    genome: CellGenome = field(default_factory=CellGenome)
    policy: CellPolicy = field(default_factory=CellPolicy)
    cell_id: str = field(default_factory=lambda: f"cell-{next(_cell_id_sequence)}")
    position: Position = (0, 0)
    energy: float = 24.0
    max_energy: float = 24.0
    max_age: int = 80
    age: int = 0
    carried_resource: int = 0
    delivered_resource: int = 0
    repairs_completed: int = 0
    alive: bool = True
    parent_id: Optional[str] = None
    outcome_memory: list[ActionOutcome] = field(default_factory=list)
    max_outcomes: int = 128

    def sense(self, world: CellWorld) -> CellSensors:
        return world.sense(self)

    def reason(
        self,
        sensors: CellSensors,
        rng: random.Random,
        *,
        allowed_actions: Optional[Sequence[CellAction]] = None,
    ) -> CellAction:
        """Turn local evidence plus learned memory into one bounded action."""

        if not self.alive:
            return CellAction.WAIT
        actions = tuple(allowed_actions) if allowed_actions is not None else self.allowed_actions()
        return self.policy.choose(sensors.key(), self.genome, rng, allowed_actions=actions)

    def allowed_actions(self, *, include_communication: bool = True) -> tuple[CellAction, ...]:
        """Return only bounded world actions explicitly present in this genome."""
        actions = tuple(CellAction(capability) for capability in sorted(self.genome.action_capabilities))
        if include_communication:
            return actions
        return tuple(action for action in actions if action not in COMMUNICATION_ACTIONS)

    def step(self, world: CellWorld, rng: random.Random) -> ActionOutcome:
        """Sense, reason, act, and learn from the world-owned outcome."""

        if not self.alive:
            return ActionOutcome(CellAction.WAIT, -1.0, False, 0.0, note="dead")
        before = self.sense(world)
        allowed = self.allowed_actions(include_communication=False)
        action = self.reason(before, rng, allowed_actions=allowed)
        outcome = world.apply(self, action)
        after = self.sense(world)
        self.policy.learn(
            before.key(), action, outcome.reward, after.key(), self.genome,
            allowed_actions=allowed,
        )
        self.outcome_memory.append(outcome)
        if len(self.outcome_memory) > self.max_outcomes:
            del self.outcome_memory[: len(self.outcome_memory) - self.max_outcomes]
        self.repairs_completed += outcome.repaired
        return outcome

    def reproduce(self, rng: random.Random, *, home: Position) -> "AdaptiveCell":
        """Create a child with mutated genome and bounded inherited lifetime learning."""

        if not self.alive:
            raise RuntimeError("dead cells cannot reproduce")
        child_genome = self.genome.mutate(rng)
        child_policy = self.policy.inherited_copy(rng, self.genome.inheritance_rate)
        return AdaptiveCell(
            genome=child_genome,
            policy=child_policy,
            position=home,
            energy=self.max_energy,
            max_energy=self.max_energy,
            max_age=self.max_age,
            parent_id=self.cell_id,
        )

    def survival_score(self) -> float:
        """Return an environmental performance summary, not an internal reward."""

        if not self.alive and self.energy <= 0:
            survival = 0.0
        else:
            survival = max(0.0, min(1.0, self.energy / self.max_energy))
        return round(
            0.50 * self.delivered_resource
            + 0.20 * self.repairs_completed
            + 0.30 * survival,
            6,
        )

    def to_state(self) -> Dict[str, object]:
        return {
            "cell_id": self.cell_id,
            "genome": self.genome.to_state(),
            "policy": self.policy.to_state(),
            "position": list(self.position),
            "energy": self.energy,
            "max_energy": self.max_energy,
            "max_age": self.max_age,
            "age": self.age,
            "carried_resource": self.carried_resource,
            "delivered_resource": self.delivered_resource,
            "repairs_completed": self.repairs_completed,
            "alive": self.alive,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_state(cls, payload: Mapping[str, object]) -> "AdaptiveCell":
        raw_genome = payload.get("genome", {})
        raw_policy = payload.get("policy", {})
        raw_position = payload.get("position", [0, 0])
        if not isinstance(raw_genome, Mapping) or not isinstance(raw_policy, Mapping):
            raise ValueError("cell state needs genome and policy mappings")
        if not isinstance(raw_position, Sequence) or len(raw_position) != 2:
            raise ValueError("cell state position must have two coordinates")
        return cls(
            cell_id=str(payload.get("cell_id", f"cell-{next(_cell_id_sequence)}")),
            genome=CellGenome.from_state(raw_genome),
            policy=CellPolicy.from_state(raw_policy),
            position=(int(raw_position[0]), int(raw_position[1])),
            energy=float(payload.get("energy", 24.0)),
            max_energy=float(payload.get("max_energy", 24.0)),
            max_age=int(payload.get("max_age", 80)),
            age=int(payload.get("age", 0)),
            carried_resource=int(payload.get("carried_resource", 0)),
            delivered_resource=int(payload.get("delivered_resource", 0)),
            repairs_completed=int(payload.get("repairs_completed", 0)),
            alive=bool(payload.get("alive", True)),
            parent_id=str(payload["parent_id"]) if payload.get("parent_id") is not None else None,
        )


def run_lifetime(cell: AdaptiveCell, world: CellWorld, *, ticks: int, seed: int) -> AdaptiveCell:
    """Run one bounded lifetime and return the same learned cell instance."""

    if ticks <= 0:
        raise ValueError("ticks must be positive")
    rng = random.Random(seed)
    for _ in range(ticks):
        if not cell.alive:
            break
        cell.step(world, rng)
    return cell


def evaluate_cell(
    cell: AdaptiveCell,
    *,
    world_seeds: Iterable[int],
    ticks: int = 70,
) -> float:
    """Evaluate a frozen policy on independent worlds without lifetime learning.

    This low-level evaluator is intentionally simple.  The protected
    holdout-promotion and evaluator-cell curriculum live in ``cellular_eval``.
    """

    scores: list[float] = []
    for offset, seed in enumerate(world_seeds):
        # A held-out rollout receives *only* the candidate's heritable genome
        # and learned policy. Position, age, energy, cargo, delivery counters,
        # repairs, liveness, and action history belong to its previous lifetime
        # and must never leak into an independent measurement.
        frozen = AdaptiveCell(
            genome=cell.genome,
            policy=copy.deepcopy(cell.policy),
            position=(0, 0),
            energy=cell.max_energy,
            max_energy=cell.max_energy,
            max_age=cell.max_age,
            alive=True,
        )
        world = CellWorld(seed=int(seed))
        rng = random.Random(int(seed) * 7919 + offset)
        for _ in range(ticks):
            if not frozen.alive:
                break
            sensors = frozen.sense(world)
            action = frozen.reason(sensors, rng)
            # The truth-style evaluation does not permit the candidate to
            # improve itself while being graded.
            outcome = world.apply(frozen, action)
            frozen.outcome_memory.append(outcome)
        scores.append(frozen.survival_score())
    return round(sum(scores) / len(scores), 6) if scores else 0.0
