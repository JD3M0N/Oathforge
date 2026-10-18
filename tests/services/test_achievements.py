"""Achievement transaction, ownership and delivery regression tests."""
import asyncio
import random
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, func
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.database.models import (Character, QuestProgress, AchievementUnlock, AchievementProgress,
    AchievementEventReceipt, AchievementNotification, AchievementPreferences)
from oathforge.services import achievements as a, characters, combat_service, quests, exploration, activities, inventory
from oathforge.services.events import Outcome
from oathforge.engine.combat import EncounterState
from oathforge.bot import achievement_views

pytestmark = pytest.mark.usefixtures("database")

async def hero(tg_id=1):
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, tg_id, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        return char.id

async def load(s, cid):
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())

def event(cid, identity, kind, **data):
    return a.GameplayEvent(identity, cid, kind, data, identity)

async def test_thousand_replays_and_rollback():
    cid = await hero()
    e = event(cid, "craft:one", "craft", recipe="iron_ingot")
    async with session_scope() as s:
        char = await load(s, cid)
        assert await a.apply_events(s, char, [e] * 1000) == ["handmade"]
        data = await a.snapshot(s, char)
        assert data["points"] == 10
        assert await s.scalar(select(func.count()).select_from(AchievementEventReceipt).where(AchievementEventReceipt.event_id == "craft:one")) == 1
        assert await s.scalar(select(func.count()).select_from(AchievementNotification)) == 1
    with pytest.raises(RuntimeError):
        async with session_scope() as s:
            char = await load(s, cid)
            await a.apply_events(s, char, [event(cid, "combat:rollback", "combat", status="victory")])
            raise RuntimeError("action rolled back")
    async with session_scope() as s:
        char = await load(s, cid)
        assert (await a.snapshot(s, char))["count"] == 1
        assert await a.apply_events(s, char, [e]) == []
        assert await s.scalar(select(AchievementEventReceipt.id).where(
            AchievementEventReceipt.event_id == "combat:rollback")) is None

async def test_sequence_distinct_and_batching():
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        await a.apply_events(s, char, [event(cid, "v1", "combat", status="victory", eligible=True, enemies=2, hp=2, consumed=0)])
        assert not await s.scalar(select(AchievementUnlock.id).where(AchievementUnlock.achievement_key == "back_on_feet"))
        await a.apply_events(s, char, [event(cid, "d1", "combat", status="defeat"),
                                      event(cid, "v2", "combat", status="victory", eligible=True, enemies=2, hp=1, consumed=1)])
        assert await s.scalar(select(AchievementUnlock.id).where(AchievementUnlock.achievement_key == "back_on_feet"))
        for i in range(5):
            await a.apply_events(s, char, [event(cid, f"recipe:{i}", "craft", recipe="iron_ingot")])
        row = await s.scalar(select(AchievementProgress).where(AchievementProgress.achievement_key == "craft_repertoire"))
        assert row.state["values"] == ["iron_ingot"]
        assert await s.scalar(select(func.count()).select_from(AchievementNotification)) == 1

async def test_backfill_proves_only_saved_facts():
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        char.flags = {"stats": {"places": ["crownreach_plaza"]}, "crypt_unlocked": True}
        char.masteries = {"mining": 500}
        char.bestiary = {"boar": {"seen": 3, "killed": 3}}
        prog = await quests.ensure_progress(s, char)
        prog["sealed_box"].state, prog["sealed_box"].stage = "completed", "completed_alone"
        granted = await a.backfill_character(s, char)
        assert {"beneath_crown", "experienced", "field_notes", "know_enemy", "story_begins"} <= set(granted)
        assert not {"sealed_no_more", "no_reserves", "know_city", "handmade", "two_skies"} & set(granted)
        assert await a.backfill_character(s, char) == []
        assert all(u.retroactive for u in (await s.scalars(select(AchievementUnlock))).all())
        assert await s.scalar(select(func.count()).select_from(AchievementNotification)) == 1
        # Read-only views never create missing progress or awards.
        before = await s.scalar(select(func.count()).select_from(AchievementEventReceipt))
        await a.snapshot(s, char)
        assert await s.scalar(select(func.count()).select_from(AchievementEventReceipt)) == before

