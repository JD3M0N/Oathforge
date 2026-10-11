"""Loads and cross-validates the YAML content. Fails fast at startup."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from oathforge.config import CONTENT_DIR
from oathforge.content.media import MediaCatalog, scan_images
from oathforge.content.schemas import (
    ABILITIES,
    AbilityInfo,
    Background,
    Continent,
    Faction,
    GameClass,
    Item,
    Lineage,
    Location,
    Monster,
    Npc,
    Quest,
    Skill,
    Zone,
)

EFFECT_KINDS = {
    "give_item", "take_item", "gold", "reputation", "set_flag", "xp",
    "npc_memory", "trust", "damage", "world_rumor",
}


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


def _read(directory: Path, name: str) -> dict:
    return _read_file(directory / f"{name}.yaml")


def _read_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


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


def _parse(model, raw: dict) -> dict:
    return {key: model.model_validate(value) for key, value in raw.items()}


def load_content(directory: Path = CONTENT_DIR) -> Content:
    rules = _read(directory, "abilities")
    world = load_world(directory)
    locations = world.locations
    respawn = [k for k, loc in locations.items() if loc.respawn]
    content = Content(
        abilities=_parse(AbilityInfo, rules["abilities"]),
        skills=_parse(Skill, rules["skills"]),
        lineages=_parse(Lineage, _read(directory, "lineages")),
        backgrounds=_parse(Background, _read(directory, "backgrounds")),
        classes=_parse(GameClass, _read(directory, "classes")),
        items=_parse(Item, _read(directory, "items")),
        monsters=_parse(Monster, _read(directory, "monsters")),
        locations=locations,
        npcs=_parse(Npc, _read(directory, "npcs")),
        factions=_parse(Faction, _read(directory, "factions")),
        quests=_parse(Quest, _read(directory, "quests")),
        continents=world.continents,
        zones=world.zones,
        media=world.media,
        start_location=world.start,
        respawn_location=respawn[0] if respawn else world["start"],
    )
    validate_references(content)
    return content


def validate_references(c: Content) -> None:
    errors: list[str] = []

    def need(kind: str, key: str | None, pool: dict, where: str) -> None:
        if key is not None and key not in pool:
            errors.append(f"{where}: unknown {kind} '{key}'")

    if sorted(c.abilities) != sorted(ABILITIES):
        errors.append("abilities.yaml must define exactly the six abilities")
    need("location", c.start_location, c.locations, "locations.start")
    for key, lin in c.lineages.items():
        for s in lin.skills:
            need("skill", s, c.skills, f"lineage {key}")
        for a in lin.bonuses:
            need("ability", a, c.abilities, f"lineage {key}")
    for key, bg in c.backgrounds.items():
        for s in bg.skills:
            need("skill", s, c.skills, f"background {key}")
        for i in bg.items:
            need("item", i, c.items, f"background {key}")
    for key, cls in c.classes.items():
        for s in cls.skills:
            need("skill", s, c.skills, f"class {key}")
        for i in [*cls.items, *cls.equip]:
            need("item", i, c.items, f"class {key}")
        need("ability", cls.primary, c.abilities, f"class {key}")
    for key, item in c.items.items():
        if item.type == "weapon" and item.weapon is None:
            errors.append(f"item {key}: weapon without stats")
        if item.type in ("weapon", "armor", "shield") and item.slot is None:
            errors.append(f"item {key}: equippable without slot")
    for key, mon in c.monsters.items():
        for loot in mon.loot:
            need("item", loot.item, c.items, f"monster {key}")
    for key, loc in c.locations.items():
        if loc.hub and c.zones[loc.zone].kind != "city":
            errors.append(f"location {key}: hub outside a city zone")
        for ex in loc.exits:
            need("location", ex.to, c.locations, f"location {key} exit")
        for enc in [*loc.encounters, *loc.fixed_encounters]:
            for m in enc.monsters:
                need("monster", m, c.monsters, f"location {key} encounter")
        for okey, obj in loc.scene_objects.items():
            need("skill", obj.skill, c.skills, f"location {key} object {okey}")
        for dkey, disc in loc.discoveries.items():
            need("skill", disc.skill, c.skills, f"location {key} discovery {dkey}")
            for i in disc.gives:
                need("item", i, c.items, f"location {key} discovery {dkey}")
    for zkey, zone in c.zones.items():
        if c.media.zones.get(zkey) and not any(loc.hub for loc in c.locations.values() if loc.zone == zkey):
            errors.append(f"zone {zkey}: has images but no hub location to show them from")
    for key, npc in c.npcs.items():
        need("faction", npc.faction, c.factions, f"npc {key}")
        for loc in npc.schedule.values():
            need("location", loc, c.locations, f"npc {key} schedule")
        if npc.shop:
            for i in npc.shop.items:
                need("item", i, c.items, f"npc {key} shop")
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
        for where, effects in effect_lists:
            for eff in effects:
                _validate_effect(c, eff, where, errors)
        for skey, stage in quest.stages.items():
            for lkey in stage.location_text:
                need("location", lkey, c.locations, f"quest {key} stage {skey}")

    if errors:
        raise ValueError("Content validation failed:\n  " + "\n  ".join(errors))


def _validate_effect(c: Content, eff: dict, where: str, errors: list[str]) -> None:
    if len(eff) != 1:
        errors.append(f"{where}: effect must have exactly one key: {eff}")
        return
    (kind, arg), = eff.items()
    if kind not in EFFECT_KINDS:
        errors.append(f"{where}: unknown effect '{kind}'")
    elif kind in ("give_item", "take_item"):
        for item in arg:
            if item not in c.items:
                errors.append(f"{where}: unknown item '{item}'")
    elif kind == "reputation":
        for fac in arg:
            if fac not in c.factions:
                errors.append(f"{where}: unknown faction '{fac}'")
    elif kind in ("npc_memory", "trust"):
        if arg.get("npc") not in c.npcs:
            errors.append(f"{where}: unknown npc in {kind}")


@lru_cache
def get_content() -> Content:
    return load_content()
