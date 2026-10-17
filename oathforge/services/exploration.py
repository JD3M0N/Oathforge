"""World clock, movement, investigation and resting."""

import random
import time

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.content.schemas import EncounterEntry, Exit, Location
from oathforge.database.models import Character
from oathforge.engine.checks import check, dc_for
from oathforge.services import characters, combat_service, inventory, quests, world_map
from oathforge.services.events import Outcome

GAME_DAY_SECONDS = 4 * 3600  # one in-game day every four real hours
ENCOUNTER_CHANCE_PER_DANGER = 0.15  # one road: 15 % per ⚠️
TRIP_EXTRA_PER_STRETCH = 0.05  # each further dangerous road on a longer trip
TRIP_CHANCE_CAP = 0.45  # a trip rolls one ambush at most, never above this
TRIP = "trip"  # char.flags: a trip stopped halfway ({"to": place, "rolled": True}), to carry on


def game_time(now: float | None = None) -> float:
    """Real time as the game clock reads it: GAME_CLOCK_OFFSET_HOURS (testing) moves it forward."""
    now = time.time() if now is None else now
    return now + get_settings().game_clock_offset_hours * GAME_DAY_SECONDS / 24


def game_hour(now: float | None = None) -> int:
    return int((game_time(now) % GAME_DAY_SECONDS) / GAME_DAY_SECONDS * 24)


