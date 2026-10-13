"""Persisted encounters on top of the pure combat engine."""

import random
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge import recorder
from oathforge.content import get_content
from oathforge.database.models import Character, CombatAction, Encounter, EncounterParticipant
from oathforge.engine import combat as engine
from oathforge.engine.combat import Action, AttackProfile, Combatant, CombatError, EncounterState, LogEntry
from oathforge.engine.dice import roll
from oathforge.i18n import t
from oathforge.services import bestiary, characters, inventory, quests
from oathforge.services.events import Event, Outcome, render_event


def ability_defs(char: Character) -> dict:
    return dict(get_content().classes[char.class_key].abilities)


def monster_combatant(key: str, cid: str) -> Combatant:
    m = get_content().monsters[key]
    return Combatant(
        id=cid, side="enemy", ref=key, name=m.name.model_dump(), hp=m.hp, max_hp=m.hp, ac=m.ac, row=m.row,
        dex_mod=m.dex, wis_mod=m.wis, passive_perception=10 + m.wis, immune=list(m.immune), cowardly=m.cowardly, xp=m.xp,
        creature_type=m.type, resist=list(m.resist), weak_to=list(m.vulnerable), immune_damage=list(m.immune_damage),
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
    bestiary.see(char, monster_keys)

    session.add(CombatAction(encounter_id=enc.id, round=1, actor="start", action={},
                             result=[entry.model_dump(mode="json") for entry in logs]))
    out = Outcome(encounter_id=enc.id)
    out.add("combat.start", enemies=_names_list([state.combatants[k] for k in state.combatants if k != "p1"]))
    out.events += [log_event(state, e) for e in logs]
    await _sync_and_maybe_finish(session, char, enc, state, rng, out)
    _record(enc, char, state, None, logs)
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
    _record(enc, char, state, action, logs)
    return out


def _record(enc: Encounter, char: Character, state: EncounterState, action: Action | None,
            logs: list[LogEntry]) -> None:
    """Debug copy of the encounter in artifacts/battles/ (full log, not the 30-entry window)."""
    recorder.battle(
        enc.id, enc.location, character=f"{char.name} ({char.class_key} {char.level})",
        actor_action=action.model_dump(exclude_none=True) if action else None,
        lines=[render_event(log_event(state, e), "es") for e in logs],
        raw=[e.model_dump(mode="json") for e in logs], state=state.model_dump(mode="json"),
    )


async def _sync_and_maybe_finish(session, char, enc, state: EncounterState, rng, out: Outcome) -> None:
    from oathforge.services import activities  # activities starts encounters too
    p = state.combatants["p1"]
    char.hp = p.hp
    char.resources = {k: v for k, v in p.abilities.items()}
    enc.state = state.model_dump(mode="json")
    if state.status == "active":
        return
    enc.status = state.status
    char.state = "idle"
    c = get_content()
    first = len(out.events)
    if state.status == "victory":
        defeated = [cb for cb in state.combatants.values() if cb.side == "enemy" and cb.defeated]
        bestiary.kill(char, [cb.ref for cb in defeated])
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
        await activities.skin(session, char, [cb.ref for cb in defeated], rng, out)
        if enc.fixed_flag:
            char.flags = {**char.flags, enc.fixed_flag: True}
        for cb in defeated:
            out.extend(await quests.on_defeat(session, char, cb.ref, rng))
    elif state.status == "defeat":
        await characters.defeat_penalty(char, out)
    elif state.status == "fled":
        char.hp = max(1, char.hp)
    # an ambushed stay or a tracked prey: pay what was pending (or not)
    defeated_refs = [cb.ref for cb in state.combatants.values() if cb.side == "enemy" and cb.defeated]
    await activities.on_encounter_end(session, char, state.status, defeated_refs, rng, out)
    # rewards and penalties, kept for the battle report
    session.add(CombatAction(encounter_id=enc.id, round=state.round, actor="end", action={},
                             result=[{"key": e.key, "params": e.params} for e in out.events[first:]]))


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
    if "save" in p and p["save"] in c.abilities:
        p["save"] = c.abilities[p["save"]].short.model_dump()
    if "skill" in p and p["skill"] in c.skills:
        p["skill"] = c.skills[p["skill"]].name.model_dump()
    if "status" in p:
        p["status"] = _both(f"status.{p['status']}")
    if "type" in p:
        p["type"] = _both(f"dmg.{p['type']}")
    if entry.key == "combat.damage":  # logs saved before v0.2.0 have no effect
        effect = p.pop("effect", "")
        p["effect"] = _both(f"combat.effect.{effect}") if effect else ""
        hp, max_hp = p.pop("hp", None), p.pop("max_hp", None)  # HP left, since v0.5.8
        p["left"] = _both("combat.hp_left", hp=hp, max_hp=max_hp) if hp is not None else ""
    if isinstance(p.get("roll"), int) and isinstance(p.get("total"), int):  # 🎲 14 +5 = 19
        diff = p["total"] - p["roll"]
        p["bonus"] = f" {diff:+d}" if diff else ""
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


# ---------------------------------------------------------------- battle report

@dataclass
class BattleReport:
    """A finished encounter replayed from its CombatAction rows: every round, totals and rewards."""
    encounter_id: int
    location: str
    status: str
    state: EncounterState
    rounds: list[tuple[int, list[LogEntry]]]
    rewards: list[Event]
    stats: dict = field(default_factory=dict)


async def battle_report(session: AsyncSession, char: Character, encounter_id: int | None = None) -> BattleReport | None:
    """The given (or the latest) finished encounter of this character, or None."""
    stmt = select(Encounter).where(Encounter.character_id == char.id, Encounter.status != "active")
    if encounter_id is not None:
        stmt = stmt.where(Encounter.id == encounter_id)
    enc = await session.scalar(stmt.order_by(Encounter.id.desc()).limit(1))
    if enc is None:
        return None
    rows = (await session.scalars(select(CombatAction).where(CombatAction.encounter_id == enc.id)
                                  .order_by(CombatAction.id))).all()
    entries: list[LogEntry] = []
    rewards: list[Event] = []
    for row in rows:
        if row.actor == "end":
            rewards += [Event(e["key"], e.get("params", {})) for e in row.result]
        else:
            entries += [LogEntry.model_validate(e) for e in row.result]
    state = EncounterState.model_validate(enc.state)
    rounds: list[tuple[int, list[LogEntry]]] = []
    for e in entries:
        if e.key == "combat.round":
            rounds.append((e.params.get("round", len(rounds) + 1), []))
        else:
            if not rounds:  # encounters saved before v0.5.8 have no round markers
                rounds.append((1, []))
            rounds[-1][1].append(e)
    rounds = [(n, es) for n, es in rounds if es]
    return BattleReport(enc.id, enc.location, enc.status, state, rounds, rewards, battle_stats(state, entries))


def battle_stats(state: EncounterState, entries: list[LogEntry]) -> dict:
    """Totals seen from the player's side: damage, accuracy, crits, healing and who fell."""
    stats = {"dealt": 0, "received": 0, "attacks": 0, "hits": 0, "crits": 0, "enemy_attacks": 0, "enemy_hits": 0,
             "healed": 0, "defeated": {}}
    for e in entries:
        p = e.params
        mine = p.get("actor") == "p1"
        if e.key in ("combat.hit", "combat.crit", "combat.miss"):
            hit = e.key != "combat.miss"
            if mine:
                stats["attacks"] += 1
                stats["hits"] += hit
                stats["crits"] += e.key == "combat.crit"
            elif p.get("target") == "p1":
                stats["enemy_attacks"] += 1
                stats["enemy_hits"] += hit
        elif e.key == "combat.damage":
            target = state.combatants.get(p.get("target"))
            if target is not None:
                stats["received" if target.side == "player" else "dealt"] += p.get("amount", 0)
        elif e.key in ("combat.heal", "combat.potion") and mine:
            stats["healed"] += p.get("amount", 0)
        elif e.key == "combat.defeated":
            target = state.combatants.get(p.get("target"))
            if target is not None and target.side == "enemy":
                stats["defeated"][target.ref or target.id] = stats["defeated"].get(target.ref or target.id, 0) + 1
    return stats
