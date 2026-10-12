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
            text = render.outcome_text(o, lang)  # hit-by-hit logs live in the panel, rewards stay here
            if text:
                check(text)
                assert "🗡️" not in text and "💨" not in text
            check(render.combat_panel(char, enc.state, lang))
        check(render.combat_panel(char, enc.state, lang))
        assert enc.status == "victory"
        # the panel log must not leak raw i18n keys
        text, _ = render.combat_panel(char, enc.state, lang)
        assert "combat." not in text and "status." not in text and "dmg." not in text
        assert "🛡️" in text  # AC next to each combatant
        # a crit with its damage indented below it, a miss, and a new round as a separator
        from oathforge.engine.combat import EncounterState, LogEntry
        state = EncounterState.model_validate(enc.state)
        entries = [LogEntry(key="combat.round", params={"round": 2}),
                   LogEntry(key="combat.crit", params={"actor": "p1", "target": "m1", "weapon": {"es": "Espada", "en": "Sword"},
                                                       "roll": 20, "total": 25, "ac": 13, "adv": False, "dis": False,
                                                       "crit": True, "sneak": 0}),
                   LogEntry(key="combat.damage", params={"target": "m1", "amount": 14, "type": "slashing",
                                                         "effect": "", "hp": 0, "max_hp": 30}),
                   LogEntry(key="combat.defeated", params={"target": "m1"}),
                   LogEntry(key="combat.miss", params={"actor": "m2", "target": "p1", "weapon": {"es": "Garra", "en": "Claw"},
                                                       "roll": 3, "total": 7, "ac": 18, "adv": False, "dis": False})]
        blocks = render.combat_blocks(state, entries, lang)
        assert len(blocks) == 3
        assert blocks[0][0].startswith("<i>") and "2" in blocks[0][0]
        crit = blocks[1]
        assert crit[0].startswith("<b>💥") and "🎲 20 +5 = 25" in crit[0] and "🛡️ 13" in crit[0]
        assert crit[1].startswith("   └ 🩸") and "❤️ 0/30" in crit[1] and crit[2].startswith("   └ 💀")
        assert blocks[2][0].startswith("💨") and "❌" in blocks[2][0]
        check("\n".join(line for b in blocks for line in b))


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


@pytest.mark.parametrize("lang", ["es", "en"])
async def test_level_up_cards_are_separate_messages(lang):
    from oathforge.services.events import Outcome

    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 7, lang)
        char = await characters.create_character(s, user, "Edda", "dwarf", "acolyte", "paladin")
        out = Outcome().add("loot.gold", gold=5)
        start_hp = char.max_hp
        characters.grant_xp(char, 1800, out)  # level 1 → 5 at once

    bullets = render.outcome_text(out, lang)
    assert "🪙" in bullets and "✨" in bullets  # gold and XP stay in the bullet message
    assert "🎉" not in bullets and "🌟" not in bullets
    cards = render.level_up_cards(out, lang)
    assert len(cards) == 4  # one card per level gained
    for card in cards:
        check(card)
        assert "/class_paladin" in card and "progress." not in card and "ability." not in card
    aura = get_content().classes["paladin"].abilities["aura_of_resolve"]
    assert aura.description.get(lang) in cards[1]  # level 3 explains the new ability
    assert f"{start_hp} →" in cards[0]
    assert "💪" in cards[2]  # level 4: attribute boost


@pytest.mark.parametrize("lang", ["es", "en"])
async def test_class_pages(lang):
    from oathforge.bot.handlers.commands import CLASS_LINK

    c = get_content()
    text, kb = render.classes_list(lang)
    check((text, kb))
    for key, cl in c.classes.items():
        assert f"/class_{key}" in text
        page, page_kb = render.class_page(key, lang)
        check((page, page_kb))
        assert "classes." not in page and "ability." not in page and "🔒" not in page
        for a in cl.abilities.values():
            assert a.description.get(lang) in page.replace("&#x27;", "'")
        assert CLASS_LINK.match(f"/class_{key}").group(1) == key
        assert CLASS_LINK.match(f"/class_{key}@OathForgeBot").group(1) == key
    unknown, _ = render.class_page("nope", lang)
    assert "/class_paladin" in unknown

    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 8, lang)
        char = await characters.create_character(s, user, "Edda", "dwarf", "acolyte", "paladin")
        page, _ = render.class_page("paladin", lang, char)  # own class: unlocked ✅, the rest 🔒
        assert "✅" in page and "🔒" in page
        sheet, _ = await render.sheet(s, char, lang)
        assert "/class_paladin" in sheet


@pytest.mark.parametrize("lang", ["es", "en"])
async def test_battle_report(lang):
    from oathforge.engine.combat import Action

    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 9, lang)
        char = await characters.create_character(s, user, "Edda", "dwarf", "acolyte", "paladin")
        assert await combat_service.battle_report(s, char) is None
        check(render.report_page(None, 0, lang))
        char.location = "crypt_sanctum"
        char.hp = char.max_hp = 300
        enc, _ = await combat_service.start_encounter(s, char, ["crypt_skeleton", "crypt_skeleton"], random.Random(5))
        rng = random.Random(6)
        while enc.status == "active":
            await combat_service.act(s, char, enc, Action(kind="attack", weapon="main"), rng)
        await s.flush()
        assert enc.status == "victory"
        panel, kb = render.combat_panel(char, enc.state, lang)
        assert "rep|-|-" in [b.callback_data for row in kb.inline_keyboard for b in row]

        report = await combat_service.battle_report(s, char)
        assert report.encounter_id == enc.id and report.status == "victory"
        assert [n for n, _ in report.rounds] == list(range(1, len(report.rounds) + 1))
        assert report.rounds[0][1][0].key == "combat.initiative"  # the opening logs are kept too
        assert len(report.rounds) == report.state.round
        everything = [e for _, es in report.rounds for e in es]
        dealt = sum(e.params["amount"] for e in everything if e.key == "combat.damage" and e.params["target"] != "p1")
        assert report.stats["dealt"] == dealt > 0
        assert report.stats["defeated"] == {"crypt_skeleton": 2}
        assert report.stats["hits"] <= report.stats["attacks"]
        assert any(ev.key == "progress.xp" for ev in report.rewards)

        summary, kb = render.report_page(report, 0, lang)
        check((summary, kb))
        assert "✨" in summary and "report." not in summary
        for page in range(1, len(report.rounds) + 1):
            text, kb = render.report_page(report, page, lang)
            check((text, kb))
            assert "combat." not in text
        data = [b.callback_data for row in kb.inline_keyboard for b in row]
        assert f"rep|{enc.id}:0|-" in data or len(report.rounds) == 1
