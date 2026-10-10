"""World clock, movement, investigation and resting."""

import random
import time

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.content.schemas import Exit
from oathforge.database.models import Character
from oathforge.engine.checks import check, dc_for
from oathforge.services import characters, combat_service, inventory
from oathforge.services.events import Outcome

GAME_DAY_SECONDS = 4 * 3600  # one in-game day every four real hours
ENCOUNTER_CHANCE_PER_DANGER = 0.15


def game_hour(now: float | None = None) -> int:
    now = time.time() if now is None else now
    return int((now % GAME_DAY_SECONDS) / GAME_DAY_SECONDS * 24)


def is_night(now: float | None = None) -> bool:
    h = game_hour(now)
    return h >= 20 or h < 6


def npcs_present(location: str, now: float | None = None) -> list[str]:
    period = "night" if is_night(now) else "day"
    return [k for k, npc in get_content().npcs.items() if npc.schedule.get(period) == location]


def exits(char: Character) -> list[Exit]:
    loc = get_content().locations[char.location]
    return [e for e in loc.exits if not e.requires_flag or char.flags.get(e.requires_flag)]


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
    if char.state == "in_combat":
        return Outcome.refused("explore.err.in_combat")
    exit_ = next((e for e in exits(char) if e.to == dest), None)
    if exit_ is None:
        return Outcome.refused("explore.err.no_route")
    c = get_content()
    char.location = dest
    out = Outcome().add("explore.arrived", place=c.locations[dest].name.model_dump(), minutes=exit_.minutes)

    fixed = pending_fixed_encounter(char)
    if fixed:
        _, enc_out = await combat_service.start_encounter(session, char, list(fixed.monsters), rng, fixed.flag)
        return out.extend(enc_out)
    table = c.locations[dest].encounters
    if exit_.danger and table and rng.random() < exit_.danger * ENCOUNTER_CHANCE_PER_DANGER:
        entry = rng.choices(table, weights=[e.weight for e in table])[0]
        out.add("explore.ambush")
        _, enc_out = await combat_service.start_encounter(session, char, list(entry.monsters), rng)
        out.extend(enc_out)
    return out


async def investigate(session: AsyncSession, char: Character, rng: random.Random) -> Outcome:
    """Roll for every undiscovered secret here. Repeating is allowed; skill gains diminish."""
    if char.state == "in_combat":
        return Outcome.refused("explore.err.in_combat")
    c = get_content()
    loc = c.locations[char.location]
    pending = {k: d for k, d in loc.discoveries.items()
               if not char.flags.get(d.sets_flag) and (not d.requires_flag or char.flags.get(d.requires_flag))}
    out = Outcome()
    if not pending:
        return out.add("explore.nothing_more")
    skills = await characters.skills_of(session, char)
    found = False
    for key, disc in pending.items():
        dc = dc_for(disc.tier)
        res = check(rng, disc.skill, characters.skill_bonus(char, skills, disc.skill), dc)
        out.add("check.result", skill=c.skills[disc.skill].name.model_dump(), roll=res.kept, total=res.total,
                dc=dc, result="✅" if res.success else "❌")
        if not res.success:
            continue
        found = True
        out.text(disc.text)
        char.flags = {**char.flags, disc.sets_flag: True}
        for item, qty in disc.gives.items():
            await inventory.add_item(session, char, item, qty)
            out.add("loot.item", item=c.items[item].name.model_dump(), qty=qty)
        if disc.gold:
            char.gold += disc.gold
            out.add("loot.gold", gold=disc.gold)
        await characters.practice(session, char, disc.skill, disc.tier, f"discover:{key}", out)
        if disc.sets_flag == "crypt_unlocked":
            out.add("explore.new_route")
    if not found:
        out.add("explore.found_nothing")
    return out


async def check_skill(session: AsyncSession, char: Character, skill: str, tier: str, rng: random.Random,
                      context: str) -> tuple[Outcome, bool]:
    """A free-form skill check requested through the AI interpreter."""
    c = get_content()
    skills = await characters.skills_of(session, char)
    dc = dc_for(tier)
    res = check(rng, skill, characters.skill_bonus(char, skills, skill), dc)
    out = Outcome().add("check.result", skill=c.skills[skill].name.model_dump(), roll=res.kept, total=res.total,
                        dc=dc, result="✅" if res.success else "❌")
    if res.success:
        await characters.practice(session, char, skill, tier, context, out)
    return out, res.success


async def rest(session: AsyncSession, char: Character) -> Outcome:
    loc = get_content().locations[char.location]
    if loc.rest_cost is None:
        return Outcome.refused("explore.err.no_rest")
    if char.state == "in_combat":
        return Outcome.refused("explore.err.in_combat")
    if char.gold < loc.rest_cost:
        return Outcome.refused("shop.err.no_gold", price=loc.rest_cost)
    char.gold -= loc.rest_cost
    char.hp = char.max_hp
    char.resources = characters.full_resources(char.class_key, char.level)
    char.conditions = {k: v for k, v in char.conditions.items() if k != "injured"}
    return Outcome().add("explore.rested", cost=loc.rest_cost, hp=char.hp)
