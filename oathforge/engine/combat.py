"""Turn-based combat. Pure: state in, state + log out. No I/O, no AI.

The whole encounter is a pydantic model so it can be stored as JSON and
reloaded between Telegram updates. Log entries are i18n keys plus params;
combatant ids in params are resolved to names at render time.
"""

import random
from typing import Literal

from pydantic import BaseModel, Field

from oathforge.engine.checks import check, dc_for
from oathforge.engine.dice import d20, roll

NEGATIVE_STATUSES = {"bleeding", "burning", "poisoned", "frightened", "stunned", "vulnerable", "asleep", "restrained", "hexed",
                     "marked"}
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


# ---------------------------------------------------------------- setup

def start(state: EncounterState, rng: random.Random) -> list[LogEntry]:
    """Roll initiative, then let enemies act until it is a player's turn."""
    rolls = {}
    for cid, c in state.combatants.items():
        r = d20(rng).kept
        c.initiative = r + c.dex_mod
        rolls[cid] = [r, c.dex_mod]
    state.order = sorted(
        state.combatants,
        key=lambda cid: (
            state.combatants[cid].initiative,
            state.combatants[cid].dex_mod,
            state.combatants[cid].side == "player",
        ),
        reverse=True,
    )
    state.turn_index = 0
    logs = [LogEntry(key="combat.round", params={"round": 0}),  # round 0: who goes first
            LogEntry(key="combat.initiative", params={"order": list(state.order), "rolls": rolls}),
            LogEntry(key="combat.round", params={"round": state.round})]
    logs += _begin_turn(state, rng)
    logs += _run_enemies(state, rng)
    _append(state, logs)
    return logs


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


# ---------------------------------------------------------------- player turn

def player_act(
    state: EncounterState,
    actor_id: str,
    action: Action,
    rng: random.Random,
    ability_defs: dict,
) -> list[LogEntry]:
    """Apply one player action. ``ability_defs`` maps ability key -> ClassAbility."""
    if state.status != "active":
        raise CombatError("combat.err.over")
    actor = state.current
    if actor.id != actor_id or actor.side != "player":
        raise CombatError("combat.err.not_your_turn")

    logs: list[LogEntry] = []
    kind = action.kind

    if kind == "end_turn":
        logs += _end_turn(state, rng)
        logs += _run_enemies(state, rng)
        _append(state, logs)
        return logs

    if kind == "move":
        if actor.moved:
            raise CombatError("combat.err.already_moved")
        actor.row = "back" if actor.row == "front" else "front"
        actor.moved = True
        logs.append(LogEntry(key="combat.move", params={"actor": actor.id, "row": actor.row}))
        _append(state, logs)
        return logs

    ability = ability_defs.get(action.ability) if action.ability else None
    uses_bonus = kind == "ability" and ability is not None and ability.action == "bonus"
    if uses_bonus and actor.bonus_used:
        raise CombatError("combat.err.no_bonus")
    if not uses_bonus and actor.action_used:
        raise CombatError("combat.err.no_action")

    if kind == "attack":
        logs += _player_attack(state, actor, action.weapon, action.target, rng, extra=None)
    elif kind == "ability":
        logs += _use_ability(state, actor, action, ability, rng)
    elif kind == "defend":
        actor.statuses["defending"] = 1
        logs.append(LogEntry(key="combat.defend", params={"actor": actor.id}))
    elif kind == "heal_item":
        healed = _heal(actor, action.heal_amount or 0)
        _spend(actor, "healing_potion")
        logs.append(LogEntry(key="combat.potion", params={"actor": actor.id, "amount": healed}))
    elif kind == "item":
        logs += _use_item(state, actor, action, ability_defs.get(f"item:{action.ability}"), rng)
    elif kind == "flee":
        logs += _flee(state, actor, rng)
    elif kind == "interact":
        logs += _interact(state, actor, action, rng)
    else:  # pragma: no cover - guarded by the Literal
        raise CombatError("combat.err.invalid")

    if uses_bonus:
        actor.bonus_used = True
    else:
        actor.action_used = True

    _check_end(state, logs)
    if state.status == "active" and actor.action_used and (
        not actor.active or not available_bonus_actions(state, actor, ability_defs)
    ):
        logs += _end_turn(state, rng)
        logs += _run_enemies(state, rng)
    _append(state, logs)
    return logs


