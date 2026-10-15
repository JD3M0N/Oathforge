"""World clock, movement, investigation and resting."""

import random
import time

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.content.schemas import EncounterEntry, Exit, Location
from oathforge.database.models import Character
from oathforge.engine.checks import check, dc_for
from oathforge.engine.dice import roll
from oathforge.services import characters, combat_service, inventory, quests, world_map
from oathforge.services.events import Outcome

GAME_DAY_SECONDS = 4 * 3600  # one in-game day every four real hours
ENCOUNTER_CHANCE_PER_DANGER = 0.15


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


def encounter_table(loc: Location, now: float | None = None) -> list[EncounterEntry]:
    """Night has its own creatures where the location defines them (bats instead of boars)."""
    if loc.night_encounters and is_night(now):
        return loc.night_encounters
    return loc.encounters


def pending_fixed_encounter(char: Character):
    for fe in get_content().locations[char.location].fixed_encounters:
        if char.flags.get(fe.flag):
            continue
        if fe.if_flag and not char.flags.get(fe.if_flag):
            continue
        if fe.unless_flag and char.flags.get(fe.unless_flag):
            continue
        return fe
    return None


async def travel(session: AsyncSession, char: Character, dest: str, rng: random.Random) -> Outcome:
    if refusal := characters.ensure_free(char):
        return refusal
    route = world_map.route_to(char, dest)  # a whole walk across the city, or one road or room elsewhere
    if route is None:
        return Outcome.refused("explore.err.no_route")
    c = get_content()
    characters.drop_pending_skin(char)
    char.location = dest
    out = Outcome().add("explore.arrived", place=c.locations[dest].name.model_dump(), minutes=route.minutes)

    out.extend(await quests.on_visit(session, char, dest, rng))

    fixed = pending_fixed_encounter(char)
    if fixed:
        _, enc_out = await combat_service.start_encounter(session, char, list(fixed.monsters), rng, fixed.flag)
        return out.extend(enc_out)
    table = encounter_table(c.locations[dest])
    if route.danger and table and rng.random() < route.danger * ENCOUNTER_CHANCE_PER_DANGER:
        entry = rng.choices(table, weights=[e.weight for e in table])[0]
        out.add("explore.ambush")
        _, enc_out = await combat_service.start_encounter(session, char, list(entry.monsters), rng)
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
    table = encounter_table(loc)
    entry = rng.choices(table, weights=[e.weight for e in table])[0]
    out = Outcome().add("explore.hunt_night" if is_night() and loc.night_encounters else "explore.hunt_day")
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
    """The chapel's healer: a few coins for a quick heal. Grave wounds still need a long rest."""
    loc = get_content().locations[char.location]
    if loc.healer is None:
        return Outcome.refused("explore.err.no_healer")
    if refusal := characters.ensure_free(char):
        return refusal
    cap = inventory.hp_cap(char)
    if char.hp >= cap:
        return Outcome.refused("explore.err.injured_cap" if cap < char.max_hp else "inv.err.full_hp")
    if char.gold < loc.healer.cost:
        return Outcome.refused("shop.err.no_gold", price=loc.healer.cost)
    char.gold -= loc.healer.cost
    before = char.hp
    char.hp = min(cap, char.hp + roll(loc.healer.heal, rng).total)
    out = Outcome().add("explore.healed", cost=loc.healer.cost, amount=char.hp - before, hp=char.hp,
                        max_hp=char.max_hp)
    if cap < char.max_hp:
        out.add("explore.healed_injured")
    return out.extend(await quests.advance(session, char, "heal", char.location, rng))
