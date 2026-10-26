"""Quest actions and the mission chain."""

import random

import pytest

from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.services.events import Outcome
from oathforge.services import characters, inventory, npcs, quests
from tests.services.helpers import get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


# ---------------------------------------------------------------- quest



async def open_rumor(s, char) -> None:
    prog = (await quests.progress(s, char, lock=True))["camp_rumor"]
    prog.stage, prog.state = "active", "active"
    char.location = "broken_crown_tavern"


async def test_a_written_decision_pays_reputation_leaves_a_flag_and_cannot_be_taken_twice():
    _, cid = await new_character()
    rng = random.Random(3)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await open_rumor(s, char)
        out = await quests.perform(s, char, "camp_rumor.check", ["bram"], rng)
        assert out.ok and char.flags["rumor_checked"] and "rumor_believed" not in char.flags
        reps = await npcs.reputations(s, char)
        assert reps["silver_covenant"] >= 5
        prog = (await quests.progress(s, char))["camp_rumor"]
        assert prog.stage == "done" and prog.state == "completed"
        # already done: cannot repeat or take the other branch
        assert not (await quests.perform(s, char, "camp_rumor.believe", ["bram"], rng)).ok
        assert not (await quests.perform(s, char, "camp_rumor.check", ["bram"], rng)).ok


async def test_quest_action_needs_npc_present_and_location():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert not (await quests.perform(s, char, "camp_rumor.check", ["bram"], random.Random(0))).ok  # still locked
        await open_rumor(s, char)
        char.location = "crownreach_plaza"
        assert not (await quests.perform(s, char, "camp_rumor.check", ["bram"], random.Random(0))).ok  # wrong place
        char.location = "broken_crown_tavern"
        assert not (await quests.perform(s, char, "camp_rumor.check", [], random.Random(0))).ok  # Bram is not here
        assert (await quests.perform(s, char, "camp_rumor.believe", ["bram"], random.Random(0))).ok
        assert char.flags.get("rumor_believed")


# ---------------------------------------------------------------- missions

async def test_mission_chain_talk_then_hunt():
    _, cid = await new_character()
    rng = random.Random(1)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_talk(s, char, "vale", rng)
        assert (await quests.progress(s, char))["tut_muster"].state == "active"  # still has to read the rulebook
        await quests.on_read(s, char, "dice", rng)  # another page does not count
        assert (await quests.progress(s, char))["tut_muster"].state == "active"
        out = await quests.on_read(s, char, "activities", rng)
        prog = await quests.progress(s, char)
        assert prog["tut_muster"].state == "completed" and prog["tut_town"].state == "active"
        assert char.xp == 25 and any(e.key == "quest.new" for e in out.events)
        assert await inventory.count(s, char, "skinning_knife") == 1
        assert not (await quests.on_talk(s, char, "vale", rng)).events  # nothing left to count

        await quests.on_talk(s, char, "bram", rng)
        assert (await quests.progress(s, char))["tut_town"].state == "active"  # still has to see the workshops
        await quests.on_visit(s, char, "crownreach_workshops", rng)
        assert (await quests.progress(s, char))["tut_town"].state == "active"  # and the tavern
        await quests.on_visit(s, char, "broken_crown_tavern", rng)
        prog = await quests.progress(s, char)
        assert prog["tut_town"].state == "completed" and prog["tut_market"].state == "active"

        await quests.on_talk(s, char, "mira", rng)
        await quests.on_talk(s, char, "tessa", rng)
        prog = await quests.progress(s, char)
        assert prog["tut_market"].state == "completed" and prog["tut_boars"].state == "active"

        await quests.on_defeat(s, char, "boar", rng)  # a kill alone is not a hunt
        assert (await quests.progress(s, char))["tut_boars"].counters == {}
        out = await quests.advance(s, char, "hunt", "tusk_meadow", rng)
        assert any(e.key == "quest.progress" and e.params["n"] == 1 for e in out.events)
        await quests.advance(s, char, "hunt", "ironvein_mine", rng)  # elsewhere does not count
        await quests.advance(s, char, "hunt", "tusk_meadow", rng)
        assert (await quests.progress(s, char))["tut_boars"].state == "active"  # the meat is missing
        await quests.on_items(s, char, "skin", {"boar_hide": 1, "raw_meat": 2}, rng)
        prog = await quests.progress(s, char)
        assert prog["tut_boars"].state == "completed" and prog["tut_herbs"].state == "active"
        assert char.xp == 25 + 25 + 25 + 100  # the fights' XP comes from the fight, not from here
        assert await inventory.count(s, char, "sickle") == 1
        assert prog["camp_order"].state == "locked"


async def test_mission_unlocks_by_flag_and_counts_only_when_active(monkeypatch):
    from oathforge.content.schemas import Quest
    monkeypatch.setitem(get_content().quests, "flagged", Quest.model_validate({
        "order": 99, "giver": "bram", "name": {"es": "Con bandera", "en": "Flagged"}, "summary": {"es": "-", "en": "-"},
        "start_stage": "locked", "unlock_stage": "active", "unlock_flag": "test_flag", "objective_stage": "active",
        "complete_stage": "done", "rewards": [{"xp": 10}], "objectives": [{"kind": "kill", "target": "bandit", "count": 3}],
        "stages": {"locked": {"state": "locked", "journal": {"es": "-", "en": "-"}},
                   "active": {"journal": {"es": "-", "en": "-"}},
                   "done": {"state": "completed", "journal": {"es": "-", "en": "-"}}}}))
    _, cid = await new_character()
    rng = random.Random(1)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.on_defeat(s, char, "bandit", rng)  # still locked: no count
        assert (await quests.progress(s, char))["flagged"].counters == {}
        char.flags = {**char.flags, "test_flag": True}
        await quests.refresh(s, char, Outcome())
        assert (await quests.progress(s, char))["flagged"].state == "active"
        for _ in range(3):
            await quests.on_defeat(s, char, "bandit", rng)
        assert (await quests.progress(s, char))["flagged"].state == "completed"


