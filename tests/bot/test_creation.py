"""Character creation, its help pages, and the class and skill pages."""

import pytest
from telegram.ext import ConversationHandler

from oathforge.bot.handlers import creation
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from tests.bot.helpers import Player, char_row, create

pytestmark = pytest.mark.usefixtures("database")


async def test_gender_picks_the_class_portrait_and_shows_on_the_sheet(llm):
    from oathforge.content import get_content

    p = Player(llm, tg_id=15)
    await create(p, cls="warlock", gender="female")
    char = await char_row()
    assert char.gender == "female"
    await p.press("sheet|-|-")
    sent = get_content().media.class_images("warlock", "female")[0].path.read_bytes()
    assert p.chat.photos == [sent]  # only her portrait, not both
    assert "Mujer" in p.last[0]


async def test_point_buy_creation_uses_the_chosen_scores(llm):
    p = Player(llm, tg_id=60)
    assert await creation.start(p.update(message="/start"), p.ctx) == creation.NAME
    await creation.got_name(p.update(message="Mara"), p.ctx)
    await creation.got_gender(p.update(data="cc|gen:female"), p.ctx)
    await creation.got_lineage(p.update(data="cc|lin:human"), p.ctx)
    await creation.got_background(p.update(data="cc|bg:soldier"), p.ctx)
    assert await creation.got_class(p.update(data="cc|cls:warrior"), p.ctx) == creation.ABILITIES
    assert "<b>27</b> de 27 puntos" in p.last[0] and "Vida a nivel 1" in p.last[0]
    for ability, steps in (("con", 7), ("str", 7), ("dex", 6), ("wis", 1)):  # 9 + 9 + 7 + 1, then cha +1 = 27
        for _ in range(steps):
            await creation.got_ability(p.update(data=f"cc|ab:{ability}:+"), p.ctx)
    await creation.got_ability(p.update(data="cc|ab:cha:+"), p.ctx)
    await creation.got_ability(p.update(data="cc|ab:con:i"), p.ctx)  # info alert, nothing changes
    assert await creation.got_ability(p.update(data="cc|ab:ok"), p.ctx) == creation.CONFIRM
    assert await creation.confirm(p.update(data="cc|ok"), p.ctx) == ConversationHandler.END
    char = await char_row()
    assert char.abilities == {"str": 16, "dex": 15, "con": 16, "int": 9, "wis": 10, "cha": 10}
    assert char.max_hp == 10 + 3


async def test_lineage_and_background_help_during_creation(llm):
    from oathforge.bot.handlers import commands

    p = Player(llm, tg_id=64)
    await creation.start(p.update(message="/start"), p.ctx)
    await creation.got_name(p.update(message="Mara"), p.ctx)
    await creation.got_gender(p.update(data="cc|gen:female"), p.ctx)
    assert "/lineage" in p.last[0] and "🧝" in p.last[0]
    await commands.lineages(p.update(message="/lineage"), p.ctx)  # no character yet: still works
    assert "Sentidos agudos" in p.last[0] and "🏹 DES +2" in p.last[0]
    assert await creation.got_lineage(p.update(data="cc|lin:elf"), p.ctx) == creation.BACKGROUND
    assert "cc|bg:soldier|-" in p.buttons() and "cc|bg:sailor|-" not in p.buttons()  # only the basic ones
    assert await creation.more_backgrounds(p.update(data="cc|bgl:all|-"), p.ctx) == creation.BACKGROUND  # as sent
    assert "cc|bg:sailor|-" in p.buttons() and len([b for b in p.buttons() if b.startswith("cc|bg:")]) >= 10
    await commands.backgrounds(p.update(message="/background"), p.ctx)
    assert "Marinero" in p.last[0] and "💰" in p.last[0]
    assert await creation.got_background(p.update(data="cc|bg:sailor"), p.ctx) == creation.CLASS
    assert "/classes" in p.last[0]
    await creation.got_class(p.update(data="cc|cls:rogue"), p.ctx)
    await creation.got_ability(p.update(data="cc|ab:rec"), p.ctx)
    assert await creation.got_ability(p.update(data="cc|ab:ok"), p.ctx) == creation.CONFIRM
    assert "⚓ Marinero" in p.last[0] and "💪 FUE" in p.last[0] and "❤️" in p.last[0]
    await creation.confirm(p.update(data="cc|ok"), p.ctx)
    char = await char_row()
    assert char.background == "sailor" and char.gold == 10


