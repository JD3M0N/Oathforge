"""NPC memory and trust, and the media file_id cache."""

import random

import pytest
from sqlalchemy import func, select

from oathforge.database.models import NpcMemory
from oathforge.database.session import session_scope
from oathforge.services import npcs
from tests.services.helpers import get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


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
