"""Combat state: constants, the serializable models (EncounterState, Combatant, Entity…), read-only queries and the end-of-fight check."""

from typing import Literal

from pydantic import BaseModel, Field


NEGATIVE_STATUSES = {
    "bleeding",
    "burning",
    "poisoned",
    "frightened",
    "stunned",
    "vulnerable",
    "asleep",
    "restrained",
    "hexed",
    "marked",
}
# A status refreshes, it never stacks: applying it again keeps the longer of the two durations, and the
# duration goes down once per turn of whoever carries it (_tick_statuses).
HARD_CONTROL = ("stunned", "asleep", "restrained", "frightened")
BOSS_CONTROL_TURNS = 1  # on a boss, hard control lasts this long and the rest becomes `vulnerable`
# how many of each kind of entity one hero may have at once (roadmap_balance §7): the Summoner keeps two,
# every other kind of helper is a single one. A being that is already in the fight cannot be called again.
MAX_BY_KIND = {"summon": 2, "servant": 1, "companion": 1, "construct": 1, "turret": 1, "totem": 1}
CONVERGENCE_TO_HIT = 2
CONVERGENCE_DAMAGE = 3
COMMAND_FLOOR = 1  # an ordered strike never does less than this
DOT = {"bleeding": "1d4", "burning": "1d6"}
BLESS_BONUS = 2
INSPIRATION_DIE = "1d6"
HEX_DIE = "1d6"  # necrotic, on every hit against a hexed target
MARK_DIE = "1d6"  # piercing, on every hit against a marked quarry (the hunter's counterpart of the hex)
SKIP_TURN = ("stunned", "asleep")
FLEE_DC_BASE = 10  # fleeing: this plus FLEE_DC_PER_FOE for each enemy still standing
FLEE_DC_PER_FOE = 2


class CombatError(Exception):
    """The requested action is not legal right now. ``key`` is an i18n key."""

    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


class AttackProfile(BaseModel):
    key: str
    name: dict[str, str]
    to_hit: int
    damage: str
    damage_type: str
    ranged: bool = False
    finesse: bool = False
    applies: dict | None = None  # {status, turns, chance}


class EntityTemplate(BaseModel):
    """An entity as the fight needs it: the numbers already scaled to the hero, nothing left to look up."""

    key: str
    name: dict[str, str]
    kind: Literal["summon", "servant", "companion", "construct", "turret", "totem"]
    role: Literal["damage", "area", "guard", "disrupt"]
    icon: str = "✦"
    hp: int
    to_hit: int = 0
    damage: str | None = None
    damage_type: str = "force"
    ranged: bool = False
    status: str | None = None
    status_turns: int = 1
    period: int = 1
    duration: int | None = None


class Entity(BaseModel):
    """One helper in the fight. It belongs to a combatant, acts once per turn of its owner and is stored
    with the encounter, so a restart leaves it exactly where it was."""

    id: str
    owner: str
    key: str
    name: dict[str, str]
    kind: str
    role: str
    icon: str = "✦"
    hp: int
    max_hp: int
    to_hit: int = 0
    damage: str | None = None
    damage_type: str = "force"
    ranged: bool = False
    status: str | None = None
    status_turns: int = 1
    period: int = 1
    ttl: int | None = None  # turns of its owner it still has left; None: the whole fight
    born: int = 1  # the round it joined: its `period` counts from there
    acted_round: int = 0  # the last round it acted in, so nothing makes it act twice in one
    boost: int = 0  # turns of Convergence left
    defeated: bool = False
    persistent: bool = False  # a servant or a companion: its state goes back to the character

    @property
    def active(self) -> bool:
        return not self.defeated


class Shape(BaseModel):
    """A form the hero can take, ready for the fight."""

    key: str
    name: dict[str, str]
    icon: str = "🐾"
    ac_bonus: int = 0
    temp_hp: int = 0
    attacks: list[AttackProfile]


