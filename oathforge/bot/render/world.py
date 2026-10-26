"""Scene, activities list, home, settings, map, conversations and bestiary."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.i18n import t
from oathforge.services import actions, activities, bestiary, exploration, home, inventory, npcs, quests, world_map
from oathforge.bot.render.common import MAX_MESSAGE, RULE, _go_button, creature_icon, journal_tabs, status_line
from oathforge.bot.render.crafting import activity_entries, activity_panel


# ---------------------------------------------------------------- scene

async def scene(session: AsyncSession, char: Character, lang: str,
                started: str | None = None, compact: bool = False) -> tuple[str, InlineKeyboardMarkup]:
    """Where you are and who is around; what you can do with your hands lives in ⚒ Activities.
    ``compact``: only the heading and the status line, under the result of an action."""
    c = get_content()
    loc = c.locations[char.location]
    night = exploration.is_night()
    present = exploration.npcs_present(char.location)
    lines = [f"📍 <b>{escape(loc.name.get(lang))}</b>", status_line(char, lang), ""]
    if not compact:
        desc = loc.night.get(lang) if night and loc.night else loc.description.get(lang)
        lines.append(escape(desc))
        for extra in await quests.location_texts(session, char):
            lines += ["", f"<i>{escape(extra[lang])}</i>"]
        if present:
            lines += ["", t(lang, "scene.people")]
            lines += [f"• {escape(c.npcs[k].name.get(lang))} <i>({escape(c.npcs[k].title.get(lang))})</i>" for k in present]
        lines += ["", f"<i>{t(lang, 'scene.hint')}</i>"]

    n = nonce()
    act = await activities.open_activity(session, char)
    if act is not None and act.status == "running":
        return activity_panel(char, act, lines, n, lang, started)
    buttons = [btn(t(lang, "btn.travel"), cb("trv")), btn(t(lang, "btn.investigate"), cb("look", "-", n))]
    if present:
        buttons.append(btn(t(lang, "btn.talk"), cb("talkm")))
    if any(c.npcs[k].shop for k in present):
        buttons.append(btn(t(lang, "btn.shop"), cb("shopm")))
    things = len(await activity_entries(session, char, lang))
    if things:
        buttons.append(btn(t(lang, "btn.activities", n=things), cb("acts")))
    buttons.append(btn(t(lang, "btn.view_place"), cb("place")))
    rows = grid(buttons)
    trip_to = exploration.trip(char) if char.state == "idle" else None
    if trip_to:  # an ambush stopped the trip halfway: carry on in one tap
        rows.insert(0, [btn(t(lang, "btn.continue_trip", place=c.locations[trip_to].phrase()[lang]),
                            cb("go", trip_to, n))])
    for qkey, quest in await quests.ready_to_turn_in(session, char, present):
        rows.append([btn(t(lang, "btn.turn_in", quest=quest.name.get(lang)), cb("qturn", qkey, n))])
    for a in await quests.available_actions(session, char, present):
        if a.action.npc is None:
            rows.append([btn(a.action.label.get(lang), cb("qa", a.ref, n))])
    return "\n".join(lines).rstrip(), markup(rows)  # inventory, hero and journal live in the fixed keyboard


async def activities_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """⚒ Activities: what you can do here, how long it takes and what you lack; then 🛠️ Professions."""
    if char.state == "busy":  # already working: its panel (the callers send a fight to the combat panel)
        return await scene(session, char, lang)
    loc = get_content().locations[char.location]
    n = nonce()
    entries = await activity_entries(session, char, lang, n)
    head = t(lang, "acts.title", place=escape(loc.name.get(lang))) + "\n" + status_line(char, lang)
    parts = [head, *(line for line, _ in entries)] if entries else [head, t(lang, "acts.none")]
    if loc.teaches is not None:
        parts.append(f"<i>{t(lang, 'acts.guild', prof=escape(get_content().professions[loc.teaches].name.get(lang)))}</i>")
    rows = grid([b for _, b in entries if b is not None])
    last = [btn(t(lang, "btn.professions"), cb("prof"))]
    if loc.home:
        last.insert(0, btn(t(lang, "btn.specializations"), cb("spec")))
    if home.at_home(char):
        last.insert(0, btn(t(lang, "btn.room"), cb("room")))
    rows.append([*last, btn(t(lang, "btn.back"), cb("scene"))])
    return "\n\n".join(parts)[:MAX_MESSAGE], markup(rows)


async def room_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """🏠 Your room at the guild: the bed and the chest, with what waits in it and what you could store."""
    c = get_content()
    lines = [t(lang, "home.title", place=escape(c.locations[char.location].name.get(lang))), RULE]
    if not char.home:
        lines.append(t(lang, "home.none"))
        return "\n".join(lines), markup([[btn(t(lang, "btn.back"), cb("scene"))]])
    lines.append(t(lang, "home.bed") if home.has_bed(char) else t(lang, "home.no_bed"))
    if not home.chest_level(char):
        lines.append(t(lang, "home.no_chest"))
        return "\n".join(lines), markup([[btn(t(lang, "btn.back"), cb("scene"))]])
    stored = await home.stored(session, char)
    lines.append(t(lang, "home.chest", used=len(stored), capacity=home.capacity(char)))
    lines.append("")
    if stored:
        lines += [t(lang, "home.line", item=escape(c.items[i.item_key].label(lang)), qty=i.qty, key=i.item_key)
                  for i in stored]
    else:
        lines.append(t(lang, "home.chest_empty"))
    if home.at_home(char):
        bag = [i for i in await inventory.items_of(session, char) if not i.equipped_slot]
        if bag:
            lines += ["", t(lang, "home.bag_title")]
            lines += [t(lang, "home.bag_line", item=escape(c.items[i.item_key].label(lang)), qty=i.qty,
                         key=i.item_key) for i in bag]
    return "\n".join(lines)[:MAX_MESSAGE], markup([[btn(t(lang, "btn.back"), cb("scene"))]])


def settings_view(user, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """⚙️ Settings: language and manual rolls (off by default; the die is decoration)."""
    on = actions.manual_rolls(user)
    text = t(lang, "settings.text", language=t(lang, "settings.language_name"),
             rolls=t(lang, "roll.on" if on else "roll.off"))
    rows = [[btn("🇪🇸 Español", cb("setl", "es")), btn("🇬🇧 English", cb("setl", "en"))],
            [btn(t(lang, "btn.roll_off" if on else "btn.roll_on"), cb("rollset", "off" if on else "on"))]]
    return text, markup(rows)


def zone_caption(zone_key: str, lang: str) -> str:
    """Caption for the zone's images ("View city"): name and day/night description."""
    zone = get_content().zones[zone_key]
    desc = zone.night if exploration.is_night() and zone.night else zone.description
    return f"🏙️ <b>{escape(zone.name.get(lang))}</b>\n\n{escape(desc.get(lang))}"


