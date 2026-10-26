"""The player's turn: attacks, abilities, items, spells, fleeing and scene objects."""

import random

from oathforge.engine.checks import check, dc_for
from oathforge.engine.combat.entities import _command, _converge, _shift, _summon
from oathforge.engine.combat.resolve import _apply_damage, _apply_status, _attack, _heal, _resolve_target, _save
from oathforge.engine.combat.state import (
    FLEE_DC_BASE,
    FLEE_DC_PER_FOE,
    Action,
    AttackProfile,
    Combatant,
    CombatError,
    EncounterState,
    LogEntry,
    _append,
    _check_end,
    available_bonus_actions,
    gain_resource,
    valid_targets,
)
from oathforge.engine.combat.turns import _end_turn, _run_enemies
from oathforge.engine.dice import roll

# ---------------------------------------------------------------- player turn


def player_act(
    state: EncounterState, actor_id: str, action: Action, rng: random.Random, ability_defs: dict
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
    if (
        state.status == "active"
        and actor.action_used
        and (not actor.active or not available_bonus_actions(state, actor, ability_defs))
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
        logs.append(
            LogEntry(
                key="combat.resource_gained",
                params={
                    "actor": actor.id,
                    "resource": actor.resource_key,
                    "amount": actor.resource_on_attack,
                    "left": actor.resource,
                },
            )
        )
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
    foes_before = {e.id: e.hp for e in state.enemies_of(actor)}
    quarry = None
    if ability.consumes and ability.kind in ("strike", "spell", "save"):
        quarry = _resolve_target(state, actor, action.target, ranged=ability.ranged or ability.kind != "strike")
    if ability.kind == "strike":
        profile = next((a for a in actor.attacks if a.ranged == ability.ranged), None)
        if profile is None:
            raise CombatError("combat.err.no_weapon")
        logs.append(LogEntry(key="combat.ability", params={"actor": actor.id, "ability": action.ability}))
        logs += _player_attack(
            state, actor, profile.key, action.target, rng, extra=(ability.extra_damage, ability.damage_type)
        )
    elif ability.kind in ("spell", "save"):
        logs.append(LogEntry(key="combat.ability", params={"actor": actor.id, "ability": action.ability}))
        logs += _cast(
            state,
            actor,
            ability,
            action.ability,
            action.target,
            rng,
            to_hit=actor.spell_to_hit,
            dc=actor.spell_dc,
            dmg_bonus=actor.spell_damage_bonus,
        )
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
        logs.append(
            LogEntry(
                key="combat.hide",
                params={"actor": actor.id, "roll": res.kept, "total": res.total, "dc": dc, "success": res.success},
            )
        )
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
    if quarry is not None and ability.consume_damage and quarry.active and ability.consumes in quarry.statuses:
        del quarry.statuses[ability.consumes]  # spent: it no longer ticks, and it hurts now
        logs.append(
            LogEntry(key="combat.consumed", params={"actor": actor.id, "target": quarry.id, "status": ability.consumes})
        )
        logs += _apply_damage(state, quarry, roll(ability.consume_damage, rng).total, ability.damage_type or "force")
    if ability.leech_pct:
        dealt = sum(foes_before[i] - max(0, state.combatants[i].hp) for i in foes_before)
        gained = _heal(actor, dealt * ability.leech_pct // 100)
        if gained:
            logs.append(LogEntry(key="combat.leech", params={"actor": actor.id, "amount": gained}))
    if ability.reduces_cooldowns and actor.cooldowns:  # the ability's own cooldown is set below, so it is not cut
        actor.cooldowns = {
            k: v - ability.reduces_cooldowns for k, v in actor.cooldowns.items() if v - ability.reduces_cooldowns > 0
        }
        logs.append(
            LogEntry(key="combat.cooldowns_cut", params={"actor": actor.id, "turns": ability.reduces_cooldowns})
        )
    if uses is not None:
        actor.abilities[action.ability] = uses - 1
    if actor.resource_max:  # paid once, whatever the ability did
        spent = min(ability.cost, actor.resource)
        actor.resource -= spent
        if spent:
            logs.append(
                LogEntry(
                    key="combat.resource_spent",
                    params={"actor": actor.id, "resource": actor.resource_key, "amount": spent, "left": actor.resource},
                )
            )
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
        logs += _cast(
            state,
            actor,
            item,
            action.ability,
            action.target,
            rng,
            to_hit=item.attack_bonus,
            dc=item.save_dc,
            dmg_bonus=0,
            name=action.item_name,
        )
    _spend(actor, action.ability)
    return logs


def _cast(
    state, actor, ability, key, target_id, rng, to_hit: int, dc: int, dmg_bonus: int, name: dict | None = None
) -> list[LogEntry]:
    """Resolve a spell, save, heal or buff; class abilities and combat items share it."""
    logs: list[LogEntry] = []
    if ability.kind == "spell":
        target = _resolve_target(state, actor, target_id, ranged=True)
        damage = _with_bonus(ability.damage or "1d4", dmg_bonus)
        dtype = ability.damage_type or "radiant"
        if ability.auto_hit:
            logs += _apply_damage(state, target, roll(damage, rng).total, dtype)
        else:
            profile = AttackProfile(
                key=key,
                name=name if name is not None else ability.name.model_dump(),
                to_hit=to_hit,
                damage=damage,
                damage_type=dtype,
                ranged=True,
            )
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
            logs.append(
                LogEntry(
                    key="combat.buff",
                    params={"actor": actor.id, "ability": key, "status": ability.status, "turns": ability.status_turns},
                )
            )
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
        if ability.temp_hp and healed:  # a barrier only for healing that was real, never for a full life bar
            barrier = roll(ability.temp_hp, rng).total + _heal_add(actor, ability)
            actor.temp_hp = max(actor.temp_hp, barrier)
            logs.append(LogEntry(key="combat.temp_hp", params={"actor": actor.id, "amount": actor.temp_hp}))
    return logs


def _flee(state, actor, rng) -> list[LogEntry]:
    foes = state.enemies_of(actor)
    dc = FLEE_DC_BASE + FLEE_DC_PER_FOE * len(foes)
    skill = max(("athletics", "acrobatics"), key=lambda s: actor.skill_bonus.get(s, 0))
    res = check(rng, skill, actor.skill_bonus.get(skill, 0), dc)
    if res.success:
        actor.fled = True
    return [
        LogEntry(
            key="combat.flee",
            params={"actor": actor.id, "roll": res.kept, "total": res.total, "dc": dc, "success": res.success},
        )
    ]


def _interact(state, actor, action, rng) -> list[LogEntry]:
    obj = state.scene_objects.get(action.object or "")
    if obj is None:
        raise CombatError("combat.err.no_object")
    dc = dc_for(obj.tier)
    res = check(rng, obj.skill, actor.skill_bonus.get(obj.skill, 0), dc)
    logs = [
        LogEntry(
            key="combat.interact",
            params={
                "actor": actor.id,
                "object": obj.key,
                "skill": obj.skill,
                "roll": res.kept,
                "total": res.total,
                "dc": dc,
                "success": res.success,
            },
        )
    ]
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
