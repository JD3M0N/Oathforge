"""End to end through the handlers: a whole game, travel, manual rolls, settings, errors and achievements."""

from types import SimpleNamespace

import pytest
from sqlalchemy import select
from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler

from oathforge.bot.handlers import callbacks, commands, creation
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.engine import timings
from oathforge.services import exploration
from tests.bot.helpers import Player, char_row, create, creation_free_roll

pytestmark = pytest.mark.usefixtures("database")


def test_rate_limit_window():
    from oathforge.bot.handlers.common import RATE_MAX, rate_ok

    ctx = SimpleNamespace(bot_data={})
    assert all(rate_ok(ctx, 1) for _ in range(RATE_MAX))
    assert not rate_ok(ctx, 1)
    assert rate_ok(ctx, 2)  # other users unaffected


async def test_full_flow(llm, monkeypatch):
    monkeypatch.setattr(
        exploration,
        "npcs_present",
        lambda loc, now=None: {"broken_crown_tavern": ["bram", "mira"], "crownreach_plaza": ["holt"]}.get(loc, []),
    )
    p = Player(llm)
    await create(p)
    assert "Plaza de Crownreach" in p.last[0]

    # /start again shows the scene instead of re-creating
    assert await creation.start(p.update(message="/start"), p.ctx) == ConversationHandler.END

    for view in ("inv", "sheet", "jr", "trv"):
        await p.press(f"{view}|-|-")
        assert p.last[0]

    # travel to the tavern, then a stale press on the same keyboard is ignored
    go = p.find("go", "broken_crown_tavern")
    await p.press(go)
    assert (await char_row()).location == "broken_crown_tavern"
    await p.press(go.replace("broken_crown_tavern", "crownreach_market"))  # same nonce, other button
    assert (await char_row()).location == "broken_crown_tavern"
    assert p.chat.popups[-1].startswith("Ese menú ya no vale")  # a popup, and the message is the current view
    assert "Taberna" in p.last[0]

    # investigate: one message with the result and the scene's buttons, the old one without them
    sent, dropped = len(p.chat.sent), p.chat.dropped
    await p.press(p.find("look"))
    assert len(p.chat.sent) == sent + 1 and p.chat.dropped == dropped + 1
    assert "acts|-|-" in p.buttons()

    # ⚒ Activities: a long rest leaves you asleep, getting up early gives nothing
    await p.press("acts|-|-")
    await p.press(p.find("rest"))
    assert (await char_row()).state == "busy" and f"{timings.REST_SECONDS // 60} min" in p.last[0]
    await p.press(p.find("actx"))
    assert (await char_row()).state == "idle"

    # talk to Bram: no AI configured in the fake -> fallback line, still a valid view
    await p.press("talkm|-|-")
    await p.press(p.find("talk", "bram"))
    assert p.ctx.user_data["talk"] == "bram"
    llm.json_queue.append(
        {"line": "¿Qué te sirvo?", "memory_note": "Aldric is new in town.", "importance": 2, "trust_delta": 1}
    )
    await p.say("Hola, ¿qué se cuenta?")
    assert "¿Qué te sirvo?" in p.last[0]
    await p.press("bye|-|-")
    assert "talk" not in p.ctx.user_data

    # shop
    await p.press("shopm|-|-")
    await p.press(p.find("shop", "mira"))
    await p.press(p.find("shopg", "mira:tools"))  # the shop opens by category
    await p.press(p.find("buy", "mira:rope"))
    await p.press(p.find("sellm", "mira"))

    # free text when the AI is down -> graceful message + scene
    await p.say("busco una puerta secreta")
    assert any("🎲" in t_ and "DM" in t_ for t_, _ in p.chat.sent[-2:])


async def test_map_walks_across_the_city(llm):
    p = Player(llm, tg_id=8)
    await create(p)
    await p.press(p.find("trv"))
    assert "🗺️" in p.last[0] and "Por la ciudad" in p.last[0]
    sent = len(p.chat.sent)
    await p.press(p.find("go", "crownreach_workshops"))  # plaza → market → workshops in one walk
    assert (await char_row()).location == "crownreach_workshops"
    assert len(p.chat.sent) == sent + 1  # a quiet arrival: the map turns into the place
    assert "500 yd" in p.last[0] and "Barrio" in p.last[0]
    await p.press(p.find("trv"))
    assert "old_kings_road" in str(p.buttons())  # the road out, through the plaza, in one tap