async def test_preferences_limits_replacement_ownership_and_language():
    cid, other = await hero(), await hero(2)
    async with session_scope() as s:
        char = await load(s, cid)
        keys = ["whispers", "no_stone", "craft_repertoire", "experienced"]
        for i, key in enumerate(keys[:3]):
            assert (await a.preference(s, char, "track", key, f"n{i}")).ok
        assert (await a.preference(s, char, "track", keys[3], "full")).error == "achievements.full"
        assert (await a.preference(s, char, "track", keys[3], "replace", keys[0])).ok
        assert (await a.preference(s, char, "track", keys[0], "replace")).error == "achievements.stale"
        assert (await a.preference(s, char, "title", "cryptbreaker", "bad")).error == "achievements.invalid"
        await a.apply_events(s, char, [event(cid, "boss", "kill", monster="crypt_warden")])
        assert (await a.preference(s, char, "title", "cryptbreaker", "title")).ok
        assert (await a.preference(s, char, "feature", "cryptbreaker", "feature")).ok
        snap = await a.snapshot(s, char)
        assert "Rompecriptas" in achievement_views.identity(snap, "es")[0]
        assert "Cryptbreaker" in achievement_views.identity(snap, "en")[0]
        other_char = await load(s, other)
        assert (await a.preference(s, other_char, "title", "cryptbreaker", "theft")).error == "achievements.invalid"
        with pytest.raises(ValueError):
            await a.apply_events(s, other_char, [event(cid, "wrong", "seen", monster="boar")])
        await a.apply_events(s, char, [event(cid, "rank", "mastery", skill="mining", rank=3)])
        assert "experienced" not in (await s.get(AchievementPreferences, cid)).tracked
        assert (await a.preference(s, char, "title", "-", "remove-title")).ok
        assert (await s.get(AchievementPreferences, cid)).title is None
        await a.apply_events(s, char, [event(cid, "seen", "seen", monster="boar"),
            event(cid, "crafted", "craft", recipe="iron_ingot"),
            event(cid, "won", "combat", status="victory")])
        for key in ("field_notes", "handmade"):
            assert (await a.preference(s, char, "feature", key, f"feature-{key}")).ok
        assert (await a.preference(s, char, "feature", "first_victory", "feature-full")).error == "achievements.full"
        assert (await a.preference(s, char, "feature", "first_victory", "feature-replace", "handmade")).ok
        assert (await s.get(AchievementPreferences, cid)).featured == ["cryptbreaker", "field_notes", "first_victory"]


async def test_notification_failure_restart_and_lease():
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        await a.apply_events(s, char, [event(cid, "one", "craft", recipe="iron_ingot")])
        first = await a.claim_notification(s, cid, now=100)
        assert first and await a.claim_notification(s, cid, now=101) is None
    async with session_scope() as s:
        renewed = await a.claim_notification(s, cid, now=221)
        assert renewed[0] != first[0]
        await a.finish_notification(s, cid, first[0], True)
        assert (await s.scalar(select(AchievementNotification))).status == "sending"
        await a.finish_notification(s, cid, renewed[0], False)
    from oathforge.bot.handlers.achievements import deliver
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=RuntimeError("offline")))
    await deliver(bot, 1, 1)
    async with session_scope() as s:
        assert (await s.scalar(select(AchievementNotification))).status == "pending"
    bot.send_message = AsyncMock()
    await deliver(bot, 1, 1)
    await deliver(bot, 1, 1)
    assert bot.send_message.await_count == 1
    async with session_scope() as s:
        assert (await s.scalar(select(AchievementNotification))).status == "sent"
        assert await s.scalar(select(func.count()).select_from(AchievementUnlock)) == 1

