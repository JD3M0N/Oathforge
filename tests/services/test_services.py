import asyncio
import random

import pytest
from sqlalchemy import func, select

from oathforge.database.models import ActionLog, Character, ItemInstance, NpcMemory, QuestProgress
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action
from oathforge.services import (
    audit, characters, combat_service, exploration, inventory, npcs, quests,
)

pytestmark = pytest.mark.usefixtures("database")


async def new_character(tg_id=1, cls="paladin", lineage="human", bg="soldier") -> tuple[int, int]:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, tg_id, "es")
        char = await characters.create_character(s, user, "Aldric", lineage, bg, cls)
        return user.id, char.id


async def get_char(s, char_id, lock=True) -> Character:
    stmt = select(Character).where(Character.id == char_id)
    return await s.scalar(stmt.with_for_update() if lock else stmt)


# ---------------------------------------------------------------- creation

async def test_create_character_sets_everything_up():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert char.abilities == {"str": 16, "con": 15, "cha": 14, "wis": 13, "dex": 11, "int": 9}
        assert char.hp == char.max_hp == 12
        assert char.location == "crownreach_plaza" and char.gold == 15
        gear = await characters.equipped(s, char)
        assert set(gear) == {"main_hand", "body", "off_hand"}
        assert characters.armor_class(char, gear) == 18
        skills = await characters.skills_of(s, char)
        assert skills["athletics"].proficient and skills["intimidation"].proficient
        assert characters.skill_bonus(char, skills, "athletics") == 3 + 2
        prog = await quests.progress(s, char)
        assert prog["sealed_box"].stage == "not_started"
        assert char.resources == {"consecrated_strike": 2}


async def test_user_language_normalized():
    async with session_scope() as s:
        u = await characters.get_or_create_user(s, 99, "en-GB")
        assert u.language == "en"
        u2 = await characters.get_or_create_user(s, 100, "fr")
        assert u2.language == "es"


def test_name_validation():
    assert characters.valid_name("Lyra")
    assert characters.valid_name("Ser Aldric-Vane")
    assert not characters.valid_name("x")
    assert not characters.valid_name("<b>hack</b>")


# ---------------------------------------------------------------- exploration

async def test_travel_only_along_routes():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await exploration.travel(s, char, "crypt_sanctum", random.Random(0))
        assert not out.ok and char.location == "crownreach_plaza"
        out = await exploration.travel(s, char, "broken_crown_tavern", random.Random(0))
        assert out.ok and char.location == "broken_crown_tavern"


async def test_locked_route_needs_flag():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "whispering_woods"
        assert "crypt_entrance" not in [e.to for e in exploration.exits(char)]
        char.flags = {"crypt_unlocked": True}
        assert "crypt_entrance" in [e.to for e in exploration.exits(char)]


async def test_fixed_encounter_triggers_once():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.flags = "whispering_woods", {"crypt_unlocked": True}
        out = await exploration.travel(s, char, "crypt_entrance", random.Random(1))
        assert out.encounter_id and char.state in ("in_combat", "idle")
        enc = await combat_service.active_encounter(s, char)
        if enc:
            assert enc.fixed_flag == "cleared_crypt_entrance"


async def test_investigate_finds_discovery_once():
    _, cid = await new_character(cls="rogue", bg="scholar")
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "crypt_ossuary"
        gold0 = char.gold
        for seed in range(40):
            await exploration.investigate(s, char, random.Random(seed))
        assert char.flags.get("found_ossuary_coins") and char.flags.get("warden_lore")
        assert char.gold == gold0 + 25
        out = await exploration.investigate(s, char, random.Random(0))
        assert out.events[0].key == "explore.nothing_more"


async def test_rest_costs_gold_and_restores():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp, char.resources = "broken_crown_tavern", 1, {"consecrated_strike": 0}
        char.conditions = {"injured": True}
        out = await exploration.rest(s, char)
        assert out.ok and char.hp == char.max_hp and char.gold == 10
        assert char.resources["consecrated_strike"] == 2 and "injured" not in char.conditions


