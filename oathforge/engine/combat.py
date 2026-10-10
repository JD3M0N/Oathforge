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

NEGATIVE_STATUSES = {"bleeding", "burning", "poisoned", "frightened", "stunned", "vulnerable"}
DOT = {"bleeding": "1d4", "burning": "1d6"}


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
    passive_perception: int = 10
    initiative: int = 0
    attacks: list[AttackProfile] = []
    statuses: dict[str, int] = {}
    immune: list[str] = []
    # player-only
    level: int = 1
    skill_bonus: dict[str, int] = {}
    abilities: dict[str, int | None] = {}  # ability key -> uses left (None = unlimited)
    sneak_dice: int = 0
    extra_attack: bool = False
    halve_first_hit: bool = False
    relentless: bool = False
    # monster-only
    cowardly: bool = False
    xp: int = 0
    # turn state
    action_used: bool = False
    bonus_used: bool = False
    moved: bool = False
    sneak_used: bool = False
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
    log: list[LogEntry] = Field(default_factory=list)

    @property
    def current(self) -> Combatant:
        return self.combatants[self.order[self.turn_index]]

    def side(self, side: str) -> list[Combatant]:
        return [c for c in self.combatants.values() if c.side == side and c.active]

    def enemies_of(self, c: Combatant) -> list[Combatant]:
        return self.side("enemy" if c.side == "player" else "player")


class Action(BaseModel):
    kind: Literal["attack", "ability", "defend", "move", "flee", "interact", "heal_item", "end_turn"]
    weapon: str | None = None
    ability: str | None = None
    target: str | None = None
    object: str | None = None
    heal_amount: int | None = None  # resolved by the inventory service


# ---------------------------------------------------------------- setup

def start(state: EncounterState, rng: random.Random) -> list[LogEntry]:
    """Roll initiative, then let enemies act until it is a player's turn."""
    for c in state.combatants.values():
        c.initiative = d20(rng).kept + c.dex_mod
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
    logs = [LogEntry(key="combat.initiative", params={"order": list(state.order)})]
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
        if a and a.action == "bonus" and (uses is None or uses > 0):
            if a.kind == "heal" and c.hp >= c.max_hp:
                continue
            out.append(key)
    return out


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
        logs.append(LogEntry(key="combat.potion", params={"actor": actor.id, "amount": healed}))
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
    return logs


def _use_ability(state, actor, action, ability, rng) -> list[LogEntry]:
    if ability is None or action.ability not in actor.abilities:
        raise CombatError("combat.err.unknown_ability")
    uses = actor.abilities[action.ability]
    if uses is not None and uses <= 0:
        raise CombatError("combat.err.no_uses")
    logs: list[LogEntry] = []
    if ability.kind == "strike":
        profile = next((a for a in actor.attacks if not a.ranged), None)
        if profile is None:
            raise CombatError("combat.err.no_weapon")
        logs.append(LogEntry(key="combat.ability", params={"actor": actor.id, "ability": action.ability}))
        logs += _player_attack(
            state, actor, profile.key, action.target, rng,
            extra=(ability.extra_damage, ability.damage_type),
        )
    elif ability.kind == "heal":
        if actor.hp >= actor.max_hp:
            raise CombatError("combat.err.full_hp")
        healed = _heal(actor, (ability.heal_per_level or 0) * actor.level)
        logs.append(LogEntry(key="combat.heal", params={"actor": actor.id, "ability": action.ability, "amount": healed}))
    elif ability.kind == "hide":
        dc = max((e.passive_perception for e in state.enemies_of(actor)), default=10)
        res = check(rng, "stealth", actor.skill_bonus.get("stealth", 0), dc)
        if res.success:
            actor.statuses["hidden"] = 99
        logs.append(LogEntry(key="combat.hide", params={
            "actor": actor.id, "roll": res.kept, "total": res.total, "dc": dc, "success": res.success,
        }))
    else:
        raise CombatError("combat.err.passive")
    if uses is not None:
        actor.abilities[action.ability] = uses - 1
    return logs


