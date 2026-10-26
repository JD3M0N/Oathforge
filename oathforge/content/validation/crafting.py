"""Recipes, professions, field specializations and where each profession is taught."""

from typing import TYPE_CHECKING

from oathforge.content.validation.common import collector
from oathforge.engine.gathering import GATHER_SKILLS, MASTERIES

if TYPE_CHECKING:
    from oathforge.content.loader import Content


def crafting_errors(c: "Content") -> list[str]:
    """Every recipe can be made somewhere; every profession has a station or a practice and one teacher."""
    errors, need = collector()
    stations = {s for loc in c.locations.values() for s in loc.stations}
    for key, recipe in c.recipes.items():
        if recipe.profession not in c.professions and recipe.profession not in MASTERIES:
            errors.append(f"recipe {key}: '{recipe.profession}' is neither a profession nor a field mastery")
        elif recipe.profession in MASTERIES and recipe.station is None:
            errors.append(f"recipe {key}: a mastery recipe needs its own station")
        station = recipe.station or (
            c.professions[recipe.profession].station if recipe.profession in c.professions else None
        )
        if station is None:
            errors.append(f"recipe {key}: no station (neither its own nor its discipline's)")
        elif station not in stations:
            errors.append(f"recipe {key}: no location has a '{station}'")
        for i in [*recipe.ingredients, *recipe.outputs]:
            need("item", i, c.items, f"recipe {key}")
        if not recipe.ingredients or not (recipe.outputs or recipe.installs):
            errors.append(f"recipe {key}: needs ingredients, and outputs or installs")
        if any(q <= 0 for q in [*recipe.ingredients.values(), *recipe.outputs.values()]):
            errors.append(f"recipe {key}: quantities must be positive")
        if recipe.quest is not None:
            need("quest", recipe.quest, c.quests, f"recipe {key}")
        if recipe.technique is not None:
            techniques = c.professions[recipe.profession].techniques if recipe.profession in c.professions else {}
            if recipe.technique not in techniques:
                errors.append(f"recipe {key}: unknown technique '{recipe.technique}' for {recipe.profession}")
            elif techniques[recipe.technique].rank > recipe.min_rank:
                errors.append(
                    f"recipe {key}: its technique unlocks at rank {techniques[recipe.technique].rank}, "
                    f"after the recipe's own {recipe.min_rank}"
                )
        if recipe.special and recipe.technique is not None:
            errors.append(f"recipe {key}: a special recipe comes from a blueprint, not from a technique")
        if recipe.special and not any(i.teaches == key for i in c.items.values()):
            errors.append(f"recipe {key}: special, but no blueprint teaches it")
    for key, prof in c.professions.items():
        if prof.station is None and prof.practice is None:
            errors.append(f"profession {key}: needs a station or a practice")
        if prof.station is not None and prof.station not in stations:
            errors.append(f"profession {key}: no location has a '{prof.station}'")
        if prof.practice is not None and (prof.practice not in GATHER_SKILLS or not prof.hobby):
            errors.append(f"profession {key}: practice '{prof.practice}' must be a gathering skill of a hobby")
    if not any(loc.home for loc in c.locations.values()) and any(r.installs for r in c.recipes.values()):
        errors.append("recipes install furniture, but no location grants rooms (home: true)")
    branches: dict[str, list[str]] = {}
    for key, spec in c.specializations.items():
        if spec.skill not in GATHER_SKILLS:
            errors.append(f"specialization {key}: '{spec.skill}' is not a field discipline")
        branches.setdefault(spec.skill, []).append(key)
    for skill, keys in branches.items():
        if len(keys) != 2:
            errors.append(f"specialization {skill}: it must have exactly two branches, not {len(keys)}")
    for skill in GATHER_SKILLS:
        if c.specializations and skill not in branches:
            errors.append(f"specialization {skill}: this discipline has no branches")
    taught: dict[str, list[str]] = {}
    for key, loc in c.locations.items():
        if loc.teaches is None:
            continue
        if loc.teaches not in c.professions:
            errors.append(f"location {key}: teaches unknown profession '{loc.teaches}'")
        elif c.professions[loc.teaches].hobby:
            errors.append(f"location {key}: '{loc.teaches}' is a hobby, nobody needs to teach it")
        else:
            taught.setdefault(loc.teaches, []).append(key)
    for key, places in taught.items():
        if len(places) > 1:
            errors.append(f"profession {key}: taught in more than one place ({', '.join(sorted(places))})")
    for key, prof in c.professions.items():
        if not prof.hobby and key not in taught:
            errors.append(f"profession {key}: no stall teaches it")
    return errors
