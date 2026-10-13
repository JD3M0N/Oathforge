"""Field activities (gather, stay, track), skinning and expedition chronicles."""

import random
import time

import pytest
from sqlalchemy import select

from oathforge.config import get_settings
from oathforge.database.models import Character, WorldActivity
from oathforge.database.session import session_scope
from oathforge.engine import gathering
from oathforge.engine.combat import Action
from oathforge.services import activities, characters, chronicles, combat_service, exploration, inventory
from oathforge.services.events import Outcome

pytestmark = pytest.mark.usefixtures("database")

LATER = 3600  # seconds after the start: every activity is over


async def new_character(tg_id=1, cls="paladin", location="ironvein_mine", tools=("pickaxe",)) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, tg_id, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", cls)
        char.location = location
        for tool in tools:
            await inventory.add_item(s, char, tool)
        return char.id


async def get_char(s, char_id) -> Character:
    return await s.scalar(select(Character).where(Character.id == char_id).with_for_update())


async def activity(s, char_id) -> WorldActivity:
    return await s.scalar(select(WorldActivity).where(WorldActivity.character_id == char_id)
                          .order_by(WorldActivity.id.desc()))


async def fight_to_the_end(s, char, seed=0) -> Outcome:
    enc = await combat_service.active_encounter(s, char, lock=True)
    rng, out, steps = random.Random(seed), Outcome(), 0
    while enc.status == "active" and steps < 100:
        steps += 1
        out.extend(await combat_service.act(s, char, enc, Action(kind="attack", weapon="main"), rng))
    return out


async def test_gather_needs_the_tool_and_is_paid_once():
    cid = await new_character(tools=())
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await activities.start(s, char, "gather", "mining", now)
        assert out.error == "activity.err.no_tool" and char.state == "idle"
        await inventory.add_item(s, char, "pickaxe")
        assert (await activities.start(s, char, "gather", "mining", now)).ok
        assert char.state == "busy"
    async with session_scope() as s:  # a new session, as after a restart: the timer is in the database
        char = await get_char(s, cid)
        assert (await activities.claim(s, char, now + 60)).error == "activity.err.not_ready"
        out = await activities.claim(s, char, now + gathering.GATHER_SECONDS)
        assert out.ok and out.activity_id and char.state == "idle"
        act = await activity(s, cid)
        assert act.status == "done" and act.result["outcome"] == "gather"
        assert characters.mastery_xp(char, "mining") == 10
        got = {k: await inventory.count(s, char, k) for k in act.result["items"]}
        assert got == act.result["items"] and 2 <= sum(got.values()) <= 3
    async with session_scope() as s:  # pressing "Collect" again pays nothing
        char = await get_char(s, cid)
        assert (await activities.claim(s, char, now + LATER)).error == "activity.err.none"
        assert characters.mastery_xp(char, "mining") == 10


async def test_busy_blocks_travel_hunting_and_a_second_activity():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await activities.start(s, char, "stay", "mining")).ok
        assert (await exploration.travel(s, char, "old_kings_road", random.Random(0))).error == "activity.err.busy"
        assert (await exploration.hunt(s, char, random.Random(0))).error == "activity.err.busy"
        assert (await activities.start(s, char, "gather", "mining")).error == "activity.err.busy"
        assert char.location == "ironvein_mine"


async def test_unavailable_activities():
    cid = await new_character(location="crownreach_plaza")
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await activities.start(s, char, "gather", "mining")).error == "activity.err.unavailable"
        assert (await activities.start(s, char, "track", "tracking")).error == "activity.err.unavailable"
        assert activities.options(char) == []
        char.location = "ironvein_mine"
        assert ("stay", "mining") in activities.options(char) and ("track", "tracking") in activities.options(char)


async def test_cancel_gives_nothing_and_old_buttons_do_nothing():
    cid = await new_character()
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await activities.start(s, char, "gather", "mining", now)
        assert (await activities.cancel(s, char, now + 10)).ok and char.state == "idle"
        assert (await activities.claim(s, char, now + LATER)).error == "activity.err.none"
        assert (await activities.cancel(s, char)).error == "activity.err.none"
        assert await inventory.count(s, char, "iron_ore") == 0
        assert (await activity(s, cid)).status == "cancelled"