def game_day(now: float | None = None) -> int:
    return int(game_time(now) // GAME_DAY_SECONDS)


def tried(char: Character, key: str) -> bool:
    """A check already attempted today at this level can't be retried until tomorrow or a level up."""
    last = (char.checks_tried or {}).get(key)
    return last is not None and last == [game_day(), char.level]


def mark_tried(char: Character, key: str) -> None:
    today = game_day()
    kept = {k: v for k, v in (char.checks_tried or {}).items() if v[0] == today}
    char.checks_tried = {**kept, key: [today, char.level]}


def free_check_key(skill: str, location: str) -> str:
    return f"free:{skill}:{location}"


def open_discoveries(char: Character) -> dict:
    """Secrets here not found yet and not already tried today."""
    loc = get_content().locations[char.location]
    return {k: d for k, d in loc.discoveries.items()
            if not char.flags.get(d.sets_flag) and (not d.requires_flag or char.flags.get(d.requires_flag))
            and not tried(char, f"discover:{k}")}


DAWN, DUSK = 6, 20  # game hours: night is from DUSK to DAWN


def is_night(now: float | None = None) -> bool:
    h = game_hour(now)
    return h >= DUSK or h < DAWN


def clock(now: float | None = None) -> str:
    """The game time as "14:20"."""
    minutes = int((game_time(now) % GAME_DAY_SECONDS) / GAME_DAY_SECONDS * 24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def until_switch(now: float | None = None) -> int:
    """Real minutes until day turns to night or night to day."""
    seconds_into_day = game_time(now) % GAME_DAY_SECONDS
    hour = GAME_DAY_SECONDS / 24
    switches = [DAWN * hour, DUSK * hour, (24 + DAWN) * hour]
    nxt = min(s for s in switches if s > seconds_into_day)
    return max(1, round((nxt - seconds_into_day) / 60))


def npcs_present(location: str, now: float | None = None) -> list[str]:
    period = "night" if is_night(now) else "day"
    return [k for k, npc in get_content().npcs.items() if npc.schedule.get(period) == location]


def exits(char: Character) -> list[Exit]:
    return world_map.open_exits(char, char.location)


def encounter_table(loc: Location, level: int, now: float | None = None) -> list[EncounterEntry]:
    """Night has its own creatures where the location defines them (bats instead of boars).

    Entries with a ``min_level`` above the hero's level are left out.
    """
    table = loc.night_encounters if loc.night_encounters and is_night(now) else loc.encounters
    return [e for e in table if e.min_level <= level]


def pending_fixed_encounter(char: Character):
    return world_map.blocks_passage(char, char.location)


def trip(char: Character) -> str | None:
    """Where a trip stopped halfway was heading, if the character can still carry on."""
    to = ((char.flags or {}).get(TRIP) or {}).get("to")
    return to if to and to != char.location and world_map.route_to(char, to) else None


def drop_trip(char: Character) -> None:
    if TRIP in (char.flags or {}):
        char.flags = {k: v for k, v in char.flags.items() if k != TRIP}


def trip_chance(route: world_map.Route) -> float:
    """One ambush roll for the whole trip: the worst road sets it, each further dangerous road adds a little."""
    risky = sum(1 for s in route.stretches if s.danger)
    if not risky:
        return 0.0
    return min(TRIP_CHANCE_CAP, ENCOUNTER_CHANCE_PER_DANGER * route.danger + TRIP_EXTRA_PER_STRETCH * (risky - 1))


def _ambush_stop(char: Character, route: world_map.Route, rng: random.Random):
    """Where on the way the ambush happens, or None: a dangerous road with creatures at its end, weighted by
    danger. A place whose own fight is waiting (a crypt room) keeps that fight instead."""
    c = get_content()
    spots = [(i, s) for i, s in enumerate(route.stretches)
             if s.danger and encounter_table(c.locations[s.to], char.level) and not world_map.blocks_passage(char, s.to)]
    chance = trip_chance(route)
    if not spots or not chance or rng.random() >= chance:
        return None
    return spots[0] if len(spots) == 1 else rng.choices(spots, weights=[s.danger for _, s in spots])[0]


def _names(keys) -> dict:
    c = get_content()
    return {lang: ", ".join(c.locations[k].name.get(lang) for k in keys) for lang in ("es", "en")}


async def travel(session: AsyncSession, char: Character, dest: str, rng: random.Random) -> Outcome:
    """Go anywhere the map offers: the engine walks the way and rolls one ambush for the whole trip, which
    stops it halfway (the rest is kept to carry on, with no further roll)."""
    if refusal := characters.ensure_free(char):
        return refusal
    route = world_map.route_to(char, dest)
    if route is None:
        return Outcome.refused("explore.err.no_route")
    c = get_content()
    pending = (char.flags or {}).get(TRIP) or {}
    rolled = pending.get("to") == dest and pending.get("rolled")  # carrying on: the trip already rolled
    drop_trip(char)
    characters.drop_pending_skin(char)

    stop = None if rolled else _ambush_stop(char, route, rng)
    walked = route.stretches[:stop[0] + 1] if stop else route.stretches
    end = walked[-1].to if walked else dest
    yards = sum(s.yards for s in walked) if walked else route.yards
    characters.bump_stats(char, yards=yards)
    out = Outcome()
    passed = [s.to for s in walked[:-1]]
    for place in passed + [end]:
        characters.visited(char, place)
    char.location = end
    if stop:
        out.add("explore.trip_stopped", place=c.locations[end].name.model_dump(),
                dest=c.locations[dest].name.model_dump(), yards=yards)
        char.flags = {**char.flags, TRIP: {"to": dest, "rolled": True}}
    elif passed:
        out.add("explore.arrived_via", place=c.locations[end].name.model_dump(), via=_names(passed), yards=yards)
    else:
        out.add("explore.arrived", place=c.locations[end].name.model_dump(), yards=yards)
    for place in passed + [end]:
        out.extend(await quests.on_visit(session, char, place, rng))

    if stop:
        table = encounter_table(c.locations[end], char.level)
        entry = rng.choices(table, weights=[e.weight for e in table])[0]
        out.add("explore.ambush")
        _, enc_out = await combat_service.start_encounter(session, char, list(entry.monsters), rng)
        return out.extend(enc_out)
    fixed = pending_fixed_encounter(char)
    if fixed:
        _, enc_out = await combat_service.start_encounter(session, char, list(fixed.monsters), rng, fixed.flag)
        out.extend(enc_out)
    return out


async def hunt(session: AsyncSession, char: Character, rng: random.Random) -> Outcome:
    """Look for prey on purpose: a fight from the location's day or night table."""
    if refusal := characters.ensure_free(char):
        return refusal
    loc = get_content().locations[char.location]
    if not loc.hunting:
        return Outcome.refused("explore.err.no_hunting")
    fixed = pending_fixed_encounter(char)
    if fixed:
        _, enc_out = await combat_service.start_encounter(session, char, list(fixed.monsters), rng, fixed.flag)
        return Outcome().add("explore.hunt_boss").extend(enc_out)
    table = encounter_table(loc, char.level)
    entry = rng.choices(table, weights=[e.weight for e in table])[0]
    out = Outcome()
    if char.hp * 2 < char.max_hp:
        out.add("explore.low_hp", hp=char.hp, max_hp=char.max_hp)
    night = is_night() and bool(loc.night_encounters)
    own = loc.hunt_night if night else loc.hunt_day
    if own is not None:
        out.text(own)
    else:
        out.add("explore.hunt_night" if night else "explore.hunt_day")
    _, enc_out = await combat_service.start_encounter(session, char, list(entry.monsters), rng)
    return out.extend(enc_out)


async def investigate(session: AsyncSession, char: Character, rng: random.Random) -> Outcome:
    """Roll once for every undiscovered secret here; a failed secret can't be retried until tomorrow."""
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    loc = c.locations[char.location]
    pending = {k: d for k, d in loc.discoveries.items()
               if not char.flags.get(d.sets_flag) and (not d.requires_flag or char.flags.get(d.requires_flag))}
    out = Outcome()
    if not pending:
        return out.add("explore.nothing_more")
    pending = {k: d for k, d in pending.items() if not tried(char, f"discover:{k}")}
    if not pending:
        return out.add("explore.already_tried")
    skills = await characters.skills_of(session, char)
    found = False
    for key, disc in pending.items():
        dc = dc_for(disc.tier)
        res = check(rng, disc.skill, characters.skill_bonus(char, skills, disc.skill), dc)
        mark_tried(char, f"discover:{key}")
        out.add("check.result", skill=c.skills[disc.skill].name.model_dump(), roll=res.kept, total=res.total,
                dc=dc, result="✅" if res.success else "❌")
        if not res.success:
            continue
        found = True
        out.text(disc.text)
        char.flags = {**char.flags, disc.sets_flag: True}
        for item, qty in disc.gives.items():
            await inventory.add_item(session, char, item, qty)
            out.add("loot.item", item=c.items[item].name.model_dump(), qty=qty, item_key=item)
        if disc.gold:
            char.gold += disc.gold
            out.add("loot.gold", gold=disc.gold)
        await characters.practice(session, char, disc.skill, disc.tier, f"discover:{key}", out)
        if disc.sets_flag == "crypt_unlocked":
            out.add("explore.new_route")
    if not found:
        out.add("explore.found_nothing")
    await quests.refresh(session, char, out)  # a discovery flag can open a mission (crypt_unlocked)
    return out


async def check_skill(session: AsyncSession, char: Character, skill: str, tier: str,
                      rng: random.Random) -> tuple[Outcome, bool]:
    """A free-form skill check requested through the AI interpreter; one attempt per skill and place a day."""
    if refusal := characters.ensure_free(char):
        return refusal, False
    c = get_content()
    key = free_check_key(skill, char.location)
    if tried(char, key):
        return Outcome.refused("check.already_tried", skill=c.skills[skill].name.model_dump()), False
    skills = await characters.skills_of(session, char)
    dc = dc_for(tier)
    res = check(rng, skill, characters.skill_bonus(char, skills, skill), dc)
    mark_tried(char, key)
    out = Outcome().add("check.result", skill=c.skills[skill].name.model_dump(), roll=res.kept, total=res.total,
                        dc=dc, result="✅" if res.success else "❌")
    if res.success:
        await characters.practice(session, char, skill, tier, key, out)
    return out, res.success


def wake_rested(char: Character) -> Outcome:
    """The end of a long rest (activities.claim): full HP and uses, and grave wounds healed."""
    char.hp = char.max_hp
    char.resources = characters.full_resources(char.class_key, char.level)
    char.conditions = {k: v for k, v in char.conditions.items() if k != "injured"}
    return Outcome().add("explore.rested", hp=char.hp)


async def cure_wounds(session: AsyncSession, char: Character, rng: random.Random) -> Outcome:
    """The chapel's healer: a quick heal that also closes grave wounds (the "injured" condition)."""
    loc = get_content().locations[char.location]
    if loc.healer is None:
        return Outcome.refused("explore.err.no_healer")
    if refusal := characters.ensure_free(char):
        return refusal
    injured = bool(char.conditions.get("injured"))
    if char.hp >= char.max_hp and not injured:
        return Outcome.refused("inv.err.full_hp")
    # beta: Ysolde heals everything for free and closes grave wounds, so nobody gets stuck injured and broke
    # after a defeat; revisit with the economy (healer.cost and healer.heal stay in place.yaml for then)
    if injured:
        char.conditions = {k: v for k, v in char.conditions.items() if k != "injured"}
    before = char.hp
    char.hp = char.max_hp
    out = Outcome().add("explore.healed", amount=char.hp - before, hp=char.hp, max_hp=char.max_hp)
    if injured:
        out.add("explore.healed_injured")
    return out.extend(await quests.advance(session, char, "heal", char.location, rng))


def _objective_spots(char: Character, kind: str, target: str) -> set[str]:
    """Places where a mission objective can be done (derived from the world, never a secret one)."""
    c = get_content()
    if kind == "visit" or (kind in ("rest", "heal") and target != "any"):
        return {target}
    if kind == "talk":
        return {loc for loc in [c.npcs[target].schedule.get("night" if is_night() else "day")] if loc}
    if kind == "kill":
        return {k for k, loc in c.locations.items()
                if any(target in e.monsters for e in [*loc.encounters, *loc.night_encounters, *loc.fixed_encounters])}
    if kind == "gather":
        return {k for k, loc in c.locations.items() if any(r.item == target for g in loc.gathering for r in g.resources)}
    if kind == "craft":
        return {k for k, loc in c.locations.items() if loc.stations}
    return set()


async def objective_routes(session: AsyncSession, char: Character, limit: int = 2) -> list[tuple[dict, world_map.Route]]:
    """The nearest known place for the next step of each active mission: (mission name, route). Only places
    the character could go to from the map anyway, so it never gives a secret away."""
    c = get_content()
    prog = await quests.progress(session, char)
    routes = {r.to: r for r in world_map.destinations(char)}
    out: list[tuple[dict, world_map.Route]] = []
    for qkey, quest in quests.ordered_quests():
        p = prog.get(qkey)
        if p is None or p.state != "active":
            continue
        spots: set[str] = {a.location for a in quest.actions.values() if a.location and p.stage in a.stages}
        if p.stage == quest.objective_stage:
            nxt = next((o for o, n in quests.objective_progress(quest, p) if n < o.count), None)
            if nxt is not None:
                spots |= _objective_spots(char, nxt.kind, nxt.target)
        if char.location in spots:
            continue
        best = min((routes[k] for k in spots if k in routes), key=lambda r: (r.minutes, r.to), default=None)
        if best is not None and all(best.to != r.to for _, r in out):
            out.append((quest.name.model_dump(), best))
        if len(out) >= limit:
            break
    return out
