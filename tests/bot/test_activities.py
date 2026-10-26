"""Field activities, professions and crafting through the buttons and commands."""

from types import SimpleNamespace

import pytest
from sqlalchemy import select

from oathforge.bot.handlers import commands
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.engine import timings
from tests.bot.helpers import FakeBot, Player, char_row, create

pytestmark = pytest.mark.usefixtures("database")


async def test_mining_buttons_collect_and_chronicle(llm):
    from oathforge.database.models import WorldActivity
    from oathforge.services import inventory

    p = Player(llm, tg_id=63)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "ironvein_mine"
        await inventory.add_item(s, char, "pickaxe")
    await p.press("acts|-|-")
    sent = len(p.chat.sent)
    await p.press(p.find("act", "gather:mining"))
    assert len(p.chat.sent) == sent + 1  # the Activities message becomes "you start working"
    assert "Te pones a trabajar" in p.last[0] and "Minería" in p.last[0]
    assert (
        f"Termina en {timings.GATHER_SECONDS // 60} min" in p.last[0]
        and "actx" in str(p.buttons())
        and "Recoger" not in str(p.last[1])
    )
    await p.press(p.find("actc"))  # 🔄 Refresh before the end: just the panel again, no error
    assert "Termina en" in p.last[0] and "Aún no ha terminado" not in p.chat.sent[-2][0]
    await p.press("trv|-|-")  # an old travel button: the travel menu is not offered while busy
    assert "Termina en" in p.last[0]
    async with session_scope() as s:
        act = await s.scalar(select(WorldActivity).with_for_update())
        act.ends_at -= 600  # five minutes later
    await p.press("scene|-|-")
    llm.text_queue.append("Aldric arranca la mena de la roca con paciencia.")
    await p.press(p.find("actc"))
    result = p.last[0]  # chronicle, loot and the scene's buttons in a single message
    assert "⛏️" in result and "Terminas tu trabajo" in result and "Aldric arranca" in result
    assert ("Mena de hierro" in result or "Carbón" in result) and "XP de Minería" in result and "1/15" in result
    assert "Viajar" in str(p.last[1].inline_keyboard)  # back to the normal scene


async def test_activities_end_by_themselves_even_offline(llm):
    from oathforge.bot.handlers import common
    from oathforge.database.models import WorldActivity
    from oathforge.services import inventory

    p = Player(llm, tg_id=74)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "ironvein_mine"
        await inventory.add_item(s, char, "pickaxe")
    await p.press("acts|-|-")
    await p.press(p.find("act", "gather:mining"))
    job = SimpleNamespace(bot=FakeBot(p.chat), bot_data={"llm": llm})
    sent = len(p.chat.sent)
    await common.finish_due_activities(job)  # not over yet: nothing
    assert len(p.chat.sent) == sent
    async with session_scope() as s:
        act = await s.scalar(select(WorldActivity).with_for_update())
        act.ends_at -= 600
    await common.finish_due_activities(job)
    delivered = p.chat.sent[sent:]
    assert any("Terminas tu trabajo" in text for text, _ in delivered)
    assert any("Viajar" in str(getattr(kb, "inline_keyboard", ())) for _, kb in delivered)
    assert "Logros conseguidos" in p.last[0] and "ach|" in str(p.last[1].inline_keyboard)
    sent = len(p.chat.sent)
    await common.finish_due_activities(job)  # paid once
    await p.press("actc|-|x1")  # an old Refresh button
    assert "Terminas tu trabajo" not in "".join(t_ or "" for t_, _ in p.chat.sent[sent:])


