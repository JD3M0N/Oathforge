"""Items: weapons, equipment, tools and blueprints, and the loot of monsters."""

from typing import TYPE_CHECKING

from oathforge.content.validation.common import collector
from oathforge.engine.gathering import GATHER_SKILLS

if TYPE_CHECKING:
    from oathforge.content.loader import Content


def item_errors(c: "Content") -> list[str]:
    """Weapons have stats and equipment a slot; tools and blueprints make sense; monster loot exists."""
    errors, need = collector()
    for key, item in c.items.items():
        if item.type == "weapon" and item.weapon is None:
            errors.append(f"item {key}: weapon without stats")
        if item.type in ("weapon", "armor", "shield") and item.slot is None:
            errors.append(f"item {key}: equippable without slot")
    for key, mon in c.monsters.items():
        for loot in [*mon.loot, *mon.harvest]:
            need("item", loot.item, c.items, f"monster {key}")
    for key, item in c.items.items():
        if item.tool is not None:
            if item.type != "tool":
                errors.append(f"item {key}: only a tool can have a tool profile")
            if item.tool.skill not in GATHER_SKILLS:
                errors.append(f"item {key}: '{item.tool.skill}' is not a field discipline")
            if item.tool.base is not None and item.tool.base not in c.items:
                errors.append(f"item {key}: it replaces an unknown tool '{item.tool.base}'")
            if not (item.tool.time_pct or item.tool.rare_rel or item.tool.extra_chance):
                errors.append(f"item {key}: a specialized tool must do something")
        if item.type == "blueprint" and item.teaches is None:
            errors.append(f"item {key}: a blueprint must say which recipe it teaches")
        if item.teaches is not None:
            if item.type != "blueprint":
                errors.append(f"item {key}: only a blueprint teaches a recipe")
            elif item.teaches not in c.recipes:
                errors.append(f"item {key}: teaches unknown recipe '{item.teaches}'")
            elif not c.recipes[item.teaches].special:
                errors.append(f"item {key}: recipe '{item.teaches}' is common, so it needs no blueprint")
    return errors