def _flee(state, actor, rng) -> list[LogEntry]:
    foes = state.enemies_of(actor)
    dc = 10 + 2 * len(foes)
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


# ---------------------------------------------------------------- core resolution

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


def _attack(state, attacker, target, profile: AttackProfile, rng, extra) -> list[LogEntry]:
    adv = "hidden" in attacker.statuses or "stunned" in target.statuses
    dis = (
        "poisoned" in attacker.statuses
        or "frightened" in attacker.statuses
        or "defending" in target.statuses
        or (profile.ranged and attacker.row == "front"
            and any(f.row == "front" for f in state.enemies_of(attacker)))
    )
    attacker.statuses.pop("hidden", None)
    r = d20(rng, adv, dis)
    total = r.kept + profile.to_hit
    hit = not r.nat1 and (r.nat20 or total >= target.ac)
    params = {
        "actor": attacker.id, "target": target.id, "weapon": profile.name,
        "roll": r.kept, "total": total, "ac": target.ac, "adv": adv and not dis, "dis": dis and not adv,
    }
    if not hit:
        return [LogEntry(key="combat.miss", params=params)]

    crit = r.nat20
    dmg = roll(profile.damage, rng, crit).total
    if extra and extra[0]:
        dmg += roll(extra[0], rng, crit).total
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
    ap = profile.applies
    if ap and target.active and rng.random() < ap.get("chance", 1.0):
        logs += _apply_status(target, ap["status"], ap["turns"])
    return logs


def _apply_damage(state, target: Combatant, amount: int, damage_type: str) -> list[LogEntry]:
    if "vulnerable" in target.statuses:
        amount = amount * 3 // 2
    if target.halve_first_hit and not target.dodge_used and amount > 1:
        amount //= 2
        target.dodge_used = True
    target.hp = max(0, target.hp - amount)
    logs = [LogEntry(key="combat.damage", params={"target": target.id, "amount": amount, "type": damage_type})]
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
    if status in target.immune:
        return [LogEntry(key="combat.immune", params={"target": target.id, "status": status})]
    target.statuses[status] = max(turns, target.statuses.get(status, 0))
    return [LogEntry(key="combat.status", params={"target": target.id, "status": status, "turns": turns})]


def _heal(c: Combatant, amount: int) -> int:
    before = c.hp
    c.hp = min(c.max_hp, c.hp + max(0, amount))
    return c.hp - before


# ---------------------------------------------------------------- turn flow

def _begin_turn(state: EncounterState, rng) -> list[LogEntry]:
    """Start-of-turn effects for the current combatant. Skips turns as needed."""
    logs: list[LogEntry] = []
    while state.status == "active":
        c = state.current
        c.action_used = c.bonus_used = c.moved = c.sneak_used = False
        c.statuses.pop("defending", None)
        if c.active:
            for status, expr in DOT.items():
                if status in c.statuses and c.active:
                    dmg = roll(expr, rng).total
                    logs.append(LogEntry(key="combat.dot", params={"target": c.id, "status": status}))
                    logs += _apply_damage(state, c, dmg, status)
            _check_end(state, logs)
            if state.status != "active":
                break
        if not c.active:
            _advance(state)
            continue
        if "stunned" in c.statuses:
            logs.append(LogEntry(key="combat.stunned", params={"target": c.id}))
            _tick_statuses(c)
            _advance(state)
            continue
        break
    return logs


def _end_turn(state: EncounterState, rng) -> list[LogEntry]:
    _tick_statuses(state.current)
    _advance(state)
    return _begin_turn(state, rng)


def _tick_statuses(c: Combatant) -> None:
    for status in list(c.statuses):
        if status in ("hidden", "defending"):
            continue
        c.statuses[status] -= 1
        if c.statuses[status] <= 0:
            del c.statuses[status]


def _advance(state: EncounterState) -> None:
    state.turn_index += 1
    if state.turn_index >= len(state.order):
        state.turn_index = 0
        state.round += 1
        for c in state.combatants.values():
            c.dodge_used = False


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
    if not foes:
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