def test_day_night_clock():
    assert exploration.game_hour(0) == 0 and exploration.is_night(0)
    assert not exploration.is_night(exploration.GAME_DAY_SECONDS / 2)


# ---------------------------------------------------------------- inventory & shops

async def test_potion_heals_and_is_consumed():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = 2
        out = await inventory.use_item_outside_combat(s, char, "healing_potion", random.Random(0))
        assert out.ok and char.hp > 2
        assert await inventory.count(s, char, "healing_potion") == 0
        again = await inventory.use_item_outside_combat(s, char, "healing_potion", random.Random(0))
        assert not again.ok


async def test_buy_sell_and_reputation_prices():
    _, cid = await new_character()
    assert inventory.buy_price("chain_mail", 100) < inventory.buy_price("chain_mail", 0) < inventory.buy_price("chain_mail", -100)
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.gold = 3
        out = await inventory.buy(s, char, "tessa", "chain_mail", 0)
        assert not out.ok and char.gold == 3
        out = await inventory.buy(s, char, "tessa", "torch", 0)
        assert out.ok and char.gold == 2
        rope = next(i for i in await inventory.items_of(s, char) if i.item_key == "rope")
        out = await inventory.sell(s, char, "tessa", rope.id, 0)
        assert out.ok


async def test_cannot_sell_equipped_or_quest_items():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        sword = next(i for i in await inventory.items_of(s, char) if i.item_key == "longsword")
        assert not (await inventory.sell(s, char, "tessa", sword.id, 0)).ok


async def test_equip_swaps_slot():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await inventory.add_item(s, char, "dagger")
        dagger = next(i for i in await inventory.items_of(s, char) if i.item_key == "dagger")
        assert (await inventory.equip(s, char, dagger.id)).ok
        gear = await characters.equipped(s, char)
        assert gear["main_hand"].item_key == "dagger"


async def test_remove_item_is_all_or_nothing():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert not await inventory.remove_item(s, char, "healing_potion", 2)
        assert await inventory.count(s, char, "healing_potion") == 1


async def test_concurrent_potion_double_spend(is_postgres):
    if not is_postgres:
        pytest.skip("row-lock concurrency needs PostgreSQL (set TEST_DATABASE_URL)")
    _, cid = await new_character()

    async def spend():
        async with session_scope() as s:
            char = await get_char(s, cid, lock=False)
            ok = await inventory.remove_item(s, char, "healing_potion", 1)
            await asyncio.sleep(0.05)
            return ok

    results = await asyncio.gather(spend(), spend())
    assert sorted(results) == [False, True]
    async with session_scope() as s:
        n = await s.scalar(select(func.count()).select_from(ItemInstance)
                           .where(ItemInstance.owner_character_id == cid, ItemInstance.item_key == "healing_potion"))
        assert n == 0


# ---------------------------------------------------------------- idempotency

async def test_duplicate_nonce_is_rejected():
    uid, cid = await new_character()
    async with session_scope() as s:
        assert await audit.claim(s, "1:abc", user_id=uid, character_id=cid, verb="go") is not None
    async with session_scope() as s:
        assert await audit.claim(s, "1:abc", user_id=uid, character_id=cid, verb="go") is None
        assert await audit.claim(s, "1:other", user_id=uid, character_id=cid, verb="go") is not None
    async with session_scope() as s:
        assert await s.scalar(select(func.count()).select_from(ActionLog)) == 2


# ---------------------------------------------------------------- combat

async def _fight(s, char, monsters, seed=0):
    rng = random.Random(seed)
    enc, out = await combat_service.start_encounter(s, char, monsters, rng)
    steps = 0
    while enc.status == "active" and steps < 100:
        steps += 1
        out.extend(await combat_service.act(s, char, enc, Action(kind="attack", weapon="main"), rng))
    return enc, out


async def test_combat_victory_grants_rewards():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 200  # make the outcome certain
        enc, out = await _fight(s, char, ["bandit"])
        assert enc.status == "victory" and char.state == "idle"
        assert char.xp == 25
        assert any(e.key == "progress.xp" for e in out.events)


