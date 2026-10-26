"""Places, cities, zones and NPCs."""

from typing import TYPE_CHECKING

from oathforge.engine.gathering import GATHER_SKILLS
from oathforge.content.validation.common import collector

if TYPE_CHECKING:
    from oathforge.content.loader import Content


def world_errors(c: "Content") -> list[str]:
    """Exits, encounters, gathering and discoveries of every place; the city graph; zone images; NPCs."""
    errors, need = collector()
    need("location", c.start_location, c.locations, "locations.start")
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
    return errors


def _city_graph_errors(c: "Content") -> list[str]:
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
