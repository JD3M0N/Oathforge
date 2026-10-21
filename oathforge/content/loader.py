"""Loads and cross-validates the YAML content. Fails fast at startup."""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from string import Formatter

import yaml

from oathforge.config import CONTENT_DIR
from oathforge.content.media import MediaCatalog, scan_images
from oathforge.content.schemas import (
    ABILITIES,
    CHRONICLE_KEYS,
    FALLBACK_KEYS,
    FALLBACK_PLACEHOLDERS,
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
    Profession,
    Quest,
    Recipe,
    RuleSection,
    Skill,
    Specialization,
    Text,
    Zone,
)
from oathforge.engine.gathering import GATHER_SKILLS, MASTERIES
from oathforge.content.achievement_schemas import Achievement, validate_catalog

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
    achievements: dict[str, Achievement] = field(default_factory=dict)
    chronicles: dict[str, list[Text]] = field(default_factory=dict)  # = fallbacks["chronicles"]
    # generic texts when Gemini is down or out of budget: content/fallbacks/<category>.yaml -> key -> texts
    fallbacks: dict[str, dict[str, list[Text]]] = field(default_factory=dict)
    professions: dict[str, Profession] = field(default_factory=dict)
    recipes: dict[str, Recipe] = field(default_factory=dict)
    specializations: dict[str, Specialization] = field(default_factory=dict)  # two branches per mastery
    rulebook: dict[str, RuleSection] = field(default_factory=dict)  # /rulebook pages, in order  # outcome -> generic texts when the AI chronicler is not used


