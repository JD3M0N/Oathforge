"""Fights through the service: rewards, defeat, illegal actions and level up."""

import random

import pytest

from oathforge.database.session import session_scope
from oathforge.engine.combat import Action
from oathforge.services import characters, combat_service
from tests.services.helpers import fight, get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


async def test_combat_victory_grants_rewards():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 200  # make the outcome certain
        enc, out = await fight(s, char, ["bandit"])
        assert enc.status == "victory" and char.state == "idle"
        assert char.xp == 25
        assert any(e.key == "progress.xp" for e in out.events)


@pytest.mark.usefixtures("ruins")
async def test_combat_defeat_respawns_injured():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp, char.gold = "old_kings_road", 1, 100
        enc, out = await fight(s, char, ["test_warden"])
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
