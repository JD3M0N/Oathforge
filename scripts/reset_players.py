"""Delete every player and everything they left behind, to start a clean test round.

    .venv\\Scripts\\python scripts\\reset_players.py          # shows what would be deleted
    .venv\\Scripts\\python scripts\\reset_players.py --yes    # deletes it

Keeps the schema and ``media_files`` (Telegram's image cache, not player data).
Ids keep counting up, so new combats never reuse an old ``artifacts/battles`` file.
Stop the bot first: its in-memory state (half-finished character creation) is not in the DB.
"""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from oathforge.config import get_settings
from oathforge.database.models import Base

KEEP = {"media_files"}


async def main(confirm: bool) -> None:
    url = get_settings().database_url
    tables = [t.name for t in Base.metadata.sorted_tables if t.name not in KEEP]
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            print(f"database: {url.split('@')[-1]}")
            for name in tables:
                count = (await conn.execute(text(f'SELECT count(*) FROM "{name}"'))).scalar()
                print(f"  {name:24} {count}")
            if not confirm:
                print("nothing deleted; run again with --yes")
                return
            for name in reversed(tables):  # children first
                await conn.execute(text(f'DELETE FROM "{name}"'))
            print("deleted")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main("--yes" in sys.argv))
