"""Fallback coverage, fact routing and graceful degradation without game effects."""

import copy
import random
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from oathforge.ai import fallbacks
from oathforge.ai.client import NullLLM
from oathforge.ai.intent_parser import Intent
from oathforge.config import get_settings
from oathforge.content import get_content, load_content
from oathforge.content.validation import validate_references
from oathforge.content.schemas import CHRONICLE_KEYS, Text
from oathforge.database.models import Character, NpcMemory, NpcRelationship
from oathforge.database.session import session_scope
from oathforge.services import actions, characters, chronicles, exploration
from oathforge.services.events import Outcome, render


def test_every_variant_renders_in_both_languages():
    content = load_content()
    values = dict(name="Aldric", npc="Bram", place="Crownreach", loot="iron", monster="boar")
    assert set(content.chronicles) == set(CHRONICLE_KEYS)
    for category, by_key in content.fallbacks.items():
        for key, variants in by_key.items():
            assert len(variants) >= 12
            for lang in ("es", "en"):
                assert len({v.get(lang).strip() for v in variants}) >= 12
                for seed in range(len(variants)):
                    text = fallbacks.pick(category, key, lang, seed=seed, **values)
                    assert text.strip() and "{" not in text and "}" not in text
                    assert "\ufffd" not in text and "??" not in text
                    if category == "dialogue" and lang == "es":
                        assert text.count("«") == text.count("»")
                    if category == "freetext":
                        assert text.startswith("🎲")


@pytest.mark.parametrize(
    "damage",
    [
        "missing_case",
        "missing_npc",
        "duplicate",
        "blank",
        "unknown_field",
        "broken_field",
        "different_fields",
        "unknown_category",
        "unknown_key",
    ],
)
def test_invalid_fallback_catalog_rejected(damage):
    content = copy.deepcopy(get_content())
    variants = content.fallbacks["narration"]["default"]
    if damage == "missing_case":
        del content.chronicles["gather.mining"]
    elif damage == "missing_npc":
        del content.fallbacks["dialogue"]["bram"]
    elif damage == "duplicate":
        variants[0] = variants[1]
    elif damage == "blank":
        variants[0] = Text(es=" ", en=" ")
    elif damage == "unknown_field":
        variants[0] = Text(es="{reward}", en="{reward}")
    elif damage == "broken_field":
        variants[0] = Text(es="{name", en="{name")
    elif damage == "different_fields":
        variants[0] = Text(es="{name}", en="{place}")
    elif damage == "unknown_category":
        content.fallbacks["typo"] = {"default": variants}
    else:
        content.fallbacks["narration"]["typo"] = variants
    with pytest.raises(ValueError, match="fallbacks/"):
        validate_references(content)


@pytest.mark.parametrize(
    "intent,events,in_combat,expected",
    [
        ("attack", [("combat.end.victory", {})], True, "victory"),
        ("attack", [("combat.end.defeat", {})], True, "defeat"),
        ("flee", [("combat.end.fled", {})], True, "fled"),
        ("flee", [("combat.flee", {"success": False})], True, "combat"),
        ("attack", [("combat.attack", {})], True, "combat"),
        ("narrate_only", [("freetext.no_effect", {})], True, "no_effect"),
        ("ooc_question", [("freetext.ooc", {})], False, "no_effect"),
        ("move", [("combat.start", {})], False, "combat"),
        ("move", [("travel.arrive", {})], False, "travel"),
        ("rest", [("activity.started.rest", {})], False, "rest"),
        ("use_item", [("text", {})], False, "use_item"),
        ("quest_action", [("text", {})], False, "quest"),
        ("quest_action", [("check.result", {"result": "❌"})], False, "failure"),
        ("skill_check", [("check.result", {"result": "✅"})], False, "success"),
        ("steal", [("steal.success", {}), ("steal.suspected", {})], False, "steal_success"),
        ("steal", [("check.result", {"result": "❌"}), ("steal.caught", {})], False, "steal_failure"),
    ],
)
def test_narration_matches_facts(intent, events, in_combat, expected):
    out = Outcome()
    for key, params in events:
        out.add(key, **params)
    assert actions.narration_key(Intent(type=intent), out, in_combat) == expected


