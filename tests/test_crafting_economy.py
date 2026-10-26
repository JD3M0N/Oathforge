"""The crafting catalogue as an economy: no ingredient without a source, no money machine, no dead end."""

from oathforge.content import get_content
from oathforge.services import crafting, inventory


def sources_of(key: str) -> set[str]:
    """Where an item can come from: the field, a recipe, a creature, a shop or a mission."""
    c = get_content()
    out = set()
    if any(r.item == key for loc in c.locations.values() for g in loc.gathering for r in g.resources):
        out.add("field")
    if any(key in r.outputs for r in c.recipes.values()):
        out.add("recipe")
    if any(x.item == key for m in c.monsters.values() for x in [*m.loot, *m.harvest]):
        out.add("creature")
    if any(n.shop and key in n.shop.items for n in c.npcs.values()):
        out.add("shop")
    if any(
        key in (eff.get("give_item") or {})
        for q in c.quests.values()
        for eff in [*q.rewards, *(e for a in q.actions.values() for e in a.effects)]
    ):
        out.add("quest")
    return out


def test_every_ingredient_can_be_obtained():
    missing = {i for r in get_content().recipes.values() for i in r.ingredients if not sources_of(i)}
    assert not missing, f"ingredients with nowhere to come from: {sorted(missing)}"


def test_no_recipe_eats_its_own_output():
    for key, r in get_content().recipes.items():
        assert not set(r.ingredients) & set(r.outputs), f"{key} asks for what it makes"


def test_a_t0_recipe_never_depends_on_another_trade_without_a_way_out():
    """You must be able to keep working alone: what another trade makes has to be buyable or gatherable."""
    c = get_content()
    for key, r in c.recipes.items():
        if r.tier or r.quest:
            continue
        for item in r.ingredients:
            makers = {c.recipes[rk].profession for rk in c.recipes if item in c.recipes[rk].outputs}
            others = makers - {r.profession} - set(crafting.gathering.MASTERIES)
            if others and makers == others:  # only another trade makes it
                assert sources_of(item) - {"recipe"}, f"{key} needs {item}, and only another trade has it"


def test_crafting_never_turns_coins_into_more_coins():
    """Buying the ingredients at a shop and selling what they make must not pay for itself."""
    c = get_content()
    for key, r in c.recipes.items():
        if not all(sources_of(i) & {"shop"} for i in r.ingredients):
            continue  # it cannot be bought outright, so there is no cycle to close
        cost = sum(c.items[i].value * q for i, q in r.ingredients.items())
        back = sum(inventory.sell_price(o, 0) * q for o, q in r.outputs.items())
        assert back <= cost, f"{key} turns {cost} gold of shopping into {back} gold of selling"


def test_t1_combat_gear_asks_for_a_level_the_crafter_may_not_have():
    """The deal of T1: a low-level artisan forges it, and nobody wears it before its time."""
    c = get_content()
    gear = [o for k, r in c.recipes.items() if r.tier for o in r.outputs if c.items[o].slot or c.items[o].heal]
    assert gear, "T1 should have something to wear or drink"
    assert all(c.items[o].min_level > 1 for o in gear), [o for o in gear if c.items[o].min_level == 1]
    # and nothing that is used by rank (tools, furniture, materials) carries a level
    for key, r in c.recipes.items():
        for out_key in r.outputs:
            item = c.items[out_key]
            if item.tool or item.type == "material":
                assert item.min_level == 1, f"{out_key} is used by rank, it should ask for no level"
