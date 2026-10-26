"""Entities and forms: summons, commands, convergence, helpers acting on their own and shapeshifting."""

from oathforge.engine.combat.resolve import _apply_damage, _apply_status, _resolve_target
from oathforge.engine.combat.state import (
    COMMAND_FLOOR,
    CONVERGENCE_DAMAGE,
    CONVERGENCE_TO_HIT,
    MAX_BY_KIND,
    Combatant,
    CombatError,
    EncounterState,
    Entity,
    EntityTemplate,
    LogEntry,
    _check_end,
    valid_targets,
)
from oathforge.engine.dice import d20, roll

# ---------------------------------------------------------------- entities and forms


def spawn(
    state: EncounterState,
    owner: Combatant,
    tpl: EntityTemplate,
    *,
    hp: int | None = None,
    persistent: bool = False,
    acts_now: bool = False,
) -> Entity:
    """Put a helper in the fight. A summoned one waits for the next turn (nothing acts the turn it arrives);
    a permanent one, which is there from the start, may act at the end of the hero's first turn."""
    eid = f"e{len(state.entities) + 1}"
    ent = Entity(
        id=eid,
        owner=owner.id,
        key=tpl.key,
        name=tpl.name,
        kind=tpl.kind,
        role=tpl.role,
        icon=tpl.icon,
        hp=tpl.hp if hp is None else hp,
        max_hp=tpl.hp,
        to_hit=tpl.to_hit,
        damage=tpl.damage,
        damage_type=tpl.damage_type,
        ranged=tpl.ranged,
        status=tpl.status,
        status_turns=tpl.status_turns,
        period=tpl.period,
        ttl=tpl.duration,
        born=state.round,
        persistent=persistent,
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
    return [
        LogEntry(key="combat.summoned", params={"actor": actor.id, "entity": ent.name, "icon": ent.icon, "hp": ent.hp})
    ]


def _command(state, actor, ability, target_id, rng) -> list[LogEntry]:
    ent = next(
        (e for e in state.entities.values() if e.owner == actor.id and e.key == ability.entity and e.active), None
    )
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
    return [
        LogEntry(key="combat.converge", params={"actor": actor.id, "count": len(mine), "turns": ability.boost_turns})
    ]


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
        assert ent.damage is not None  # content validation: damage and area entities have damage
        r = d20(rng)
        total = r.kept + ent.to_hit + (CONVERGENCE_TO_HIT if boosted else 0)
        crit = r.kept == 20
        params = {
            "entity": ent.name,
            "icon": ent.icon,
            "target": target.id,
            "roll": r.kept,
            "total": total,
            "ac": target.ac,
        }
        if r.nat1 or not (crit or total >= target.ac):
            return [LogEntry(key="combat.entity_miss", params=params)]
        dmg = max(COMMAND_FLOOR, roll(ent.damage, rng, crit).total + extra)
        logs.append(LogEntry(key="combat.entity_crit" if crit else "combat.entity_hit", params=params))
        return logs + _apply_damage(state, target, dmg, ent.damage_type)
    if ent.role == "area":  # a whole row, never missing; each takes its own roll
        assert ent.damage is not None  # content validation: damage and area entities have damage
        victims = [f for f in state.enemies_of(owner) if f.row == target.row]
        logs.append(
            LogEntry(key="combat.entity_area", params={"entity": ent.name, "icon": ent.icon, "count": len(victims)})
        )
        for v in victims:
            if v.active:
                logs += _apply_damage(
                    state, v, max(COMMAND_FLOOR, roll(ent.damage, rng).total + extra), ent.damage_type
                )
        return logs
    # disrupt: an affliction, not damage. On a boss it is capped like any other control (_apply_status)
    logs.append(
        LogEntry(key="combat.entity_afflicts", params={"entity": ent.name, "icon": ent.icon, "target": target.id})
    )
    assert ent.status is not None  # content validation: a disrupt entity has a status
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
    return [
        LogEntry(
            key="combat.shifted", params={"actor": actor.id, "form": shape.name, "icon": shape.icon, "temp": gained}
        )
    ]
