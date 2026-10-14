"""The world as a graph: routes between places, who can go where and what there is to do (read only).

Places are nodes and exits are directed edges weighted in game minutes; distance in yards comes from a
walking pace. How you move depends on the zone you stand in:

- city: anywhere in the city along the shortest path (Dijkstra); you leave it only from its hub (the plaza);
- wilds and dungeon: one stretch at a time, since each road rolls its own ambush and each room its fight.
"""

import heapq
from dataclasses import dataclass

from oathforge.content import get_content
from oathforge.content.schemas import Exit
from oathforge.database.models import Character

YARDS_PER_MINUTE = 100  # D&D normal pace: 300 feet a minute (1 km ≈ 1094 yd)


@dataclass(frozen=True)
class Route:
    to: str
    minutes: int
    yards: int
    danger: int = 0  # the worst stretch on the way
    via: tuple[str, ...] = ()  # places walked through before arriving


def yards(exit_: Exit) -> int:
    return exit_.yards if exit_.yards is not None else exit_.minutes * YARDS_PER_MINUTE


def open_exits(char: Character, loc_key: str) -> list[Exit]:
    """Exits from ``loc_key`` whose route the character has found (requires_flag)."""
    loc = get_content().locations[loc_key]
    return [e for e in loc.exits if not e.requires_flag or char.flags.get(e.requires_flag)]


def zone_kind(loc_key: str) -> str:
    c = get_content()
    return c.zones[c.locations[loc_key].zone].kind


def hub_of(zone: str) -> str | None:
    return next((k for k, loc in get_content().locations.items() if loc.zone == zone and loc.hub), None)


def _adjacent(char: Character, origin: str) -> list[Route]:
    return [Route(e.to, e.minutes, yards(e), e.danger) for e in open_exits(char, origin)]


def shortest_routes(char: Character, origin: str) -> dict[str, Route]:
    """Shortest route (in minutes) from ``origin`` to every place of its zone, without leaving it."""
    c = get_content()
    zone = c.locations[origin].zone
    best: dict[str, Route] = {origin: Route(origin, 0, 0)}
    queue: list[tuple[int, str]] = [(0, origin)]
    while queue:
        minutes, here = heapq.heappop(queue)
        if minutes > best[here].minutes:
            continue
        route = best[here]
        for e in open_exits(char, here):
            if c.locations[e.to].zone != zone:
                continue
            nxt = Route(e.to, minutes + e.minutes, route.yards + yards(e), max(route.danger, e.danger),
                        route.via + ((here,) if here != origin else ()))
            if e.to not in best or nxt.minutes < best[e.to].minutes:
                best[e.to] = nxt
                heapq.heappush(queue, (nxt.minutes, e.to))
    del best[origin]
    return best


def _by_time(routes) -> list[Route]:
    return sorted(routes, key=lambda r: (r.minutes, r.to))


def destinations(char: Character, origin: str | None = None) -> list[Route]:
    """Where the character can go right now in one move."""
    origin = origin or char.location
    if zone_kind(origin) != "city":
        return _by_time(_adjacent(char, origin))
    c = get_content()
    zone = c.locations[origin].zone
    routes = list(shortest_routes(char, origin).values())
    if c.locations[origin].hub:
        routes += [r for r in _adjacent(char, origin) if c.locations[r.to].zone != zone]
    return _by_time(routes)


def departures(char: Character) -> tuple[str | None, list[Route]]:
    """In a city: its hub and the roads that leave the city from there."""
    c = get_content()
    zone = c.locations[char.location].zone
    hub = hub_of(zone)
    if zone_kind(char.location) != "city" or hub is None:
        return None, []
    return hub, _by_time(r for r in _adjacent(char, hub) if c.locations[r.to].zone != zone)


def beyond(char: Character) -> list[Route]:
    """In the wilds: the rest of the zone, with its route (to show, not to jump there)."""
    if zone_kind(char.location) != "wilds":
        return []
    near = {r.to for r in _adjacent(char, char.location)}
    return _by_time(r for k, r in shortest_routes(char, char.location).items() if k not in near)


def route_to(char: Character, dest: str) -> Route | None:
    return next((r for r in destinations(char) if r.to == dest), None)


def cleared(char: Character, loc_key: str) -> bool:
    """A dungeon room whose fights are all behind the character."""
    fixed = get_content().locations[loc_key].fixed_encounters
    return bool(fixed) and any(char.flags.get(fe.flag) for fe in fixed)


def activities(loc_key: str, present: list[str]) -> list[tuple[str, dict]]:
    """What can be done at a place, as (i18n key under ``map.do.``, params); ``present`` are its NPCs now."""
    c = get_content()
    loc = c.locations[loc_key]
    out: list[tuple[str, dict]] = []
    shops = [c.npcs[k].name.model_dump() for k in present if c.npcs[k].shop]
    for name in shops:
        out.append(("shop", {"npc": name}))
    if loc.healer is not None:
        out.append(("heal", {"cost": loc.healer.cost}))
    if loc.rest_cost is not None:
        out.append(("rest_free" if loc.rest_cost == 0 else "rest", {"cost": loc.rest_cost}))
    out += [(f"gather_{g.skill}", {}) for g in loc.gathering]
    if loc.hunting:
        out.append(("hunt", {}))
    if loc.stations:
        out.append(("craft", {}))
    if loc.guild:
        out.append(("guild", {}))
    talk = [c.npcs[k].name.model_dump() for k in present if not c.npcs[k].shop]
    for name in talk:
        out.append(("npc", {"npc": name}))
    return out
