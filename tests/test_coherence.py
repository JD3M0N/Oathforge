"""The content holds together as a game: every item can be had, every monster lives somewhere, every NPC
stands somewhere, and gear does not get cheaper as it gets better. `oath validate` checks that references
exist; these check that nothing is left out of the game."""

from collections import defaultdict

from oathforge.content import get_content


def _given(effects: list[dict]) -> set[str]:
    return {item for e in effects for kind, arg in e.items() if kind == "give_item" for item in arg}


def item_sources() -> dict[str, set[str]]:
    """item -> how a player can get it: shop, loot, recipe, gathering, discovery, quest or starting kit."""
    c = get_content()
    found: dict[str, set[str]] = defaultdict(set)
    for npc in c.npcs.values():
        for item in npc.shop.items if npc.shop else []:
            found[item].add("shop")
    for monster in c.monsters.values():
        for drop in [*monster.loot, *monster.harvest]:
            found[drop.item].add("loot")
    for recipe in c.recipes.values():
        for item in recipe.outputs:
            found[item].add("recipe")
    for loc in c.locations.values():
        for g in loc.gathering:
            for r in g.resources:
                found[r.item].add("gathering")
        for d in loc.discoveries.values():
            for item in d.gives:
                found[item].add("discovery")
    for quest in c.quests.values():
        given = _given(quest.rewards)
        for action in quest.actions.values():
            given |= _given(action.effects)
            if action.check:
                given |= _given(action.check.success_effects) | _given(action.check.failure_effects)
        for trigger in quest.triggers:
            given |= _given(trigger.effects)
        for item in given:
            found[item].add("quest")
    for kit in [*(b.items for b in c.backgrounds.values()), *([*k.items, *k.equip] for k in c.classes.values())]:
        for item in kit:
            found[item].add("starting kit")
    return found


def test_every_item_can_be_obtained():
    missing = sorted(set(get_content().items) - set(item_sources()))
    assert not missing, f"no shop, loot, recipe, place or quest gives these: {missing}"


def test_every_monster_lives_somewhere():
    c = get_content()
    placed = {
        m
        for loc in c.locations.values()
        for table in (loc.encounters, loc.night_encounters, loc.fixed_encounters)
        for enc in table
        for m in enc.monsters
    }
    missing = sorted(set(c.monsters) - placed)
    assert not missing, f"no encounter table or fixed fight has these: {missing}"


def test_every_npc_stands_somewhere():
    c = get_content()
    nowhere = sorted(k for k, npc in c.npcs.items() if not npc.schedule)
    assert not nowhere, f"these NPCs have no schedule, so no place shows them: {nowhere}"


def test_better_gear_is_never_cheaper():
    """Within the same kind of gear (type and slot), a higher min_level never costs less."""
    groups: dict[tuple, list] = defaultdict(list)
    for key, item in get_content().items.items():
        if item.type in ("weapon", "armor", "shield") and item.value:
            groups[(item.type, item.slot)].append((item.min_level, item.value, key))
    cheaper = [
        f"{high[2]} (level {high[0]}, {high[1]} gold) < {low[2]} (level {low[0]}, {low[1]} gold)"
        for gear in groups.values()
        for low in gear
        for high in gear
        if high[0] > low[0] and high[1] < low[1]
    ]
    assert not cheaper, "higher-level gear for less gold:\n" + "\n".join(cheaper)