async def test_menus_are_bilingual_bounded_and_hide_conditions():
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        snap = await a.snapshot(s, char)
        for lang in ("es", "en"):
            for arg in ("-", "categories", "l:pending:0", "l:pending:999", "l:pending:bad",
                        *[f'd:{e["key"]}' for e in snap["entries"]]):
                text, keyboard = achievement_views.view(snap, lang, arg)
                assert len(text) < 4096
                assert all(len(b.callback_data.encode()) <= 64 for row in keyboard.inline_keyboard for b in row)
            text, _ = achievement_views.view(snap, lang, "d:sealed_no_more")
            assert get_content().achievements["sealed_no_more"].description.get(lang) not in text
        await a.preference(s, char, "reveal", "sealed_no_more", "reveal")
        text, _ = achievement_views.view(await a.snapshot(s, char), "en", "d:sealed_no_more")
        assert "Open the sealed locket" in text

async def test_meta_all_relic_endings():
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        events = []
        cat = get_content().achievements
        for place in cat["know_city"].condition.values:
            events.append(event(cid, f"visit:{place}", "visit", location=place))
        for quest in cat["long_road"].condition.values:
            events.append(event(cid, f"quest:{quest}", "quest", quest=quest))
        events += [event(cid, "boss", "kill", monster="crypt_warden"),
                   event(cid, "relic_complete", "quest", quest="sealed_box")]
        granted = await a.apply_events(s, char, events)
        assert "warden_crownreach" in granted
        assert not {"silver_allegiance", "crimson_bargain", "sealed_no_more"} & set(granted)

async def test_concurrent_events_and_notification_claim(is_postgres):
    if not is_postgres:
        pytest.skip("requires PostgreSQL row locks")
    cid = await hero()
    async def grant():
        async with session_scope() as s:
            char = await load(s, cid)
            return await a.apply_events(s, char, [event(cid, "same", "craft", recipe="iron_ingot")])
    results = await asyncio.gather(grant(), grant())
    assert sum(len(r) for r in results) == 1
    async def claim():
        async with session_scope() as s:
            return await a.claim_notification(s, cid)
    assert sum(r is not None for r in await asyncio.gather(claim(), claim())) == 1

@pytest.mark.parametrize("hp,consumed,old", [(0,0,False),(1,0,False),(2,1,False),(1,0,True)])
async def test_encounter_metrics_before_rewards_and_legacy(hp, consumed, old):
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        char.location, char.level, char.hp, char.max_hp = "ironvein_mine", 3, 80, 80
        enc, out = await combat_service.start_encounter(s, char, ["cave_bat", "cave_bat"], random.Random(2))
        assert enc.achievement_metrics["eligible"]
        if old:
            enc.achievement_metrics = None
        else:
            enc.achievement_metrics = {**enc.achievement_metrics, "consumed": consumed}
        char.level = 6  # eligibility was frozen when the encounter started
        state = EncounterState.model_validate(enc.state)
        state.status = "victory"
        state.combatants["p1"].hp = hp
        for cb in state.combatants.values():
            if cb.side == "enemy":
                cb.hp = 0
        await combat_service._sync_and_maybe_finish(s, char, enc, state, random.Random(3), out)
        keys = {u.achievement_key for u in (await s.scalars(select(AchievementUnlock))).all()}
        assert ("last_breath" in keys) == (hp == 1 and not old)
        assert ("no_reserves" in keys) == (consumed == 0 and not old)

async def test_gather_tool_cancel_and_restart():
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        char.location = "ironvein_mine"
        await inventory.add_item(s, char, "pickaxe")
        await activities.start(s, char, "gather", "mining", now=0)
        await activities.cancel(s, char, now=1)
        assert not await s.scalar(select(AchievementUnlock.id).where(AchievementUnlock.achievement_key == "trade_tools"))
        await activities.start(s, char, "gather", "mining", now=2)
    async with session_scope() as s:
        char = await load(s, cid)
        await activities.claim(s, char, now=1000)
        assert await s.scalar(select(AchievementUnlock.id).where(AchievementUnlock.achievement_key == "trade_tools"))
        assert not (await activities.claim(s, char, now=1001)).ok

