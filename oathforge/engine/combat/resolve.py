"""Core resolution: saves, attacks, damage, statuses and healing."""

from oathforge.engine.dice import d20, roll
from oathforge.engine.combat.state import (
    AttackProfile,
    BLESS_BONUS,
    BOSS_CONTROL_TURNS,
    CombatError,
    Combatant,
    HARD_CONTROL,
    HEX_DIE,
    INSPIRATION_DIE,
    LogEntry,
    MARK_DIE,
    NEGATIVE_STATUSES,
    gain_resource,
    valid_targets,
)


# ---------------------------------------------------------------- core resolution


def _save(target: Combatant, ability: str, dc: int, rng) -> tuple[bool, list[LogEntry]]:
    """Saving throw of ``target`` (dex or wis) against ``dc``. Returns (saved, logs)."""
    mod = target.wis_mod if ability == "wis" else target.dex_mod
    r = d20(rng)
    total = r.kept + mod
    saved = not r.nat1 and (r.kept == 20 or total >= dc)
    return saved, [
        LogEntry(
            key="combat.save",
            params={"target": target.id, "save": ability, "roll": r.kept, "total": total, "dc": dc, "success": saved},
        )
    ]


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
        or (profile.ranged and attacker.row == "front" and any(f.row == "front" for f in state.enemies_of(attacker)))
    )
    attacker.statuses.pop("hidden", None)
    r = d20(rng, adv, dis)
    total = r.kept + profile.to_hit + (BLESS_BONUS if "blessed" in attacker.statuses else 0)
    if attacker.statuses.pop("inspired", None):
        total += roll(INSPIRATION_DIE, rng).total
    hit = not r.nat1 and (r.kept >= attacker.crit_range or total >= target.ac)
    params = {
        "actor": attacker.id,
        "target": target.id,
        "weapon": profile.name,
        "roll": r.kept,
        "total": total,
        "ac": target.ac,
        "adv": adv and not dis,
        "dis": dis and not adv,
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
        attacker.sneak_dice
        and not attacker.sneak_used
        and (profile.finesse or profile.ranged)
        and ((adv and not dis) or any(s in NEGATIVE_STATUSES for s in target.statuses))
    ):
        sneak = roll(f"{attacker.sneak_dice}d6", rng, crit).total
        attacker.sneak_used = True
        dmg += sneak
    params.update(crit=crit, sneak=sneak)
    hurt_before = target.hp + target.temp_hp
    logs = [LogEntry(key="combat.crit" if crit else "combat.hit", params=params)]
    logs += _apply_damage(state, target, dmg, profile.damage_type)
    for amount, dtype in extras:
        if target.active:
            logs += _apply_damage(state, target, amount, dtype)
    ap = profile.applies
    if ap and target.active and rng.random() < ap.get("chance", 1.0):
        logs += _apply_status(target, ap["status"], ap["turns"])
    logs += _answer_blow(state, attacker, target, hurt_before, rng)
    return logs


def _answer_blow(state, attacker: Combatant, target: Combatant, hurt_before: int, rng) -> list[LogEntry]:
    """Once per attack, and only if the blow really hurt (HP or temporary HP): the bar fills and the attacker
    takes thorns damage. The answer goes straight to _apply_damage, so it can never answer itself."""
    if target.side != "player" or not (target.thorns or target.resource_on_hurt):
        return []
    if target.hp + target.temp_hp >= hurt_before:
        return []
    logs: list[LogEntry] = []
    if gain_resource(target, target.resource_on_hurt):
        logs.append(
            LogEntry(
                key="combat.resource_gained",
                params={
                    "actor": target.id,
                    "resource": target.resource_key,
                    "amount": target.resource_on_hurt,
                    "left": target.resource,
                },
            )
        )
    if target.thorns and attacker.active and attacker.side != target.side:
        logs.append(LogEntry(key="combat.thorns", params={"actor": target.id, "target": attacker.id}))
        logs += _apply_damage(state, attacker, roll(target.thorns, rng).total, target.thorns_type)
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
    if target.plate > 0 and amount > 0:  # the plate takes it first; anyone can wear it down
        worn = min(target.plate, amount)
        target.plate -= worn
        amount -= worn
        guarded.append(
            LogEntry(key="combat.plate_hit", params={"target": target.id, "amount": worn, "left": target.plate})
        )
        if target.plate == 0:
            guarded.append(LogEntry(key="combat.plate_broken", params={"target": target.id}))
        if amount == 0:
            return guarded
    if target.side == "player" and state.entities and amount > 0:
        guard = next(
            (e for e in state.entities.values() if e.owner == target.id and e.role == "guard" and e.active), None
        )
        if guard is not None:  # its HP are what it can take in the hero's place
            taken = min(guard.hp, amount)
            guard.hp -= taken
            amount -= taken
            guarded.append(
                LogEntry(key="combat.guard_absorbs", params={"entity": guard.name, "amount": taken, "left": guard.hp})
            )
            if guard.hp <= 0:
                guard.defeated = True
                guarded.append(LogEntry(key="combat.entity_breaks", params={"entity": guard.name}))
            if amount == 0:
                return guarded
    absorbed = min(target.temp_hp, amount)
    target.temp_hp -= absorbed
    target.hp = max(0, target.hp - (amount - absorbed))
    logs = guarded + [
        LogEntry(
            key="combat.damage",
            params={
                "target": target.id,
                "amount": amount,
                "type": damage_type,
                "effect": effect,
                "hp": target.hp,
                "max_hp": target.max_hp,
            },
        )
    ]
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
    if target.rearm and not target.rearmed and not target.defeated and target.hp * 2 <= target.max_hp:
        target.rearmed, target.plate = True, target.rearm
        logs.append(LogEntry(key="combat.plate_rearm", params={"target": target.id, "plate": target.rearm}))
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
        logs.append(
            LogEntry(
                key="combat.boss_resists",
                params={"target": target.id, "status": status, "turns": turns, "spill": spill},
            )
        )
        target.statuses["vulnerable"] = max(spill, target.statuses.get("vulnerable", 0))
    target.statuses[status] = max(turns, target.statuses.get(status, 0))
    return logs + [LogEntry(key="combat.status", params={"target": target.id, "status": status, "turns": turns})]


def _heal(c: Combatant, amount: int) -> int:
    before = c.hp
    c.hp = min(c.max_hp, c.hp + max(0, amount))
    return c.hp - before
