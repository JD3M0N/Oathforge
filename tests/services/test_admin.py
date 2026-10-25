"""Deleting one player removes everything that hangs from them and nothing of anyone else."""

import pytest
from sqlalchemy import func, select

from oathforge.database.models import (
    ActionLog, Character, CombatAction, Encounter, ItemInstance, NpcMemory, Party, User,
)
from oathforge.database.session import session_scope
from oathforge.services import admin, characters

pytestmark = pytest.mark.usefixtures("database")


async def new_player(s, telegram_id: int, name: str) -> Character:
    user = await characters.get_or_create_user(s, telegram_id, "es")
    return await characters.create_character(s, user, name, "human", "soldier", "warrior")


async def count(s, model, *where) -> int:
    return await s.scalar(select(func.count()).select_from(model).where(*where))


async def test_delete_player_cascades_and_spares_the_others():
    async with session_scope() as s:
        aldric = await new_player(s, 111, "Aldric")
        brenna = await new_player(s, 222, "Brenna")
        await characters.get_or_create_user(s, 333, "en")  # no character yet
        party = Party(leader_character_id=aldric.id)
        s.add(party)
        await s.flush()
        mine = Encounter(character_id=aldric.id, location="toll_post", state={})
        theirs = Encounter(character_id=brenna.id, party_id=party.id, location="toll_post", state={})
        s.add_all([mine, theirs])
        await s.flush()
        s.add_all([
            CombatAction(encounter_id=mine.id, round=1, actor="p1", action={}, result=[]),
            NpcMemory(npc_key="bram", character_id=aldric.id, text="owes me"),
            ItemInstance(owner_character_id=aldric.id, item_key="iron_ingot"),
            ItemInstance(owner_character_id=brenna.id, item_key="iron_sword", crafted_by=aldric.id),
            ActionLog(user_id=aldric.user_id, character_id=aldric.id, verb="test"),
        ])
        aldric_id, aldric_user, brenna_id, theirs_id = aldric.id, aldric.user_id, brenna.id, theirs.id

    async with session_scope() as s:
        (found,) = await admin.find_players(s, "aldric")
        assert found.telegram_id == 111
        counts = await admin.delete_player(s, found.user_id)
        assert counts["users"] == 1 and counts["characters"] == 1 and counts["combat_actions"] == 1

    async with session_scope() as s:
        assert await count(s, User) == 2 and await count(s, Character) == 1
        assert await count(s, Encounter, Encounter.character_id == aldric_id) == 0
        assert await count(s, CombatAction) == 0 and await count(s, NpcMemory) == 0 and await count(s, Party) == 0
        log = await s.scalar(select(ActionLog))  # the audit log stays, anonymised (SET NULL)
        assert log.user_id is None and log.character_id is None
        sword = await s.scalar(select(ItemInstance).where(ItemInstance.owner_character_id == brenna_id,
                                                          ItemInstance.item_key == "iron_sword"))
        assert sword.crafted_by is None  # Brenna keeps it
        assert (await s.get(Encounter, theirs_id)).party_id is None
        assert await count(s, User, User.id == aldric_user) == 0
        assert await count(s, ItemInstance, ItemInstance.owner_character_id == aldric_id) == 0


async def test_find_players_by_id_name_and_listing():
    async with session_scope() as s:
        await new_player(s, 111, "Aldric")
        await new_player(s, 222, "ALDRIC")
        await characters.get_or_create_user(s, 333, "en")

    async with session_scope() as s:
        assert len(await admin.find_players(s, "Aldric")) == 2  # ambiguous: the CLI asks for the id
        (by_id,) = await admin.find_players(s, "222")
        assert by_id.name == "ALDRIC" and by_id.level == 1
        assert await admin.find_players(s, "nobody") == []
        players = await admin.list_players(s)
        assert [p.telegram_id for p in players] == [111, 222, 333] and players[2].name is None
