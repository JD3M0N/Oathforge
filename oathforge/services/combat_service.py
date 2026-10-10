"""Persisted encounters on top of the pure combat engine."""

import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.database.models import Character, CombatAction, Encounter, EncounterParticipant
from oathforge.engine import combat as engine
from oathforge.engine.combat import Action, AttackProfile, Combatant, CombatError, EncounterState, LogEntry
from oathforge.engine.dice import roll
from oathforge.i18n import t
from oathforge.services import characters, inventory, quests
from oathforge.services.events import Event, Outcome


def ability_defs(char: Character) -> dict:
    return dict(get_content().classes[char.class_key].abilities)


def monster_combatant(key: str, cid: str) -> Combatant:
    m = get_content().monsters[key]
    return Combatant(
        id=cid, side="enemy", ref=key, name=m.name.model_dump(), hp=m.hp, max_hp=m.hp, ac=m.ac, row=m.row,
        dex_mod=m.dex, passive_perception=10 + m.wis, immune=list(m.immune), cowardly=m.cowardly, xp=m.xp,
        attacks=[
            AttackProfile(key=f"a{i}", name=a.name.model_dump(), to_hit=a.to_hit, damage=a.damage,
                          damage_type=a.damage_type, ranged=a.ranged,
                          applies=a.applies.model_dump() if a.applies else None)
            for i, a in enumerate(m.attacks)
        ],
    )


async def active_encounter(session: AsyncSession, char: Character, lock: bool = False) -> Encounter | None:
    stmt = (select(Encounter)
            .where(Encounter.character_id == char.id, Encounter.status == "active")
            .order_by(Encounter.id.desc()))
    if lock:
        stmt = stmt.with_for_update()
    return await session.scalar(stmt)


async def start_encounter(
    session: AsyncSession, char: Character, monster_keys: list[str], rng: random.Random,
    fixed_flag: str | None = None,
) -> tuple[Encounter, Outcome]:
    c = get_content()
    loc = c.locations[char.location]
    player = await characters.build_combatant(session, char)
    state = EncounterState(location=char.location, combatants={"p1": player})
    for i, key in enumerate(monster_keys, start=1):
        state.combatants[f"m{i}"] = monster_combatant(key, f"m{i}")
    for okey, obj in loc.scene_objects.items():
        state.scene_objects[okey] = engine.SceneObjectState(
            key=okey, skill=obj.skill, tier=obj.tier, damage=obj.effect.damage,
            damage_type=obj.effect.damage_type, targets=obj.effect.targets,
            status=obj.effect.status.model_dump() if obj.effect.status else None,
        )
    logs = engine.start(state, rng)
    enc = Encounter(character_id=char.id, location=char.location, status="active",
                    state=state.model_dump(mode="json"), fixed_flag=fixed_flag)
    session.add(enc)
    await session.flush()
    session.add(EncounterParticipant(encounter_id=enc.id, character_id=char.id, combatant_id="p1"))
    char.state = "in_combat"

    out = Outcome(encounter_id=enc.id)
    out.add("combat.start", enemies=_names_list([state.combatants[k] for k in state.combatants if k != "p1"]))
    out.events += [log_event(state, e) for e in logs]
    await _sync_and_maybe_finish(session, char, enc, state, rng, out)
    return enc, out


async def act(
    session: AsyncSession, char: Character, enc: Encounter, action: Action, rng: random.Random
) -> Outcome:
    state = EncounterState.model_validate(enc.state)
    if action.kind == "heal_item":
        if state.current.id != "p1" or state.current.action_used:
            return Outcome.refused("combat.err.no_action")
        amount = await inventory.consume_healing(session, char, "healing_potion", rng)
        if amount is None:
            return Outcome.refused("inv.err.no_potion")
        action = action.model_copy(update={"heal_amount": amount})
    try:
        logs = engine.player_act(state, "p1", action, rng, ability_defs(char))
    except CombatError as e:
        return Outcome.refused(e.key)
    session.add(CombatAction(encounter_id=enc.id, round=state.round, actor="p1",
                             action=action.model_dump(mode="json"),
                             result=[entry.model_dump(mode="json") for entry in logs]))
    out = Outcome(encounter_id=enc.id)
    out.events += [log_event(state, e) for e in logs]
    await _sync_and_maybe_finish(session, char, enc, state, rng, out)
    return out


