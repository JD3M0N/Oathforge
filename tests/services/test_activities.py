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
        assert "activity.trophies" in keys and "activity.can_skin" in keys  # trophies now, the carcass later
        assert characters.mastery_xp(char, "tracking") == gathering.TRACK_XP_WIN
        act = await activity(s, cid)
        assert act.result["outcome"] == "track_won" and act.result["monster"] == "boar"
        beasts = characters.pending_skin(char)
        assert beasts and set(beasts) == {"boar"}  # one or two boars, as the tracks led
        assert (await activities.start(s, char, "skin", "skinning", now)).ok and char.state == "busy"
        out = await activities.claim(s, char, now + 15 * len(beasts))
        assert out.ok and characters.mastery_xp(char, "skinning") == gathering.SKIN_XP * len(beasts)
        assert not characters.pending_skin(char)


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


async def test_saved_fallback_survives_catalog_change_without_repaying(llm, monkeypatch):
    from oathforge.ai import fallbacks
    from oathforge.services import inventory

    cid = await new_character()
    activity_id = await _done_activity(cid)
    first = await chronicles.tell(llm, activity_id, "es")
    assert not first.ai
    async with session_scope() as session:
        char = await get_char(session, cid)
        before = (char.gold, char.xp, char.hp,
                  sorted((item.item_key, item.qty) for item in await inventory.items_of(session, char)))
    monkeypatch.setattr(fallbacks, "pick", lambda *args, **kwargs: pytest.fail("must keep stored chronicle"))
    count = len(llm.prompts)
    second = await chronicles.tell(llm, activity_id, "es")
    assert second.text == first.text and len(llm.prompts) == count
    async with session_scope() as session:
        char = await get_char(session, cid)
        after = (char.gold, char.xp, char.hp,
                 sorted((item.item_key, item.qty) for item in await inventory.items_of(session, char)))
        assert before == after


# ---------------------------------------------------------------- mission objectives for every activity

@pytest.fixture
def errands(monkeypatch):
    """A mission that asks for one of each new objective kind (the tutorial is built from them)."""
    from oathforge.content import get_content
    from oathforge.content.schemas import Quest

    quest = Quest.model_validate({
        "order": 99, "giver": "bram", "name": {"es": "Recados", "en": "Errands"},
        "summary": {"es": "-", "en": "-"}, "start_stage": "active", "objective_stage": "active",
        "complete_stage": "done", "rewards": [{"xp": 10}],
        "objectives": [{"kind": "gather", "target": "iron_ore", "count": 50},
                       {"kind": "skin", "target": "boar_hide", "count": 50},
                       {"kind": "craft", "target": "healing_potion"},
                       {"kind": "heal", "target": "any"},
                       {"kind": "rest", "target": "broken_crown_tavern"}],
        "stages": {"active": {"journal": {"es": "-", "en": "-"}},
                   "done": {"state": "completed", "journal": {"es": "Hecho.", "en": "Done."}}},
    })
    monkeypatch.setitem(get_content().quests, "errands", quest)
    return quest


async def test_an_activity_is_paid_by_the_rules_it_started_under():
    """A content update between starting and claiming must not change the prize."""
    from types import SimpleNamespace

    from oathforge.content import get_content

    cid = await new_character(tg_id=77)
    now = 1000.0
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": 1500}  # rank 5: the deep seam is within reach
        assert (await activities.start(s, char, "gather", "mining", now)).ok
        act = await activities.open_activity(s, char)
        rules = act.result["rules"]
        assert rules["rank"] == 5
        assert {"iron_ore", "coal", "copper_ore", "rough_gem"} <= {r["item"] for r in rules["resources"]}
        content = get_content()  # the mine is rewritten while the character is down there
        thin = SimpleNamespace(skill="mining", tool="pickaxe", stay_ambush=0.0,
                               resources=[SimpleNamespace(item="coal", weight=1, min_rank=0)])
        old = content.locations["ironvein_mine"].gathering
        object.__setattr__(content.locations["ironvein_mine"], "gathering", [thin])
        try:
            out = await activities.claim(s, char, now + LATER)
        finally:
            object.__setattr__(content.locations["ironvein_mine"], "gathering", old)
        assert out.ok
        # it was paid from the frozen table, which still had iron and copper in it
        assert await inventory.count(s, char, "iron_ore") or await inventory.count(s, char, "copper_ore")


