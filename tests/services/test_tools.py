"""Specialized tools: one per discipline, fixed when the job starts, and their percentages."""

import pytest
from sqlalchemy import select

from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.engine import gathering
from oathforge.services import activities, characters, inventory, specializations

pytestmark = pytest.mark.usefixtures("database")

MINE = "ironvein_mine"


async def new_character(location=MINE) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        char.location = location
        await inventory.add_item(s, char, "pickaxe")
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


async def test_a_tool_is_chosen_only_if_owned_and_earned():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await activities.select_tool(s, char, "nope")).error == "tool.err.unknown"
        assert (await activities.select_tool(s, char, "quick_pickaxe")).error == "tool.err.not_owned"
        await inventory.add_item(s, char, "quick_pickaxe")
        assert (await activities.select_tool(s, char, "quick_pickaxe")).error == "tool.err.rank"
        char.masteries = {"mining": gathering.RANK_XP[2]}
        assert (await activities.select_tool(s, char, "quick_pickaxe")).ok
        assert activities.chosen_tool(char, "mining") == "quick_pickaxe"
        assert activities.tool_for(char, "gather", "mining") == "quick_pickaxe"  # it replaces the plain one


async def test_only_the_chosen_tool_counts():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": gathering.RANK_XP[3]}
        for key in ("quick_pickaxe", "prospectors_pickaxe", "heavy_pickaxe"):
            await inventory.add_item(s, char, key)
        await activities.select_tool(s, char, "prospectors_pickaxe")
        mods = activities.modifiers(char, "mining")
        assert mods.rare_rel > 0 and mods.time_pct == 0 and mods.extra_chance == 0  # carrying three adds nothing
        await activities.select_tool(s, char, "quick_pickaxe")
        mods = activities.modifiers(char, "mining")
        assert mods.time_pct > 0 and mods.rare_rel == 0


async def test_a_tool_and_a_branch_add_up_once_and_are_frozen_at_the_start():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": gathering.RANK_XP[3]}
        char.gold = 1000
        await inventory.add_item(s, char, "prospectors_pickaxe")
        await activities.select_tool(s, char, "prospectors_pickaxe")
        char.location = "adventurers_guild"
        await specializations.choose(s, char, "mining_prospecting")
        char.location = MINE
        mods = activities.modifiers(char, "mining")
        tool = 0.05
        branch = 0.25
        assert abs(mods.rare_rel - (tool + branch)) < 1e-9  # added once, not multiplied together
        assert (await activities.start(s, char, "gather", "mining", 100.0)).ok
        act = await activities.open_activity(s, char)
        assert abs(act.result["rules"]["mods"]["rare_rel"] - mods.rare_rel) < 1e-9
        # putting another tool on mid-job is refused, and the snapshot would ignore it anyway
        await inventory.add_item(s, char, "quick_pickaxe")
        assert (await activities.select_tool(s, char, "quick_pickaxe")).error == "activity.err.busy"


async def test_a_faster_tool_shortens_the_job_it_starts():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": gathering.RANK_XP[2]}
        await inventory.add_item(s, char, "quick_pickaxe")
        await activities.select_tool(s, char, "quick_pickaxe")
        assert (await activities.start(s, char, "gather", "mining", 100.0)).ok
        act = await activities.open_activity(s, char)
        assert act.ends_at - act.started_at == 270  # five minutes, ten percent less


async def test_a_tool_of_another_discipline_changes_nothing():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.masteries = {"mining": gathering.RANK_XP[3], "woodcutting": gathering.RANK_XP[3]}
        await inventory.add_item(s, char, "felling_axe")
        assert (await activities.select_tool(s, char, "felling_axe")).ok
        assert activities.chosen_tool(char, "mining") is None
        assert activities.tool_for(char, "gather", "mining") == "pickaxe"
        assert activities.modifiers(char, "mining") == gathering.Mods()