async def _sync_and_maybe_finish(session, char, enc, state: EncounterState, rng, out: Outcome) -> None:
    p = state.combatants["p1"]
    char.hp = p.hp
    char.resources = {k: v for k, v in p.abilities.items()}
    enc.state = state.model_dump(mode="json")
    if state.status == "active":
        return
    enc.status = state.status
    char.state = "idle"
    c = get_content()
    if state.status == "victory":
        defeated = [cb for cb in state.combatants.values() if cb.side == "enemy" and cb.defeated]
        characters.grant_xp(char, sum(cb.xp for cb in defeated), out)
        gold = sum(roll(c.monsters[cb.ref].gold, rng).total for cb in defeated)
        if gold:
            char.gold += gold
            out.add("loot.gold", gold=gold)
        for cb in defeated:
            for loot in c.monsters[cb.ref].loot:
                if rng.random() < loot.chance:
                    await inventory.add_item(session, char, loot.item, loot.qty)
                    out.add("loot.item", item=c.items[loot.item].name.model_dump(), qty=loot.qty)
        if enc.fixed_flag:
            char.flags = {**char.flags, enc.fixed_flag: True}
        for cb in defeated:
            out.extend(await quests.on_defeat(session, char, cb.ref, rng))
    elif state.status == "defeat":
        await characters.defeat_penalty(char, out)
    elif state.status == "fled":
        char.hp = max(1, char.hp)


# ---------------------------------------------------------------- rendering helpers

def _both(key: str, **params) -> dict:
    return {lang: t(lang, key, **params) for lang in ("es", "en")}


def _names_list(cs: list[Combatant]) -> dict:
    return {lang: ", ".join(c.name[lang] for c in cs) for lang in ("es", "en")}


def log_event(state: EncounterState, entry: LogEntry) -> Event:
    """Turn an engine log entry (ids, raw keys) into a renderable Event (localized names)."""
    c = get_content()
    p = dict(entry.params)
    for k in ("actor", "target"):
        if k in p and p[k] in state.combatants:
            p[k] = state.combatants[p[k]].name
    if "ability" in p:
        ability = next((cls.abilities[p["ability"]] for cls in c.classes.values() if p["ability"] in cls.abilities), None)
        p["ability"] = ability.name.model_dump() if ability else p["ability"]
    if "object" in p:
        obj = c.locations[state.location].scene_objects.get(p["object"]) if state.location in c.locations else None
        p["object"] = obj.name.model_dump() if obj else p["object"]
    if "skill" in p and p["skill"] in c.skills:
        p["skill"] = c.skills[p["skill"]].name.model_dump()
    if "status" in p:
        p["status"] = _both(f"status.{p['status']}")
    if "type" in p:
        p["type"] = _both(f"dmg.{p['type']}")
    if "row" in p:
        p["row"] = _both(f"row.{p['row']}")
    if "success" in p:
        p["result"] = "✅" if p.pop("success") else "❌"
    if "adv" in p or "dis" in p:
        adv, dis = p.pop("adv", False), p.pop("dis", False)
        p["mod"] = _both("combat.adv") if adv else _both("combat.dis") if dis else ""
    if "sneak" in p:
        sneak = p.pop("sneak")
        p["extra"] = _both("combat.sneak", amount=sneak) if sneak else ""
        p.pop("crit", None)
    if "order" in p:
        order = p.pop("order")
        p["order"] = {
            lang: " · ".join(f"{state.combatants[i].name[lang]} {state.combatants[i].initiative}" for i in order)
            for lang in ("es", "en")
        }
    return Event(entry.key, p)
