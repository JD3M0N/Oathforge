"""Turn flow: start, begin and end of a turn, statuses ticking, the enemies' turns and the end of the fight."""

import random

from oathforge.engine.dice import d20, roll
from oathforge.engine.combat.entities import _run_entities
from oathforge.engine.combat.resolve import _apply_damage, _attack
from oathforge.engine.combat.state import (
    Combatant, DOT, EncounterState, LogEntry, SKIP_TURN, _append, _check_end, gain_resource, valid_targets,
)


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
    if me.pattern and me.pattern_state != "ready":
        return _pattern_turn(state, me, target, rng)
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
    logs += _attack(state, me, target, profile, rng, None)
    if me.pattern:  # after enough ordinary turns it aims, out loud
        me.pattern_count += 1
        broken = me.plate_max and me.plate == 0
        if me.pattern_count >= me.pattern["cycle_broken" if broken else "cycle"]:
            me.pattern_state = "aiming"
            logs.append(LogEntry(key="combat.boss_aim", params={"actor": me.id}))
    return logs


def _pattern_turn(state: EncounterState, me: Combatant, target: Combatant, rng) -> list[LogEntry]:
    """A boss that aimed last turn fires its heavy attack; the turn after, it reloads and is exposed.
    ``defend`` is the answer anyone has: it gives the shot disadvantage."""
    if me.pattern_state == "aiming":
        me.pattern_state = "reloading"
        logs = [LogEntry(key="combat.boss_fire", params={"actor": me.id})]
        logs += _attack(state, me, target, me.heavy, rng, None, weapon=False)
        me.statuses["vulnerable"] = 2  # ticks once at the end of this turn: it lasts through the hero's next one
        return logs
    me.pattern_state, me.pattern_count = "ready", 0
    return [LogEntry(key="combat.boss_reload", params={"actor": me.id})]
