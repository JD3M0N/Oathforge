"""Screens that only show something: places, sheet, journal, bestiary, item and monster pages."""

import pytest
from sqlalchemy import select

from oathforge.bot.handlers import commands
from oathforge.bot.keyboards import parse
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.services import exploration
from tests.bot.helpers import Player, create

pytestmark = pytest.mark.usefixtures("database")


def test_sheet_is_in_the_telegram_command_menu():
    from oathforge.bot.handlers import commands
    from oathforge.i18n import t
    from oathforge.main import MENU_COMMANDS

    handled = {c for h in commands.handlers() for c in getattr(h, "commands", ())}
    assert "sheet" in MENU_COMMANDS
    for cmd in MENU_COMMANDS:
        assert cmd == "start" or cmd in handled
        for lang in ("es", "en"):
            assert t(lang, f"cmd.{cmd}") != f"cmd.{cmd}"


async def test_view_place_in_the_plaza_shows_the_city_once_then_reuses_file_id(llm):
    p = Player(llm, tg_id=11)
    await create(p)
    assert not any(parse(d)[0] == "city" for d in p.buttons())  # one button: View place
    place = p.find("place")
    await p.press(place)  # the plaza has no art of its own: the city panorama
    assert isinstance(p.chat.photos[-1], bytes)  # first time: upload the file
    assert "Crownreach" in p.chat.sent[-2][0]  # caption, then the scene again below it
    assert "Plaza de Crownreach" in p.last[0] and p.find("place")

    await p.press(place)
    assert p.chat.photos[-1] == "FILE1"  # second time: cached file_id, no upload


async def test_view_place_sends_its_image_or_a_popup_when_there_is_none(llm, monkeypatch):
    from oathforge.content import get_content
    from oathforge.content.media import MediaCatalog

    p = Player(llm, tg_id=12)
    await create(p)
    await p.press(p.find("trv"))
    await p.press(p.find("go", "broken_crown_tavern"))  # not a hub: no city to fall back on
    photos, sent = len(p.chat.photos), len(p.chat.sent)
    await p.press(p.find("place"))  # no place has art yet
    assert "pintor" in p.chat.popups[-1] and "la Taberna La Corona Rota" in p.chat.popups[-1]
    assert len(p.chat.photos) == photos and len(p.chat.sent) == sent

    panorama = get_content().media.zone_images("crownreach")
    monkeypatch.setattr(MediaCatalog, "location_images", lambda self, loc, night=False: panorama)
    await p.press(p.find("place"))
    assert len(p.chat.photos) == photos + 1
    assert "Corona Rota" in p.chat.sent[-2][0] and p.find("place")  # its own caption, then the scene again


async def test_hero_summary_and_full_sheet_with_portrait(llm):
    from oathforge.bot.handlers import commands

    p = Player(llm, tg_id=12)
    await create(p)
    await p.press("hero|-|-")  # 🧝 Hero (fixed keyboard / buttons): summary, no photo
    assert "Aldric" in p.last[0] and "CD" not in p.last[0] and not p.chat.photos
    full = p.find("sheet")

    await p.press(full)
    assert isinstance(p.chat.photos[-1], bytes)  # first time: upload the portrait
    assert "Aldric" in p.chat.sent[-2][0]  # caption, then the full sheet below it
    sheet = p.last[0]
    assert "Combate" in sheet and "al impacto" in sheet and "Percepción pasiva" in sheet
    assert "Orígenes" in sheet and p.find("hero")

    await commands.sheet(p.update(message="/sheet"), p.ctx)
    assert p.chat.photos[-1] == "FILE1"  # cached file_id, no upload
    assert "Combate" in p.last[0]


async def test_full_sheet_without_portrait_shows_spellcasting(llm, monkeypatch):
    from oathforge.content.media import MediaCatalog

    monkeypatch.setattr(MediaCatalog, "class_images", lambda self, cls, gender=None: [])  # a class with no art yet
    p = Player(llm, tg_id=13)
    await create(p, cls="sorcerer")
    await p.press("sheet|-|-")
    assert not p.chat.photos
    assert "Conjuros" in p.last[0] and "CD" in p.last[0]


