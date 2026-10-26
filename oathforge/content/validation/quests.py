"""Quests: stages, actions, triggers, objectives and their effects."""

from typing import TYPE_CHECKING

from oathforge.content.validation.common import collector

if TYPE_CHECKING:
    from oathforge.content.loader import Content

EFFECT_KINDS = {
    "give_item",
    "take_item",
    "gold",
    "reputation",
    "set_flag",
    "xp",
    "milestone",
    "npc_memory",
    "trust",
    "damage",
    "world_rumor",
    "profession_xp",
}


def quest_errors(c: "Content") -> list[str]:
    """Every quest points at real stages, places, NPCs, items and monsters, and its effects are valid."""
    errors, need = collector()
    for key, quest in c.quests.items():
        need("stage", quest.start_stage, quest.stages, f"quest {key}")
        effect_lists = []
        for akey, action in quest.actions.items():
            where = f"quest {key} action {akey}"
            need("location", action.location, c.locations, where)
            need("npc", action.npc, c.npcs, where)
            need("item", action.requires_item, c.items, where)
            need("stage", action.to_stage, quest.stages, where)
            for s in action.stages:
                need("stage", s, quest.stages, where)
            effect_lists.append((where, action.effects))
            if action.check:
                need("skill", action.check.skill, c.skills, where)
                effect_lists.append((where, action.check.success_effects))
                effect_lists.append((where, action.check.failure_effects))
        for trig in quest.triggers:
            where = f"quest {key} trigger {trig.target}"
            need("monster", trig.target, c.monsters, where)
            need("stage", trig.to_stage, quest.stages, where)
            for s in trig.stages:
                need("stage", s, quest.stages, where)
            effect_lists.append((where, trig.effects))
        where = f"quest {key}"
        need("npc", quest.giver, c.npcs, where)
        need("quest", quest.after, c.quests, where)
        for field in ("unlock_stage", "objective_stage", "turn_in_stage", "complete_stage"):
            need("stage", getattr(quest, field), quest.stages, f"{where} {field}")
        if quest.unlock_profession and quest.unlock_profession not in c.professions:
            errors.append(f"{where}: unknown profession '{quest.unlock_profession}'")
        if (quest.after or quest.unlock_flag or quest.unlock_profession) and quest.unlock_stage is None:
            errors.append(f"{where}: locked missions need an unlock_stage")
        if quest.objectives and (quest.objective_stage is None or quest.complete_stage is None):
            errors.append(f"{where}: objectives need objective_stage and complete_stage")
        if quest.turn_in_stage is not None:
            if quest.giver is None:
                errors.append(f"{where}: a mission you hand in needs a giver to hand it to")
            if quest.stages[quest.turn_in_stage].state != "ready":
                errors.append(f"{where}: stage '{quest.turn_in_stage}' pays on turn-in, so its state must be 'ready'")
        for skey, stage in quest.stages.items():
            if stage.state == "ready" and quest.turn_in_stage != skey:
                errors.append(f"{where} stage {skey}: 'ready' is only for the mission's turn_in_stage")
        # a craft objective may also name furniture a starter recipe installs ("furniture:bed")
        furniture = {f"furniture:{r.installs}": None for r in c.recipes.values() if r.installs}
        items, places = ("item", c.items), ("location", {**c.locations, "any": None})
        any_items = ("item", {**c.items, "any": None})
        pools = {
            "kill": ("monster", c.monsters),
            "talk": ("npc", c.npcs),
            "visit": ("location", c.locations),
            "hunt": places,
            "gather": items,
            "skin": items,
            "craft": ("item", {**c.items, **furniture}),
            "rest": places,
            "heal": places,
            "read": ("rulebook section", c.rulebook),
            "equip": any_items,
            "stash": any_items,
            "take": any_items,
            "buy": any_items,
            "sell": any_items,
            "learn_profession": ("profession", {**c.professions, "any": None}),
            "blueprint": items,
            "short_rest": ("target", {"any": None}),
            "smoke": ("target", {"any": None}),
            "branch": ("branch", {**c.class_specializations, "any": None}),
        }
        for obj in quest.objectives:
            need(*pools[obj.kind][:1], obj.target, pools[obj.kind][1], f"{where} objective")
        effect_lists.append((f"{where} rewards", quest.rewards))
        for where, effects in effect_lists:
            for eff in effects:
                _validate_effect(c, eff, where, errors)
        for skey, stage in quest.stages.items():
            for lkey in stage.location_text:
                need("location", lkey, c.locations, f"quest {key} stage {skey}")
    return errors


def _validate_effect(c: "Content", eff: dict, where: str, errors: list[str]) -> None:
    if len(eff) != 1:
        errors.append(f"{where}: effect must have exactly one key: {eff}")
        return
    ((kind, arg),) = eff.items()
    if kind not in EFFECT_KINDS:
        errors.append(f"{where}: unknown effect '{kind}'")
    elif kind in ("give_item", "take_item"):
        for item in arg:
            if item not in c.items:
                errors.append(f"{where}: unknown item '{item}'")
    elif kind == "profession_xp":
        for prof in arg:
            if prof not in c.professions:
                errors.append(f"{where}: unknown profession '{prof}'")
    elif kind == "milestone":
        if c.progression is None or arg not in c.progression.milestones:
            errors.append(f"{where}: unknown milestone '{arg}'")
    elif kind == "reputation":
        for fac in arg:
            if fac not in c.factions:
                errors.append(f"{where}: unknown faction '{fac}'")
    elif kind in ("npc_memory", "trust"):
        if arg.get("npc") not in c.npcs:
            errors.append(f"{where}: unknown npc in {kind}")
