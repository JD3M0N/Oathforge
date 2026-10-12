"""Smoke-render every view in both languages and check Telegram-safe HTML."""

import random
from html.parser import HTMLParser

import pytest
from sqlalchemy import select

from oathforge.bot import render
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.services import characters, combat_service, quests

pytestmark = pytest.mark.usefixtures("database")
ALLOWED = {"b", "i", "s", "u", "code", "pre", "a"}


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        assert tag in ALLOWED, f"tag <{tag}> not allowed by Telegram"
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, f"unbalanced </{tag}>"


def check(view):
    text, kb = view if isinstance(view, tuple) else (view, None)
    assert text and len(text) <= 4096
    p = TagChecker()
    p.feed(text)
    assert not p.stack, f"unclosed {p.stack}"
    if kb is not None:
        for row in kb.inline_keyboard:
            for b in row:
                assert len(b.callback_data.encode()) <= 64, b.callback_data


@pytest.mark.parametrize("lang", ["es", "en"])
async def test_all_views_render(lang):
    c = get_content()
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 5, lang)
        char = await characters.create_character(s, user, "Edda <x>", "dwarf", "acolyte", "paladin")
        for loc in c.locations:
            char.location = loc
            check(await render.scene(s, char, lang))
            check(render.travel_menu(char, lang))
            check(render.talk_menu(char, lang))
            check(render.shop_menu(char, lang))
        for npc in c.npcs:
            check(await render.conversation(s, char, npc, lang))
            check(await render.conversation(s, char, npc, lang, line="<script>alert(1)</script> & co"))
            if c.npcs[npc].shop:
                check(await render.shop(s, char, npc, lang))
                check(await render.sell_menu(s, char, npc, lang))
        check(await render.sheet(s, char, lang))
        check(await render.inventory_view(s, char, lang))
        check(await render.journal(s, char, lang))
        check(await render.missions(s, char, lang))
        for key in c.quests:
            check(await render.mission(s, char, key, lang))
        check(await render.rumors(s, lang))
        check(render.bestiary_list(char, lang))
        for kills in (0, 1, 3):  # every reveal level of every stat block
            char.bestiary = {k: {"seen": 1, "killed": kills} for k in c.monsters}
            check(render.bestiary_list(char, lang))
            for key in c.monsters:
                text, _ = render.bestiary_entry(char, key, lang)
                check(text)
                assert "bestiary." not in text and "creature." not in text and "dmg." not in text

        prog = (await quests.progress(s, char, lock=True))["sealed_box"]
        prog.stage, prog.state = "not_started", "available"
        char.location = "whispering_woods"
        out = await quests.perform(s, char, "sealed_box.approach_guard", [], random.Random(0))
        check(render.outcome_text(out, lang, narration="Llueve <fuerte> & frío"))

        char.location = "crypt_sanctum"
        char.hp = char.max_hp = 300
        enc, out = await combat_service.start_encounter(s, char, ["crypt_warden", "crypt_skeleton"], random.Random(2))
        check(render.outcome_text(out, lang))
        check(render.combat_panel(char, enc.state, lang))
        check(render.combat_panel(char, enc.state, lang, target_menu="atk:main"))
        check(render.combat_panel(char, enc.state, lang, target_menu="obj:iron_chandelier"))
        from oathforge.engine.combat import Action
        rng = random.Random(4)
        for _ in range(60):
            if enc.status != "active":
                break
            o = await combat_service.act(s, char, enc, Action(kind="attack", weapon="main"), rng)
            check(render.outcome_text(o, lang))
        check(render.combat_panel(char, enc.state, lang))
        assert enc.status == "victory"
        # the panel log must not leak raw i18n keys
        text, _ = render.combat_panel(char, enc.state, lang)
        assert "combat." not in text and "status." not in text and "dmg." not in text


@pytest.mark.parametrize("lang", ["es", "en"])
async def test_hero_sheet_shows_gear_and_ai_budget(lang):
    from oathforge.ai.client import Budget
    from oathforge.config import Settings

    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 6, lang)
        char = await characters.create_character(s, user, "Edda", "dwarf", "acolyte", "paladin")
        user_id = user.id
    await Budget(Settings()).record(user_id, "m", 1, 1)
    async with session_scope() as s:
        char = await characters.get_character(s, user_id)
        text, kb = await render.sheet(s, char, lang)
    check((text, kb))
    limit = Settings().ai_user_daily_calls
    assert f"1/{limit}" in text
    assert Settings.model_fields["ai_user_daily_calls"].default == 150  # testing phase (0.2.x)
    assert get_content().items["longsword"].name.get(lang) in text
    assert "🔒" in text  # higher-level abilities appear locked
