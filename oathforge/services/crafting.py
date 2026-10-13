"""Crafting: an active profession, its station here and every ingredient, or nothing is spent.

The request only carries a recipe id; ingredients, outputs and XP always come from content/recipes.yaml.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.content.schemas import Recipe
from oathforge.database.models import Character
from oathforge.i18n import t
from oathforge.services import characters, inventory, professions
from oathforge.services.events import Outcome

LOW_RANK_GAP = 2  # a recipe this many ranks below yours gives half XP


def recipes_here(char: Character) -> dict[str, Recipe]:
    """Recipes of your active professions and hobbies whose station is where you stand."""
    c = get_content()
    stations = set(c.locations[char.location].stations)
    mine = professions.usable(char)
    return {k: r for k, r in c.recipes.items()
            if r.profession in mine and c.professions[r.profession].station in stations}


async def missing(session: AsyncSession, char: Character, recipe: Recipe) -> dict[str, int]:
    """Ingredients still needed: item -> how many are missing."""
    out = {}
    for item, qty in recipe.ingredients.items():
        have = await inventory.count(session, char, item)
        if have < qty:
            out[item] = qty - have
    return out


async def craft(session: AsyncSession, char: Character, recipe_key: str) -> Outcome:
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    recipe = c.recipes.get(recipe_key)
    if recipe is None:
        return Outcome.refused("craft.err.unknown")
    prof = c.professions[recipe.profession]
    if recipe.profession not in professions.usable(char):
        return Outcome.refused("craft.err.not_your_profession", prof=prof.name.model_dump())
    if prof.station not in c.locations[char.location].stations:
        return Outcome.refused("craft.err.no_station", station={lang: t(lang, f"station.{prof.station}")
                                                                for lang in ("es", "en")})
    rank = professions.rank(char, recipe.profession)
    if rank < recipe.min_rank:
        return Outcome.refused("craft.err.rank", prof=prof.name.model_dump(), rank=recipe.min_rank)
    lacking = await missing(session, char, recipe)
    if lacking:
        return Outcome.refused("craft.err.missing", items=_items_text(lacking))
    for item, qty in recipe.ingredients.items():  # checked above, under the character's row lock
        if not await inventory.remove_item(session, char, item, qty):
            raise RuntimeError(f"ingredient {item} vanished while crafting")  # rolls the transaction back
    out = Outcome()
    for item, qty in recipe.outputs.items():
        await inventory.add_item(session, char, item, qty, crafted_by=char.id)
        out.add("craft.made", item=c.items[item].name.model_dump(), qty=qty)
    xp = recipe.xp // 2 if rank - recipe.min_rank >= LOW_RANK_GAP else recipe.xp
    professions.grant_xp(char, recipe.profession, xp, out)
    return out


def _items_text(items: dict[str, int]) -> dict:
    c = get_content()
    return {lang: ", ".join(f"{q} × {c.items[k].name.get(lang)}" for k, q in items.items()) for lang in ("es", "en")}
