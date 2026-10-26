"""The launch reset and its backup (B13): wipe the game, keep the people, and be able to go back."""

import datetime as dt
import json

import pytest
from sqlalchemy import func, select

from oathforge.database.models import ActionLog, AiUsage, Character, ItemInstance, MediaFile, User, WorldFact
from oathforge.database.session import session_scope
from oathforge.services import characters, inventory, launch, quests

pytestmark = pytest.mark.usefixtures("database")


async def populate():
    """Two accounts with heroes, a rumour, quota counters, an audit line and a cached picture."""
    async with session_scope() as s:
        for tg, name in ((1, "Aldric"), (2, "Brenna")):
            user = await characters.get_or_create_user(s, tg, "en")
            characters.set_setting(user, "manual_rolls", tg == 1)
            characters.set_setting(user, "keyboard", {"sent": True, "character": tg})
            char = await characters.create_character(s, user, name, "human", "soldier", "paladin")
            await inventory.add_item(s, char, "pickaxe")
            await quests.ensure_progress(s, char)
            s.add(ActionLog(user_id=user.id, character_id=char.id, verb="combat", payload={"n": tg}))
            s.add(AiUsage(user_id=user.id, day=dt.date(2026, 10, 25), model="m", calls=tg * 10))
        s.add(WorldFact(key="rumor:1", value={"es": "x"}, tags=[], source="character:1"))
        s.add(MediaFile(bot_id=1, asset_key="k", checksum="c" * 64, file_id="f", file_unique_id="u"))
        await s.flush()


async def snapshot(s):
    return await launch.counts(s)


async def test_a_dry_run_changes_nothing_and_names_what_goes_and_what_stays():
    await populate()
    async with session_scope() as s:
        before = await snapshot(s)
        report = await launch.reset_for_launch(s, apply=False)
        assert not report.applied and report.before == before
        assert report.wiped["characters"] == 2 and "users" not in report.wiped
        assert set(report.kept) == set(launch.KEEP_TABLES)
        assert await snapshot(s) == before


async def test_the_reset_wipes_the_game_and_keeps_accounts_quota_and_audit():
    await populate()
    async with session_scope() as s:
        report = await launch.reset_for_launch(s, apply=True)
        assert report.applied and report.orphans == []
        after = report.after
        assert after["characters"] == after["item_instances"] == after["quest_progress"] == after["world_facts"] == 0
        assert (
            after["users"] == 2 and after["ai_usage"] == 2 and after["media_files"] == 1 and after["action_logs"] == 2
        )
        users = (await s.scalars(select(User).order_by(User.telegram_id))).all()
        assert [u.language for u in users] == ["en", "en"]
        assert users[0].settings == {"manual_rolls": True} and users[1].settings == {"manual_rolls": False}
        assert report.settings_trimmed == 2
        assert all(row.character_id is None for row in (await s.scalars(select(ActionLog))).all())
        assert sum((await s.scalars(select(AiUsage.calls))).all()) == 30  # the daily budget is not reset


async def test_an_account_can_start_again_after_the_reset():
    await populate()
    async with session_scope() as s:
        await launch.reset_for_launch(s, apply=True)
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "en")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        assert char.level == 1 and char.location == "crownreach_plaza"
        assert (await s.scalar(select(func.count()).select_from(User))) == 2


async def test_a_backup_restores_the_database_exactly_after_the_reset():
    await populate()
    async with session_scope() as s:
        before = await snapshot(s)
        data = json.loads(launch.to_json(await launch.dump(s)))  # through real JSON, as on disk
        sample = (await s.scalars(select(Character).order_by(Character.id))).first()
        started = sample.created_at if hasattr(sample, "created_at") else None
        await launch.reset_for_launch(s, apply=True)
        assert (await snapshot(s))["characters"] == 0
        restored = await launch.restore(s, data)
        assert await snapshot(s) == before == restored
        again = (await s.scalars(select(Character).order_by(Character.id))).first()
        assert again.name == sample.name and again.flags == sample.flags
        if started is not None:
            assert again.created_at == started
        assert await s.scalar(select(func.count()).select_from(ItemInstance)) == before["item_instances"] > 2


async def test_a_backup_from_another_version_is_refused_without_touching_anything():
    await populate()
    async with session_scope() as s:
        before = await snapshot(s)
        with pytest.raises(ValueError):
            await launch.restore(s, {"format": 2, "tables": {}})
        with pytest.raises(ValueError):
            await launch.restore(s, {"format": 1, "tables": {"ghost_table": []}})
        assert await snapshot(s) == before
