"""Hunting tables, the bestiary, prices and level gates."""

import random

import pytest

from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine.combat import EncounterState
from oathforge.services import combat_service, exploration, inventory, quests
from tests.services.helpers import fight, get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


# ---------------------------------------------------------------- hunting and bestiary


@pytest.mark.parametrize("night", [False, True])
async def test_the_meadow_has_boars_day_and_night(monkeypatch, night):
    """«Tusks in the Meadow» does not depend on the hour either."""
    monkeypatch.setattr(exploration, "is_night", lambda now=None: night)
    loc = get_content().locations["tusk_meadow"]
    assert any("boar" in e.monsters for e in exploration.encounter_table(loc, 1))


async def test_a_single_objective_says_what_comes_next():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await quests.on_talk(s, char, "vale", random.Random(0))
        nxt = [e for e in out.events if e.key == "quest.next"]
        assert nxt and "rulebook" in nxt[0].params["step"]["en"]


async def test_a_quest_giver_repeats_the_hint_when_the_ai_is_down(llm):
    from oathforge.services import actions

    user_id, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "adventurers_guild"  # Vale signs up recruits at the guild hall
    line, _ = await actions.talk(llm, user_id, "vale", "¿Y ahora qué?")  # the fake LLM answers nothing
    assert "te recuerda lo que toca" in line and "/rulebook" in line


@pytest.mark.parametrize("night", [False, True])
async def test_the_mine_has_bats_day_and_night(monkeypatch, night):
    """The tutorial's bat hunt («Alas al anochecer») does not depend on the hour."""
    monkeypatch.setattr(exploration, "is_night", lambda now=None: night)
    loc = get_content().locations["ironvein_mine"]
    assert any("cave_bat" in e.monsters for e in exploration.encounter_table(loc, 1))


@pytest.mark.parametrize("night,expected", [(False, {"boar"}), (True, {"cave_bat"})])
async def test_hunt_uses_the_day_or_night_table(monkeypatch, night, expected):
    monkeypatch.setattr(exploration, "is_night", lambda now=None: night)
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "tusk_meadow"
        out = await exploration.hunt(s, char, random.Random(0))
        assert out.ok and char.state == "in_combat"
        enc = await combat_service.active_encounter(s, char)
        refs = {c["ref"] for c in enc.state["combatants"].values() if c["side"] == "enemy"}
        assert refs == expected
        assert set(char.bestiary) == expected


async def test_hunt_only_where_there_is_prey_and_boss_first():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await exploration.hunt(s, char, random.Random(0))).error == "explore.err.no_hunting"
        char.location, char.flags = "tusk_meadow", {"old_tusk_hunt": True}
        out = await exploration.hunt(s, char, random.Random(0))
        assert out.events[0].key == "explore.hunt_boss"
        enc = await combat_service.active_encounter(s, char)
        assert enc.fixed_flag == "cleared_old_tusk"


async def test_bestiary_records_seen_and_killed():
    from oathforge.services import bestiary

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = char.max_hp = 200
        assert bestiary.tier(char.bestiary.get("grey_wolf")) == 0
        await fight(s, char, ["grey_wolf", "grey_wolf"])
        assert char.bestiary["grey_wolf"] == {"seen": 1, "killed": 2}
        assert bestiary.tier(char.bestiary["grey_wolf"]) == 2
        await fight(s, char, ["grey_wolf"], seed=1)
        assert bestiary.tier(char.bestiary["grey_wolf"]) == 3
        assert [k for k, _ in bestiary.known(char)] == ["grey_wolf"]


def test_anything_worth_a_coin_sells_for_at_least_one():
    assert inventory.sell_price("torch", 0) == 1
    assert inventory.sell_price("longsword", 0) == 8


async def test_two_enemies_of_the_same_kind_get_letters():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        enc, _ = await combat_service.start_encounter(s, char, ["boar", "boar", "cave_bat"], random.Random(0))
        names = {c.name["es"] for k, c in EncounterState.model_validate(enc.state).combatants.items() if k != "p1"}
        assert names == {"Jabalí A", "Jabalí B", "Murciélago de cueva"}


async def test_tutorial_runs_time_each_mission():
    from datetime import datetime, timedelta, timezone

    from oathforge.services import admin

    _, cid = await new_character()
    rng = random.Random(0)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_talk(s, char, "vale", rng)
        await quests.on_read(s, char, "activities", rng)
    async with session_scope() as s:
        runs = await admin.tutorial_runs(s, now=datetime.now(timezone.utc) + timedelta(minutes=30))
        run = next(r for r in runs if r.name == "Aldric")
        assert list(run.minutes) == ["tut_muster"] and run.current == "tut_town" and not run.done
        assert 29 < run.waiting < 31  # stuck on the second mission for half an hour


def test_packs_of_two_wait_for_level_two(monkeypatch):
    """Level 1 fights one boar at a time (tutorial); pairs come from level 2."""
    monkeypatch.setattr(exploration, "is_night", lambda now=None: False)
    loc = get_content().locations["tusk_meadow"]
    assert all(len(e.monsters) == 1 for e in exploration.encounter_table(loc, 1))
    assert any(len(e.monsters) == 2 for e in exploration.encounter_table(loc, 2))