def _player_attack(state, actor, weapon_key, target_id, rng, extra) -> list[LogEntry]:
    profile = next((a for a in actor.attacks if a.key == weapon_key), None) or (
        actor.attacks[0] if actor.attacks and weapon_key is None else None
    )
    if profile is None:
        raise CombatError("combat.err.no_weapon")
    target = _resolve_target(state, actor, target_id, profile.ranged)
    if not profile.ranged and actor.row == "back":
        if actor.moved:
            raise CombatError("combat.err.too_far")
        actor.row, actor.moved = "front", True
    logs = _attack(state, actor, target, profile, rng, extra)
    if actor.extra_attack and extra is None:
        followups = valid_targets(state, actor, profile.ranged)
        if followups:
            nxt = target if target.active else followups[0]
            logs += _attack(state, actor, nxt, profile, rng, None)
    if gain_resource(actor, actor.resource_on_attack):  # once per action, not per swing
        logs.append(LogEntry(key="combat.resource_gained", params={
            "actor": actor.id, "resource": actor.resource_key, "amount": actor.resource_on_attack,
            "left": actor.resource}))
    return logs


def _use_ability(state, actor, action, ability, rng) -> list[LogEntry]:
    if ability is None or action.ability not in actor.abilities:
        raise CombatError("combat.err.unknown_ability")
    uses = actor.abilities[action.ability]
    if uses is not None and uses <= 0:
        raise CombatError("combat.err.no_uses")
    if actor.cooldowns.get(action.ability, 0) > 0:
        raise CombatError("combat.err.cooldown")
    if actor.resource_max and ability.cost > actor.resource:
        raise CombatError("combat.err.no_resource")
    logs: list[LogEntry] = []
    if ability.kind == "strike":
        profile = next((a for a in actor.attacks if a.ranged == ability.ranged), None)
        if profile is None:
            raise CombatError("combat.err.no_weapon")
        logs.append(LogEntry(key="combat.ability", params={"actor": actor.id, "ability": action.ability}))
        logs += _player_attack(
            state, actor, profile.key, action.target, rng,
            extra=(ability.extra_damage, ability.damage_type),
        )
    elif ability.kind in ("spell", "save"):
        logs.append(LogEntry(key="combat.ability", params={"actor": actor.id, "ability": action.ability}))
        logs += _cast(state, actor, ability, action.ability, action.target, rng,
                      to_hit=actor.spell_to_hit, dc=actor.spell_dc, dmg_bonus=actor.spell_damage_bonus)
    elif ability.kind == "curse":
        target = _resolve_target(state, actor, action.target, ranged=True)
        logs.append(LogEntry(key="combat.ability", params={"actor": actor.id, "ability": action.ability}))
        if ability.status:
            logs += _apply_status(target, ability.status, ability.status_turns)
    elif ability.kind == "turn":
        targets = [e for e in state.enemies_of(actor) if e.creature_type == ability.targets_type]
        if not targets:
            raise CombatError("combat.err.no_type_targets")
        logs.append(LogEntry(key="combat.turn", params={"actor": actor.id, "ability": action.ability}))
        for t in targets:
            if ability.damage:
                logs += _apply_damage(state, t, roll(ability.damage, rng).total, ability.damage_type or "radiant")
            if ability.status and t.active:
                logs += _apply_status(t, ability.status, ability.status_turns)
    elif ability.kind == "buff":
        logs += _cast(state, actor, ability, action.ability, None, rng, 0, 0, 0)
    elif ability.kind == "surge":
        if not actor.action_used:
            raise CombatError("combat.err.surge_unused")
        actor.action_used = False
        logs.append(LogEntry(key="combat.surge", params={"actor": actor.id, "ability": action.ability}))
    elif ability.kind == "heal":
        if actor.hp >= actor.max_hp:
            raise CombatError("combat.err.full_hp")
        logs += _cast(state, actor, ability, action.ability, None, rng, 0, 0, 0)
    elif ability.kind == "hide":
        dc = max((e.passive_perception for e in state.enemies_of(actor)), default=10)
        res = check(rng, "stealth", actor.skill_bonus.get("stealth", 0), dc)
        if res.success:
            actor.statuses["hidden"] = 99
        logs.append(LogEntry(key="combat.hide", params={
            "actor": actor.id, "roll": res.kept, "total": res.total, "dc": dc, "success": res.success,
        }))
    elif ability.kind == "summon":
        logs += _summon(state, actor, ability)
    elif ability.kind == "command":
        logs += _command(state, actor, ability, action.target, rng)
    elif ability.kind == "converge":
        logs += _converge(state, actor, ability)
    elif ability.kind == "shift":
        logs += _shift(state, actor, ability)
    else:
        raise CombatError("combat.err.passive")
    if uses is not None:
        actor.abilities[action.ability] = uses - 1
    if actor.resource_max:  # paid once, whatever the ability did
        spent = min(ability.cost, actor.resource)
        actor.resource -= spent
        if spent:
            logs.append(LogEntry(key="combat.resource_spent", params={
                "actor": actor.id, "resource": actor.resource_key, "amount": spent, "left": actor.resource}))
        gain_resource(actor, ability.generates)
    if ability.cooldown:
        actor.cooldowns = {**actor.cooldowns, action.ability: ability.cooldown}
    return logs