async def _ambushed_stay(monkeypatch, cid):
    monkeypatch.setattr(gathering, "roll_ambush", lambda rng, chance: True)
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await activities.start(s, char, "stay", "mining", now)
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 300  # make a victory certain
        out = await activities.claim(s, char, now + gathering.STAY_SECONDS)
        assert out.events[0].key == "activity.stay_ambush" and out.activity_id is None
        assert char.state == "in_combat"
        act = await activity(s, cid)
        assert act.status == "awaiting_combat" and act.encounter_id
        assert await inventory.count(s, char, "iron_ore") == 0  # nothing paid yet
        return dict(act.result["pending"])


async def test_stay_ambush_victory_keeps_everything(monkeypatch):
    cid = await new_character()
    pending = await _ambushed_stay(monkeypatch, cid)
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await fight_to_the_end(s, char)
        assert out.activity_id
        act = await activity(s, cid)
        assert act.status == "done" and act.result["outcome"] == "stay_won" and act.result["items"] == pending
        for item, qty in pending.items():
            assert await inventory.count(s, char, item) >= qty
        assert characters.mastery_xp(char, "mining") >= 25


@pytest.mark.parametrize("status,outcome", [("fled", "stay_fled"), ("defeat", "stay_lost")])
async def test_stay_ambush_flee_keeps_half_and_defeat_loses_it(monkeypatch, status, outcome):
    cid = await new_character()
    pending = await _ambushed_stay(monkeypatch, cid)
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = Outcome()
        await activities.on_encounter_end(s, char, status, [], random.Random(0), out)
        act = await activity(s, cid)
        assert act.result["outcome"] == outcome and out.activity_id == act.id
        expected = gathering.half(pending) if status == "fled" else {}
        assert act.result["items"] == expected
        for item, qty in expected.items():
            assert await inventory.count(s, char, item) == qty
        # a second end never pays again
        await activities.on_encounter_end(s, char, "victory", [], random.Random(0), Outcome())
        assert (await activity(s, cid)).result["outcome"] == outcome


async def test_tracking_only_tracks(monkeypatch):
    monkeypatch.setattr(gathering, "roll_prey", lambda rng: False)
    cid = await new_character(location="tusk_meadow", tools=())
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await activities.start(s, char, "track", "anything", now)).ok
        out = await activities.claim(s, char, now + gathering.TRACK_SECONDS)
        assert out.events[0].key == "activity.track_tracks" and char.state == "idle"
        assert characters.mastery_xp(char, "tracking") == gathering.TRACK_XP_TRACKS


async def test_tracking_prey_gives_trophies_and_skinning(monkeypatch):
    monkeypatch.setattr(gathering, "roll_prey", lambda rng: True)
    monkeypatch.setattr(exploration, "is_night", lambda now=None: False)  # boars
    cid = await new_character(location="tusk_meadow", tools=("skinning_knife",))
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 300
        await activities.start(s, char, "track", "tracking", now)
        out = await activities.claim(s, char, now + gathering.TRACK_SECONDS)
        assert out.events[0].key == "activity.track_found" and char.state == "in_combat"
        out = await fight_to_the_end(s, char)
        keys = [e.key for e in out.events]
        assert "activity.skinned" in keys or "activity.trophies" in keys
        assert characters.mastery_xp(char, "tracking") == gathering.TRACK_XP_WIN
        assert characters.mastery_xp(char, "skinning") > 0
        act = await activity(s, cid)
        assert act.result["outcome"] == "track_won" and act.result["monster"] == "boar"


async def test_tracking_finds_the_mission_boss_first():
    cid = await new_character(location="tusk_meadow", tools=())
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.flags = {"old_tusk_hunt": True}
        char.hp = char.max_hp = 300
        await activities.start(s, char, "track", "tracking", now)
        await activities.claim(s, char, now + gathering.TRACK_SECONDS)
        enc = await combat_service.active_encounter(s, char)
        assert enc.fixed_flag == "cleared_old_tusk"


