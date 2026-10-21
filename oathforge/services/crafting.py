"""Crafting and refining: the right discipline, its station here and every ingredient, or nothing is spent.

The request only carries a recipe id and a quantity; ingredients, outputs and XP always come from
content/recipes.yaml. A recipe's discipline may be a profession, a hobby or a field mastery: refining
(ore -> ingot, log -> plank) belongs to the mastery, so anyone can do it and its XP goes there.
"""

import random

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.content.schemas import Recipe, Station
from oathforge.database.models import Character
from oathforge.engine import gathering
from oathforge.i18n import t
from oathforge.services import characters, home, inventory, professions, quests
from oathforge.services import achievements
from oathforge.services.events import Outcome

LOW_RANK_GAP = 2  # a recipe this many ranks below yours gives half XP


def is_mastery(key: str) -> bool:
    """Is this discipline a field mastery (mining, woodcutting...) instead of a profession?"""
    return key in gathering.MASTERIES


def station_of(recipe: Recipe) -> Station | None:
    """Where it is made: the recipe's own station, or the one of its profession."""
    if recipe.station is not None:
        return recipe.station
    prof = get_content().professions.get(recipe.profession)
    return prof.station if prof is not None else None


def rank_in(char: Character, key: str) -> int:
    """The character's rank in a discipline, whether it is a mastery or a profession."""
    if is_mastery(key):
        return gathering.rank_for(characters.mastery_xp(char, key))
    return professions.rank(char, key)


def disciplines(char: Character) -> set[str]:
    """What you can craft or refine with: your active professions, every hobby and every mastery."""
    return set(professions.usable(char)) | set(gathering.MASTERIES)


def known(char: Character) -> list[str]:
    """The special recipes this character learned from a blueprint."""
    return list((char.crafting or {}).get("known", []))


def knows(char: Character, recipe_key: str) -> bool:
    recipe = get_content().recipes[recipe_key]
    return not recipe.special or recipe_key in known(char)


def recipes_here(char: Character, open_quests: set[str] = frozenset()) -> dict[str, Recipe]:
    """Recipes you may work on where you stand: your disciplines and this place's stations.

    A starter recipe (``quest``) joins them only while that mission is running: it asks for no trade, so it
    must not outlive the mission that justifies it.
    """
    c = get_content()
    stations = set(c.locations[char.location].stations)
    mine = disciplines(char)
    return {k: r for k, r in c.recipes.items()
            if station_of(r) in stations and knows(char, k)
            and (r.quest in open_quests if r.quest is not None else r.profession in mine)}


async def learn_blueprint(session: AsyncSession, char: Character, item_key: str) -> Outcome:
    """Read a blueprint: it teaches its recipe for good and is spent. Knowing it already, it is not spent."""
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    item = c.items.get(item_key)
    if item is None or item.type != "blueprint" or item.teaches is None:
        return Outcome.refused("craft.err.not_blueprint")
    recipe = c.recipes[item.teaches]
    name = c.items[next(iter(recipe.outputs))].labelled()
    if item.teaches in known(char):
        return Outcome.refused("craft.err.known", item=name)
    if not await inventory.remove_item(session, char, item_key, 1):
        return Outcome.refused("inv.err.not_found")
    char.crafting = {**(char.crafting or {}), "known": known(char) + [item.teaches]}
    out = Outcome().add("craft.learned", item=name, prof=discipline_name(recipe.profession), rank=recipe.min_rank)
    await achievements.emit(session, char, out, "blueprint", {"recipe": item.teaches}, f"blueprint:{item.teaches}")
    return out


async def missing(session: AsyncSession, char: Character, recipe: Recipe, qty: int = 1) -> dict[str, int]:
    """Ingredients still needed for ``qty`` batches: item -> how many are missing."""
    out = {}
    for item, per_unit in recipe.ingredients.items():
        need = per_unit * qty
        have = await inventory.count(session, char, item)
        if have < need:
            out[item] = need - have
    return out


async def craft(session: AsyncSession, char: Character, recipe_key: str, rng: random.Random | None = None,
                qty: int = 1) -> Outcome:
    """Make ``qty`` batches of a recipe: all of them or none, in this one transaction."""
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    recipe = c.recipes.get(recipe_key)
    if recipe is None:
        return Outcome.refused("craft.err.unknown")
    limit = get_settings().craft_batch_max
    if qty < 1 or qty > limit:
        return Outcome.refused("craft.err.qty", max=limit)
    if not knows(char, recipe_key):
        return Outcome.refused("craft.err.blueprint")
    name = discipline_name(recipe.profession)
    if recipe.quest is not None:  # a starter recipe: the mission, not a trade, is what opens it
        if qty != 1:
            return Outcome.refused("craft.err.qty", max=1)
        if not await quests.is_active(session, char, recipe.quest):
            return Outcome.refused("craft.err.quest_only")
    elif recipe.profession not in disciplines(char):
        return Outcome.refused("craft.err.not_your_profession", prof=name)
    station = station_of(recipe)
    if station not in c.locations[char.location].stations:
        return Outcome.refused("craft.err.no_station", station={lang: t(lang, f"station.{station}")
                                                               for lang in ("es", "en")})
    rank = rank_in(char, recipe.profession)
    if rank < recipe.min_rank:
        return Outcome.refused("craft.err.rank", prof=name, rank=recipe.min_rank)
    lacking = await missing(session, char, recipe, qty)
    if lacking:
        return Outcome.refused("craft.err.missing", items=_items_text(lacking))
    for item, per_unit in recipe.ingredients.items():  # checked above, under the character's row lock
        if not await inventory.remove_item(session, char, item, per_unit * qty):
            raise RuntimeError(f"ingredient {item} vanished while crafting")  # rolls the transaction back
    out = Outcome()
    if recipe.installs is not None:  # furniture stays in the room instead of going into the bag
        home.install(char, recipe.installs, out)
    for item, per_unit in recipe.outputs.items():
        await inventory.add_item(session, char, item, per_unit * qty, crafted_by=char.id)
        out.add("craft.made", item=c.items[item].labelled(), qty=per_unit * qty)
    xp = (recipe.xp // 2 if rank - recipe.min_rank >= LOW_RANK_GAP else recipe.xp) * qty
    await grant_discipline_xp(session, char, recipe.profession, xp, out)
    made = {item: per_unit * qty for item, per_unit in recipe.outputs.items()}
    if recipe.installs is not None:
        made = {**made, f"furniture:{recipe.installs}": 1}
    out.extend(await quests.on_items(session, char, "craft", made, rng or random.Random()))
    await achievements.emit(session, char, out, "craft", {"recipe": recipe_key})
    return out


async def grant_discipline_xp(session: AsyncSession, char: Character, key: str, xp: int, out: Outcome) -> None:
    """XP of a refining recipe goes to its mastery; XP of a profession recipe, to the profession."""
    if is_mastery(key):
        characters.grant_mastery(char, key, xp, out)
        rank = gathering.rank_for(characters.mastery_xp(char, key))
        await achievements.mastery(session, char, out, key, f"mastery:{key}:{rank}")
    else:
        professions.grant_xp(char, key, xp, out)
        await achievements.profession(session, char, out, key)


def discipline_name(key: str) -> dict:
    """{es, en} name of a discipline, be it a mastery or a profession."""
    if is_mastery(key):
        return characters.mastery_name(key)
    return get_content().professions[key].name.model_dump()


def _items_text(items: dict[str, int]) -> dict:
    c = get_content()
    return {lang: ", ".join(f"{q} × {c.items[k].name.get(lang)}" for k, q in items.items()) for lang in ("es", "en")}
