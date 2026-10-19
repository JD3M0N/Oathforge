"""Timed field activities: Gather (5 min, safe), Stay (15 min, more loot, may end in an ambush)
and Track (5 min, then a fight with the prey). A long rest at an inn is one too (80 min asleep), and so is
skinning the beasts just killed (/skin, a few seconds).

    start  -> the character is busy until ``ends_at`` (unix seconds stored in the database)
    claim  -> the result is rolled once from the activity's seed, stored and paid
    ambush / prey -> a normal encounter; ``on_encounter_end`` pays (or not) what was pending

The AI never takes part here: the chronicle is written afterwards from the stored result.
"""

import math
import random
import secrets
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.content.schemas import Gathering, Location
from oathforge.database.models import Character, WorldActivity
from oathforge.engine import gathering
from oathforge.i18n import t
from oathforge.services import characters, combat_service, exploration, inventory, quests
from oathforge.services import achievements
from oathforge.services.events import Outcome

KINDS = ("gather", "stay", "track", "rest", "skin")
OPEN = ("running", "awaiting_combat")
SKINNING_KNIFE = "skinning_knife"


def _now(now: float | None) -> float:
    return time.time() if now is None else now


def _gathering(loc: Location, skill: str) -> Gathering | None:
    return next((g for g in loc.gathering if g.skill == skill), None)


def options(char: Character) -> list[tuple[str, str]]:
    """(kind, mastery) pairs that can be started where the character stands."""
    loc = get_content().locations[char.location]
    out = [(kind, g.skill) for g in loc.gathering for kind in ("gather", "stay")]
    if loc.hunting:
        out.append(("track", "tracking"))
    return out


def loot_text(items: dict[str, int]) -> dict:
    """{"es": "3 × Mena de hierro, 1 × Carbón", "en": ...}"""
    c = get_content()
    return {lang: ", ".join(f"{q} × {c.items[k].label(lang)}" for k, q in items.items()) or "—"
            for lang in ("es", "en")}


async def open_activity(session: AsyncSession, char: Character, lock: bool = False) -> WorldActivity | None:
    stmt = (select(WorldActivity)
            .where(WorldActivity.character_id == char.id, WorldActivity.status.in_(OPEN))
            .order_by(WorldActivity.id.desc()))
    if lock:
        stmt = stmt.with_for_update()
    return await session.scalar(stmt)


def tool_for(char: Character, kind: str, skill: str) -> str | None:
    """The item an activity needs where the character stands (a pickaxe to mine, a knife to skin)."""
    if kind == "skin":
        return SKINNING_KNIFE
    g = _gathering(get_content().locations[char.location], skill) if kind in ("gather", "stay") else None
    return g.tool if g else None


async def check(session: AsyncSession, char: Character, kind: str, skill: str) -> Outcome | None:
    """Why ``kind`` cannot start here (a refusal), or None. The rules of ``start``, shared with the
    Activities view so a button never offers what the service would refuse."""
    c = get_content()
    loc = c.locations[char.location]
    if kind == "rest":
        if loc.rest_cost is None:
            return Outcome.refused("explore.err.no_rest")
        if char.gold < loc.rest_cost:
            return Outcome.refused("shop.err.no_gold", price=loc.rest_cost)
    elif kind == "track":
        if not loc.hunting:
            return Outcome.refused("activity.err.unavailable")
    elif kind == "skin":
        if not characters.pending_skin(char):
            return Outcome.refused("activity.err.nothing_to_skin")
    elif kind not in ("gather", "stay") or _gathering(loc, skill) is None:
        return Outcome.refused("activity.err.unavailable")
    tool = tool_for(char, kind, skill)
    if tool and await inventory.count(session, char, tool) == 0:
        return Outcome.refused("activity.err.no_tool", tool=c.items[tool].name.model_dump())
    return None


async def availability(session: AsyncSession, char: Character) -> list[tuple[str, str, Outcome | None]]:
    """Every timed activity of this place, (kind, mastery, refusal or None): gather, stay, track, skin, rest."""
    loc = get_content().locations[char.location]
    kinds = options(char)
    if characters.pending_skin(char):
        kinds.append(("skin", "skinning"))
    if loc.rest_cost is not None:
        kinds.append(("rest", "rest"))
    return [(kind, skill, await check(session, char, kind, skill)) for kind, skill in kinds]