@pytest.mark.usefixtures("ruins")
async def test_the_whole_chain_from_the_muster_to_the_first_act():
    """With the table of twenty levels the old chain goes a little past five; no gate stops it,
    because the gates of roadmap_balance only start at nine."""
    _, cid = await new_character()
    rng = random.Random(5)

    async def fight(char, monster, hunt_at=None):
        characters.grant_xp(char, get_content().monsters[monster].xp, Outcome())
        await quests.on_defeat(s, char, monster, rng)
        if hunt_at:
            await quests.advance(s, char, "hunt", hunt_at, rng)

    async with session_scope() as s:
        char = await get_char(s, cid)
        # the tutorial: talk, city, market, hunt and skin, gather, cook, mine, hunt, heal and rest, a boss
        await quests.on_talk(s, char, "vale", rng)
        await quests.on_read(s, char, "activities", rng)
        await quests.on_talk(s, char, "bram", rng)
        await quests.on_visit(s, char, "crownreach_workshops", rng)
        await quests.on_visit(s, char, "broken_crown_tavern", rng)
        await quests.on_talk(s, char, "mira", rng)
        await quests.on_talk(s, char, "tessa", rng)
        for _ in range(2):
            await fight(char, "boar", "tusk_meadow")
        await quests.on_items(s, char, "skin", {"raw_meat": 2}, rng)
        await quests.on_items(s, char, "gather", {"bloodroot": 3}, rng)
        await quests.on_items(s, char, "craft", {"hunter_stew": 1}, rng)
        assert await inventory.count(s, char, "pickaxe") == 1
        await quests.on_items(s, char, "gather", {"iron_ore": 2, "coal": 1}, rng)
        await quests.on_items(s, char, "gather", {"iron_ore": 1}, rng)
        assert await inventory.count(s, char, "woodaxe") == 1  # the room mission needs wood
        await quests.on_items(s, char, "craft", {"furniture:chest": 1}, rng)
        await quests.on_items(s, char, "craft", {"furniture:bed": 1}, rng)
        for monster in ("cave_bat", "giant_rat", "cave_bat"):
            await fight(char, monster, "ironvein_mine")
        await quests.on_talk(s, char, "ysolde", rng)
        await quests.advance(s, char, "rest", "broken_crown_tavern", rng)
        await quests.on_talk(s, char, "vale", rng)
        prog = await quests.progress(s, char)
        assert prog["old_tusk"].state == "active" and char.flags.get("old_tusk_hunt")
        assert prog["camp_order"].state == "active"  # the campaign opened with the last lesson; Old Tusk is optional
        await fight(char, "old_tusk")
        prog = await quests.progress(s, char)
        assert prog["old_tusk"].state == "ready"  # beating it is not getting paid: Bram owes you
        gold, xp = char.gold, char.xp
        assert not (await quests.turn_in(s, char, "old_tusk", [], rng)).ok  # Bram is not here
        assert (char.gold, char.xp) == (gold, xp)
        char.location = "broken_crown_tavern"
        assert (await quests.turn_in(s, char, "old_tusk", ["bram"], rng)).ok
        assert (char.gold, char.xp) == (gold, xp + 300)
        again = await quests.turn_in(s, char, "old_tusk", ["bram"], rng)  # the service pays once
        assert not again.ok and (char.gold, char.xp) == (gold, xp + 300)
        prog = await quests.progress(s, char)
        assert all(prog[k].state == "completed" for k, q in get_content().quests.items() if q.tutorial)
        assert prog["camp_order"].state == "active" and char.level >= 3  # the first act opens
        # Act I: Tamsin, two bandits, a leather armor; then the gear lesson opens
        await quests.on_talk(s, char, "tamsin", rng)
        for _ in range(2):
            await fight(char, "bandit")
        prog = await quests.progress(s, char)
        assert prog["camp_order"].state == "completed" and prog["camp_gear"].state == "active"
        assert await inventory.count(s, char, "leather_armor") >= 1
        assert characters.eligible_level(char) == char.level  # nothing gates it below nine


async def test_ensure_progress_adds_missions_to_old_characters():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for p in (await quests.progress(s, char)).values():
            if p.quest_key != "camp_collector":
                await s.delete(p)
    async with session_scope() as s:
        char = await get_char(s, cid)
        journal = await quests.journal(s, char)
        assert [k for k, _, p in journal if p is None] == [
            k for k, _ in quests.ordered_quests() if k != "camp_collector"]
        await quests.refresh(s, char, Outcome())
        prog = await quests.progress(s, char)
        assert set(prog) == set(get_content().quests) and prog["tut_muster"].state == "active"


async def test_veterans_of_the_old_chain_skip_the_tutorial():
    """A character who finished the old first missions (night_wings) gets the tutorial already done."""
    from oathforge.database.models import QuestProgress

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for p in (await quests.progress(s, char)).values():
            if p.quest_key.startswith("tut_"):
                await s.delete(p)
        s.add(QuestProgress(character_id=cid, quest_key="night_wings", stage="done", state="completed", counters={}))
    async with session_scope() as s:
        char = await get_char(s, cid)
        xp = char.xp
        await quests.refresh(s, char, Outcome())
        prog = await quests.progress(s, char)
        assert all(prog[k].state == "completed" for k in prog if k.startswith("tut_"))
        assert prog["old_tusk"].state == "active" and char.xp == xp  # the last test opens, and no rewards paid
        assert await quests.location_texts(s, char) is not None  # the old row is ignored, not an error