class Combatant(BaseModel):
    id: str
    side: Literal["player", "enemy"]
    ref: str  # character id or monster key
    name: dict[str, str]
    hp: int
    max_hp: int
    ac: int
    row: Literal["front", "back"] = "front"
    dex_mod: int = 0
    wis_mod: int = 0  # saving throws
    passive_perception: int = 10
    initiative: int = 0
    attacks: list[AttackProfile] = []
    statuses: dict[str, int] = {}
    immune: list[str] = []
    creature_type: str = "humanoid"
    resist: list[str] = []  # damage types: half damage
    weak_to: list[str] = []  # damage types: double damage
    immune_damage: list[str] = []  # damage types: no damage
    # player-only
    level: int = 1
    skill_bonus: dict[str, int] = {}
    abilities: dict[str, int | None] = {}  # ability key -> uses left (None = unlimited)
    # the class's own bar (Conviction, Focus, Mana…). resource_max 0 means the class still runs on uses.
    resource: int = 0
    resource_max: int = 0
    resource_key: str = ""
    resource_per_turn: int = 0  # put back at the start of its own turn
    resource_on_attack: int = 0  # put back by a basic attack action, once per action
    cooldowns: dict[str, int] = {}  # ability key -> turns of combat left before it can be used again
    shapes: dict[str, Shape] = {}  # forms the hero can take in this fight
    form: str | None = None  # the form they are in now
    form_ac: int = 0  # what the current form added to AC, so leaving it takes it away again
    base_attacks: list[AttackProfile] = []  # their own attacks, kept while a form replaces them
    forms_taken: list[str] = []  # forms already taken this fight: their reserve is given only the first time
    mark: str | None = None  # the quarry their entities concentrate on
    thorns: str | None = None  # dice of damage the attacker takes back when this one is really hurt
    thorns_type: str = "radiant"
    resource_on_hurt: int = 0  # what the bar gets when this one is really hurt
    sneak_dice: int = 0
    extra_attack: bool = False
    halve_first_hit: bool = False
    relentless: bool = False
    crit_range: int = 20
    spell_to_hit: int = 0
    casting_mod: int = 0
    spell_dc: int = 10
    spell_damage_bonus: int = 0
    temp_hp: int = 0
    bonus_damage: str | None = None  # once per turn on a weapon hit (e.g. Divine Strike)
    bonus_damage_type: str = "radiant"
    consumables: dict[str, int] = {}  # combat items carried (potions, scrolls, bombs): key -> count
    # monster-only
    boss: bool = False
    cowardly: bool = False
    xp: int = 0
    # a boss with a pattern (roadmap_balance §9.1): a plate that wears away before its HP, a signalled heavy
    # attack, and a reload where it is exposed. ``pattern``: {"cycle": normal turns before it aims, "cycle_broken": same
    # once the plate is gone}
    plate: int = 0
    plate_max: int = 0
    rearm: int = 0  # the plate it hardens again with, once, when it is down to half its HP
    rearmed: bool = False
    pattern: dict | None = None
    pattern_state: Literal["ready", "aiming", "reloading"] = "ready"
    pattern_count: int = 0
    heavy: AttackProfile | None = None
    # turn state
    action_used: bool = False
    bonus_used: bool = False
    moved: bool = False
    sneak_used: bool = False
    bonus_damage_used: bool = False
    dodge_used: bool = False
    defeated: bool = False
    fled: bool = False

    @property
    def active(self) -> bool:
        return not (self.defeated or self.fled)


class LogEntry(BaseModel):
    key: str
    params: dict = {}


class SceneObjectState(BaseModel):
    key: str
    skill: str
    tier: str
    damage: str | None = None
    damage_type: str = "bludgeoning"
    targets: Literal["one", "all_enemies"] = "one"
    status: dict | None = None


class EncounterState(BaseModel):
    location: str
    round: int = 1
    order: list[str] = []
    turn_index: int = 0
    combatants: dict[str, Combatant] = {}
    scene_objects: dict[str, SceneObjectState] = {}
    status: Literal["active", "victory", "defeat", "fled"] = "active"
    hunt: bool = False  # started from 🏹 Hunt / 🐾 Track: a victory counts for "hunt" objectives
    entity_defs: dict[str, EntityTemplate] = {}  # what the hero may summon or command in this fight
    entities: dict[str, Entity] = {}
    log: list[LogEntry] = Field(default_factory=list)

    @property
    def current(self) -> Combatant:
        return self.combatants[self.order[self.turn_index]]

    def side(self, side: str) -> list[Combatant]:
        return [c for c in self.combatants.values() if c.side == side and c.active]

    def enemies_of(self, c: Combatant) -> list[Combatant]:
        return self.side("enemy" if c.side == "player" else "player")


class Action(BaseModel):
    kind: Literal["attack", "ability", "defend", "move", "flee", "interact", "heal_item", "item", "end_turn"]
    weapon: str | None = None
    ability: str | None = None  # kind "item": the item key; its ItemCombat comes in ability_defs["item:<key>"]
    target: str | None = None
    object: str | None = None
    heal_amount: int | None = None  # resolved by the inventory service
    item_name: dict[str, str] = {}  # kind "item": shown as the "weapon" of a scroll's attack


# ---------------------------------------------------------------- queries


def melee_targets(state: EncounterState, attacker: Combatant) -> list[Combatant]:
    foes = state.enemies_of(attacker)
    front = [f for f in foes if f.row == "front"]
    return front or foes


def valid_targets(state: EncounterState, attacker: Combatant, ranged: bool) -> list[Combatant]:
    return state.enemies_of(attacker) if ranged else melee_targets(state, attacker)


def available_bonus_actions(state: EncounterState, c: Combatant, ability_defs: dict) -> list[str]:
    if c.bonus_used:
        return []
    out = []
    for key, uses in c.abilities.items():
        a = ability_defs.get(key)
        if a and a.action == "bonus" and (uses is None or uses > 0) and affordable(c, key, a):
            if a.kind == "heal" and c.hp >= c.max_hp:
                continue
            if a.kind == "surge" and not c.action_used:
                continue
            out.append(key)
    return out


def affordable(c: Combatant, key: str, ability) -> bool:
    """Can this combatant pay for the ability right now (bar and cooldown)?"""
    return not (c.cooldowns.get(key, 0) > 0 or (c.resource_max and getattr(ability, "cost", 0) > c.resource))


def gain_resource(c: Combatant, amount: int) -> int:
    """Put `amount` back into the bar, never past its maximum. Returns what went in."""
    if not c.resource_max or amount <= 0:
        return 0
    before = c.resource
    c.resource = min(c.resource_max, c.resource + amount)
    return c.resource - before


def _check_end(state: EncounterState, logs: list[LogEntry]) -> None:
    if state.status != "active":
        return
    if not state.side("enemy"):
        state.status = "victory"
    elif not state.side("player"):
        players = [c for c in state.combatants.values() if c.side == "player"]
        state.status = "fled" if all(p.fled for p in players) else "defeat"
    else:
        return
    logs.append(LogEntry(key=f"combat.end.{state.status}"))


def _append(state: EncounterState, logs: list[LogEntry]) -> None:
    state.log = (state.log + logs)[-30:]