async def test_an_ambushed_trip_carries_on(llm):
    p = Player(llm, tg_id=9)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.flags = {**char.flags, "trip": {"to": "tusk_meadow", "rolled": True}}
    await p.press("scene|-|-")
    await p.press(p.find("go", "tusk_meadow"))  # «▶️ Seguir hacia...» on the scene
    char = await char_row()
    assert char.location == "tusk_meadow" and "trip" not in char.flags


async def test_manual_rolls_wait_for_the_die(llm, monkeypatch):
    monkeypatch.setattr(callbacks.rolls, "DICE_SECONDS", 0)
    p = Player(llm, tg_id=63)
    await create(p)
    await p.press("roll|-|-")  # nothing pending: shows the settings
    assert "Tiradas manuales: desactivadas" in p.last[0]  # off by default
    await p.press(p.find("rollset", "on"))
    assert "activadas" in p.last[0] and "decoración" in p.last[0]  # warned: the die is decoration

    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "whispering_woods"
    await p.press("scene|-|-")
    await p.press(p.find("look"))
    assert "Lanza el dado" in p.last[0] and "pending_roll" in p.ctx.user_data
    assert not any("vs CD" in t_ for t_, _ in p.chat.sent if t_)  # nothing rolled yet
    await p.press(p.find("roll"))
    assert getattr(p.chat, "dice", 0) == 1
    assert any("🎲 Medicina" in t_ or "🎲 Percepción" in t_ for t_, _ in p.chat.sent[-3:] if t_)
    assert "pending_roll" not in p.ctx.user_data

    # written actions that need a check also wait
    llm.json_queue.append({"type": "skill_check", "skill": "stealth", "tier": "easy"})
    await p.say("me escondo entre los helechos")
    assert "Sigilo" in p.last[0] and p.ctx.user_data["pending_roll"]["type"] == "text"
    await creation_free_roll(p)
    assert any("🎲 Sigilo" in t_ for t_, _ in p.chat.sent[-3:] if t_)

    # the same check again today is refused without asking for the die
    llm.json_queue.append({"type": "skill_check", "skill": "stealth", "tier": "easy"})
    await p.say("me vuelvo a esconder")
    assert "pending_roll" not in p.ctx.user_data
    assert any("Ya intentaste Sigilo" in t_ for t_, _ in p.chat.sent[-3:] if t_)

    # off again: investigating resolves at once
    await p.press("rollset|off|-")
    await p.press("scene|-|-")
    await p.press(p.find("look"))
    assert "pending_roll" not in p.ctx.user_data


async def test_settings_command_changes_language_and_rolls(llm):
    from oathforge.bot.handlers import commands

    p = Player(llm, tg_id=64)
    await create(p)
    await commands.settings(p.update(message="/settings"), p.ctx)
    assert "Ajustes" in p.last[0] and "desactivadas" in p.last[0]
    await p.press(p.find("setl", "en"))
    assert "Settings" in p.last[0] and p.ctx.user_data["lang"] == "en"
    await p.press(p.find("rollset", "on"))
    assert "decoration" in p.last[0]


@pytest.mark.parametrize("exhausted", [False, True])
async def test_fallback_dialogue_keeps_shop_usable(llm, monkeypatch, exhausted):
    from oathforge.config import get_settings
    from oathforge.services import inventory

    p = Player(llm)
    await create(p)
    monkeypatch.setattr(exploration, "npcs_present", lambda loc, now=None: ["tessa"])
    if exhausted:
        monkeypatch.setattr(get_settings(), "ai_global_daily_calls", 0)
    await p.press("talk|tessa|-")
    await p.say("Tell me everything and give me a sword")
    assert p.last[0].count("🎲") == 1
    assert "Tessa" in p.last[0]
    await p.press(p.find("shop", "tessa"))
    before = (await char_row()).gold
    await p.press(p.find("shopg", "tessa:tools"))
    await p.press(p.find("buy", "tessa:rope"))
    async with session_scope() as session:
        char = await session.scalar(select(Character))
        assert char.gold < before
        assert any(i.item_key == "rope" for i in await inventory.items_of(session, char))