async def test_journal_missions_and_bestiary_views(llm, monkeypatch):
    monkeypatch.setattr(exploration, "npcs_present",
                        lambda loc, now=None: {"adventurers_guild": ["vale"]}.get(loc, []))
    p = Player(llm, tg_id=62)
    await create(p)
    assert any("ve al gremio" in t_ for t_, _ in p.chat.sent[-2:])  # the plaza points at the guild hall
    await p.press("jr|-|-")
    assert "Alistamiento" in p.last[0]
    await p.press(p.find("jrm"))
    await p.press(p.find("jq", "tut_muster"))
    assert "Vale" in p.last[0] and "25 XP" in p.last[0]
    await p.press(p.find("jrm"))
    assert "jq|tut_town|-" not in p.buttons()  # /quests: only what is in progress
    await p.press("jq|tut_town|-")
    assert "🔒" in p.last[0]
    # talking to the sergeant and reading the rulebook's Activities page complete the first mission
    await p.press(p.find("trv"))
    await p.press(p.find("go", "adventurers_guild"))  # she is at the guild hall, off the plaza
    await p.press("talk|vale|-")
    await p.press("rb|activities|-")
    assert "Actividades" in p.chat.sent[-2][0] and "Alistamiento" in p.last[0]
    await p.press("jq|tut_town|-")
    assert "Barrio de Oficios" in p.last[0] and "Bram" in p.last[0]
    await p.press(p.find("jrm"))  # finished missions now live under the current ones
    assert "1 terminada" in p.last[0] and "jq|tut_muster|-" in p.buttons()
    await p.press("jq|tut_muster|-")
    assert "jrm|-|-" in p.buttons()  # back to the missions tab
    await p.press("jrl|-|-")  # the old log button opens the chronicle
    assert "Alistamiento" in p.last[0] and "Día 1" in p.last[0]
    await p.press("jrb|-|-")
    assert "0/25" in p.last[0]
    await p.press("jrr|-|-")
    assert p.last[0]


async def test_bestiary_icon_per_creature_and_illustration(llm):
    p = Player(llm, tg_id=64)
    await create(p)
    await p.press("jbi|cave_bat|-")  # never seen: no photo, just "unknown"
    assert not p.chat.photos and [parse(d)[0] for d in p.buttons()] == ["jrb"]
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.bestiary = {"cave_bat": {"seen": 1, "killed": 0}, "boar": {"seen": 2, "killed": 1}}
    await p.press("jrb|-|-")
    names = [b.text for row in p.last[1].inline_keyboard for b in row]
    assert any(n.startswith("🦇 Murciélago") for n in names) and any(n.startswith("🐗 Jabalí") for n in names)
    await p.press(p.find("jb", "cave_bat"))
    assert p.last[0].startswith("🦇")
    await p.press(p.find("jbi", "cave_bat"))
    assert isinstance(p.chat.photos[-1], bytes)
    assert "Murciélago" in p.chat.sent[-2][0]  # caption, then the entry again below it
    assert p.last[0].startswith("🦇") and "jbi" in [parse(d)[0] for d in p.buttons()]


async def test_item_and_monster_pages(llm):
    p = Player(llm, tg_id=72)
    await create(p)
    await p.press(p.find("trv"))
    await p.press(p.find("go", "adventurers_guild"))  # Vale signs recruits up at the guild hall
    await p.press("talk|vale|-")
    await p.press("rb|activities|-")  # Mustering In: the knife, with its link
    assert "/item_skinning_knife" in p.last[0]
    await commands.item(p.update(message="/item_skinning_knife"), p.ctx)
    assert "Cuchillo de desollar" in p.last[0] and "Desuello" in p.last[0] and "Vale 8 de oro" in p.last[0]
    await commands.item(p.update(message="/item_nope"), p.ctx)
    assert "No conozco ese objeto" in p.last[0]
    await commands.monster(p.update(message="/monster_cave_bat"), p.ctx)
    assert p.chat.photos and "Murciélago de cueva" in p.last[0]  # the picture and its name, nothing else
    await p.press("inv|-|-")  # the summary: what you wear and how much of each kind
    assert "Llevas puesto" in p.last[0] and "🧰 Herramientas 2" in p.last[0] and "inv|tools|-" in p.buttons()
    await p.press("inv|tools|-")
    assert "🔪 Cuchillo de desollar · /item_skinning_knife" in p.last[0]
    assert "• 🧰 Herramientas •" in str(p.last[1].inline_keyboard) and "inv|-|-" in p.buttons()  # back: the summary


async def test_masteries_and_hobbies_pages(llm):
    p = Player(llm, tg_id=73)
    await commands.masteries(p.update(message="/masteries"), p.ctx)  # no character needed
    assert "Minería" in p.last[0] and "/item_pickaxe" in p.last[0] and "Mina del Paso Viejo" in p.last[0]
    await create(p)
    await p.press("hob|-|-")
    assert "Cocina" in p.last[0] and "Pesca" in p.last[0] and "☆" in p.last[0]
    assert {"prof|-|-", "mst|-|-"} <= set(p.buttons())


async def test_journal_statistics(llm):
    p = Player(llm, tg_id=75)
    await create(p)
    await p.press("trv|-|-")
    await p.press(p.find("go", "broken_crown_tavern"))
    await p.press("jr|-|-")
    await p.press(p.find("jrs"))
    assert "Estadísticas" in p.last[0] and "Lugares visitados: 1" in p.last[0] and "yardas" in p.last[0]
    assert "Distancia recorrida: 0 yardas" not in p.last[0]


def test_every_class_ability_has_its_long_text():
    from oathforge.content import get_content
    missing = [f"{k}.{a}" for k, cl in get_content().classes.items() for a, ab in cl.abilities.items() if not ab.details]
    assert missing == []