def place_caption(loc_key: str, lang: str) -> str:
    """Caption for the place's images ("View place"): name and day/night description."""
    loc = get_content().locations[loc_key]
    desc = loc.night if exploration.is_night() and loc.night else loc.description
    return f"🖼️ <b>{escape(loc.name.get(lang))}</b>\n\n{escape(desc.get(lang))}"


def _place_activities(loc_key: str, lang: str) -> str:
    """🛒 Tienda de Mira · 🛏️ Descanso largo (5 🪙) · 💬 Bram"""
    parts = []
    for key, params in world_map.activities(loc_key, exploration.npcs_present(loc_key)):
        params = {k: v.get(lang, v.get("en")) if isinstance(v, dict) else v for k, v in params.items()}
        parts.append(t(lang, f"map.do.{key}", **{k: escape(str(v)) for k, v in params.items()}))
    return " · ".join(parts)


def _route_lines(char: Character, route: world_map.Route, lang: str) -> list[str]:
    """• <b>Capilla del Alba</b> · 4 min · 400 yd · por Plaza  (and what there is to do below)"""
    c = get_content()
    loc = c.locations[route.to]
    tags = [t(lang, "map.route", minutes=route.minutes, yards=route.yards)]
    if route.via:
        tags.append(t(lang, "map.via", places=escape(", ".join(c.locations[k].phrase()[lang] for k in route.via))))
    if loc.hub and loc.zone == c.locations[char.location].zone:
        tags.append(t(lang, "map.gate"))
    if world_map.cleared(char, route.to):
        tags.append(t(lang, "map.cleared"))
    lines = [f"• <b>{escape(loc.name.get(lang))}</b> · " + " · ".join(tags) + (" " + "⚠️" * route.danger
                                                                              if route.danger else "")]
    todo = _place_activities(route.to, lang)
    if todo:
        lines.append(f"      {todo}")
    return lines


