"""The world: guide and articles, rulebook, places, zones, continents, NPCs, shops and factions."""

from typing import Literal

from pydantic import Field

from oathforge.content.schemas.common import Station, Strict, Text, Tier
from oathforge.content.schemas.monsters import StatusApply


class WorldGuide(Strict):
    summary: Text
    setting: Text
    society: Text
    technology: Text
    magic: Text
    backgrounds: Text

    def context(self, lang: str) -> str:
        return "\n".join((
            self.summary.get(lang), self.setting.get(lang), self.society.get(lang),
            self.technology.get(lang), self.magic.get(lang), self.backgrounds.get(lang),
        ))


class Article(Strict):
    """The article before a place's name in a sentence; empty where the language uses none ("Crownreach Market")."""
    es: str = ""
    en: str = ""


class SceneEffect(Strict):
    damage: str | None = None
    damage_type: str = "bludgeoning"
    targets: Literal["one", "all_enemies"] = "one"
    status: StatusApply | None = None


class SceneObject(Strict):
    name: Text
    description: Text
    skill: str
    tier: Tier
    effect: SceneEffect


class Exit(Strict):
    to: str
    minutes: int = 10  # game minutes on foot: the edge weight of the world graph
    danger: int = Field(0, ge=0, le=3)
    requires_flag: str | None = None
    yards: int | None = Field(None, gt=0)  # distance when the terrain is slow; else minutes × walking pace


class EncounterEntry(Strict):
    monsters: list[str]
    weight: int = 1
    min_level: int = 1  # packs of two start later, so the first levels fight one creature at a time


class FixedEncounter(Strict):
    monsters: list[str]
    flag: str  # set when cleared, so it only happens once per character
    unless_flag: str | None = None
    if_flag: str | None = None


class Discovery(Strict):
    skill: str
    tier: Tier
    text: Text
    sets_flag: str
    gives: dict[str, int] = {}
    gold: int = 0
    requires_flag: str | None = None


class GatherResource(Strict):
    item: str
    weight: int = 1
    min_rank: int = Field(0, ge=0, le=5)  # mastery rank needed to find it


class Gathering(Strict):
    """A field activity here: "Gather" (5 min, safe) and "Stay" (15 min, more loot, may end in an ambush)."""

    skill: Literal["mining", "woodcutting", "herbalism", "fishing"]
    tool: str | None = None  # item needed in the inventory
    resources: list[GatherResource]
    stay_ambush: float = Field(0.0, ge=0, le=1)  # the ambushers come from the place's encounter table


class Healer(Strict):
    cost: int
    heal: str  # dice


class Location(Strict):
    name: Text
    article: Article | None = None  # {es: el, en: the}: «Llegas al Mercado», "You reach the Old Pass Mine"
    description: Text
    night: Text | None = None
    kind: Literal["city", "wild", "dungeon"]
    exits: list[Exit]
    encounters: list[EncounterEntry] = []
    night_encounters: list[EncounterEntry] = []  # replaces `encounters` at night when not empty
    hunting: bool = False  # shows "Hunt" (a fight now) and "Track" (5 min, tracking XP and trophies)
    hunt_day: Text | None = None  # the line before a hunt here; without it a generic one is used
    hunt_night: Text | None = None
    gathering: list[Gathering] = []
    stations: list[Station] = []  # crafting stations here: "Craft" in the scene
    teaches: str | None = None  # the profession learned and swapped here, with its master (one stall per trade)
    home: bool = False  # it grants rooms: your bed and your chest are here
    fixed_encounters: list[FixedEncounter] = []
    scene_objects: dict[str, SceneObject] = {}
    discoveries: dict[str, Discovery] = {}
    rest_cost: int | None = None  # long rest (8 game hours) at an inn
    healer: Healer | None = None  # "Cure wounds" for a few coins (the chapel)
    respawn: bool = False
    hub: bool = False  # the city's plaza: "View city" when the zone has images, and the only way out of the city
    # filled by the loader from the folder: world/<continent>/<zone>/<location>/place.yaml
    zone: str = ""
    continent: str = ""

    def phrase(self) -> dict:
        """The name inside a sentence, with its article: {"es": "el Mercado de Crownreach", "en": "Crownreach Market"}.
        The translator joins «a el» into «al» and «de el» into «del»."""
        return {lang: f"{getattr(self.article, lang) if self.article else ''} {self.name.get(lang)}".strip()
                for lang in ("es", "en")}


class RuleSection(Strict):
    """A page of /rulebook (content/rulebook.yaml)."""
    icon: str
    title: Text
    body: Text  # plain text: it is escaped; /commands in it stay tappable


class Zone(Strict):
    """A city, a wild area or a dungeon: a group of locations sharing images and audio."""

    name: Text
    description: Text
    night: Text | None = None
    kind: Literal["city", "wilds", "dungeon"]


class Continent(Strict):
    name: Text
    description: Text


class Shop(Strict):
    items: list[str]
    buys: bool = True


class Npc(Strict):
    name: Text
    title: Text
    faction: str | None = None
    schedule: dict[Literal["day", "night"], str]
    greeting: Text
    greeting_return: Text | None = None  # instead of `greeting` once the hero has finished one of their missions
    persona: str
    goals: str
    secrets: str
    knowledge: str
    passive_perception: int = 10
    steal_gold: str | None = None
    shop: Shop | None = None


class Faction(Strict):
    name: Text
    description: Text