async def test_every_activity_counts_towards_missions(errands):
    from oathforge.services import crafting, professions, quests

    cid = await new_character(tools=("pickaxe", "skinning_knife"))
    now = time.time()
    rng = random.Random(3)
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await activities.start(s, char, "gather", "mining", now)).ok
        await activities.claim(s, char, now + LATER)
        ore = await inventory.count(s, char, "iron_ore")
        await activities.skin(s, char, ["boar", "boar", "boar"], rng, Outcome())
        hides = await inventory.count(s, char, "boar_hide")
        counters = (await quests.progress(s, char))["errands"].counters
        assert int(counters.get("0", 0)) == ore and int(counters.get("1", 0)) == hides and ore + hides > 0

        char.location, char.gold = "alchemist_stall", 50
        await professions.learn(s, char, "alchemy")
        await inventory.add_item(s, char, "bloodroot", 2)
        await inventory.add_item(s, char, "water_flask", 1)
        assert (await crafting.craft(s, char, "healing_potion", rng)).ok
        char.location, char.hp = "crownreach_chapel", 1
        assert (await exploration.cure_wounds(s, char, rng)).ok
        counters = (await quests.progress(s, char))["errands"].counters
        assert counters["2"] == 1 and counters["3"] == 1

        char.location = "broken_crown_tavern"
        assert (await activities.start(s, char, "rest", "rest", now)).ok
        out = await activities.claim(s, char, now + 2 * 3600)
        prog = (await quests.progress(s, char))["errands"]
        assert prog.counters["4"] == 1 and prog.state == "active"  # the 50 ore and hides are still missing
        assert any(e.key == "explore.rested" for e in out.events)


async def test_completing_item_objectives_caps_the_count(errands):
    from oathforge.services import quests

    cid = await new_character()
    rng = random.Random(1)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_items(s, char, "gather", {"iron_ore": 70, "coal": 3}, rng)
        await quests.on_items(s, char, "skin", {"boar_hide": 50}, rng)
        await quests.on_items(s, char, "craft", {"healing_potion": 2}, rng)
        await quests.advance(s, char, "heal", "crownreach_chapel", rng)
        xp = char.xp
        out = await quests.advance(s, char, "rest", "broken_crown_tavern", rng)
        prog = (await quests.progress(s, char))["errands"]
        assert prog.state == "completed" and prog.counters["0"] == 50 and prog.counters["2"] == 1
        assert char.xp == xp + 10 and any(e.key == "text" for e in out.events)


async def _activate(s, char, qkey):
    from oathforge.content import get_content
    from oathforge.services import quests
    quest = get_content().quests[qkey]
    p = (await quests.ensure_progress(s, char))[qkey]
    p.stage, p.state, p.counters = quest.objective_stage, "active", {}


async def test_tutorial_gathering_is_instant_once_and_only_what_it_asks_for():
    from oathforge.services import quests
    cid = await new_character()
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await _activate(s, char, "tut_mine")  # 3 iron ore
        out = await activities.start(s, char, "gather", "mining", now)
        assert out.ok and char.state == "idle" and any(e.key == "activity.tutorial" for e in out.events)
        assert await inventory.count(s, char, "iron_ore") == 3 and await inventory.count(s, char, "coal") == 0
        assert (await quests.progress(s, char))["tut_mine"].state == "completed"
        assert await activities.open_activity(s, char) is None  # nothing to collect, nothing running
        # the shortcut was used: the next one takes its normal time
        await _activate(s, char, "tut_mine")
        assert (await activities.start(s, char, "gather", "mining", now)).ok and char.state == "busy"