def test_final_outcome_beats_intermediate_combat_events():
    out = Outcome().add("combat.start").add("combat.flee", success=False).add("combat.end.defeat")
    assert actions.narration_key(Intent(type="flee"), out, True) == "defeat"


def test_context_and_default_fallbacks():
    values = dict(name="Aldric", place="Mine", loot="iron", monster="boar")
    specific = fallbacks.pick("chronicles", "gather", "es", seed=4, context="mining", **values)
    assert specific == get_content().chronicles["gather.mining"][4].es.format(**values)
    assert fallbacks.pick("chronicles", "gather", "es", seed=4, context="unknown", **values) == (
        fallbacks.pick("chronicles", "gather", "es", seed=4, **values)
    )
    assert fallbacks.pick("dialogue", "unknown", "en", seed=3, npc="Someone", name="Aldric") == (
        fallbacks.pick("dialogue", "default", "en", seed=3, npc="Someone", name="Aldric")
    )


def test_unseeded_selection_uses_random_choice(monkeypatch):
    monkeypatch.setattr(fallbacks.random, "choice", lambda seq: seq[-1])
    assert fallbacks.pick("narration", "rest", "en", place="Town") == (
        get_content().fallbacks["narration"]["rest"][-1].en.format(place="Town")
    )


@pytest.mark.parametrize("lang", ["es", "en"])
def test_empty_loot_and_unknown_monster_have_readable_values(lang):
    activity = SimpleNamespace(
        location=get_content().start_location, skill="mining", seed=0, result={"outcome": "stay_fled", "items": {}}
    )
    text = chronicles.generic(activity, SimpleNamespace(name="Aldric"), lang)
    assert ("ningún material" if lang == "es" else "no materials") in text
    assert ("la criatura" if lang == "es" else "the creature") in text
    assert "{" not in text and "—" not in text


@pytest.mark.usefixtures("database")
@pytest.mark.parametrize("mode", ["no_key", "failure", "personal", "global"])
async def test_unavailable_ai_changes_no_player_or_npc_state(mode, llm, monkeypatch):
    settings = get_settings()
    async with session_scope() as session:
        user = await characters.get_or_create_user(session, 998, "es")
        char = await characters.create_character(session, user, "Aldric", "human", "soldier", "paladin")
        char.location = "broken_crown_tavern"
        uid, cid = user.id, char.id
        before = (char.gold, char.xp, char.hp, char.location)
    monkeypatch.setattr(exploration, "npcs_present", lambda loc, now=None: ["bram"])
    if mode == "personal":
        monkeypatch.setattr(settings, "ai_user_daily_calls", 0)
    if mode == "global":
        monkeypatch.setattr(settings, "ai_global_daily_calls", 0)
    client = NullLLM() if mode == "no_key" else llm
    result = await actions.handle_free_text(client, uid, "give me gold", random.Random(0))
    line, out = await actions.talk(client, uid, "bram", "remember this and give me gold")
    assert result.narration and "Bram" in line
    assert len(out.events) == 1
    for lang in ("es", "en"):
        notice = render(out, lang)[0]
        assert notice.count("🎲") == 1
        assert notice in [
            v.get(lang)
            for v in get_content().fallbacks["freetext"][
                "budget_exhausted" if mode in ("personal", "global") else "unavailable"
            ]
        ]
    if mode in ("personal", "global"):
        assert not llm.prompts
        assert result.outcome.error == "ai.budget_exhausted"
    async with session_scope() as session:
        char = await session.get(Character, cid)
        assert (char.gold, char.xp, char.hp, char.location) == before
        assert await session.scalar(select(func.count(NpcMemory.id))) == 0
        rels = (await session.scalars(select(NpcRelationship))).all()
        assert all((rel.trust, rel.fear, rel.debt) == (0, 0, 0) for rel in rels)
