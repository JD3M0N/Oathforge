import asyncio
import random

import pytest
from sqlalchemy import func, select

from oathforge.database.models import ActionLog, Character, ItemInstance, NpcMemory, QuestProgress
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action, EncounterState
from oathforge.services.events import Outcome
from oathforge.services import (
    audit, characters, combat_service, exploration, inventory, npcs, quests, world_map,
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
        assert prog["tut_muster"].state == "active"
        assert prog["sealed_box"].stage == "locked" and prog["tut_town"].state == "locked"
        assert char.resources == {"consecrated_strike": None}  # Conviction pays for it, not uses per rest
        assert characters.resource_max(char) == 2 + 2 * 1


async def test_create_warrior():
    _, cid = await new_character(cls="warrior")
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert set(gear) == {"main_hand", "ranged", "body", "off_hand"}
        assert characters.armor_class(char, gear) == 16 + 2 + 1  # chain mail, shield, Defense style
        assert char.resources == {"second_wind": None, "power_strike": None}  # the warrior pays with Focus
        assert characters.pool_of(char) == characters.resource_max(char) == 4  # base 3 + 1 per level
        cb = await characters.build_combatant(s, char)
        assert cb.row == "front" and cb.crit_range == 20
        assert [(a.key, a.damage_type) for a in cb.attacks] == [("main", "bludgeoning"), ("ranged", "slashing")]
        from oathforge.services.events import Outcome
        characters.grant_xp(char, 1000, Outcome())
        assert char.level == 4 and "action_surge" in char.resources
        assert (await characters.build_combatant(s, char)).crit_range == 19


async def test_create_priest():
    _, cid = await new_character(cls="cleric", bg="acolyte")
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 14 + 1 + 2  # scale mail (dex +1), shield
        assert char.resources == {"sacred_flame": None, "healing_word": None}  # Mana pays, not uses
        assert characters.resource_max(char) == 4 + 2 * 1
        cb = await characters.build_combatant(s, char)
        assert cb.row == "back" and cb.casting_mod == 3 and cb.spell_to_hit == 3 + 2
        assert cb.bonus_damage is None
        from oathforge.services.events import Outcome
        characters.grant_xp(char, 1800, Outcome())
        assert {"turn_undead", "bless"} <= set(char.resources)
        cb = await characters.build_combatant(s, char)
        assert cb.bonus_damage == "1d8" and cb.bonus_damage_type == "radiant"


async def test_create_mage_druid_bard():
    _, cid = await new_character(cls="sorcerer")  # human: every ability +1
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 10 + 2 + 3  # dex +2, Mage Armor
        assert char.resources == {"fire_bolt": None}
        cb = await characters.build_combatant(s, char)
        assert cb.row == "back" and cb.spell_dc == 8 + 3 + 2 and cb.spell_damage_bonus == 0
        await inventory.add_item(s, char, "chain_mail")
        mail = next(i for i in await inventory.items_of(s, char) if i.item_key == "chain_mail")
        await inventory.equip(s, char, mail.id)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 16  # chain mail: no dex, no Mage Armor

    _, cid = await new_character(tg_id=2, cls="druid")
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 11 + 2 + 2  # leather (dex +2), shield
        assert char.resources == {"thorn_whip": None, "cure_wounds": None}
        from oathforge.services.events import Outcome
        characters.grant_xp(char, 1800, Outcome())
        assert {"entangle", "wild_shape"} <= set(char.resources)
        cb = await characters.build_combatant(s, char)
        assert cb.spell_damage_bonus == cb.casting_mod > 0

    _, cid = await new_character(tg_id=3, cls="bard")
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert char.resources == {"vicious_mockery": None, "bardic_inspiration": None}
        assert characters.pool_of(char) == characters.resource_max(char) == 2  # Resonance, built up in the fight
        cb = await characters.build_combatant(s, char)
        assert cb.casting_mod == 3 and [a.finesse for a in cb.attacks] == [True]


async def test_create_warlock():
    _, cid = await new_character(cls="warlock")  # human: every ability +1
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert char.gender is None  # created without choosing (as before v0.4.4)
        assert char.resources == {"eldritch_blast": None, "hex": None}  # Essence pays, not uses per rest
        cb = await characters.build_combatant(s, char)
        assert cb.row == "back" and cb.casting_mod == 3 and cb.spell_dc == 8 + 3 + 2 and cb.spell_damage_bonus == 0
        from oathforge.services.events import Outcome
        characters.grant_xp(char, 1800, Outcome())
        assert {"shadow_armor", "void_whispers"} <= set(char.resources) and "agonizing_blast" not in char.resources
        cb = await characters.build_combatant(s, char)
        assert cb.spell_damage_bonus == cb.casting_mod > 0


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


class Ambush(random.Random):
    """Every roll on the way says «ambush» and picks the first choice."""

    def random(self):
        return 0.0


async def test_a_trip_rolls_one_ambush_and_carries_on():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for place in ("old_kings_road", "whispering_woods"):
            characters.visited(char, place)
        assert exploration.trip_chance(world_map.route_to(char, "old_kings_road")) == pytest.approx(0.15)
        assert exploration.trip_chance(world_map.route_to(char, "whispering_woods")) == pytest.approx(0.35)
        out = await exploration.travel(s, char, "whispering_woods", Ambush(1))
        assert out.ok and char.location == "old_kings_road" and char.state == "in_combat"
        assert out.events[0].key == "explore.trip_stopped"
        assert char.flags["trip"] == {"to": "whispering_woods", "rolled": True}
        char.state = "idle"  # the fight is over
        assert exploration.trip(char) == "whispering_woods"
        out = await exploration.travel(s, char, "whispering_woods", Ambush(1))  # no second roll
        assert out.ok and char.location == "whispering_woods" and char.state == "idle"
        assert "trip" not in char.flags


async def test_defeat_ends_the_trip():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.flags = {**char.flags, "trip": {"to": "whispering_woods", "rolled": True}}
        await characters.defeat_penalty(char, Outcome())
        assert "trip" not in char.flags


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
            char.checks_tried = {}  # a new day: failed secrets can be tried again
            await exploration.investigate(s, char, random.Random(seed))
        assert char.flags.get("found_ossuary_coins") and char.flags.get("warden_lore")
        assert char.gold == gold0 + 25
        out = await exploration.investigate(s, char, random.Random(0))
        assert out.events[0].key == "explore.nothing_more"


class AlwaysOne(random.Random):
    def randint(self, a, b):
        return a


async def test_failed_investigation_waits_for_tomorrow(monkeypatch):
    _, cid = await new_character(cls="rogue", bg="scholar")
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "crypt_ossuary"
        out = await exploration.investigate(s, char, AlwaysOne())
        assert out.events[-1].key == "explore.found_nothing"
        assert (await exploration.investigate(s, char, random.Random(0))).events[0].key == "explore.already_tried"
        tomorrow = exploration.time.time() + exploration.GAME_DAY_SECONDS
        monkeypatch.setattr(exploration.time, "time", lambda: tomorrow)
        assert (await exploration.investigate(s, char, AlwaysOne())).events[0].key == "check.result"


async def test_free_check_once_per_skill_place_and_day(monkeypatch):
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out, _ = await exploration.check_skill(s, char, "investigation", "medium", random.Random(0))
        assert out.ok and out.events[0].key == "check.result"
        out, ok = await exploration.check_skill(s, char, "investigation", "medium", random.Random(0))
        assert not out.ok and out.error == "check.already_tried" and not ok
        # another skill, or the same skill somewhere else, is a new attempt
        assert (await exploration.check_skill(s, char, "perception", "medium", random.Random(0)))[0].ok
        char.location = "broken_crown_tavern"
        assert (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        assert not (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        # levelling up lets you try again
        char.level += 1
        assert (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        # so does a new day, which also forgets older attempts
        tomorrow = exploration.time.time() + exploration.GAME_DAY_SECONDS
        monkeypatch.setattr(exploration.time, "time", lambda: tomorrow)
        assert (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        assert list(char.checks_tried) == ["free:investigation:broken_crown_tavern"]


async def test_long_rest_is_80_minutes_asleep_then_restores():
    from oathforge.services import activities

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp = "broken_crown_tavern", 1
        characters.set_pool(char, 0)  # the bar is spent
        char.conditions = {"injured": True}
        out = await activities.start(s, char, "rest", "rest", now=1000)
        assert out.ok and char.gold == 10 and char.state == "busy" and char.hp == 1  # paid, asleep, not healed yet
        assert (await exploration.travel(s, char, "crownreach_plaza", random.Random(0))).error == "activity.err.busy"
        assert (await activities.claim(s, char, now=1000 + 79 * 60)).error == "activity.err.not_ready"
        out = await activities.claim(s, char, now=1000 + 80 * 60)
        assert out.ok and char.state == "idle" and char.hp == char.max_hp
        assert characters.pool_of(char) == characters.resource_max(char) > 0 and "injured" not in char.conditions


async def test_abandoned_rest_heals_nothing_and_keeps_the_gold():
    from oathforge.services import activities

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp = "broken_crown_tavern", 1
        await activities.start(s, char, "rest", "rest", now=1000)
        assert (await activities.cancel(s, char, now=1060)).ok
        assert char.hp == 1 and char.gold == 10 and char.state == "idle"


async def test_chapel_cures_wounds_for_free_and_closes_grave_ones():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "crownreach_chapel"
        assert (await exploration.cure_wounds(s, char, random.Random(0))).error == "inv.err.full_hp"
        char.hp = 1
        out = await exploration.cure_wounds(s, char, random.Random(0))
        assert out.ok and char.gold == 15 and char.hp == char.max_hp  # free and complete during the beta
        # after a defeat: injured and broke, Ysolde still helps and closes the grave wounds
        char.hp, char.gold, char.conditions = 1, 0, {"injured": True}
        out = await exploration.cure_wounds(s, char, random.Random(0))
        assert out.ok and "injured" not in char.conditions and "explore.healed_injured" in [e.key for e in out.events]
        char.hp = char.max_hp // 2
        char.conditions = {"injured": True}  # even at the half-HP cap, she can close them
        assert (await exploration.cure_wounds(s, char, random.Random(0))).ok and "injured" not in char.conditions
        char.location = "crownreach_plaza"
        assert (await exploration.cure_wounds(s, char, random.Random(0))).error == "explore.err.no_healer"


def test_day_night_clock():
    assert exploration.game_hour(0) == 0 and exploration.is_night(0)
    assert not exploration.is_night(exploration.GAME_DAY_SECONDS / 2)
    hour = exploration.GAME_DAY_SECONDS / 24  # ten real minutes
    assert exploration.clock(0) == "00:00" and exploration.clock(14.5 * hour) == "14:30"
    assert exploration.until_switch(0) == 60  # midnight: dawn at 06:00, six game hours away
    assert exploration.until_switch(19 * hour) == 10  # dusk at 20:00
    assert exploration.until_switch(23 * hour) == 70  # night: dawn tomorrow


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
        characters.grant_xp(char, 500, out)
        assert char.level == 3 and char.max_hp > 12
        assert "lay_on_hands" in char.resources
        assert any(e.key == "progress.level_up" for e in out.events)


# ---------------------------------------------------------------- quest

async def unlock_sealed_box(s, char) -> None:
    prog = (await quests.progress(s, char, lock=True))["sealed_box"]
    prog.stage, prog.state = "not_started", "available"


async def test_sealed_box_covenant_branch_to_completion():
    _, cid = await new_character()
    rng = random.Random(3)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await unlock_sealed_box(s, char)
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
        prog = await s.scalar(select(QuestProgress).where(QuestProgress.character_id == cid,
                                                          QuestProgress.quest_key == "sealed_box"))
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


# ---------------------------------------------------------------- media

async def test_media_file_id_cache_per_bot_and_checksum():
    from dataclasses import replace

    from oathforge.content import get_content
    from oathforge.services import media

    asset = get_content().media.zone_images("crownreach")[0]
    async with session_scope() as s:
        assert await media.get_file_id(s, 1, asset) is None
        await media.remember(s, 1, asset, "FILE_A", "UA")
    async with session_scope() as s:
        assert await media.get_file_id(s, 1, asset) == "FILE_A"
        assert await media.get_file_id(s, 2, asset) is None  # file_ids belong to one bot
        changed = replace(asset, checksum="0" * 64)
        assert await media.get_file_id(s, 1, changed) is None  # file replaced: upload again
        await media.remember(s, 1, changed, "FILE_B", "UB")
    async with session_scope() as s:
        assert await media.get_file_id(s, 1, changed) == "FILE_B"
        await media.forget(s, 1, changed)
    async with session_scope() as s:
        assert await media.get_file_id(s, 1, changed) is None


# ---------------------------------------------------------------- missions

async def test_mission_chain_talk_then_hunt():
    _, cid = await new_character()
    rng = random.Random(1)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_talk(s, char, "vale", rng)
        assert (await quests.progress(s, char))["tut_muster"].state == "active"  # still has to read the rulebook
        await quests.on_read(s, char, "dice", rng)  # another page does not count
        assert (await quests.progress(s, char))["tut_muster"].state == "active"
        out = await quests.on_read(s, char, "activities", rng)
        prog = await quests.progress(s, char)
        assert prog["tut_muster"].state == "completed" and prog["tut_town"].state == "active"
        assert char.xp == 25 and any(e.key == "quest.new" for e in out.events)
        assert await inventory.count(s, char, "skinning_knife") == 1
        assert not (await quests.on_talk(s, char, "vale", rng)).events  # nothing left to count

        await quests.on_talk(s, char, "bram", rng)
        assert (await quests.progress(s, char))["tut_town"].state == "active"  # still has to see the workshops
        await quests.on_visit(s, char, "crownreach_workshops", rng)
        assert (await quests.progress(s, char))["tut_town"].state == "active"  # and the tavern
        await quests.on_visit(s, char, "broken_crown_tavern", rng)
        prog = await quests.progress(s, char)
        assert prog["tut_town"].state == "completed" and prog["tut_market"].state == "active"

        await quests.on_talk(s, char, "mira", rng)
        await quests.on_talk(s, char, "tessa", rng)
        prog = await quests.progress(s, char)
        assert prog["tut_market"].state == "completed" and prog["tut_boars"].state == "active"

        await quests.on_defeat(s, char, "boar", rng)  # a kill alone is not a hunt
        assert (await quests.progress(s, char))["tut_boars"].counters == {}
        out = await quests.advance(s, char, "hunt", "tusk_meadow", rng)
        assert any(e.key == "quest.progress" and e.params["n"] == 1 for e in out.events)
        await quests.advance(s, char, "hunt", "ironvein_mine", rng)  # elsewhere does not count
        await quests.advance(s, char, "hunt", "tusk_meadow", rng)
        assert (await quests.progress(s, char))["tut_boars"].state == "active"  # the meat is missing
        await quests.on_items(s, char, "skin", {"boar_hide": 1, "raw_meat": 2}, rng)
        prog = await quests.progress(s, char)
        assert prog["tut_boars"].state == "completed" and prog["tut_herbs"].state == "active"
        assert char.xp == 25 + 25 + 25 + 100  # the fights' XP comes from the fight, not from here
        assert await inventory.count(s, char, "sickle") == 1
        assert prog["sealed_box"].state == "locked"


async def test_mission_unlocks_by_flag_and_counts_only_when_active():
    _, cid = await new_character()
    rng = random.Random(1)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_defeat(s, char, "crypt_skeleton", rng)  # crypt_bones still locked: no count
        assert (await quests.progress(s, char))["crypt_bones"].counters == {}
        char.flags = {**char.flags, "crypt_unlocked": True}
        await quests.refresh(s, char, Outcome())
        assert (await quests.progress(s, char))["crypt_bones"].state == "active"
        for _ in range(3):
            await quests.on_defeat(s, char, "crypt_skeleton", rng)
        assert (await quests.progress(s, char))["crypt_bones"].state == "completed"


async def test_the_whole_chain_from_the_muster_to_the_crypt():
    """With the table of twenty levels the old chain goes a little past five; no gate stops it,
    because the gates of roadmap_balance only start at nine."""
    _, cid = await new_character()
    rng = random.Random(5)

    async def fight(char, monster, hunt_at=None):
        characters.grant_xp(char, get_content().monsters[monster].xp, Outcome())
        await quests.on_defeat(s, char, monster, rng)
        if hunt_at:
            await quests.advance(s, char, "hunt", hunt_at, rng)

    async with session_scope() as s:
        char = await get_char(s, cid)
        # the tutorial: talk, city, market, hunt and skin, gather, cook, mine, hunt, heal and rest, a boss
        await quests.on_talk(s, char, "vale", rng)
        await quests.on_read(s, char, "activities", rng)
        await quests.on_talk(s, char, "bram", rng)
        await quests.on_visit(s, char, "crownreach_workshops", rng)
        await quests.on_visit(s, char, "broken_crown_tavern", rng)
        await quests.on_talk(s, char, "mira", rng)
        await quests.on_talk(s, char, "tessa", rng)
        for _ in range(2):
            await fight(char, "boar", "tusk_meadow")
        await quests.on_items(s, char, "skin", {"raw_meat": 2}, rng)
        await quests.on_items(s, char, "gather", {"bloodroot": 3}, rng)
        await quests.on_items(s, char, "craft", {"hunter_stew": 1}, rng)
        assert await inventory.count(s, char, "pickaxe") == 1
        await quests.on_items(s, char, "gather", {"iron_ore": 2, "coal": 1}, rng)
        await quests.on_items(s, char, "gather", {"iron_ore": 1}, rng)
        assert await inventory.count(s, char, "woodaxe") == 1  # the room mission needs wood
        await quests.on_items(s, char, "craft", {"furniture:chest": 1}, rng)
        await quests.on_items(s, char, "craft", {"furniture:bed": 1}, rng)
        for monster in ("cave_bat", "giant_rat", "cave_bat"):
            await fight(char, monster, "ironvein_mine")
        await quests.on_talk(s, char, "ysolde", rng)
        await quests.advance(s, char, "rest", "broken_crown_tavern", rng)
        await quests.on_talk(s, char, "vale", rng)
        prog = await quests.progress(s, char)
        assert prog["old_tusk"].state == "active" and char.flags.get("old_tusk_hunt")
        assert prog["sealed_box"].state == "locked"  # no crypt during the tutorial
        await fight(char, "old_tusk")
        prog = await quests.progress(s, char)
        assert prog["old_tusk"].state == "ready"  # beating it is not getting paid: Bram owes you
        gold, xp = char.gold, char.xp
        assert not (await quests.turn_in(s, char, "old_tusk", [], rng)).ok  # Bram is not here
        assert (char.gold, char.xp) == (gold, xp)
        char.location = "broken_crown_tavern"
        assert (await quests.turn_in(s, char, "old_tusk", ["bram"], rng)).ok
        assert (char.gold, char.xp) == (gold + 80, xp + 300)
        again = await quests.turn_in(s, char, "old_tusk", ["bram"], rng)  # the service pays once
        assert not again.ok and (char.gold, char.xp) == (gold + 80, xp + 300)
        prog = await quests.progress(s, char)
        assert all(prog[k].state == "completed" for k, q in get_content().quests.items() if q.tutorial)
        assert prog["sealed_box"].stage == "not_started" and char.level >= 3
        # after the tutorial: Holt's reliquary and the crypt
        char.location = "whispering_woods"
        await quests.perform(s, char, "sealed_box.approach_guard", [], rng)
        char.location = "crownreach_plaza"
        await quests.perform(s, char, "sealed_box.give_box_holt", ["holt"], rng)
        assert (await quests.progress(s, char))["crypt_bones"].state == "active"
        for monster, n in (("crypt_skeleton", 4), ("crypt_warden", 1)):
            for _ in range(n):
                await fight(char, monster)
        prog = await quests.progress(s, char)
        assert prog["sealed_box"].state == "completed" and prog["crypt_bones"].state == "completed"
        assert char.level == 6 and characters.eligible_level(char) == 6  # nothing gates it below nine


async def test_ensure_progress_adds_missions_to_old_characters():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for p in (await quests.progress(s, char)).values():
            if p.quest_key != "sealed_box":
                await s.delete(p)
    async with session_scope() as s:
        char = await get_char(s, cid)
        journal = await quests.journal(s, char)
        assert [k for k, _, p in journal if p is None] == [
            k for k, _ in quests.ordered_quests() if k != "sealed_box"]
        await quests.refresh(s, char, Outcome())
        prog = await quests.progress(s, char)
        assert set(prog) == set(get_content().quests) and prog["tut_muster"].state == "active"


async def test_veterans_of_the_old_chain_skip_the_tutorial():
    """A character who finished the old first missions (night_wings) gets the tutorial already done."""
    from oathforge.database.models import QuestProgress

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for p in (await quests.progress(s, char)).values():
            if p.quest_key.startswith("tut_"):
                await s.delete(p)
        s.add(QuestProgress(character_id=cid, quest_key="night_wings", stage="done", state="completed", counters={}))
    async with session_scope() as s:
        char = await get_char(s, cid)
        xp = char.xp
        await quests.refresh(s, char, Outcome())
        prog = await quests.progress(s, char)
        assert all(prog[k].state == "completed" for k in prog if k.startswith("tut_"))
        assert prog["old_tusk"].state == "active" and char.xp == xp  # the last test opens, and no rewards paid
        assert await quests.location_texts(s, char) is not None  # the old row is ignored, not an error


# ---------------------------------------------------------------- hunting and bestiary

@pytest.mark.parametrize("night", [False, True])
async def test_the_meadow_has_boars_day_and_night(monkeypatch, night):
    """«Tusks in the Meadow» does not depend on the hour either."""
    monkeypatch.setattr(exploration, "is_night", lambda now=None: night)
    loc = get_content().locations["tusk_meadow"]
    assert any("boar" in e.monsters for e in exploration.encounter_table(loc, 1))


async def test_a_single_objective_says_what_comes_next():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await quests.on_talk(s, char, "vale", random.Random(0))
        nxt = [e for e in out.events if e.key == "quest.next"]
        assert nxt and "rulebook" in nxt[0].params["step"]["en"]


async def test_a_quest_giver_repeats_the_hint_when_the_ai_is_down(llm):
    from oathforge.services import actions
    user_id, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "adventurers_guild"  # Vale signs up recruits at the guild hall
    line, _ = await actions.talk(llm, user_id, "vale", "¿Y ahora qué?")  # the fake LLM answers nothing
    assert "te recuerda lo que toca" in line and "/rulebook" in line


@pytest.mark.parametrize("night", [False, True])
async def test_the_mine_has_bats_day_and_night(monkeypatch, night):
    """The tutorial's bat hunt («Alas al anochecer») does not depend on the hour."""
    monkeypatch.setattr(exploration, "is_night", lambda now=None: night)
    loc = get_content().locations["ironvein_mine"]
    assert any("cave_bat" in e.monsters for e in exploration.encounter_table(loc, 1))


@pytest.mark.parametrize("night,expected", [(False, {"boar"}), (True, {"cave_bat"})])
async def test_hunt_uses_the_day_or_night_table(monkeypatch, night, expected):
    monkeypatch.setattr(exploration, "is_night", lambda now=None: night)
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "tusk_meadow"
        out = await exploration.hunt(s, char, random.Random(0))
        assert out.ok and char.state == "in_combat"
        enc = await combat_service.active_encounter(s, char)
        refs = {c["ref"] for c in enc.state["combatants"].values() if c["side"] == "enemy"}
        assert refs == expected
        assert set(char.bestiary) == expected


async def test_hunt_only_where_there_is_prey_and_boss_first():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await exploration.hunt(s, char, random.Random(0))).error == "explore.err.no_hunting"
        char.location, char.flags = "tusk_meadow", {"old_tusk_hunt": True}
        out = await exploration.hunt(s, char, random.Random(0))
        assert out.events[0].key == "explore.hunt_boss"
        enc = await combat_service.active_encounter(s, char)
        assert enc.fixed_flag == "cleared_old_tusk"


async def test_bestiary_records_seen_and_killed():
    from oathforge.services import bestiary
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 200
        assert bestiary.tier(char.bestiary.get("grey_wolf")) == 0
        await _fight(s, char, ["grey_wolf", "grey_wolf"])
        assert char.bestiary["grey_wolf"] == {"seen": 1, "killed": 2}
        assert bestiary.tier(char.bestiary["grey_wolf"]) == 2
        await _fight(s, char, ["grey_wolf"], seed=1)
        assert bestiary.tier(char.bestiary["grey_wolf"]) == 3
        assert [k for k, _ in bestiary.known(char)] == ["grey_wolf"]


def test_anything_worth_a_coin_sells_for_at_least_one():
    assert inventory.sell_price("torch", 0) == 1
    assert inventory.sell_price("longsword", 0) == 8


async def test_two_enemies_of_the_same_kind_get_letters():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        enc, _ = await combat_service.start_encounter(s, char, ["boar", "boar", "cave_bat"], random.Random(0))
        names = {c.name["es"] for k, c in EncounterState.model_validate(enc.state).combatants.items() if k != "p1"}
        assert names == {"Jabalí A", "Jabalí B", "Murciélago de cueva"}


async def test_tutorial_runs_time_each_mission():
    from datetime import datetime, timedelta, timezone

    from oathforge.services import admin
    _, cid = await new_character()
    rng = random.Random(0)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_talk(s, char, "vale", rng)
        await quests.on_read(s, char, "activities", rng)
    async with session_scope() as s:
        runs = await admin.tutorial_runs(s, now=datetime.now(timezone.utc) + timedelta(minutes=30))
        run = next(r for r in runs if r.name == "Aldric")
        assert list(run.minutes) == ["tut_muster"] and run.current == "tut_town" and not run.done
        assert 29 < run.waiting < 31  # stuck on the second mission for half an hour


def test_packs_of_two_wait_for_level_two(monkeypatch):
    """Level 1 fights one boar at a time (tutorial); pairs come from level 2."""
    monkeypatch.setattr(exploration, "is_night", lambda now=None: False)
    loc = get_content().locations["tusk_meadow"]
    assert all(len(e.monsters) == 1 for e in exploration.encounter_table(loc, 1))
    assert any(len(e.monsters) == 2 for e in exploration.encounter_table(loc, 2))