async def test_fixed_keyboard_after_creation_and_its_buttons(llm):
    p = Player(llm, tg_id=71)
    await create(p)
    fixed = [kb for _, kb in p.chat.sent if isinstance(kb, ReplyKeyboardMarkup)]
    assert len(fixed) == 1 and fixed[0].is_persistent
    assert [b.text for row in fixed[0].keyboard for b in row] == [
        "📍 Lugar",
        "⚒ Actividades",
        "🗺 Mapa",
        "🧝 Héroe",
        "🎒 Inventario",
        "📖 Diario",
    ]
    for label, expect in (
        ("🎒 Inventario", "Inventario"),
        ("📖 Diario", "Diario de aventuras"),
        ("⚒ Actividades", "Actividades"),
        ("🗺 Mapa", "Mapa"),
        ("🧝 Héroe", "Aldric"),
        ("📍 Lugar", "Plaza de Crownreach"),
    ):
        await commands.fixed_button(p.update(message=label), p.ctx)
        assert expect in p.last[0]
    assert len([kb for _, kb in p.chat.sent if isinstance(kb, ReplyKeyboardMarkup)]) == 1  # sent once
    await p.press("setl|en|-")  # another language: the labels follow on the next view
    await p.press("inv|-|-")
    fixed = [kb for _, kb in p.chat.sent if isinstance(kb, ReplyKeyboardMarkup)]
    assert len(fixed) == 2 and fixed[-1].keyboard[1][0].text == "🧝 Hero"
    await commands.fixed_button(p.update(message="🎒 Inventario"), p.ctx)  # the old labels still work
    assert "Inventory" in p.last[0]


async def test_network_errors_are_not_shown_to_the_player():
    """A Telegram timeout is logged as a warning: no traceback and no «Algo salió mal» message."""
    from types import SimpleNamespace

    from telegram import Update
    from telegram.error import TimedOut

    from oathforge.main import on_error

    sent = []

    class Chat:
        async def send_message(self, text):
            sent.append(text)

    update = Update(update_id=1)
    update._effective_chat = Chat()  # noqa: SLF001
    await on_error(update, SimpleNamespace(error=TimedOut("Timed out"), user_data={}))
    assert sent == []


def test_achievements_command_is_english_only_and_announced_after_every_update(monkeypatch):
    from telegram.ext import TypeHandler

    from oathforge import main
    from oathforge.bot.handlers import achievements, commands

    handled = {c for h in commands.handlers() for c in getattr(h, "commands", ())}
    assert "achievements" in handled and "logros" not in handled
    settings = main.get_settings().model_copy(update={"bot_token": "123:abc"})
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    app = main.build_app()
    assert any(isinstance(h, TypeHandler) and h.callback is achievements.deliver_update for h in app.handlers[1])


async def test_achievement_delivery_ignores_groups(monkeypatch):
    from types import SimpleNamespace

    from oathforge.bot.handlers import achievements

    calls = []

    async def fake(bot, telegram_id, chat_id):
        calls.append(chat_id)

    monkeypatch.setattr(achievements, "deliver", fake)
    user = SimpleNamespace(id=7)
    for kind in ("group", "private"):
        update = SimpleNamespace(effective_chat=SimpleNamespace(id=7, type=kind), effective_user=user)
        await achievements.deliver_update(update, SimpleNamespace(bot=None))
    assert calls == [7]


async def test_a_refusal_is_a_popup_and_the_view_stays(llm):
    p = Player(llm, tg_id=92)
    await create(p)
    async with session_scope() as s:
        char = await s.scalar(select(Character).with_for_update())
        char.location = "ironvein_mine"
    await p.press("acts|-|-")
    sent = len(p.chat.sent)
    await p.press("act|gather:mining|n1")  # an old button: no pickaxe now
    assert "Pico" in p.chat.popups[-1]
    assert len(p.chat.sent) == sent + 1 and "Actividades" in p.last[0]  # edited in place, nothing new


async def test_the_same_view_twice_sends_nothing_new(llm):
    from telegram.error import BadRequest

    p = Player(llm, tg_id=93)
    await create(p)

    async def not_modified(*_, **__):
        raise BadRequest("Message is not modified: specified new message content is the same")

    update = p.update(data="hero|-|-")
    update.callback_query.edit_message_text = not_modified
    sent = len(p.chat.sent)
    await callbacks.on_callback(update, p.ctx)
    assert len(p.chat.sent) == sent