async def test_learn_a_profession_and_craft(llm):
    from oathforge.services import inventory

    p = Player(llm, tg_id=64)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "alchemist_stall"  # Ilva teaches alchemy and her table is here
        await inventory.add_item(s, char, "bloodroot", 2)
        await inventory.add_item(s, char, "water_flask", 1)
    await p.press("acts|-|-")
    await p.press(p.find("prof"))
    assert "0/2" in p.last[0]
    await p.press(p.find("plearn", "alchemy"))
    assert "Alquimia" in p.last[0] and "1/2" in p.last[0]  # the result on top of the same menu
    await p.press("acts|-|-")
    await p.press(p.find("crf"))
    assert "✅" in p.last[0]
    await p.press(p.find("craft", "healing_potion"))
    assert "Poción de curación" in p.last[0]
    assert "❌" in p.last[0]  # no more bloodroot


async def test_the_craft_stalls_hang_off_their_street(llm):
    """One stall per trade, grouped under Craftsmen's Row so the city map stays short."""
    p = Player(llm, tg_id=93)
    await create(p)
    await p.press(p.find("trv"))
    assert "Barrio de Oficios" in p.last[0] and "Forja de Tessa" in p.last[0]
    assert not any(b.startswith("go|forge_stall") for b in p.buttons())  # not one button per stall
    await p.press(p.find("trvs", "crownreach_workshops"))
    assert "puestos" in p.last[0] and "Curtiduría" in p.last[0]
    await p.press(p.find("go", "forge_stall"))
    assert (await char_row()).location == "forge_stall"
    await p.press("acts|-|-")
    assert "Herrería" in p.last[0]  # Tessa teaches her trade here
    await p.press(p.find("prof"))
    assert "plearn|blacksmithing" in str(p.buttons()) and "plearn|alchemy" not in str(p.buttons())


async def test_recipes_list_card_and_craft_command(llm):
    """/recipes by tabs, /r_<id> with where each ingredient comes from, and /craft_<id> n in one message."""
    from oathforge.services import characters, inventory

    p = Player(llm, tg_id=94)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "adventurers_guild"
        await inventory.add_item(s, char, "iron_ore", 9)
        await inventory.add_item(s, char, "coal", 3)
    await commands.recipes(p.update(message="/recipes"), p.ctx)
    assert "Recetas" in p.last[0] and "/r_iron_ingot" in p.last[0]
    await p.press(p.find("rcl", "missing"))
    assert "Faltan materiales" in p.last[0]
    await commands.recipe(p.update(message="/r_iron_ingot"), p.ctx)
    assert "Lingote de hierro" in p.last[0] and "horno de fundición" in p.last[0]
    assert "3/3" in p.last[0] and "Minería" in p.last[0]
    assert any(b.startswith("craft|iron_ingot:3") for b in p.buttons())  # x1, x5 capped by the materials
    await commands.craft(p.update(message="/craft_iron_ingot 2"), p.ctx)
    assert "Lingote de hierro" in p.last[0]
    async with session_scope() as s:
        char = await s.scalar(select(Character))
        assert await inventory.count(s, char, "iron_ingot") == 2
        assert characters.mastery_xp(char, "mining") == 20  # refining pays the mastery


async def test_activities_view_offers_only_what_can_start(llm):
    """⚒ Activities: without a pickaxe, mining is not a button but the way to the shop that sells it."""
    from oathforge.services import activities, inventory

    p = Player(llm, tg_id=91)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "ironvein_mine"
    await commands.fixed_button(p.update(message="⚒ Actividades"), p.ctx)
    assert "Actividades" in p.last[0] and "Te falta: Pico" in p.last[0]
    assert not any(b.startswith("act|gather:mining") for b in p.buttons())
    assert any(b.startswith("go|forge_stall") for b in p.buttons())  # 🛒 Pico · ir a la Forja de Tessa
    async with session_scope() as s:  # the view and the service agree
        char = await s.scalar(select(Character))
        refusal = dict(((k, sk), r) for k, sk, r in await activities.availability(s, char))[("gather", "mining")]
        assert refusal.error == "activity.err.no_tool"
        assert (await activities.start(s, char, "gather", "mining")).error == "activity.err.no_tool"
        await inventory.add_item(s, char, "pickaxe")
    await p.press("acts|-|-")
    assert "act|gather:mining" in str(p.buttons()) and "Pico de minero ✅" in p.last[0]
