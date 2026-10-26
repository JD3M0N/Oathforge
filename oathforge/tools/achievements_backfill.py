"""Achievement backfill: preview by default, one short transaction per character."""

import argparse
import asyncio
from sqlalchemy import select
from oathforge.database.session import init_engine, dispose_engine, session_scope
from oathforge.database.models import Character
from oathforge.services.achievements import backfill_character


async def run(apply=False, character_id=None, after_id=0):
    init_engine()
    try:
        async with session_scope() as session:
            query = select(Character.id).where(Character.id > after_id).order_by(Character.id)
            if character_id is not None:
                query = query.where(Character.id == character_id)
            ids = list(await session.scalars(query))
        for cid in ids:
            async with session_scope() as session:
                char = await session.scalar(select(Character).where(Character.id == cid).with_for_update())
                if char is None:
                    continue
                granted = await backfill_character(session, char)
                print(f"{cid}: {char.name}: {', '.join(granted) or '-'}")
                if not apply:
                    await session.rollback()
        print("APPLIED" if apply else "PREVIEW: no changes saved. Use --apply to save.")
    finally:
        await dispose_engine()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--character-id", type=int)
    parser.add_argument("--after-id", type=int, default=0)
    args = parser.parse_args(argv)
    asyncio.run(run(args.apply, args.character_id, args.after_id))
