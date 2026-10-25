"""A test-only dungeon: the game has none any more (the Sunken Crypt left in 0.10.41), but the engine still supports
rooms with a waiting fight, hidden routes, a free bed and a boss, and that support needs a place to be tested.

``install(monkeypatch)`` adds it to the loaded content for one test; nothing here is shipped.
"""

from oathforge.content import get_content
from oathforge.content.schemas import Exit, Location, Monster, Zone

SKELETON = {
    "name": {"es": "Esqueleto de prueba", "en": "Test skeleton"}, "description": {"es": "Huesos.", "en": "Bones."},
    "hp": 7, "ac": 13, "dex": 2, "xp": 50, "gold": "1d4", "icon": "💀", "type": "undead",
    "attacks": [{"name": {"es": "Espada oxidada", "en": "Rusted sword"}, "to_hit": 2, "damage": "1d4", "damage_type": "slashing"}],
    "immune": ["poisoned", "frightened", "bleeding"], "vulnerable": ["bludgeoning", "radiant"], "immune_damage": ["poison"],
    "lore": {"es": "Guardias de huesos.", "en": "Bone guards."},
}
WARDEN = {
    "name": {"es": "Guardián de prueba", "en": "Test warden"}, "description": {"es": "Un caballero.", "en": "A knight."},
    "hp": 40, "ac": 15, "dex": 0, "wis": 2, "xp": 700, "gold": "6d10", "icon": "👻", "type": "undead", "boss": True,
    "attacks": [{"name": {"es": "Espadón", "en": "Greatsword"}, "to_hit": 4, "damage": "1d8+2", "damage_type": "necrotic",
                 "applies": {"status": "frightened", "turns": 1, "chance": 0.25}},
                {"name": {"es": "Lamento", "en": "Wail"}, "to_hit": 4, "damage": "2d4", "damage_type": "cold", "ranged": True}],
    "loot": [{"item": "healing_potion", "chance": 1.0, "qty": 2}], "immune": ["poisoned", "frightened", "bleeding"],
    "vulnerable": ["radiant"], "resist": ["necrotic", "cold"], "immune_damage": ["poison"],
    "lore": {"es": "Un juramento.", "en": "An oath."},
}


def _place(name_es, name_en, exits, **extra) -> dict:
    return {"name": {"es": name_es, "en": name_en}, "article": {"es": "la", "en": "the"}, "kind": "dungeon",
            "description": {"es": "Una sala.", "en": "A room."}, "exits": exits, **extra}


PLACES = {
    "ruin_entrance": _place("Ruinas: entrada", "Ruins: entrance",
                            [{"to": "whispering_woods", "minutes": 20}, {"to": "ruin_hall", "minutes": 2}],
                            fixed_encounters=[{"monsters": ["test_skeleton"], "flag": "cleared_ruin_entrance"}]),
    "ruin_hall": _place("Ruinas: sala", "Ruins: hall",
                        [{"to": "ruin_entrance", "minutes": 2}, {"to": "ruin_ossuary", "minutes": 2},
                         {"to": "ruin_gallery", "minutes": 3, "yards": 150}],
                        fixed_encounters=[{"monsters": ["test_skeleton", "test_skeleton"], "flag": "cleared_ruin_hall"}]),
    "ruin_gallery": _place("Ruinas: galería", "Ruins: gallery",
                           [{"to": "ruin_hall", "minutes": 3, "yards": 150}, {"to": "ruin_sanctum", "minutes": 2}],
                           fixed_encounters=[{"monsters": ["test_skeleton"], "flag": "cleared_ruin_gallery"}]),
    "ruin_sanctum": _place("Ruinas: santuario", "Ruins: sanctum", [{"to": "ruin_gallery", "minutes": 2}],
                           fixed_encounters=[{"monsters": ["test_warden"], "flag": "cleared_ruin_sanctum"}],
                           scene_objects={"iron_chandelier": {
                               "name": {"es": "Lámpara de hierro", "en": "Iron chandelier"},
                               "description": {"es": "Cuelga de una cadena.", "en": "It hangs from a chain."},
                               "skill": "athletics", "tier": "medium",
                               "effect": {"damage": "3d6", "targets": "one", "status": {"status": "stunned", "turns": 1}}}}),
    "ruin_ossuary": _place("Ruinas: osario", "Ruins: ossuary", [{"to": "ruin_hall", "minutes": 2}], rest_cost=0,
                           discoveries={
                               "warden_epitaph": {"skill": "history", "tier": "medium", "sets_flag": "warden_lore",
                                                  "text": {"es": "Un epitafio.", "en": "An epitaph."}},
                               "ossuary_coins": {"skill": "investigation", "tier": "easy", "sets_flag": "found_ossuary_coins",
                                                 "gold": 25, "text": {"es": "Veinticinco monedas.", "en": "Twenty-five coins."}}}),
}


def install(monkeypatch) -> None:
    c = get_content()
    monkeypatch.setitem(c.monsters, "test_skeleton", Monster.model_validate(SKELETON))
    monkeypatch.setitem(c.monsters, "test_warden", Monster.model_validate(WARDEN))
    monkeypatch.setitem(c.zones, "test_ruins", Zone.model_validate(
        {"name": {"es": "Ruinas", "en": "Ruins"}, "kind": "dungeon",
         "description": {"es": "Unas ruinas.", "en": "Some ruins."}}))
    for key, data in PLACES.items():
        loc = Location.model_validate(data)
        object.__setattr__(loc, "zone", "test_ruins")
        monkeypatch.setitem(c.locations, key, loc)
    woods = c.locations["whispering_woods"]
    old = woods.exits
    object.__setattr__(woods, "exits", [*old, Exit(to="ruin_entrance", minutes=20, requires_flag="ruins_unlocked")])
    _restore.append((woods, old))


_restore: list = []


def uninstall() -> None:
    while _restore:
        woods, old = _restore.pop()
        object.__setattr__(woods, "exits", old)