async def start(session: AsyncSession, char: Character, kind: str, skill: str,
                now: float | None = None) -> Outcome:
    refusal = characters.ensure_free(char) or await check(session, char, kind, skill)
    if refusal:
        return refusal
    c = get_content()
    loc = c.locations[char.location]
    g = None
    if kind == "rest":
        skill = "rest"
    elif kind == "track":
        skill = "tracking"
    elif kind == "skin":
        beasts = characters.pending_skin(char)
        skill = "skinning"
    else:
        g = _gathering(loc, skill)
    if await open_activity(session, char, lock=True):
        return Outcome.refused("activity.err.busy")
    tool_checked = kind == "skin" or (kind in ("gather", "stay") and bool(g.tool))
    now = _now(now)
    characters.drop_pending_skin(char)  # skinning now, or something else: the carcasses are left behind
    if kind == "skin":
        harvest = {h.item for k in beasts for h in c.monsters[k].harvest}
        if await quests.tutorial_boost(session, char, "skin", harvest):  # the tutorial's shortcut: at once
            out = Outcome().add("activity.tutorial", skill=characters.mastery_name(skill), place=loc.phrase())
            await skin(session, char, beasts, random.Random(), out)
            return out
    if kind in ("gather", "stay"):
        rank = gathering.rank_for(characters.mastery_xp(char, skill))
        here = {r.item for r in g.resources if r.min_rank <= rank}
        boost = await quests.tutorial_boost(session, char, "gather", here)
        if boost:
            return await _tutorial_gather(session, char, kind, skill, loc, boost, now)
    seconds = skin_seconds(beasts) if kind == "skin" else gathering.SECONDS[kind]
    act = WorldActivity(character_id=char.id, location=char.location, kind=kind, skill=skill, started_at=now,
                        ends_at=now + seconds, status="running", seed=secrets.randbits(48),
                        result={"tool_checked": tool_checked, **({"monsters": beasts} if kind == "skin" else {})})
    session.add(act)
    await session.flush()
    char.state = "busy"
    settings = get_settings()
    if kind == "rest":  # paid on lying down; abandoning gives nothing back
        char.gold -= loc.rest_cost
        if settings.beta_instant_rest:  # beta only: wake up at once
            return await claim(session, char, act.ends_at)
        return Outcome().add("activity.started.rest" if loc.rest_cost else "activity.started.rest_free",
                             place=loc.phrase(), cost=loc.rest_cost, minutes=seconds // 60)
    if settings.beta_instant_tutorial and await quests.in_tutorial(session, char):  # beta only: done at once
        return Outcome().add("activity.tutorial_instant").extend(await claim(session, char, act.ends_at))
    out = Outcome().add(f"activity.started.{kind}", skill=characters.mastery_name(skill),
                        place=loc.phrase(), minutes=seconds // 60, seconds=seconds)
    if kind in ("track", "stay") and char.hp * 2 < char.max_hp:  # this may end in a fight
        out.add("explore.low_hp", hp=char.hp, max_hp=char.max_hp)
    return out


def skin_seconds(monster_keys: list[str]) -> int:
    c = get_content()
    return sum(c.monsters[k].skin_seconds for k in monster_keys)


async def offer_skinning(session: AsyncSession, char: Character, monster_keys: list[str], out: Outcome) -> None:
    """After a victory: the beasts that can be skinned wait for /skin where they fell."""
    c = get_content()
    beasts = [k for k in monster_keys if c.monsters[k].harvest]
    if not beasts:
        return
    if await inventory.count(session, char, SKINNING_KNIFE) == 0:
        out.add("activity.no_knife")
        return
    char.flags = {**(char.flags or {}), characters.PENDING_SKIN: {"monsters": beasts, "location": char.location}}
    names = {lang: ", ".join(c.monsters[k].name.get(lang) for k in beasts) for lang in ("es", "en")}
    out.add("activity.can_skin", beasts=names, seconds=skin_seconds(beasts))


async def _tutorial_gather(session, char, kind: str, skill: str, loc: Location, boost, now: float) -> Outcome:
    """The tutorial's shortcut: done at once, with exactly what the mission still asks for, no ambush."""
    qkey, item, missing = boost
    quests.use_tutorial_boost(char, qkey)
    items = {item: missing}
    xp = gathering.GATHER_XP
    act = WorldActivity(character_id=char.id, location=char.location, kind=kind, skill=skill, started_at=now,
                        ends_at=now, status="done", resolved_at=now, seed=0,
                        result={"outcome": "tutorial", "items": items, "xp": xp,
                                "tool_checked": bool(_gathering(loc, skill).tool)})
    session.add(act)
    await session.flush()
    out = Outcome().add("activity.tutorial", skill=characters.mastery_name(skill), place=loc.phrase())
    await _give(session, char, items, out, random.Random())
    characters.grant_mastery(char, skill, xp, out)
    await _achievement_activity(session, char, act, out)
    return out


async def cancel(session: AsyncSession, char: Character, now: float | None = None) -> Outcome:
    act = await open_activity(session, char, lock=True)
    if act is None or act.status != "running":
        return Outcome.refused("activity.err.none")
    act.status = "cancelled"
    act.resolved_at = _now(now)
    if char.state == "busy":
        char.state = "idle"
    return Outcome().add("activity.cancelled")


def _finish(act: WorldActivity, outcome: str, items: dict[str, int], xp: int, now: float, **extra) -> None:
    act.status = "done"
    act.resolved_at = now
    act.result = {**(act.result or {}), "outcome": outcome, "items": items, "xp": xp, **extra}


async def _give(session: AsyncSession, char: Character, items: dict[str, int], out: Outcome,
                rng: random.Random) -> None:
    """Gathered items: into the bag, and towards "gather" objectives."""
    c = get_content()
    for key, qty in items.items():
        await inventory.add_item(session, char, key, qty)
        out.add("loot.item", item=c.items[key].labelled(), qty=qty, item_key=key)
    out.extend(await quests.on_items(session, char, "gather", items, rng))


async def claim(session: AsyncSession, char: Character, now: float | None = None) -> Outcome:
    """Collect a finished activity. The result comes from the activity's own seed, so it is fixed."""
    act = await open_activity(session, char, lock=True)
    if act is None or act.status != "running":
        return Outcome.refused("activity.err.none")
    now = _now(now)
    if now < act.ends_at:
        return Outcome.refused("activity.err.not_ready", minutes=math.ceil((act.ends_at - now) / 60))
    c = get_content()
    rng = random.Random(act.seed)
    loc = c.locations[act.location]
    char.state = "idle"
    characters.bump_stats(char, activities=1)
    if act.kind == "rest":
        _finish(act, "rest", {}, 0, now)
        return exploration.wake_rested(char).extend(await quests.advance(session, char, "rest", act.location, rng))
    if act.kind == "track":
        return await _claim_track(session, char, act, loc, rng, now)
    if act.kind == "skin":
        beasts = (act.result or {}).get("monsters", [])
        out = Outcome().add("activity.done.skin", place=loc.phrase())
        got = await skin(session, char, beasts, rng, out)
        _finish(act, "skin", got, gathering.SKIN_XP * len(beasts), now)
        return out

    g = _gathering(loc, act.skill)
    rank = gathering.rank_for(characters.mastery_xp(char, act.skill))
    roll = gathering.roll_gather(rng, g.resources if g else [], rank, act.kind)
    items = roll.total()
    table = exploration.encounter_table(loc, char.level)
    if act.kind == "stay" and g and table and gathering.roll_ambush(rng, g.stay_ambush):
        entry = rng.choices(table, weights=[e.weight for e in table])[0]
        act.status = "awaiting_combat"
        act.result = {**(act.result or {}), "pending": items, "xp": roll.xp, "monsters": list(entry.monsters)}
        out = Outcome().add("activity.stay_ambush", loot=loot_text(items))
        enc, enc_out = await combat_service.start_encounter(session, char, list(entry.monsters), rng)
        act.encounter_id = enc.id
        return out.extend(enc_out)

    out = Outcome(activity_id=act.id).add(f"activity.done.{act.kind}", place=loc.phrase())
    await _give(session, char, items, out, rng)
    if roll.bonus:
        out.add("activity.bonus", loot=loot_text(roll.bonus))
    characters.grant_mastery(char, act.skill, roll.xp, out)
    _finish(act, "gather" if act.kind == "gather" else "stay_ok", items, roll.xp, now)
    await _achievement_activity(session, char, act, out)
    return out


async def _claim_track(session, char, act, loc, rng, now) -> Outcome:
    fixed = exploration.pending_fixed_encounter(char)
    table = exploration.encounter_table(loc, char.level)
    if fixed or (table and gathering.roll_prey(rng)):
        monsters = list(fixed.monsters) if fixed else list(rng.choices(table, weights=[e.weight for e in table])[0].monsters)
        act.status = "awaiting_combat"
        act.result = {**(act.result or {}), "monsters": monsters}
        out = Outcome().add("activity.track_found", monster=get_content().monsters[monsters[0]].name.model_dump())
        enc, enc_out = await combat_service.start_encounter(session, char, monsters, rng, fixed.flag if fixed else None,
                                                          hunt=True)
        act.encounter_id = enc.id
        return out.extend(enc_out)
    out = Outcome(activity_id=act.id).add("activity.track_tracks")
    characters.grant_mastery(char, "tracking", gathering.TRACK_XP_TRACKS, out)
    _finish(act, "track_tracks", {}, gathering.TRACK_XP_TRACKS, now)
    await _achievement_activity(session, char, act, out)
    return out


async def skin(session: AsyncSession, char: Character, monster_keys: list[str], rng: random.Random,
               out: Outcome, trophy: bool = False) -> dict[str, int]:
    """Skin the defeated beasts that can be skinned (needs a knife). Tracked prey gives a second
    harvest as trophies. Returns what was obtained."""
    c = get_content()
    beasts = [k for k in monster_keys if c.monsters[k].harvest]
    if not beasts:
        return {}
    if await inventory.count(session, char, SKINNING_KNIFE) == 0:
        if not trophy:
            out.add("activity.no_knife")
        return {}
    rank = gathering.rank_for(characters.mastery_xp(char, "skinning"))
    got: dict[str, int] = {}
    for key in beasts:
        for item, qty in gathering.roll_harvest(rng, c.monsters[key].harvest, rank).items():
            got[item] = got.get(item, 0) + qty
    boost = await quests.tutorial_boost(session, char, "skin", {h.item for k in beasts for h in c.monsters[k].harvest})
    if boost:  # the tutorial's shortcut: what the mission asks for is guaranteed
        qkey, item, missing = boost
        quests.use_tutorial_boost(char, qkey)
        got[item] = max(got.get(item, 0), missing)
    if got:
        out.add("activity.trophies" if trophy else "activity.skinned", loot=loot_text(got))
        for key, qty in got.items():
            await inventory.add_item(session, char, key, qty)
        out.extend(await quests.on_items(session, char, "skin", got, rng))
    if not trophy:
        characters.grant_mastery(char, "skinning", gathering.SKIN_XP * len(beasts), out)
        await achievements.emit(session, char, out, "activity", {"skill": "skinning", "tool": True})
        await achievements.mastery(session, char, out, "skinning")
    return got


async def on_encounter_end(session: AsyncSession, char: Character, status: str, defeated: list[str],
                           rng: random.Random, out: Outcome) -> None:
    """Pay what an ambushed stay or a tracked prey had pending. Called once, when the fight ends."""
    act = await session.scalar(
        select(WorldActivity)
        .where(WorldActivity.character_id == char.id, WorldActivity.status == "awaiting_combat")
        .with_for_update()
    )
    if act is None:
        return
    now = time.time()
    res = dict(act.result or {})
    monster = res.get("monsters", [None])[0]
    if act.kind == "stay":
        pending = res.get("pending", {})
        given = {"victory": pending, "fled": gathering.half(pending)}.get(status, {})
        xp = {"victory": res.get("xp", 0), "fled": res.get("xp", 0) // 2}.get(status, 0)
        if status == "victory":
            out.add("activity.stay_saved")
        elif status == "fled":
            out.add("activity.stay_half")
        else:
            out.add("activity.stay_lost", loot=loot_text(pending))
        await _give(session, char, given, out, rng)
        if xp:
            characters.grant_mastery(char, act.skill, xp, out)
        outcome = {"victory": "stay_won", "fled": "stay_fled"}.get(status, "stay_lost")
    else:
        given, xp = {}, 0
        if status == "victory":
            given = await skin(session, char, defeated, rng, out, trophy=True)
            xp = gathering.TRACK_XP_WIN
            characters.grant_mastery(char, "tracking", xp, out)
        outcome = {"victory": "track_won", "fled": "track_fled"}.get(status, "track_lost")
    _finish(act, outcome, given, xp, now, monster=monster)
    await _achievement_activity(session, char, act, out)
    out.activity_id = act.id


def remaining_minutes(act: WorldActivity, now: float | None = None) -> int:
    return max(0, math.ceil((act.ends_at - _now(now)) / 60))


def remaining_seconds(act: WorldActivity, now: float | None = None) -> int:
    return max(0, math.ceil(act.ends_at - _now(now)))


async def due(session: AsyncSession, now: float | None = None) -> list[int]:
    """Characters whose running activity is over: they get the result without pressing anything."""
    rows = await session.scalars(select(WorldActivity.character_id)
                                 .where(WorldActivity.status == "running", WorldActivity.ends_at <= _now(now)))
    return sorted(set(rows))


def describe(act: WorldActivity, lang: str) -> str:
    """'Minería en Mina del Paso Viejo' for panels."""
    c = get_content()
    skill = "" if act.kind == "rest" else characters.mastery_name(act.skill)[lang]
    return t(lang, f"activity.kind.{act.kind}", skill=skill, place=c.locations[act.location].phrase()[lang])


LOST = ("stay_lost", "track_lost")  # the ambush won: the activity did not finish


async def _achievement_activity(session, char, act, out):
    if act.kind != "rest" and (act.result or {}).get("outcome") not in LOST:
        await achievements.emit(session, char, out, "activity",
            {"skill": act.skill, "tool": bool((act.result or {}).get("tool_checked"))}, f"activity:{act.id}:done")
        await achievements.mastery(session, char, out, act.skill, f"activity:{act.id}:done")
