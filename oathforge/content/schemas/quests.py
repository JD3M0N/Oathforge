"""Quests: checks, actions, triggers, stages and objectives."""

from typing import Literal

from oathforge.content.schemas.common import Strict, Text, Tier


Effect = dict[str, object]  # validated by quests.apply_effect at load time


class QuestCheck(Strict):
    skill: str
    tier: Tier
    success_text: Text
    failure_text: Text
    success_effects: list[Effect] = []
    failure_effects: list[Effect] = []


class QuestAction(Strict):
    label: Text
    text: Text
    location: str | None = None
    npc: str | None = None
    stages: list[str]
    requires_item: str | None = None
    # a replacement handed out only while you have neither the material nor what it was for
    unless_item: str | None = None
    unless_furniture: Literal["bed", "chest"] | None = None
    check: QuestCheck | None = None
    effects: list[Effect] = []
    to_stage: str


class QuestTrigger(Strict):
    event: Literal["defeat"]
    target: str
    stages: list[str]
    to_stage: str
    text: Text
    effects: list[Effect] = []


class QuestStage(Strict):
    journal: Text
    # ready: every objective is met and the giver is owed the mission; nothing is paid until then
    state: Literal["locked", "available", "active", "ready", "completed", "failed"] = "active"
    location_text: dict[str, Text] = {}


class QuestObjective(Strict):
    """Counted goal of a mission: kill `count` monsters, talk to an NPC, reach a place, gather, skin or craft
    `count` of an item, finish a long rest, get healed or open a /rulebook section."""

    # kill: monster · talk: npc · visit: location · gather / skin / craft: item obtained (counts quantity)
    # rest / heal: location, or "any" (a long rest that ends / the chapel healer) · read: rulebook section
    # hunt: location (or "any"): a fight won from 🏹 Hunt or 🐾 Track there, any creature, day or night
    # equip / buy / sell / stash / take: item (or "any") · learn_profession: profession · blueprint: the blueprint item
    # smoke: a fight left with a smoke bomb ("any") · branch: the class branch taken (or "any")
    kind: Literal["kill", "hunt", "talk", "visit", "gather", "skin", "craft", "rest", "heal", "read",
                  "equip", "learn_profession", "stash", "take", "buy", "sell", "smoke", "branch", "blueprint",
                  "short_rest"]
    target: str  # monster, npc, location, item or rulebook section key ("any" for hunt / rest / heal)
    count: int = 1


class Quest(Strict):
    name: Text
    summary: Text
    start_stage: str
    # a character who completed any of these (old, removed) quests gets this one completed, without rewards
    legacy_done: list[str] = []
    stages: dict[str, QuestStage]
    actions: dict[str, QuestAction] = {}
    triggers: list[QuestTrigger] = []
    # missions: the journal lists them by `order`; a locked mission opens at `unlock_stage`
    # once the `after` mission is completed or the `unlock_flag` is set
    order: int = 100
    # a tutorial mission (counted by `oath tutorial-stats`); its activities take their real time
    tutorial: bool = False
    giver: str | None = None  # npc
    hint: Text | None = None
    after: str | None = None
    unlock_flag: str | None = None
    unlock_profession: str | None = None  # opens while the hero practises this trade
    unlock_stage: str | None = None
    # all objectives met on `objective_stage` -> rewards, then `complete_stage`.
    # With `turn_in_stage` the mission stops there instead, waiting for `giver` to be paid in person:
    # handing it in pays the rewards and moves it to `complete_stage`, all at once (roadmap_balance §8.1).
    objectives: list[QuestObjective] = []
    objective_stage: str | None = None
    turn_in_stage: str | None = None
    complete_stage: str | None = None
    rewards: list[Effect] = []
