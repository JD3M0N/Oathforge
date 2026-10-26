"""Test DB: TEST_DATABASE_URL (Postgres) when reachable, otherwise a SQLite file.

Concurrency tests that rely on row locks are skipped on SQLite.
"""

import asyncio
from collections import deque

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from oathforge.config import get_settings
from oathforge.database import session as db
from oathforge.database.models import Base

_URL: str | None = None


async def _pick_url(tmp_dir) -> str:
    pg = get_settings().test_database_url
    try:
        engine = create_async_engine(pg)
        async with engine.connect():
            pass
        await engine.dispose()
        return pg
    except Exception:
        return f"sqlite+aiosqlite:///{tmp_dir}/test.db"


@pytest.fixture(scope="session", autouse=True)
def artifacts_dir(tmp_path_factory):
    """Debug artifacts from tests go to a temp dir, never to the repo's artifacts/."""
    settings = get_settings()
    settings.artifacts_dir = tmp_path_factory.mktemp("artifacts")
    settings.game_clock_offset_hours = 0  # a GAME_CLOCK_OFFSET_HOURS in .env (for playtesting) never moves tests
    # the rest of .env must not move the tests either: the suite assumes the defaults
    settings.default_language = "es"
    settings.gemini_model_fallback = ""  # an extra model in the chain changes what the AI client tries
    return settings.artifacts_dir


@pytest.fixture
async def database(tmp_path_factory):
    global _URL
    if _URL is None:
        _URL = await _pick_url(tmp_path_factory.mktemp("db"))
    engine = db.init_engine(_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield _URL
    await db.dispose_engine()


@pytest.fixture
def ruins(monkeypatch):
    """A test-only dungeon (tests/ruins.py): the game has none, the engine still supports one."""
    from tests import ruins as r

    r.install(monkeypatch)
    yield
    r.uninstall()


@pytest.fixture
def is_postgres(database) -> bool:
    return database.startswith("postgresql")


class FakeLLM:
    """Scripted LLM: queue responses per call kind. None simulates a failure/timeout."""

    def __init__(self):
        self.json_queue: deque = deque()
        self.text_queue: deque = deque()
        self.prompts: list[str] = []

    async def json(self, *, tier, system, prompt, schema, user_id):
        self.prompts.append(prompt)
        if not self.json_queue:
            return None
        value = self.json_queue.popleft()
        return schema.model_validate(value) if isinstance(value, dict) else value

    async def text(self, *, tier, system, prompt, user_id):
        self.prompts.append(prompt)
        return self.text_queue.popleft() if self.text_queue else None


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