@pytest.mark.parametrize("action,expected", [
    ("give_box_holt", "silver_allegiance"), ("sell_box_mira", "crimson_bargain"), ("open_box", "sealed_no_more"),
])
async def test_relic_decisions_are_actual_transitions(action, expected):
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        char.location = "crownreach_plaza" if action == "give_box_holt" else "crownreach_market"
        row = (await quests.ensure_progress(s, char))["sealed_box"]
        row.stage, row.state = "has_box", "active"
        await inventory.add_item(s, char, "sealed_reliquary")
        out = await quests.perform(s, char, f"sealed_box.{action}", ["holt", "mira"], random.Random(1))
        assert out.ok
        assert expected in out.achievement_unlocks
        assert sum(k in out.achievement_unlocks for k in ("silver_allegiance", "crimson_bargain", "sealed_no_more")) == 1
        assert not (await quests.perform(s, char, f"sealed_box.{action}", ["holt", "mira"], random.Random(1))).ok

async def test_missed_discovery_and_known_city_do_not_count(monkeypatch):
    from oathforge.services import world_map
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        assert len(world_map.known(char)) >= 5
        await a.backfill_character(s, char)
        assert not await s.scalar(select(AchievementUnlock.id).where(AchievementUnlock.achievement_key == "know_city"))
        char.location = "whispering_woods"
        monkeypatch.setattr(exploration, "check", lambda *args: SimpleNamespace(kept=1,total=1,success=False))
        await exploration.investigate(s, char, random.Random(0))
        assert not await s.scalar(select(AchievementProgress.id).where(AchievementProgress.achievement_key == "no_stone"))

async def test_consumable_rejection_and_success_update_metrics():
    from oathforge.engine.combat import Action
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        char.location, char.level, char.hp, char.max_hp = "ironvein_mine", 3, 80, 80
        await inventory.add_item(s, char, "healing_potion")
        enc, _ = await combat_service.start_encounter(s, char, ["cave_bat", "cave_bat"], random.Random(2))
        assert not (await combat_service.act(s, char, enc, Action(kind="item", ability="unknown"), random.Random(0))).ok
        assert enc.achievement_metrics["consumed"] == 0
        out = await combat_service.act(s, char, enc, Action(kind="heal_item"), random.Random(0))
        assert out.ok
        assert enc.achievement_metrics["consumed"] == 1

async def test_delete_character_removes_achievements():
    from oathforge.services.admin import delete_player
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        await a.apply_events(s, char, [event(cid, "craft", "craft", recipe="iron_ingot")])
        await a.preference(s, char, "feature", "handmade", "feature")
        counts = await delete_player(s, char.user_id)
        assert counts["achievement_unlocks"] == 1
        for model in (AchievementProgress, AchievementUnlock, AchievementEventReceipt,
                      AchievementNotification, AchievementPreferences):
            assert await s.scalar(select(func.count()).select_from(model)) == 0

async def test_facts_come_from_the_action_without_audit_rows():
    from oathforge.database.models import ActionLog
    cid = await hero()
    async with session_scope() as s:
        char = await load(s, cid)
        out = Outcome()
        await a.emit(s, char, out, "craft", {"recipe": next(iter(get_content().recipes))})
        await a.emit(s, char, out, "craft", {"recipe": next(iter(get_content().recipes))})
        assert "handmade" in out.achievement_unlocks
        assert not await s.scalar(select(func.count(ActionLog.id)))
        char.masteries = {**(char.masteries or {}), "mining": 10 ** 6}
        await a.mastery(s, char, out, "mining")
        assert "experienced" in out.achievement_unlocks