async def test_skinning_needs_a_knife(monkeypatch):
    cid = await new_character(location="tusk_meadow", tools=())
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 300
        out = Outcome()
        assert await activities.skin(s, char, ["boar"], random.Random(0), out) == {}
        assert [e.key for e in out.events] == ["activity.no_knife"]
        await inventory.add_item(s, char, "skinning_knife")
        out = Outcome()
        got = await activities.skin(s, char, ["old_tusk"], random.Random(0), out)
        assert got == {"boar_hide": 2, "raw_meat": 4}
        assert await inventory.count(s, char, "raw_meat") == 4
        assert characters.mastery_xp(char, "skinning") == gathering.SKIN_XP
        assert await activities.skin(s, char, ["bandit"], random.Random(0), Outcome()) == {}  # not a beast to skin


# ---------------------------------------------------------------- chronicles

async def _done_activity(cid) -> int:
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await activities.start(s, char, "gather", "mining", now)
        out = await activities.claim(s, char, now + gathering.GATHER_SECONDS)
        return out.activity_id


async def test_chronicle_uses_ai_while_the_budget_lasts(llm, monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_user_daily_chronicles", 1)
    cid = await new_character()
    first = await _done_activity(cid)
    llm.text_queue.append("Aldric picó la roca hasta el anochecer.")
    ch = await chronicles.tell(llm, first, "es")
    assert ch.ai and ch.text.startswith("Aldric picó") and (ch.used, ch.limit) == (1, 1)
    assert "Materials the hero brings back" in llm.prompts[-1]
    again = await chronicles.tell(llm, first, "es")  # stored: no second call
    assert again.text == ch.text and len(llm.prompts) == 1

    second = await _done_activity(cid)
    llm.text_queue.append("never used")
    ch = await chronicles.tell(llm, second, "es")
    assert not ch.ai and len(llm.prompts) == 1 and "Aldric" in ch.text and "{" not in ch.text
    assert "cronista" in chronicles.footer(ch, "es")


async def test_chronicle_falls_back_when_the_ai_fails(llm):
    cid = await new_character()
    act_id = await _done_activity(cid)
    ch = await chronicles.tell(llm, act_id, "en")  # FakeLLM with an empty queue = failure
    assert not ch.ai and ch.used == 0 and "Aldric" in ch.text
    async with session_scope() as s:
        assert await chronicles.chronicles_today(s, cid) == 0


async def test_every_outcome_has_a_readable_generic_chronicle():
    cid = await new_character()
    act_id = await _done_activity(cid)
    async with session_scope() as s:
        act = await s.get(WorldActivity, act_id)
        char = await get_char(s, cid)
        for outcome in ("gather", "stay_ok", "stay_won", "stay_fled", "stay_lost",
                        "track_tracks", "track_won", "track_fled", "track_lost"):
            act.result = {**act.result, "outcome": outcome, "monster": "boar"}
            for lang in ("es", "en"):
                text = chronicles.generic(act, char, lang)
                assert "Aldric" in text and "{" not in text


async def test_concurrent_claims_pay_once(is_postgres):
    if not is_postgres:
        pytest.skip("row locks need PostgreSQL")
    import asyncio

    cid = await new_character()
    now = time.time()
    async with session_scope() as s:
        await activities.start(s, await get_char(s, cid), "stay", "mining", now)

    async def claim():
        async with session_scope() as s:
            return await activities.claim(s, await get_char(s, cid), now + gathering.STAY_SECONDS)

    results = await asyncio.gather(claim(), claim())
    assert sorted(r.ok for r in results) == [False, True]
    async with session_scope() as s:
        char = await get_char(s, cid)
        act = await activity(s, cid)
        if act.status == "done":  # no ambush: paid exactly once
            total = sum([await inventory.count(s, char, k) for k in act.result["items"]])
            assert total == sum(act.result["items"].values())