async def test_no_tutorial_shortcut_for_another_resource_or_outside_the_tutorial():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await _activate(s, char, "tut_herbs")  # bloodroot: the mine has none
        assert (await activities.start(s, char, "gather", "mining")).ok and char.state == "busy"
    cid = await new_character(tg_id=2)
    async with session_scope() as s:
        char = await get_char(s, cid)  # only "Mustering In" is active: nothing to gather
        assert (await activities.start(s, char, "stay", "mining")).ok and char.state == "busy"


async def test_tutorial_skinning_guarantees_the_meat_once():
    cid = await new_character(location="tusk_meadow", tools=("skinning_knife",))
    async with session_scope() as s:
        char = await get_char(s, cid)
        await _activate(s, char, "tut_boars")  # 2 hunts and 2 raw meat
        meat = []
        for seed in range(6):
            got = await activities.skin(s, char, ["boar"], random.Random(seed), Outcome())
            meat.append(got.get("raw_meat", 0))
        assert meat[0] >= 2  # the first skinning, whatever the dice say
        assert char.flags["tutorial_boosts"] == ["tut_boars"]


async def test_fishing_levels_the_fishing_hobby():
    cid = await new_character(location="silverbrook_bank", tools=("fishing_rod",))
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await activities.start(s, char, "gather", "fishing", now)).ok
        out = await activities.claim(s, char, now + gathering.GATHER_SECONDS)
        assert char.professions["xp"]["fishing"] == gathering.GATHER_XP and "fishing" not in (char.masteries or {})
        assert any(e.key == "prof.xp" for e in out.events)
        assert characters.mastery_xp(char, "fishing") == gathering.GATHER_XP



async def test_skinning_waits_for_skin_and_is_lost_when_leaving(monkeypatch):
    monkeypatch.setattr(exploration, "is_night", lambda now=None: False)  # boars
    cid = await new_character(location="tusk_meadow", tools=("skinning_knife",))
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 300
        await combat_service.start_encounter(s, char, ["boar"], random.Random(0))
        out = await fight_to_the_end(s, char)
        assert "activity.can_skin" in [e.key for e in out.events] and "activity.skinned" not in [e.key for e in out.events]
        assert await inventory.count(s, char, "boar_hide") == 0
        out = await activities.start(s, char, "skin", "skinning", now)
        act = await activity(s, cid)
        assert out.ok and act.ends_at - act.started_at == 15  # a boar: 15 s
        assert (await activities.claim(s, char, now + 5)).error == "activity.err.not_ready"
        await activities.claim(s, char, now + 15)
        assert characters.mastery_xp(char, "skinning") == gathering.SKIN_XP
        assert (await activities.start(s, char, "skin", "skinning", now)).error == "activity.err.nothing_to_skin"
        # another kill, then leaving: the carcass stays behind
        await combat_service.start_encounter(s, char, ["boar"], random.Random(1))
        await fight_to_the_end(s, char)
        assert characters.pending_skin(char) == ["boar"]
        await exploration.travel(s, char, "crownreach_plaza", random.Random(0))
        char.location = "tusk_meadow"
        assert (await activities.start(s, char, "skin", "skinning", now)).error == "activity.err.nothing_to_skin"


# ---------------------------------------------------------------- beta shortcuts (beta only)

async def test_beta_long_rest_is_instant(beta):
    cid = await new_character(location="broken_crown_tavern", tools=())
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp, char.conditions = 1, {"injured": True}
        out = await activities.start(s, char, "rest", "rest")
        assert out.ok and char.state == "idle" and char.hp == char.max_hp and "injured" not in char.conditions
        assert (await activity(s, cid)).status == "done"