def _read_fallbacks(directory: Path) -> dict[str, dict[str, list[Text]]]:
    return {path.stem: {k: [Text.model_validate(v) for v in vs] for k, vs in _read_file(path).items()}
            for path in sorted((directory / "fallbacks").glob("*.yaml"))}


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
        chronicles=fallbacks["chronicles"],
        fallbacks=fallbacks,
        professions=_parse(Profession, _read(directory, "professions")),
        recipes=_parse(Recipe, _read(directory, "recipes")),
        specializations=_parse(Specialization, _read(directory, "specializations")),
        rulebook=_parse(RuleSection, _read(directory, "rulebook")),
        achievements=_parse(Achievement, _read(directory, "achievements")),
    )
    validate_references(content)
    validate_catalog(content)
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
        for loot in [*mon.loot, *mon.harvest]:
            need("item", loot.item, c.items, f"monster {key}")
    for key, loc in c.locations.items():
        if loc.hub and c.zones[loc.zone].kind != "city":
            errors.append(f"location {key}: hub outside a city zone")
        for ex in loc.exits:
            need("location", ex.to, c.locations, f"location {key} exit")
        for enc in [*loc.encounters, *loc.night_encounters, *loc.fixed_encounters]:
            for m in enc.monsters:
                need("monster", m, c.monsters, f"location {key} encounter")
        for okey, obj in loc.scene_objects.items():
            need("skill", obj.skill, c.skills, f"location {key} object {okey}")
        for g in loc.gathering:
            need("item", g.tool, c.items, f"location {key} gathering {g.skill}")
            for r in g.resources:
                need("item", r.item, c.items, f"location {key} gathering {g.skill}")
            if g.skill not in GATHER_SKILLS:
                errors.append(f"location {key}: unknown mastery '{g.skill}'")
            if not any(r.min_rank == 0 for r in g.resources):
                errors.append(f"location {key} gathering {g.skill}: nothing to find at rank 0")
            if g.stay_ambush and not (loc.encounters or loc.night_encounters):
                errors.append(f"location {key} gathering {g.skill}: stay_ambush without an encounter table")
        for dkey, disc in loc.discoveries.items():
            need("skill", disc.skill, c.skills, f"location {key} discovery {dkey}")
            for i in disc.gives:
                need("item", i, c.items, f"location {key} discovery {dkey}")
    errors += _city_graph_errors(c)
    for key, cls in c.classes.items():
        for a in cls.signature:
            need("ability", a, cls.abilities, f"class {key} signature")
    stations = {s for loc in c.locations.values() for s in loc.stations}
    for key, recipe in c.recipes.items():
        if recipe.profession not in c.professions and recipe.profession not in MASTERIES:
            errors.append(f"recipe {key}: '{recipe.profession}' is neither a profession nor a field mastery")
        elif recipe.profession in MASTERIES and recipe.station is None:
            errors.append(f"recipe {key}: a mastery recipe needs its own station")
        station = recipe.station or (c.professions[recipe.profession].station
                                     if recipe.profession in c.professions else None)
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
                errors.append(f"recipe {key}: its technique unlocks at rank {techniques[recipe.technique].rank}, "
                              f"after the recipe's own {recipe.min_rank}")
        if recipe.special and recipe.technique is not None:
            errors.append(f"recipe {key}: a special recipe comes from a blueprint, not from a technique")
        if recipe.special and not any(i.teaches == key for i in c.items.values()):
            errors.append(f"recipe {key}: special, but no blueprint teaches it")
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
    for outcome in CHRONICLE_KEYS:
        if not c.chronicles.get(outcome):
            errors.append(f"fallbacks/chronicles.yaml: no texts for '{outcome}'")
    for outcome in c.chronicles:
        if outcome not in CHRONICLE_KEYS:
            errors.append(f"fallbacks/chronicles.yaml: unknown outcome '{outcome}'")
    for category, keys in FALLBACK_KEYS.items():
        for key in keys:
            if not c.fallbacks.get(category, {}).get(key):
                errors.append(f"fallbacks/{category}.yaml: no texts for '{key}'")
    for category, by_key in c.fallbacks.items():
        allowed = FALLBACK_PLACEHOLDERS.get(category)
        if allowed is None:
            errors.append(f"fallbacks/{category}.yaml: unknown category")
            continue
        for key, texts in by_key.items():
            if category == "dialogue" and key != "default":
                need("npc", key, c.npcs, "fallbacks/dialogue.yaml")
            if category not in ("dialogue", "chronicles") and key not in FALLBACK_KEYS[category]:
                errors.append(f"fallbacks/{category}.yaml: unknown key '{key}'")
            for lang in ("es", "en"):
                variants = [getattr(text, lang).strip() for text in texts]
                if not all(variants) or len(set(variants)) < 12:
                    errors.append(f"fallbacks/{category}.yaml {key}: need 12 distinct nonempty {lang} texts")
            for text in texts:
                placeholders = []
                for lang in ("es", "en"):
                    try:
                        fields = list(Formatter().parse(getattr(text, lang)))
                        used = {field for _, field, _, _ in fields if field is not None}
                        if any(spec or conversion for _, _, spec, conversion in fields):
                            errors.append(f"fallbacks/{category}.yaml {key}: formatting modifiers forbidden")
                    except ValueError:
                        errors.append(f"fallbacks/{category}.yaml {key}: malformed placeholders")
                        used = set()
                    placeholders.append(used)
                    if used - allowed:
                        errors.append(f"fallbacks/{category}.yaml {key}: unknown placeholders {sorted(used - allowed)}")
                if placeholders[0] != placeholders[1]:
                    errors.append(f"fallbacks/{category}.yaml {key}: es/en placeholders differ")
    for npc_key in c.npcs:
        if not c.fallbacks.get("dialogue", {}).get(npc_key):
            errors.append(f"fallbacks/dialogue.yaml: no texts for '{npc_key}'")
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
        where = f"quest {key}"
        need("npc", quest.giver, c.npcs, where)
        need("quest", quest.after, c.quests, where)
        for field in ("unlock_stage", "objective_stage", "complete_stage"):
            need("stage", getattr(quest, field), quest.stages, f"{where} {field}")
        if (quest.after or quest.unlock_flag) and quest.unlock_stage is None:
            errors.append(f"{where}: locked missions need an unlock_stage")
        if quest.objectives and (quest.objective_stage is None or quest.complete_stage is None):
            errors.append(f"{where}: objectives need objective_stage and complete_stage")
        # a craft objective may also name furniture a starter recipe installs ("furniture:bed")
        furniture = {f"furniture:{r.installs}": None for r in c.recipes.values() if r.installs}
        items, places = ("item", c.items), ("location", {**c.locations, "any": None})
        pools = {"kill": ("monster", c.monsters), "talk": ("npc", c.npcs), "visit": ("location", c.locations), "hunt": places,
                 "gather": items, "skin": items, "craft": ("item", {**c.items, **furniture}),
                 "rest": places, "heal": places,
                 "read": ("rulebook section", c.rulebook)}
        for obj in quest.objectives:
            need(*pools[obj.kind][:1], obj.target, pools[obj.kind][1], f"{where} objective")
        effect_lists.append((f"{where} rewards", quest.rewards))
        for where, effects in effect_lists:
            for eff in effects:
                _validate_effect(c, eff, where, errors)
        for skey, stage in quest.stages.items():
            for lkey in stage.location_text:
                need("location", lkey, c.locations, f"quest {key} stage {skey}")

    if errors:
        raise ValueError("Content validation failed:\n  " + "\n  ".join(errors))


def _city_graph_errors(c: Content) -> list[str]:
    """A city is walked freely along shortest paths (services/world_map.py), so it must be safe to cross:
    one hub, the only place with roads out; no dangerous streets nor fixed fights; every place reachable."""
    errors: list[str] = []
    for zkey, zone in c.zones.items():
        if zone.kind != "city":
            continue
        places = {k: loc for k, loc in c.locations.items() if loc.zone == zkey}
        hubs = [k for k, loc in places.items() if loc.hub]
        if len(hubs) != 1:
            errors.append(f"zone {zkey}: a city needs exactly one hub, found {len(hubs)}")
            continue
        for key, loc in places.items():
            if loc.fixed_encounters:
                errors.append(f"location {key}: fixed encounters in a city")
            for ex in loc.exits:
                if ex.to not in c.locations:
                    continue
                inside = c.locations[ex.to].zone == zkey
                if not inside and not loc.hub:
                    errors.append(f"location {key}: leaves the city to '{ex.to}' but is not its hub")
                if inside and (ex.danger or ex.requires_flag):
                    errors.append(f"location {key}: city street to '{ex.to}' with danger or a flag")
        seen, todo = {hubs[0]}, [hubs[0]]
        while todo:
            for ex in places[todo.pop()].exits:
                if ex.to in places and ex.to not in seen:
                    seen.add(ex.to)
                    todo.append(ex.to)
        for key in sorted(set(places) - seen):
            errors.append(f"location {key}: not reachable from the hub inside the city")
    return errors


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
