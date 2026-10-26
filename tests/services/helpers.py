"""Shortcuts shared by the service tests: create a character and load it."""

import random

from sqlalchemy import select

from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action
from oathforge.services import characters, combat_service


async def new_character(tg_id=1, cls="paladin", lineage="human", bg="soldier") -> tuple[int, int]:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, tg_id, "es")
        char = await characters.create_character(s, user, "Aldric", lineage, bg, cls)
        return user.id, char.id


async def get_char(s, char_id, lock=True) -> Character:
    stmt = select(Character).where(Character.id == char_id)
    return await s.scalar(stmt.with_for_update() if lock else stmt)


async def fight(s, char, monsters, seed=0):
    rng = random.Random(seed)
    enc, out = await combat_service.start_encounter(s, char, monsters, rng)
    steps = 0
    while enc.status == "active" and steps < 100:
        steps += 1
        out.extend(await combat_service.act(s, char, enc, Action(kind="attack", weapon="main"), rng))
    return enc, out