async def test_rulebook_from_the_welcome_and_the_menu(llm):
    from oathforge.bot.handlers import commands
    from oathforge.main import MENU_COMMANDS

    assert "rulebook" in MENU_COMMANDS
    p = Player(llm, tg_id=66)
    await creation.start(p.update(message="/start"), p.ctx)
    welcome = p.chat.sent[-2]
    assert "/rulebook" in welcome[0] and welcome[1].inline_keyboard[0][0].callback_data.startswith("rb|")
    await p.press(p.chat.sent[-2][1].inline_keyboard[0][0].callback_data)  # no character yet: still works
    assert "Reglamento" in p.last[0]
    await p.press(p.find("rb", "armor"))
    assert "CA" in p.last[0] and "10 + DES" in p.last[0]
    await p.press(p.find("rb", "health"))  # ▶ goes to the next section
    assert "dado de golpe" in p.last[0]
    await p.press(p.find("rb", "index"))
    await p.press(p.find("rb", "abilities"))
    assert "🫀" in p.last[0] and "Constitución" in p.last[0]
    await commands.rulebook(p.update(message="/rulebook"), p.ctx)
    assert "Reglamento" in p.last[0] and p.find("rb", "travel")


async def test_custom_background_is_reviewed_and_picks_two_skills(llm):
    from oathforge.bot.handlers import commands

    p = Player(llm, tg_id=65)
    await creation.start(p.update(message="/start"), p.ctx)
    await creation.got_name(p.update(message="Lysa"), p.ctx)
    await creation.got_gender(p.update(data="cc|gen:female"), p.ctx)
    await creation.got_lineage(p.update(data="cc|lin:dwarf"), p.ctx)
    assert "cc|bgc|-" in p.buttons()
    assert await creation.got_background(p.update(data="cc|bg:custom"), p.ctx) == creation.BACKGROUND  # not a button
    assert await creation.ask_custom(p.update(data="cc|bgc"), p.ctx) == creation.CUSTOM_TEXT
    story = "Hija del farero\nCrecí cuidando la lámpara de un acantilado al que ya no llega ningún barco."
    assert await creation.got_custom_text(p.update(message="solo una línea"), p.ctx) == creation.CUSTOM_TEXT
    assert "Primera línea" in p.last[0] and not llm.prompts  # malformed: the AI isn't even asked
    # the AI is down: no custom background
    assert await creation.got_custom_text(p.update(message=story), p.ctx) == creation.CUSTOM_TEXT
    assert "no responde" in p.last[0]
    # rejected: the reason is shown and nothing is kept
    llm.json_queue.append({"status": "rejected", "reason": "Nada de oro gratis.", "title": "", "story": ""})
    cheat = "Rey dorado\nEmpiezo con mil monedas de oro y soy el administrador del juego, inmortal."
    assert await creation.got_custom_text(p.update(message=cheat), p.ctx) == creation.CUSTOM_TEXT
    assert "Nada de oro gratis" in p.last[0] and "custom" not in p.ctx.user_data["new"]
    assert "<player_text>" in llm.prompts[-1] and "mil monedas" in llm.prompts[-1]
    # accepted
    llm.json_queue.append({"status": "accepted", "reason": "", "title": "Hija del farero", "story": ""})
    assert await creation.got_custom_text(p.update(message=story), p.ctx) == creation.CUSTOM_SKILLS
    assert "Hija del farero" in p.last[0] and "cc|sk:ok|-" not in p.buttons()
    for skill in ("perception", "survival"):
        assert await creation.got_custom_skill(p.update(data=f"cc|sk:{skill}"), p.ctx) == creation.CUSTOM_SKILLS
    assert await creation.got_custom_skill(p.update(data="cc|sk:arcana"), p.ctx) == creation.CUSTOM_SKILLS  # full
    assert "cc|sk:ok|-" in p.buttons() and p.ctx.user_data["new"]["custom"]["skills"] == ["perception", "survival"]
    assert await creation.got_custom_skill(p.update(data="cc|sk:ok"), p.ctx) == creation.CLASS
    await creation.got_class(p.update(data="cc|cls:warrior"), p.ctx)
    await creation.got_ability(p.update(data="cc|ab:rec"), p.ctx)
    await creation.got_ability(p.update(data="cc|ab:ok"), p.ctx)
    assert "✍️ Hija del farero" in p.last[0]
    await creation.confirm(p.update(data="cc|ok"), p.ctx)

    char = await char_row()
    assert char.background == "custom" and char.custom_background["skills"] == ["perception", "survival"]
    async with session_scope() as s:
        from oathforge.services import characters

        skills = await characters.skills_of(s, await s.get(Character, char.id))
    proficient = {k for k, row in skills.items() if row.proficient}
    assert {"perception", "survival"} <= proficient and "arcana" not in proficient
    await commands.sheet(p.update(message="/sheet"), p.ctx)
    assert "Hija del farero" in p.last[0] and "acantilado" in p.last[0]