ZONE_ICON = {"city": "🏙️", "wilds": "🌲", "dungeon": "🕯️"}
ZONE_INLINE = 2  # another zone with more known places than this gets one button that opens it


def _street_of(place: str) -> str | None:
    """The street a trade stall hangs off: its only way back."""
    exits = get_content().locations[place].exits
    return exits[0].to if len(exits) == 1 else None


async def map_view(session: AsyncSession, char: Character, lang: str, zone: str | None = None,
                   street: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """/map and «Travel»: where you are, what there is to do, and every place you can go in one tap (the engine
    walks the way). First your missions, then this zone, then the other zones you know (``zone`` opens one)."""
    c = get_content()
    here = c.locations[char.location]
    zone_here = c.zones[here.zone]
    routes = world_map.destinations(char)
    n = nonce()
    if street is not None and street in c.locations:  # one street's stalls, from the map's stalls button
        inside = [r for r in routes if _street_of(r.to) == street and c.locations[r.to].teaches]
        lines = [t(lang, "map.street_title", street=escape(c.locations[street].name.get(lang))), RULE]
        for r in inside:
            lines += _route_lines(char, r, lang)
        rows = [] if char.state != "idle" else [_go_button(r, lang, n) for r in inside]
        rows.append([btn(t(lang, "btn.back"), cb("trv"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)
    if zone is not None and zone in c.zones:  # one zone's places, from the map's zone button
        z = c.zones[zone]
        lines = [t(lang, "map.zone_title", icon=ZONE_ICON[z.kind], zone=escape(z.name.get(lang))), RULE]
        inside = [r for r in routes if c.locations[r.to].zone == zone]
        for r in inside:
            lines += _route_lines(char, r, lang)
        rows = [] if char.state != "idle" else [_go_button(r, lang, n) for r in inside]
        rows.append([btn(t(lang, "btn.back"), cb("trv"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    lines = [t(lang, "map.title", zone=escape(zone_here.name.get(lang)), kind=t(lang, f"map.kind.{zone_here.kind}")),
             t(lang, "map.here", place=escape(here.phrase()[lang]))]
    todo = _place_activities(char.location, lang)
    lines.append(f"      {todo}" if todo else f"      <i>{t(lang, 'map.nothing')}</i>")
    lines.append(RULE)
    rows: list[list] = []

    goals = await exploration.objective_routes(session, char)
    if goals:
        lines.append(t(lang, "map.objective"))
        for quest, r in goals:
            lines.append(t(lang, "map.objective_line", quest=escape(quest.get(lang, quest.get("en"))),
                           place=escape(c.locations[r.to].name.get(lang))))
            rows.append(_go_button(r, lang, n, "📜"))
        lines.append("")

    near = [r for r in routes if c.locations[r.to].zone == here.zone and not c.locations[r.to].teaches]
    stalls = [r for r in routes if c.locations[r.to].zone == here.zone and c.locations[r.to].teaches]
    others: dict[str, list[world_map.Route]] = {}
    for r in routes:
        if c.locations[r.to].zone != here.zone:
            others.setdefault(c.locations[r.to].zone, []).append(r)
    if near:
        lines.append(t(lang, f"map.near.{zone_here.kind}"))
        for r in near:
            lines += _route_lines(char, r, lang)
            for_street = [x for x in stalls if _street_of(x.to) == r.to]
            if for_street:  # the trade stalls hang off their street, not off the city
                lines.append("      " + " · ".join(escape(c.locations[x.to].name.get(lang)) for x in for_street))
                rows.append([btn(t(lang, "btn.stalls", n=len(for_street)), cb("trvs", r.to))])
        rows += [_go_button(r, lang, n) for r in near]
    for key, zroutes in others.items():
        z = c.zones[key]
        lines += ["", t(lang, "map.zone_title", icon=ZONE_ICON[z.kind], zone=escape(z.name.get(lang)))]
        if len(zroutes) <= ZONE_INLINE:
            for r in zroutes:
                lines += _route_lines(char, r, lang)
            rows += [_go_button(r, lang, n) for r in zroutes]
        else:
            lines.append("      " + " · ".join(escape(c.locations[r.to].name.get(lang)) for r in zroutes))
            rows.append([btn(t(lang, "btn.zone", icon=ZONE_ICON[z.kind], zone=z.name.get(lang), n=len(zroutes)),
                             cb("trvz", key))])
    far = world_map.beyond(char)
    if far:
        lines += ["", t(lang, "map.beyond")]
        for r in far:
            lines += _route_lines(char, r, lang)
    lines += ["", f"<i>{t(lang, f'map.hint.{zone_here.kind}')}</i>"]
    if char.state != "idle":  # busy with an activity: the map, but no roads to take
        lines += ["", t(lang, "map.busy")]
        return "\n".join(lines)[:MAX_MESSAGE], markup([[btn(t(lang, "btn.back"), cb("scene"))]])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def talk_menu(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    rows = [[btn(f"💬 {c.npcs[k].name.get(lang)}", cb("talk", k))] for k in exploration.npcs_present(char.location)]
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return t(lang, "talk.title"), markup(rows)


async def conversation(session: AsyncSession, char: Character, npc_key: str, lang: str,
                       line: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    npc = c.npcs[npc_key]
    text = [f"💬 <b>{escape(npc.name.get(lang))}</b>, {escape(npc.title.get(lang))}", ""]
    greeting = npc.greeting
    if not line and npc.greeting_return is not None and await quests.finished_giver(session, char, npc_key):
        greeting = npc.greeting_return
    text.append(escape(line) if line else escape(greeting.get(lang)))
    text += ["", f"<i>{t(lang, 'talk.hint', npc=escape(npc.name.get(lang)))}</i>"]
    n = nonce()
    present = exploration.npcs_present(char.location)
    rows = [[btn(t(lang, "btn.turn_in", quest=q.name.get(lang)), cb("qturn", qkey, n))]
            for qkey, q in await quests.ready_to_turn_in(session, char, present, npc=npc_key)]
    rows += [[btn(a.action.label.get(lang), cb("qa", a.ref, n))]
             for a in await quests.available_actions(session, char, present, npc=npc_key)]
    if npc.shop:
        rows.append([btn(t(lang, "btn.shop"), cb("shop", npc_key))])
    rows.append([btn(t(lang, "btn.leave"), cb("bye"))])
    return "\n".join(text), markup(rows)


# ---------------------------------------------------------------- bestiary

def bestiary_list(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    known = bestiary.known(char)
    lines = [t(lang, "bestiary.title", seen=len(known), total=len(c.monsters)), ""]
    rows = []
    for key, entry in known:
        m = c.monsters[key]
        rows.append([btn(f"{creature_icon(m)} {m.name.get(lang)} · ⚔️ {entry.get('killed', 0)}",
                         cb("jb", key))])
    lines.append(f"<i>{t(lang, 'bestiary.hint' if known else 'bestiary.empty')}</i>")
    return "\n".join(lines), markup(rows + journal_tabs("jrb", lang))


def bestiary_entry(char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """A stat block that fills in with experience: seen, first kill, three kills."""
    c = get_content()
    back = markup([[btn(t(lang, "btn.back"), cb("jrb"))]])
    entry = (char.bestiary or {}).get(key)
    level = bestiary.tier(entry)
    if key not in c.monsters or level == 0:
        return t(lang, "bestiary.unknown"), back
    m = c.monsters[key]
    lines = [f"{creature_icon(m)} <b>{escape(m.name.get(lang))}</b>",
             f"<i>{t(lang, 'creature.' + m.type)} · {t(lang, 'bestiary.active.' + m.active)}</i>",
             RULE, escape(m.description.get(lang))]
    if m.lore:
        lines += ["", escape(m.lore.get(lang))]
    if m.habitat:
        lines += ["", t(lang, "bestiary.habitat", place=escape(m.habitat.get(lang)))]
    lines.append(t(lang, "bestiary.record", seen=entry.get("seen", 0), killed=entry.get("killed", 0)))
    if level >= 2:
        lines += ["", f"<b>{t(lang, 'bestiary.stats')}</b>",
                  t(lang, "bestiary.hp_ac", hp=m.hp, ac=m.ac)]
        for a in m.attacks:
            icon = "🏹" if a.ranged else "🗡️"
            lines.append(f"{icon} {escape(a.name.get(lang))}: {a.to_hit:+d} · {a.damage} "
                         f"{escape(t(lang, 'dmg.' + a.damage_type))}")
    else:
        lines += ["", f"🔒 <i>{t(lang, 'bestiary.locked_stats')}</i>"]
    if level >= 3:
        lines += ["", f"<b>{t(lang, 'bestiary.secrets')}</b>"]
        for field, label in (("vulnerable", "bestiary.vulnerable"), ("resist", "bestiary.resist"),
                             ("immune_damage", "bestiary.immune")):
            values = getattr(m, field)
            if values:
                lines.append(t(lang, label, list=", ".join(t(lang, "dmg." + v) for v in values)))
        if m.immune:
            lines.append(t(lang, "bestiary.immune_status", list=", ".join(t(lang, "status." + s) for s in m.immune)))
        lines.append(t(lang, "bestiary.xp", xp=m.xp))
        loot = [c.items[l.item].name.get(lang) for l in m.loot]
        if loot:
            lines.append(t(lang, "bestiary.loot", list=escape(", ".join(loot))))
    elif level == 2:
        lines += ["", f"🔒 <i>{t(lang, 'bestiary.locked_secrets', n=bestiary.KILLS_FOR_SECRETS)}</i>"]
    if c.media.monster_images(key):
        back = markup([[btn(t(lang, "btn.creature_art"), cb("jbi", key)), btn(t(lang, "btn.back"), cb("jrb"))]])
    return "\n".join(lines)[:MAX_MESSAGE], back


def creature_caption(key: str, lang: str) -> str:
    m = get_content().monsters[key]
    return f"{creature_icon(m)} <b>{escape(m.name.get(lang))}</b>"


async def rumors(session: AsyncSession, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f"<b>{t(lang, 'journal.rumors')}</b>", ""]
    found = await npcs.recent_rumors(session, limit=8)
    lines += [f"• <i>{escape(r.get(lang, r.get('en', '')))}</i>" for r in found] or [f"<i>{t(lang, 'journal.no_rumors')}</i>"]
    return "\n".join(lines)[:MAX_MESSAGE], markup(journal_tabs("jrr", lang))