async def test_combat_defeat_respawns_injured():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp, char.gold = "old_kings_road", 1, 100
        enc, out = await _fight(s, char, ["crypt_warden"])
        assert enc.status == "defeat"
        assert char.location == "crownreach_plaza" and char.conditions.get("injured")
        assert char.gold == 90 and char.hp >= 1


async def test_combat_refuses_illegal_action():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        enc, _ = await combat_service.start_encounter(s, char, ["bandit"], random.Random(0))
        if enc.status == "active":
            out = await combat_service.act(s, char, enc, Action(kind="attack", target="m9"), random.Random(0))
            assert not out.ok and out.error == "combat.err.bad_target"


async def test_level_up():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        from oathforge.services.events import Outcome
        out = Outcome()
        characters.grant_xp(char, 900, out)
        assert char.level == 3 and char.max_hp > 12
        assert "lay_on_hands" in char.resources
        assert any(e.key == "progress.level_up" for e in out.events)


# ---------------------------------------------------------------- quest

async def test_sealed_box_covenant_branch_to_completion():
    _, cid = await new_character()
    rng = random.Random(3)
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "whispering_woods"
        out = await quests.perform(s, char, "sealed_box.approach_guard", [], rng)
        assert out.ok and await inventory.count(s, char, "sealed_reliquary") == 1
        char.location = "crownreach_plaza"
        out = await quests.perform(s, char, "sealed_box.give_box_holt", ["holt"], rng)
        assert out.ok and char.flags["crypt_unlocked"]
        assert await inventory.count(s, char, "sealed_reliquary") == 0
        reps = await npcs.reputations(s, char)
        assert reps["silver_covenant"] >= 15 and reps["crimson_syndicate"] == -5
        mems = await npcs.recall(s, "holt", char)
        assert any("reliquary" in m.text for m in mems)
        # already done: cannot repeat or take the other branch
        assert not (await quests.perform(s, char, "sealed_box.sell_box_mira", ["mira"], rng)).ok
        out = await quests.on_defeat(s, char, "crypt_warden", rng)
        prog = (await quests.progress(s, char))["sealed_box"]
        assert prog.stage == "completed_covenant" and prog.state == "completed"
        rumors = await npcs.recent_rumors(s)
        assert any("Aldric" in r["es"] for r in rumors)


async def test_quest_action_needs_npc_present_and_location():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert not (await quests.perform(s, char, "sealed_box.approach_guard", [], random.Random(0))).ok
        await inventory.add_item(s, char, "sealed_reliquary")
        prog = await s.scalar(select(QuestProgress).where(QuestProgress.character_id == cid))
        prog.stage = "has_box"
        assert not (await quests.perform(s, char, "sealed_box.give_box_holt", [], random.Random(0))).ok
        assert (await quests.perform(s, char, "sealed_box.sell_box_mira", ["mira"], random.Random(0))).ok
        assert char.flags.get("syndicate_in_crypt")


# ---------------------------------------------------------------- npcs

async def test_steal_memory_and_trust():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "broken_crown_tavern"
        outcomes = [await npcs.steal(s, char, "bram", random.Random(seed)) for seed in range(30)]
        caught = sum(1 for o in outcomes if any(e.key == "steal.caught" for e in o.events))
        assert caught > 0
        mems = await npcs.recall(s, "bram", char)
        assert mems and mems[0].importance == 5
        rel = await npcs.relationship(s, "bram", char)
        assert rel.trust == -10  # clamped
    async with session_scope() as s:
        total = await s.scalar(select(func.count()).select_from(NpcMemory))
        assert total >= caught


async def test_recall_limit_and_order():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for i in range(8):
            await npcs.remember(s, "tessa", char, f"m{i}", importance=1 + (i % 5))
        await s.flush()
        mems = await npcs.recall(s, "tessa", char)
        assert len(mems) == 5 and mems[0].importance == 5
        assert await npcs.recall(s, "bram", char) == []