def _spend(actor: Combatant, item: str) -> None:
    if actor.consumables.get(item, 0) > 0:
        actor.consumables[item] -= 1


def _use_item(state, actor, action, item, rng) -> list[LogEntry]:
    """A scroll or a bomb: the same shapes as a spell, with the item's own numbers."""
    if item is None or actor.consumables.get(action.ability or "", 0) <= 0:
        raise CombatError("combat.err.no_item")
    if item.kind == "heal" and actor.hp >= actor.max_hp:
        raise CombatError("combat.err.full_hp")
    logs = [LogEntry(key="combat.item", params={"actor": actor.id, "item": action.ability})]
    if item.kind == "escape":
        actor.fled = True
        logs.append(LogEntry(key="combat.escaped", params={"actor": actor.id}))
    else:
        logs += _cast(state, actor, item, action.ability, action.target, rng,
                      to_hit=item.attack_bonus, dc=item.save_dc, dmg_bonus=0, name=action.item_name)
    _spend(actor, action.ability)
    return logs


def _cast(state, actor, ability, key, target_id, rng, to_hit: int, dc: int, dmg_bonus: int,
          name: dict | None = None) -> list[LogEntry]:
    """Resolve a spell, save, heal or buff; class abilities and combat items share it."""
    logs: list[LogEntry] = []
    if ability.kind == "spell":
        target = _resolve_target(state, actor, target_id, ranged=True)
        damage = _with_bonus(ability.damage or "1d4", dmg_bonus)
        dtype = ability.damage_type or "radiant"
        if ability.auto_hit:
            logs += _apply_damage(state, target, roll(damage, rng).total, dtype)
        else:
            profile = AttackProfile(key=key, name=name if name is not None else ability.name.model_dump(),
                                    to_hit=to_hit, damage=damage, damage_type=dtype, ranged=True)
            logs += _attack(state, actor, target, profile, rng, None, weapon=False)
    elif ability.kind == "save":
        target = _resolve_target(state, actor, target_id, ranged=True)
        targets = [target] if ability.area == "one" else [e for e in state.enemies_of(actor) if e.row == target.row]
        damage = _with_bonus(ability.damage, dmg_bonus) if ability.damage else None
        for t in targets:
            saved, save_logs = _save(t, ability.save or "dex", dc, rng)
            logs += save_logs
            if damage and (not saved or ability.half_on_save):
                amount = roll(damage, rng).total
                logs += _apply_damage(state, t, amount // 2 if saved else amount, ability.damage_type or "force")
            if ability.status and not saved and t.active:
                logs += _apply_status(t, ability.status, ability.status_turns)
    elif ability.kind == "buff":
        if ability.status:
            # +1: the turn it is cast ticks once, so the effect covers N later turns
            actor.statuses[ability.status] = ability.status_turns + 1
            logs.append(LogEntry(key="combat.buff", params={
                "actor": actor.id, "ability": key, "status": ability.status, "turns": ability.status_turns,
            }))
        if ability.temp_hp:
            amount = roll(ability.temp_hp, rng).total + _heal_add(actor, ability)
            actor.temp_hp = max(actor.temp_hp, amount)
            logs.append(LogEntry(key="combat.temp_hp", params={"actor": actor.id, "amount": actor.temp_hp}))
    elif ability.kind == "heal":
        amount = (ability.heal_per_level or 0) * actor.level
        if ability.heal_dice:
            amount += roll(ability.heal_dice, rng).total
        amount += _heal_add(actor, ability)
        healed = _heal(actor, amount)
        logs.append(LogEntry(key="combat.heal", params={"actor": actor.id, "ability": key, "amount": healed}))
    return logs


def _flee(state, actor, rng) -> list[LogEntry]:
    foes = state.enemies_of(actor)
    dc = FLEE_DC_BASE + FLEE_DC_PER_FOE * len(foes)
    skill = max(("athletics", "acrobatics"), key=lambda s: actor.skill_bonus.get(s, 0))
    res = check(rng, skill, actor.skill_bonus.get(skill, 0), dc)
    if res.success:
        actor.fled = True
    return [LogEntry(key="combat.flee", params={
        "actor": actor.id, "roll": res.kept, "total": res.total, "dc": dc, "success": res.success,
    })]


def _interact(state, actor, action, rng) -> list[LogEntry]:
    obj = state.scene_objects.get(action.object or "")
    if obj is None:
        raise CombatError("combat.err.no_object")
    dc = dc_for(obj.tier)
    res = check(rng, obj.skill, actor.skill_bonus.get(obj.skill, 0), dc)
    logs = [LogEntry(key="combat.interact", params={
        "actor": actor.id, "object": obj.key, "skill": obj.skill,
        "roll": res.kept, "total": res.total, "dc": dc, "success": res.success,
    })]
    if not res.success:
        return logs
    del state.scene_objects[obj.key]
    foes = state.enemies_of(actor)
    if obj.targets == "all_enemies":
        targets = foes
    else:
        targets = [_resolve_target(state, actor, action.target, ranged=True)]
    for t in targets:
        if obj.damage:
            dmg = roll(obj.damage, rng).total
            logs += _apply_damage(state, t, dmg, obj.damage_type)
        if obj.status and t.active:
            logs += _apply_status(t, obj.status["status"], obj.status["turns"])
    return logs


def _heal_add(actor: Combatant, ability) -> int:
    return {"level": actor.level, "casting": actor.casting_mod}.get(ability.heal_add or "", 0)


def _with_bonus(dice: str, bonus: int) -> str:
    return f"{dice}+{bonus}" if bonus > 0 else dice


# ---------------------------------------------------------------- core resolution

def _save(target: Combatant, ability: str, dc: int, rng) -> tuple[bool, list[LogEntry]]:
    """Saving throw of ``target`` (dex or wis) against ``dc``. Returns (saved, logs)."""
    mod = target.wis_mod if ability == "wis" else target.dex_mod
    r = d20(rng)
    total = r.kept + mod
    saved = not r.nat1 and (r.kept == 20 or total >= dc)
    return saved, [LogEntry(key="combat.save", params={
        "target": target.id, "save": ability, "roll": r.kept, "total": total, "dc": dc, "success": saved,
    })]


def _resolve_target(state, actor, target_id, ranged) -> Combatant:
    targets = valid_targets(state, actor, ranged)
    if not targets:
        raise CombatError("combat.err.no_target")
    if target_id is None:
        return targets[0]
    t = state.combatants.get(target_id)
    if t is None or t not in targets:
        raise CombatError("combat.err.bad_target")
    return t


def _attack(state, attacker, target, profile: AttackProfile, rng, extra, weapon: bool = True) -> list[LogEntry]:
    """One attack roll. ``extra`` = (dice, damage type) added on a hit; ``weapon`` = False for spells."""
    adv = "hidden" in attacker.statuses or any(s in target.statuses for s in ("stunned", "asleep", "restrained"))
    dis = (
        "poisoned" in attacker.statuses
        or "frightened" in attacker.statuses
        or "restrained" in attacker.statuses
        or "defending" in target.statuses
        or (profile.ranged and attacker.row == "front"
            and any(f.row == "front" for f in state.enemies_of(attacker)))
    )
    attacker.statuses.pop("hidden", None)
    r = d20(rng, adv, dis)
    total = r.kept + profile.to_hit + (BLESS_BONUS if "blessed" in attacker.statuses else 0)
    if attacker.statuses.pop("inspired", None):
        total += roll(INSPIRATION_DIE, rng).total
    hit = not r.nat1 and (r.kept >= attacker.crit_range or total >= target.ac)
    params = {
        "actor": attacker.id, "target": target.id, "weapon": profile.name,
        "roll": r.kept, "total": total, "ac": target.ac, "adv": adv and not dis, "dis": dis and not adv,
    }
    if len(r.rolls) > 1:  # advantage or disadvantage: both dice, and which one counts
        params["rolls"] = list(r.rolls)
    if not hit:
        return [LogEntry(key="combat.miss", params=params)]

    crit = r.kept >= attacker.crit_range
    dmg = roll(profile.damage, rng, crit).total
    # extra dice of another type are applied separately, so resistances apply per type
    extras: list[tuple[int, str]] = []
    if extra and extra[0]:
        extras.append((roll(extra[0], rng, crit).total, extra[1] or profile.damage_type))
    if weapon and attacker.bonus_damage and not attacker.bonus_damage_used and not profile.ranged:
        attacker.bonus_damage_used = True
        extras.append((roll(attacker.bonus_damage, rng, crit).total, attacker.bonus_damage_type))
    if attacker.side == "player" and "hexed" in target.statuses:
        extras.append((roll(HEX_DIE, rng, crit).total, "necrotic"))
    if attacker.side == "player" and "marked" in target.statuses:
        extras.append((roll(MARK_DIE, rng, crit).total, "piercing"))
    sneak = 0
    if (
        attacker.sneak_dice and not attacker.sneak_used
        and (profile.finesse or profile.ranged)
        and ((adv and not dis) or any(s in NEGATIVE_STATUSES for s in target.statuses))
    ):
        sneak = roll(f"{attacker.sneak_dice}d6", rng, crit).total
        attacker.sneak_used = True
        dmg += sneak
    params.update(crit=crit, sneak=sneak)
    logs = [LogEntry(key="combat.crit" if crit else "combat.hit", params=params)]
    logs += _apply_damage(state, target, dmg, profile.damage_type)
    for amount, dtype in extras:
        if target.active:
            logs += _apply_damage(state, target, amount, dtype)
    ap = profile.applies
    if ap and target.active and rng.random() < ap.get("chance", 1.0):
        logs += _apply_status(target, ap["status"], ap["turns"])
    return logs


def _apply_damage(state, target: Combatant, amount: int, damage_type: str) -> list[LogEntry]:
    effect = ""
    if damage_type in target.immune_damage:
        amount, effect = 0, "immune"
    elif damage_type in target.weak_to:
        amount, effect = amount * 2, "weak"
    elif damage_type in target.resist:
        amount, effect = amount // 2, "resist"
    if "vulnerable" in target.statuses:
        amount = amount * 3 // 2
    if target.halve_first_hit and not target.dodge_used and amount > 1:
        amount //= 2
        target.dodge_used = True
    guarded: list[LogEntry] = []
    if target.side == "player" and state.entities and amount > 0:
        guard = next((e for e in state.entities.values()
                      if e.owner == target.id and e.role == "guard" and e.active), None)
        if guard is not None:  # its HP are what it can take in the hero's place
            taken = min(guard.hp, amount)
            guard.hp -= taken
            amount -= taken
            guarded.append(LogEntry(key="combat.guard_absorbs", params={
                "entity": guard.name, "amount": taken, "left": guard.hp}))
            if guard.hp <= 0:
                guard.defeated = True
                guarded.append(LogEntry(key="combat.entity_breaks", params={"entity": guard.name}))
            if amount == 0:
                return guarded
    absorbed = min(target.temp_hp, amount)
    target.temp_hp -= absorbed
    target.hp = max(0, target.hp - (amount - absorbed))
    logs = guarded + [LogEntry(key="combat.damage", params={"target": target.id, "amount": amount, "type": damage_type,
                                                  "effect": effect, "hp": target.hp, "max_hp": target.max_hp})]
    if absorbed:
        logs.append(LogEntry(key="combat.absorbed", params={"target": target.id, "amount": absorbed}))
    if amount > 0 and target.hp > 0 and target.statuses.pop("asleep", None):
        logs.append(LogEntry(key="combat.wake", params={"target": target.id}))
    if target.hp == 0:
        if target.relentless:
            target.relentless = False
            target.hp = 1
            logs.append(LogEntry(key="combat.relentless", params={"target": target.id}))
        else:
            target.defeated = True
            target.statuses.clear()
            logs.append(LogEntry(key="combat.defeated", params={"target": target.id}))
    return logs


def _apply_status(target: Combatant, status: str, turns: int) -> list[LogEntry]:
    """Apply a status. It refreshes instead of stacking: the longer of the two durations wins.

    A boss is never chained: hard control lasts BOSS_CONTROL_TURNS on it and what is left over turns
    into `vulnerable`, which the log says out loud. A whole branch is never silently useless."""
    if status in target.immune:
        return [LogEntry(key="combat.immune", params={"target": target.id, "status": status})]
    logs = []
    if target.boss and status in HARD_CONTROL and turns > BOSS_CONTROL_TURNS:
        spill, turns = turns - BOSS_CONTROL_TURNS, BOSS_CONTROL_TURNS
        logs.append(LogEntry(key="combat.boss_resists", params={
            "target": target.id, "status": status, "turns": turns, "spill": spill}))
        target.statuses["vulnerable"] = max(spill, target.statuses.get("vulnerable", 0))
    target.statuses[status] = max(turns, target.statuses.get(status, 0))
    return logs + [LogEntry(key="combat.status", params={"target": target.id, "status": status, "turns": turns})]


def _heal(c: Combatant, amount: int) -> int:
    before = c.hp
    c.hp = min(c.max_hp, c.hp + max(0, amount))
    return c.hp - before


# ---------------------------------------------------------------- entities and forms

def spawn(state: EncounterState, owner: Combatant, tpl: EntityTemplate, *, hp: int | None = None,
          persistent: bool = False, acts_now: bool = False) -> Entity:
    """Put a helper in the fight. A summoned one waits for the next turn (nothing acts the turn it arrives);
    a permanent one, which is there from the start, may act at the end of the hero's first turn."""
    eid = f"e{len(state.entities) + 1}"
    ent = Entity(
        id=eid, owner=owner.id, key=tpl.key, name=tpl.name, kind=tpl.kind, role=tpl.role, icon=tpl.icon,
        hp=tpl.hp if hp is None else hp, max_hp=tpl.hp, to_hit=tpl.to_hit, damage=tpl.damage,
        damage_type=tpl.damage_type, ranged=tpl.ranged, status=tpl.status, status_turns=tpl.status_turns,
        period=tpl.period, ttl=tpl.duration, born=state.round, persistent=persistent,
        acted_round=0 if acts_now else state.round,
    )
    state.entities[eid] = ent
    return ent


def _summon(state, actor, ability) -> list[LogEntry]:
    tpl = state.entity_defs.get(ability.entity or "")
    if tpl is None:
        raise CombatError("combat.err.unknown_ability")
    # never again what was already called in this fight, alive or not: re-summoning must not be a free heal
    if any(e.owner == actor.id and e.key == tpl.key for e in state.entities.values()):
        raise CombatError("combat.err.already_called")
    here = [e for e in state.entities.values() if e.owner == actor.id and e.kind == tpl.kind and e.active]
    if len(here) >= MAX_BY_KIND[tpl.kind]:
        raise CombatError("combat.err.summon_limit")
    ent = spawn(state, actor, tpl)
    return [LogEntry(key="combat.summoned", params={"actor": actor.id, "entity": ent.name, "icon": ent.icon,
                                                    "hp": ent.hp})]


def _command(state, actor, ability, target_id, rng) -> list[LogEntry]:
    ent = next((e for e in state.entities.values()
                if e.owner == actor.id and e.key == ability.entity and e.active), None)
    if ent is None:
        raise CombatError("combat.err.no_entity")
    if ent.role == "guard":
        raise CombatError("combat.err.cannot_command")
    if ent.acted_round >= state.round:  # it already acted this round: an order is not a second turn
        raise CombatError("combat.err.entity_acted")
    if target_id:
        actor.mark = _resolve_target(state, actor, target_id, ranged=True).id
    ent.acted_round = state.round  # the order is its action: it will not also act as the turn ends
    logs = [LogEntry(key="combat.command", params={"actor": actor.id, "entity": ent.name, "icon": ent.icon})]
    return logs + _entity_act(state, ent, actor, rng, bonus=ability.extra_damage)


def _converge(state, actor, ability) -> list[LogEntry]:
    mine = [e for e in state.entities.values() if e.owner == actor.id and e.active]
    if not mine:
        raise CombatError("combat.err.no_entity")
    for e in mine:  # it strengthens what is there; it adds no entity and gives no extra turn
        e.boost = max(e.boost, ability.boost_turns)
    return [LogEntry(key="combat.converge", params={"actor": actor.id, "count": len(mine),
                                                    "turns": ability.boost_turns})]


def _entity_target(state, ent: Entity, owner: Combatant) -> Combatant | None:
    mark = state.combatants.get(owner.mark) if owner.mark else None
    if mark is not None and mark.active and mark.side != owner.side:
        return mark
    pool = valid_targets(state, owner, ent.ranged)
    return min(pool, key=lambda f: (f.hp, f.id)) if pool else None


def _entity_act(state, ent: Entity, owner: Combatant, rng, bonus: str | None = None) -> list[LogEntry]:
    """What one helper does with its action. Deterministic by role; only the dice are random."""
    if ent.role == "guard":
        return []
    target = _entity_target(state, ent, owner)
    if target is None:
        return []
    boosted = ent.boost > 0
    extra = (roll(bonus, rng).total if bonus else 0) + (CONVERGENCE_DAMAGE if boosted else 0)
    logs: list[LogEntry] = []
    if ent.role == "damage":
        r = d20(rng)
        total = r.kept + ent.to_hit + (CONVERGENCE_TO_HIT if boosted else 0)
        crit = r.kept == 20
        params = {"entity": ent.name, "icon": ent.icon, "target": target.id, "roll": r.kept, "total": total,
                  "ac": target.ac}
        if r.nat1 or not (crit or total >= target.ac):
            return [LogEntry(key="combat.entity_miss", params=params)]
        dmg = max(COMMAND_FLOOR, roll(ent.damage, rng, crit).total + extra)
        logs.append(LogEntry(key="combat.entity_crit" if crit else "combat.entity_hit", params=params))
        return logs + _apply_damage(state, target, dmg, ent.damage_type)
    if ent.role == "area":  # a whole row, never missing; each takes its own roll
        victims = [f for f in state.enemies_of(owner) if f.row == target.row]
        logs.append(LogEntry(key="combat.entity_area", params={"entity": ent.name, "icon": ent.icon,
                                                               "count": len(victims)}))
        for v in victims:
            if v.active:
                logs += _apply_damage(state, v, max(COMMAND_FLOOR, roll(ent.damage, rng).total + extra),
                                      ent.damage_type)
        return logs
    # disrupt: an affliction, not damage. On a boss it is capped like any other control (_apply_status)
    logs.append(LogEntry(key="combat.entity_afflicts", params={"entity": ent.name, "icon": ent.icon,
                                                               "target": target.id}))
    return logs + _apply_status(target, ent.status, ent.status_turns + (1 if boosted else 0))


def _run_entities(state, owner: Combatant, rng) -> list[LogEntry]:
    """The owner's helpers act, once each, as the owner's turn ends. A marker keeps anything (a bonus action,
    a menu, a retried button) from making one act twice in the same round. Nothing acts for an owner who is
    down or gone, or once the fight is over."""
    logs: list[LogEntry] = []
    if not owner.active or state.status != "active":
        return logs
    for ent in list(state.entities.values()):
        if ent.owner != owner.id or ent.defeated or ent.acted_round >= state.round:
            continue
        ent.acted_round = state.round
        if (state.round - ent.born) % ent.period == 0:
            logs += _entity_act(state, ent, owner, rng)
        if ent.boost:
            ent.boost -= 1
        if ent.ttl is not None:
            ent.ttl -= 1
            if ent.ttl <= 0:
                ent.defeated = True
                logs.append(LogEntry(key="combat.entity_fades", params={"entity": ent.name}))
        _check_end(state, logs)
        if state.status != "active":
            break
    return logs


def _shift(state, actor: Combatant, ability) -> list[LogEntry]:
    """Take a form, or (form "none") go back. The form replaces the attacks; its reserve of temporary HP is
    given only the first time in a fight, so changing shape back and forth never heals (roadmap_balance 7.4)."""
    if ability.form == "none":
        if actor.form is None:
            raise CombatError("combat.err.no_form")
        actor.attacks, actor.base_attacks = list(actor.base_attacks), []
        actor.ac -= actor.form_ac
        actor.form, actor.form_ac = None, 0
        return [LogEntry(key="combat.unshifted", params={"actor": actor.id})]
    shape = actor.shapes.get(ability.form or "")
    if shape is None:
        raise CombatError("combat.err.unknown_ability")
    if actor.form == shape.key:
        raise CombatError("combat.err.already_form")
    if actor.form is None:
        actor.base_attacks = list(actor.attacks)
    else:  # form to form: the old one's armour goes before the new one's comes
        actor.ac -= actor.form_ac
    actor.attacks, actor.form, actor.form_ac = list(shape.attacks), shape.key, shape.ac_bonus
    actor.ac += shape.ac_bonus
    gained = 0
    if shape.key not in actor.forms_taken:
        actor.forms_taken.append(shape.key)
        gained = max(0, shape.temp_hp - actor.temp_hp)  # a reserve, not a stack on top of another
        actor.temp_hp += gained
    return [LogEntry(key="combat.shifted", params={"actor": actor.id, "form": shape.name, "icon": shape.icon,
                                                   "temp": gained})]


# ---------------------------------------------------------------- turn flow

def _begin_turn(state: EncounterState, rng) -> list[LogEntry]:
    """Start-of-turn effects for the current combatant. Skips turns as needed."""
    logs: list[LogEntry] = []
    while state.status == "active":
        c = state.current
        c.action_used = c.bonus_used = c.moved = c.sneak_used = c.bonus_damage_used = False
        c.statuses.pop("defending", None)
        if c.active:
            if c.cooldowns:  # cooldowns are counted in turns of combat, never in real seconds
                c.cooldowns = {k: v - 1 for k, v in c.cooldowns.items() if v > 1}
            if gain_resource(c, c.resource_per_turn):
                logs.append(LogEntry(key="combat.resource_gained", params={
                    "actor": c.id, "resource": c.resource_key, "amount": c.resource_per_turn,
                    "left": c.resource}))
            for status, expr in DOT.items():
                if status in c.statuses and c.active:
                    dmg = roll(expr, rng).total
                    logs.append(LogEntry(key="combat.dot", params={"target": c.id, "status": status}))
                    logs += _apply_damage(state, c, dmg, status)
            _check_end(state, logs)
            if state.status != "active":
                break
        if not c.active:
            logs += _advance(state)
            continue
        skip = next((s for s in SKIP_TURN if s in c.statuses), None)
        if skip:
            logs.append(LogEntry(key=f"combat.{skip}", params={"target": c.id}))
            _tick_statuses(c)
            logs += _advance(state)
            continue
        break
    return logs


def _end_turn(state: EncounterState, rng) -> list[LogEntry]:
    me = state.current
    logs: list[LogEntry] = []
    if me.side == "player" and me.active and state.entities:  # the hero's helpers act once, as the turn ends
        logs += _run_entities(state, me, rng)
    _tick_statuses(me)
    if state.status != "active":
        return logs
    logs += _advance(state)
    return logs + _begin_turn(state, rng)


def _tick_statuses(c: Combatant) -> None:
    for status in list(c.statuses):
        if status in ("hidden", "defending"):
            continue
        c.statuses[status] -= 1
        if c.statuses[status] <= 0:
            del c.statuses[status]


def _advance(state: EncounterState) -> list[LogEntry]:
    """Next turn; a new round leaves a ``combat.round`` marker in the log (panel separator, battle report)."""
    state.turn_index += 1
    if state.turn_index < len(state.order):
        return []
    state.turn_index = 0
    state.round += 1
    for c in state.combatants.values():
        c.dodge_used = False
    return [LogEntry(key="combat.round", params={"round": state.round})]


def _run_enemies(state: EncounterState, rng) -> list[LogEntry]:
    logs: list[LogEntry] = []
    guard = 0
    while state.status == "active" and state.current.side == "enemy":
        guard += 1
        if guard > 100:  # pragma: no cover - safety net
            break
        logs += _enemy_turn(state, state.current, rng)
        _check_end(state, logs)
        if state.status != "active":
            break
        logs += _end_turn(state, rng)
    return logs


def _enemy_turn(state: EncounterState, me: Combatant, rng) -> list[LogEntry]:
    foes = state.enemies_of(me)
    if not foes or not me.attacks:
        return []
    allies = [a for a in state.side("enemy") if a.id != me.id]
    if me.cowardly and me.hp * 4 <= me.max_hp and allies:
        me.fled = True
        return [LogEntry(key="combat.enemy_flees", params={"actor": me.id})]
    target = min(foes, key=lambda f: (f.hp, f.id))
    melee = [a for a in me.attacks if not a.ranged]
    ranged = [a for a in me.attacks if a.ranged]
    logs: list[LogEntry] = []
    if me.row == "front" and melee:
        profile = melee[0]
    elif ranged:
        profile = ranged[0]
    else:
        me.row = "front"
        logs.append(LogEntry(key="combat.move", params={"actor": me.id, "row": "front"}))
        profile = melee[0]
    targets = valid_targets(state, me, profile.ranged)
    if target not in targets:
        target = targets[0]
    return logs + _attack(state, me, target, profile, rng, None)


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
