"""Free text -> structured Intent. The engine validates every id afterwards."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from oathforge.ai.client import LLM
from oathforge.ai.prompts import INTENT_SYSTEM

IntentType = Literal[
    "move",
    "talk",
    "attack",
    "use_item",
    "skill_check",
    "inspect",
    "steal",
    "rest",
    "quest_action",
    "environment_interaction",
    "ability",
    "defend",
    "flee",
    "ooc_question",
    "narrate_only",
]
TierName = Literal["trivial", "easy", "medium", "hard", "very_hard"]


class Intent(BaseModel):
    type: IntentType
    target: str | None = Field(None, description="id from CONTEXT: exit, npc, enemy, item, quest action or object")
    weapon: str | None = Field(None, description="weapon id from CONTEXT (combat only)")
    ability: str | None = Field(None, description="ability id from CONTEXT (combat only)")
    skill: str | None = Field(None, description="skill id for skill_check / environment_interaction")
    tier: TierName | None = None
    approach: str = ""


@dataclass
class ActionContext:
    """Everything the interpreter may reference. Keys are ids, values are display names."""

    lang: str
    character: str
    location: str
    in_combat: bool = False
    exits: dict[str, str] = field(default_factory=dict)
    npcs: dict[str, str] = field(default_factory=dict)
    items: dict[str, str] = field(default_factory=dict)
    quest_actions: dict[str, str] = field(default_factory=dict)
    skills: dict[str, str] = field(default_factory=dict)
    enemies: dict[str, str] = field(default_factory=dict)
    weapons: dict[str, str] = field(default_factory=dict)
    abilities: dict[str, str] = field(default_factory=dict)
    objects: dict[str, str] = field(default_factory=dict)
    scene: str = ""

    def render(self) -> str:
        def block(title: str, d: dict[str, str]) -> str:
            return f"{title}:\n" + ("\n".join(f"  - {k}: {v}" for k, v in d.items()) or "  (none)")

        parts = [f"Character: {self.character}", f"Location: {self.location}", f"Scene: {self.scene}"]
        if self.in_combat:
            parts += [
                "MODE: COMBAT. Allowed types: attack, ability, use_item, defend, flee, environment_interaction, "
                "ooc_question, narrate_only.",
                block("Enemies (target ids)", self.enemies),
                block("Weapons", self.weapons),
                block("Abilities", self.abilities),
                block("Scene objects usable in combat", self.objects),
                block("Inventory items", self.items),
            ]
        else:
            parts += [
                "MODE: EXPLORATION. Allowed types: move, talk, attack, use_item, skill_check, inspect, steal, rest, "
                "quest_action, environment_interaction, ooc_question, narrate_only.",
                block("Exits (move targets)", self.exits),
                block("People here (talk/steal targets)", self.npcs),
                block("Inventory items", self.items),
                block("Story actions available (quest_action targets)", self.quest_actions),
                block("Skills", self.skills),
            ]
        return "\n".join(parts)


COMBAT_TYPES = {
    "attack",
    "ability",
    "use_item",
    "defend",
    "flee",
    "environment_interaction",
    "ooc_question",
    "narrate_only",
}
EXPLORE_TYPES = {
    "move",
    "talk",
    "attack",
    "use_item",
    "skill_check",
    "inspect",
    "steal",
    "rest",
    "quest_action",
    "environment_interaction",
    "ooc_question",
    "narrate_only",
}


def validate(intent: Intent, ctx: ActionContext) -> Intent:
    """Reject anything that references ids outside the context. Returns narrate_only if invalid."""
    allowed = COMBAT_TYPES if ctx.in_combat else EXPLORE_TYPES
    if intent.type not in allowed:
        return Intent(type="narrate_only", approach=intent.approach)
    pools = {
        "move": ctx.exits,
        "talk": ctx.npcs,
        "steal": ctx.npcs,
        "use_item": ctx.items,
        "quest_action": ctx.quest_actions,
    }
    if ctx.in_combat:
        pools.update(attack=ctx.enemies)
    if intent.type in pools and intent.target not in pools[intent.type]:
        return Intent(type="narrate_only", approach=intent.approach)
    if not ctx.in_combat and intent.type == "attack":
        return Intent(type="narrate_only", approach=intent.approach)
    if intent.type in ("skill_check", "environment_interaction") and not ctx.in_combat:
        if intent.skill not in ctx.skills:
            return Intent(type="narrate_only", approach=intent.approach)
    if ctx.in_combat:
        if intent.type == "ability" and intent.ability not in ctx.abilities:
            return Intent(type="narrate_only", approach=intent.approach)
        if intent.type == "attack" and intent.weapon not in ctx.weapons:
            intent = intent.model_copy(update={"weapon": next(iter(ctx.weapons), None)})
        if intent.type == "environment_interaction" and intent.target not in ctx.objects:
            return Intent(type="narrate_only", approach=intent.approach)
        if intent.type == "ability" and intent.target is not None and intent.target not in ctx.enemies:
            intent = intent.model_copy(update={"target": None})
    return intent


async def parse(llm: LLM, ctx: ActionContext, text: str, user_id: int | None) -> Intent | None:
    prompt = f"CONTEXT\n{ctx.render()}\n\n<player_text>\n{text[:600]}\n</player_text>"
    intent = await llm.json(tier="fast", system=INTENT_SYSTEM, prompt=prompt, schema=Intent, user_id=user_id)
    return validate(intent, ctx) if intent else None
