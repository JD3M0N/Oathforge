"""Branches of a mastery: rank 2, one active per discipline, paid once, and paused instead of lost."""

import pytest
from sqlalchemy import select

from oathforge.config import get_settings
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.engine import gathering
from oathforge.services import activities, characters, inventory, specializations

pytestmark = pytest.mark.usefixtures("database")

GUILD = "adventurers_guild"
RANK_2 = gathering.RANK_XP[2]


async def new_character(location=GUILD) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        char.location = location
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


async def test_a_branch_needs_rank_two_and_the_guild():
    cid = await new_character(location="crownreach_plaza")
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await specializations.choose(s, char, "mining_prospecting")).error == "spec.err.not_guild"
        char.location = GUILD
        assert (await specializations.choose(s, char, "nope")).error == "spec.err.unknown"
        assert (await specializations.choose(s, char, "mining_prospecting")).error == "spec.err.rank"
        char.masteries = {"mining": RANK_2}
        assert (await specializations.choose(s, char, "mining_prospecting")).ok
        assert specializations.active(char, "mining") == "mining_prospecting"


async def test_the_first_branch_is_free_and_the_change_is_paid_once():
    cid = await new_character()
    cost = get_settings().spec_switch_cost
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": RANK_2}
        char.gold = cost
        assert (await specializations.choose(s, char, "mining_extraction")).ok
        assert char.gold == cost  # the first one costs nothing
        assert (await specializations.choose(s, char, "mining_extraction")).error == "spec.err.already"
        assert char.gold == cost  # pressing the branch you already follow charges nothing
        out = await specializations.choose(s, char, "mining_prospecting")
        assert out.ok and char.gold == 0
        assert (await specializations.choose(s, char, "mining_extraction")).error == "shop.err.no_gold"


async def test_a_paused_branch_keeps_its_place_and_adds_nothing():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": RANK_2, "woodcutting": RANK_2}
        char.gold = 1000
        await specializations.choose(s, char, "mining_extraction")
        await specializations.choose(s, char, "mining_prospecting")
        assert sorted(specializations.learned(char)) == ["mining_extraction", "mining_prospecting"]
        assert specializations.active(char, "mining") == "mining_prospecting"
        mods = specializations.effects(char, "mining")
        assert mods.rare_rel > 0 and mods.extra_chance == 0  # only the active one counts
        # disciplines do not share the slot
        await specializations.choose(s, char, "woodcutting_production")
        assert specializations.active(char, "mining") == "mining_prospecting"
        assert specializations.active(char, "woodcutting") == "woodcutting_production"
        assert specializations.effects(char, "herbalism") == gathering.Mods()


async def test_the_branch_in_force_is_frozen_when_the_activity_starts():
    cid = await new_character(location="ironvein_mine")
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": gathering.RANK_XP[5]}
        char.gold = 1000
        await inventory.add_item(s, char, "pickaxe")
        char.location = GUILD
        await specializations.choose(s, char, "mining_prospecting")
        char.location = "ironvein_mine"
        assert (await activities.start(s, char, "gather", "mining", 100.0)).ok
        act = await activities.open_activity(s, char)
        assert act.result["rules"]["mods"]["rare_rel"] > 0
        # switching mid-activity is refused, and the snapshot would ignore it anyway
        char.location = GUILD
        assert (await specializations.choose(s, char, "mining_extraction")).error == "activity.err.busy"


async def test_you_cannot_switch_while_you_are_working():
    cid = await new_character(location="ironvein_mine")
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": RANK_2}
        await inventory.add_item(s, char, "pickaxe")
        assert (await activities.start(s, char, "gather", "mining", 100.0)).ok
        char.location = GUILD
        assert (await specializations.choose(s, char, "mining_extraction")).error == "activity.err.busy"