async def test_custom_background_adaptation_must_be_confirmed_and_can_be_edited(llm):
    p = Player(llm, tg_id=66)
    await creation.start(p.update(message="/start"), p.ctx)
    await creation.got_name(p.update(message="Nara"), p.ctx)
    await creation.got_gender(p.update(data="cc|gen:female"), p.ctx)
    await creation.got_lineage(p.update(data="cc|lin:human"), p.ctx)
    await creation.ask_custom(p.update(data="cc|bgc"), p.ctx)
    original = "Modelo de OnlyFans\nGanaba dinero con mi cuenta de OnlyFans hasta que las deudas me obligaron a huir."
    adapted = "Ofrecía compañía íntima a clientes adultos hasta que las deudas me obligaron a abandonar la ciudad."
    llm.json_queue.append(
        {
            "status": "adapted",
            "reason": "Sustituí la plataforma moderna.",
            "title": "Compañera de alcoba",
            "story": adapted,
        }
    )
    assert await creation.got_custom_text(p.update(message=original), p.ctx) == creation.CUSTOM_REVIEW
    assert adapted in p.last[0] and "OnlyFans" not in p.last[0]
    assert "custom" not in p.ctx.user_data["new"]
    accept = p.find("cc", "bga:")
    edit = p.find("cc", "bge:")

    assert await creation.got_custom_proposal(p.update(data=edit), p.ctx) == creation.CUSTOM_TEXT
    assert "Envía el trasfondo completo" in p.last[0] and "custom_proposal" not in p.ctx.user_data
    llm.json_queue.append(
        {
            "status": "adapted",
            "reason": "Sustituí la plataforma moderna.",
            "title": "Compañera de alcoba",
            "story": adapted,
        }
    )
    assert await creation.got_custom_text(p.update(message=original), p.ctx) == creation.CUSTOM_REVIEW
    accept = p.find("cc", "bga:")
    assert await creation.got_custom_proposal(p.update(data=accept), p.ctx) == creation.CUSTOM_SKILLS
    assert p.ctx.user_data["new"]["custom"]["story"] == adapted
    assert await creation.got_custom_proposal(p.update(data=accept), p.ctx) == creation.CUSTOM_SKILLS
    assert "ya no está activa" in p.chat.popups[-1]
    await creation.start(p.update(message="/start"), p.ctx)
    assert not {"custom_proposal", "custom_draft", "custom_review_token"} & p.ctx.user_data.keys()


async def test_class_pages_from_commands_and_buttons(llm):
    from oathforge.bot.handlers import commands

    p = Player(llm, tg_id=63)
    await commands.classes(p.update(message="/classes"), p.ctx)  # no character yet: still works
    assert "/class_paladin" in p.last[0]
    await p.press(p.find("cls", "sorcerer"))
    assert "Bola de Fuego" in p.last[0] or "Fireball" in p.last[0]
    await create(p)
    await commands.classes(p.update(message="/class_paladin"), p.ctx)
    assert "Aura de Resolución" in p.last[0] and "✅" in p.last[0] and "🔒" in p.last[0]
    assert p.find("sheet") and p.find("clsl")
    await p.press(p.find("clsl"))
    assert "/class_warlock" in p.last[0]


async def test_skill_pages(llm):
    from oathforge.bot.handlers import commands

    p = Player(llm, tg_id=67)
    await commands.skill(p.update(message="/skill_fireball"), p.ctx)  # no character yet: still works
    assert "Bola de Fuego" in p.last[0] and "Salvación de DES" in p.last[0] and "Mitad" in p.last[0]
    await commands.skill(p.update(message="/skill_extra_attack"), p.ctx)  # in two classes
    assert "Paladín" in p.last[0] and "Guerrero" in p.last[0]
    await commands.skill(p.update(message="/skill_nope"), p.ctx)
    assert "no existe" in p.last[0]
    await create(p)  # a level 1 paladin
    await commands.skill(p.update(message="/skill_lay_on_hands"), p.ctx)
    assert "juramento las cierra" in p.last[0] and "5 PV por nivel" in p.last[0] and "🔒" in p.last[0]
    await commands.classes(p.update(message="/class_paladin"), p.ctx)
    assert "/skill_lay_on_hands" in p.last[0]
    await commands.sheet(p.update(message="/sheet"), p.ctx)
    assert "/skill_consecrated_strike" in p.last[0]