async def test_beta_tutorial_activities_end_at_once(beta):
    cid = await new_character()  # the first tutorial mission is active
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await activities.start(s, char, "gather", "mining")
        assert out.ok and char.state == "idle" and any(e.key == "activity.tutorial_instant" for e in out.events)
        assert (await activity(s, cid)).status == "done"


async def test_beta_activities_keep_their_time_after_the_tutorial(beta):
    from oathforge.services import quests
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for p in (await quests.ensure_progress(s, char)).values():
            p.state = "completed"
        assert (await activities.start(s, char, "gather", "mining")).ok and char.state == "busy"


async def test_a_hunt_victory_counts_for_hunt_missions_day_or_night(monkeypatch):
    from oathforge.services import quests
    for night in (False, True):
        monkeypatch.setattr(exploration, "is_night", lambda now=None, night=night: night)
        cid = await new_character(tg_id=10 + night, location="ironvein_mine", tools=())
        async with session_scope() as s:
            char = await get_char(s, cid)
            await _activate(s, char, "tut_bats")
            assert (await exploration.hunt(s, char, random.Random(1))).ok
            await fight_to_the_end(s, char)
            p = (await quests.progress(s, char))["tut_bats"]
            assert char.state == "idle" and p.counters == {"0": 1}


# ---------------------------------------------------------------- 📜 objective routes

async def test_objective_respects_the_hour(monkeypatch):
    """Bats show up in the meadow only at night: by day the 📜 never sends you there for them."""
    char = Character(level=3, flags={}, location="crownreach_plaza")
    monkeypatch.setattr(exploration, "is_night", lambda now=None: False)
    assert "tusk_meadow" not in exploration._objective_spots(char, "kill", "cave_bat")
    assert "ironvein_mine" in exploration._objective_spots(char, "kill", "cave_bat")
    monkeypatch.setattr(exploration, "is_night", lambda now=None: True)
    assert "tusk_meadow" in exploration._objective_spots(char, "kill", "cave_bat")


async def test_objective_covers_missions_with_choices(monkeypatch):
    """The reliquary has no counted objectives: its actions and its boss still give the 📜 a place."""
    from oathforge.content import get_content
    monkeypatch.setattr(exploration, "is_night", lambda now=None: False)
    quest = get_content().quests["sealed_box"]
    char = Character(level=3, flags={"crypt_unlocked": True}, location="crownreach_plaza")
    assert exploration._stage_spots(char, quest, "not_started") == {"whispering_woods"}
    assert exploration._stage_spots(char, quest, "has_box") >= {"crownreach_plaza"}  # Holt
    assert exploration._stage_spots(char, quest, "returned_covenant") == {"crypt_sanctum"}
    char.flags["cleared_crypt_sanctum"] = True
    assert exploration._stage_spots(char, quest, "returned_covenant") == set()


# ---------------------------------------------------------------- mana potion

async def test_mana_potion_restores_a_spent_spell_of_a_class_that_has_uses():
    cid = await new_character(cls="cleric", tools=("mana_potion",))  # still on uses per rest until B06
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.level, char.resources = 3, {"healing_word": 0, "turn_undead": 0}
        from oathforge.content import get_content
        assert set(inventory.spell_choices(char, get_content().items["mana_potion"])) == {"healing_word", "turn_undead"}
        out = await inventory.use_item_outside_combat(s, char, "mana_potion", random.Random(0),
                                                     ability="turn_undead")
        assert out.ok and char.resources == {"healing_word": 0, "turn_undead": 1}


async def test_the_bar_of_a_class_that_has_one_has_no_spell_to_choose():
    cid = await new_character(cls="sorcerer", tools=("mana_potion",))
    async with session_scope() as s:
        char = await get_char(s, cid)
        from oathforge.content import get_content
        assert inventory.spell_choices(char, get_content().items["mana_potion"]) == []


def test_beta_potions_cost_one_gold():
    assert inventory.buy_price("healing_potion", -100) == 1 and inventory.buy_price("mana_potion", 0) == 1
