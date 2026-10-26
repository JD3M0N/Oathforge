"""Branches of a field mastery: two per discipline, one active, chosen at rank 2 at the guild.

Switching never deletes anything: the branch you leave stays learned and paused, and coming back to it
costs the same gold. A paused branch adds nothing, and the branch in force is frozen into the activity
when it starts, so nobody changes it halfway through to collect on better terms.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.content.schemas import Specialization
from oathforge.database.models import Character
from oathforge.engine import gathering
from oathforge.services import characters
from oathforge.services.events import Outcome

MIN_RANK = 2  # the rank that opens the choice


def branches(skill: str) -> dict[str, Specialization]:
    return {k: s for k, s in get_content().specializations.items() if s.skill == skill}


def active(char: Character, skill: str) -> str | None:
    return (char.crafting or {}).get("spec", {}).get(skill)


def learned(char: Character) -> list[str]:
    """Every branch this character ever took: the paused ones are not forgotten."""
    return list((char.crafting or {}).get("spec_learned", []))


def effects(char: Character, skill: str):
    """What the active branch changes, as the engine's Mods; nothing when there is none."""
    key = active(char, skill)
    spec = get_content().specializations.get(key) if key else None
    if spec is None:
        return gathering.Mods()
    return gathering.Mods(
        time_pct=spec.effects.time_pct, rare_rel=spec.effects.rare_rel, extra_chance=spec.effects.extra_chance
    )


def price(char: Character, key: str) -> int:
    """Free the first time you take a branch; after that, the guild charges for the change."""
    return 0 if not active(char, get_content().specializations[key].skill) else get_settings().spec_switch_cost


async def choose(session: AsyncSession, char: Character, key: str) -> Outcome:
    """Take a branch, or come back to one you had paused."""
    if refusal := characters.ensure_free(char):  # no switching with an activity running
        return refusal
    c = get_content()
    spec = c.specializations.get(key)
    if spec is None:
        return Outcome.refused("spec.err.unknown")
    loc = c.locations[char.location]
    if not loc.home:
        return Outcome.refused("spec.err.not_guild")
    rank = gathering.rank_for(characters.mastery_xp(char, spec.skill))
    if rank < MIN_RANK:
        return Outcome.refused("spec.err.rank", skill=characters.mastery_name(spec.skill), rank=MIN_RANK)
    if active(char, spec.skill) == key:
        return Outcome.refused("spec.err.already", spec=spec.name.model_dump())
    cost = price(char, key)
    if char.gold < cost:
        return Outcome.refused("shop.err.no_gold", price=cost)
    char.gold -= cost
    crafting = dict(char.crafting or {})
    paused = active(char, spec.skill)
    crafting["spec"] = {**crafting.get("spec", {}), spec.skill: key}
    crafting["spec_learned"] = sorted({*learned(char), key})
    char.crafting = crafting
    out = Outcome().add(
        "spec.chosen", spec=spec.name.model_dump(), skill=characters.mastery_name(spec.skill), cost=cost
    )
    if paused:
        out.add("spec.paused", spec=c.specializations[paused].name.model_dump())
    return out
