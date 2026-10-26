"""Loads the YAML content and cross-validates it (``validation/``). Fails fast at startup."""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from oathforge.config import CONTENT_DIR
from oathforge.content.achievement_schemas import Achievement, validate_catalog
from oathforge.content.media import MediaCatalog, scan_images
from oathforge.content.schemas import (
    AbilityInfo,
    Background,
    ClassSpecialization,
    Continent,
    EntityDef,
    Faction,
    FormDef,
    GameClass,
    Item,
    Lineage,
    Location,
    Monster,
    Npc,
    Profession,
    Progression,
    Quest,
    Recipe,
    RuleSection,
    Skill,
    Specialization,
    Text,
    WorldGuide,
    Zone,
)
from oathforge.content.validation import validate_references


@dataclass(frozen=True)
class Content:
    abilities: dict[str, AbilityInfo]
    skills: dict[str, Skill]
    lineages: dict[str, Lineage]
    backgrounds: dict[str, Background]
    classes: dict[str, GameClass]
    items: dict[str, Item]
    monsters: dict[str, Monster]
    locations: dict[str, Location]
    npcs: dict[str, Npc]
    factions: dict[str, Faction]
    quests: dict[str, Quest]
    continents: dict[str, Continent]
    zones: dict[str, Zone]
    media: MediaCatalog
    start_location: str
    respawn_location: str
    world_guide: WorldGuide
    progression: Progression  # XP table, milestone gates and class resources
    achievements: dict[str, Achievement] = field(default_factory=dict)
    chronicles: dict[str, list[Text]] = field(default_factory=dict)  # = fallbacks["chronicles"]
    # generic texts when Gemini is down or out of budget: content/fallbacks/<category>.yaml -> key -> texts
    fallbacks: dict[str, dict[str, list[Text]]] = field(default_factory=dict)
    professions: dict[str, Profession] = field(default_factory=dict)
    recipes: dict[str, Recipe] = field(default_factory=dict)
    specializations: dict[str, Specialization] = field(default_factory=dict)  # two branches per mastery
    class_specializations: dict[str, ClassSpecialization] = field(default_factory=dict)  # the 41 class branches
    entities: dict[str, EntityDef] = field(default_factory=dict)  # summons, servants, beasts, devices
    forms: dict[str, FormDef] = field(default_factory=dict)  # shapes (Shapeshifter)
    rulebook: dict[str, RuleSection] = field(
        default_factory=dict
    )  # /rulebook pages, in order  # outcome -> generic texts when the AI chronicler is not used


def _read_fallbacks(directory: Path) -> dict[str, dict[str, list[Text]]]:
    return {
        path.stem: {k: [Text.model_validate(v) for v in vs] for k, vs in _read_file(path).items()}
        for path in sorted((directory / "fallbacks").glob("*.yaml"))
    }


def _read(directory: Path, name: str) -> dict:
    return _read_file(directory / f"{name}.yaml")


class UniqueLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _read_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh, Loader=UniqueLoader) or {}


@dataclass(frozen=True)
class World:
    start: str
    continents: dict[str, Continent]
    zones: dict[str, Zone]
    locations: dict[str, Location]
    media: MediaCatalog


def load_world(directory: Path) -> World:
    """Walks world/<continent>/<zone>/<location>/place.yaml into flat dicts keyed by id."""
    root = directory / "world"
    meta = _read_file(root / "world.yaml")
    continents: dict[str, Continent] = {}
    zones: dict[str, Zone] = {}
    locations: dict[str, Location] = {}
    media = MediaCatalog()
    errors: list[str] = []
    for ckey in meta["continents"]:
        cdir = root / ckey
        continents[ckey] = Continent.model_validate(_read_file(cdir / "continent.yaml"))
        media.continents[ckey] = scan_images(cdir, root)
        for zdir in sorted(p for p in cdir.iterdir() if (p / "zone.yaml").is_file()):
            zkey = zdir.name
            if zkey in zones:
                errors.append(f"duplicate zone '{zkey}' in {cdir}")
            zones[zkey] = Zone.model_validate(_read_file(zdir / "zone.yaml"))
            media.zones[zkey] = scan_images(zdir, root)
            for ldir in sorted(p for p in zdir.iterdir() if (p / "place.yaml").is_file()):
                lkey = ldir.name
                if lkey in locations:
                    errors.append(f"duplicate location '{lkey}' in {zdir}")
                raw = {**_read_file(ldir / "place.yaml"), "zone": zkey, "continent": ckey}
                locations[lkey] = Location.model_validate(raw)
                media.locations[lkey] = scan_images(ldir, root)
    if errors:
        raise ValueError("World validation failed:\n  " + "\n  ".join(errors))
    return World(meta["start"], continents, zones, locations, media)


def scan_keyed_media(directory: Path, kind: str, keys: dict, into: dict) -> None:
    """Class portraits (content/classes/<class>/images/) and bestiary art (content/monsters/<monster>/images/);
    a folder must name a real class or monster."""
    root = directory / kind
    if not root.is_dir():
        return
    unknown = [d.name for d in sorted(root.iterdir()) if d.is_dir() and d.name not in keys]
    if unknown:
        raise ValueError(f"content/{kind}: folders for unknown keys {unknown}")
    for key in keys:
        into[key] = scan_images(root / key, directory)


def _parse(model, raw: dict) -> dict:
    return {key: model.model_validate(value) for key, value in raw.items()}


def load_content(directory: Path = CONTENT_DIR) -> Content:
    rules = _read(directory, "abilities")
    world = load_world(directory)
    locations = world.locations
    respawn = [k for k, loc in locations.items() if loc.respawn]
    classes = _parse(GameClass, _read(directory, "classes"))
    scan_keyed_media(directory, "classes", classes, world.media.classes)
    monsters = _parse(Monster, _read(directory, "monsters"))
    scan_keyed_media(directory, "monsters", monsters, world.media.monsters)
    fallbacks = _read_fallbacks(directory)
    content = Content(
        abilities=_parse(AbilityInfo, rules["abilities"]),
        skills=_parse(Skill, rules["skills"]),
        lineages=_parse(Lineage, _read(directory, "lineages")),
        backgrounds=_parse(Background, _read(directory, "backgrounds")),
        classes=classes,
        items=_parse(Item, _read(directory, "items")),
        monsters=monsters,
        locations=locations,
        npcs=_parse(Npc, _read(directory, "npcs")),
        factions=_parse(Faction, _read(directory, "factions")),
        quests=_parse(Quest, _read(directory, "quests")),
        continents=world.continents,
        zones=world.zones,
        media=world.media,
        start_location=world.start,
        respawn_location=respawn[0] if respawn else world.start,
        world_guide=WorldGuide.model_validate(_read_file(directory / "world" / "guide.yaml")),
        chronicles=fallbacks["chronicles"],
        fallbacks=fallbacks,
        professions=_parse(Profession, _read(directory, "professions")),
        recipes=_parse(Recipe, _read(directory, "recipes")),
        specializations=_parse(Specialization, _read(directory, "specializations")),
        class_specializations=_parse(ClassSpecialization, _read(directory, "class_specializations")),
        progression=Progression.model_validate(_read(directory, "progression")),
        entities=_parse(EntityDef, _read(directory, "entities")),
        forms=_parse(FormDef, _read(directory, "forms")),
        rulebook=_parse(RuleSection, _read(directory, "rulebook")),
        achievements=_parse(Achievement, _read(directory, "achievements")),
    )
    validate_references(content)
    validate_catalog(content)
    return content


@lru_cache
def get_content() -> Content:
    return load_content()
