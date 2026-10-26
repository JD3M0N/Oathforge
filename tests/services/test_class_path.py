"""The class path: the branch at level 10, the trainings (5, 12, 18) and the modifiers (13, 17).

Every branch in the shipped content is still 'not ready' (B07 writes their 10-20 paths), so the tests
borrow a small finished one for the length of a test. The rules under test are roadmap_balance §4.4,
§13.1 and §15.4: a choice is final, it recharges nothing, and it applies the same in every view.
"""

import asyncio

import pytest
from sqlalchemy import select

from oathforge.content import get_content
from oathforge.content.schemas import AbilityPatch, ClassAbility, ClassSpecialization, Modifier, Text
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.engine import class_build
from oathforge.services import characters, combat_service
from oathforge.services import class_specializations as paths
from oathforge.services.events import Outcome

pytestmark = pytest.mark.usefixtures("database")

BRANCH = "test_oath"


def text(s: str) -> Text:
    return Text(es=s, en=s)


def ability(level: int, kind: str = "strike", **kw) -> ClassAbility:
    return ClassAbility(name=text("x"), description=text("x"), level=level, kind=kind, **kw)


def finished_branch(**over) -> ClassSpecialization:
    """A complete 10-20 path for the warrior: a passive and a technique at 10, two modifiers at 13 and 17
    (one tunes an ability, one grants a new one) and a culminating technique at 20."""
    data = dict(
        class_key="warrior",
        name=text("Test Oath"),
        description=text("x"),
        roles=["dmg"],
        ready=True,
        abilities={
            "test_hide": ability(10, "passive", action="none", ac_bonus=1),
            "test_strike": ability(10, "strike", extra_damage="1d6", damage_type="slashing", cost=2),
            "test_finale": ability(20, "strike", extra_damage="3d6", damage_type="slashing", cost=4),
        },
        modifiers={
            "swift": Modifier(
                level=13,
                name=text("Swift"),
                description=text("cheaper"),
                patches={"second_wind": AbilityPatch(cost=-1)},
            ),
            "wide": Modifier(
                level=13,
                name=text("Wide"),
                description=text("wider"),
                patches={"test_strike": AbilityPatch(cooldown=2)},
            ),
            "sharp": Modifier(
                level=17,
                name=text("Sharp"),
                description=text("new"),
                grants={"test_extra": ability(17, "strike", extra_damage="1d4", damage_type="slashing", cost=1)},
            ),
            "calm": Modifier(level=17, name=text("Calm"), description=text("calm")),
        },
    )
    data.update(over)
    return ClassSpecialization(**data)


@pytest.fixture
def branch():
    content = get_content()
    content.class_specializations[BRANCH] = finished_branch()
    yield content.class_specializations[BRANCH]
    content.class_specializations.pop(BRANCH, None)


async def hero(level: int = 10, location: str = "adventurers_guild") -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "warrior")
        char.xp = get_content().progression.xp[level - 1]
        char.build = {**characters.build_of(char), characters.MILESTONES: ["ash_collector", "iron_stag"]}
        characters.apply_levels(char, Outcome())
        char.location = location
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


def guild() -> str:
    return next(k for k, loc in get_content().locations.items() if loc.home)


# ------------------------------------------------------------- the branch


async def test_the_branch_is_chosen_at_ten_in_the_guild_and_changes_the_catalogue(branch):
    cid = await hero(10, guild())
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert "test_strike" not in characters.abilities_of(char)
        out = await paths.choose_branch(s, char, BRANCH)
        assert out.ok and char.specialization == BRANCH
        built = characters.abilities_of(char)
        assert {"test_hide", "test_strike"} <= set(built) and "test_finale" not in built  # level 20 comes later
        assert "test_strike" in char.resources and "test_hide" not in char.resources  # a passive has no uses
        assert "test_strike" in combat_service.ability_defs(char)  # the engine sees the same catalogue


async def test_the_branch_refuses_everything_that_is_not_allowed(branch):
    low = await hero(9, guild())
    async with session_scope() as s:
        char = await get_char(s, low)
        assert (await paths.choose_branch(s, char, BRANCH)).error == "path.err.level"
        assert char.specialization is None
    async with session_scope() as s:
        await s.execute(Character.__table__.delete())
    away = await hero(10, "crownreach_plaza")
    async with session_scope() as s:
        char = await get_char(s, away)
        assert (await paths.choose_branch(s, char, BRANCH)).error == "path.err.not_guild"
        char.location = guild()
        assert (await paths.choose_branch(s, char, "pyromancer")).error == "path.err.unknown"  # another class
        get_content().class_specializations["t_unfinished"] = finished_branch(ready=False)
        try:
            assert (await paths.choose_branch(s, char, "t_unfinished")).error == "path.err.not_ready"
        finally:
            get_content().class_specializations.pop("t_unfinished", None)
        assert (await paths.choose_branch(s, char, "no_such")).error == "path.err.unknown"
        assert char.specialization is None


async def test_the_choice_is_final(branch):
    cid = await hero(10, guild())
    content = get_content()
    content.class_specializations["other"] = finished_branch(name=text("Other"))
    try:
        async with session_scope() as s:
            char = await get_char(s, cid)
            assert (await paths.choose_branch(s, char, BRANCH)).ok
            again = await paths.choose_branch(s, char, "other")
            assert again.error == "path.err.already" and char.specialization == BRANCH
    finally:
        content.class_specializations.pop("other", None)


async def test_choosing_a_branch_recharges_nothing(branch):
    cid = await hero(10, guild())
    async with session_scope() as s:
        char = await get_char(s, cid)
        characters.set_pool(char, 1)  # a Focus bar nearly empty
        before_hp = char.hp = max(1, char.max_hp // 2)
        await paths.choose_branch(s, char, BRANCH)
        assert characters.pool_of(char) == 1 and char.hp == before_hp


# ----------------------------------------------------------- trainings


async def test_the_training_of_level_five_is_offered_and_applied():
    cid = await hero(5)
    prog = get_content().progression
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert [c.key for c in paths.pending(char)] == ["training:5"]
        top, hp, dc0 = characters.resource_max(char), char.max_hp, characters.spell_stats(char)[2]
        assert (await paths.choose_option(s, char, "training:5", "hardy")).ok
        effects = prog.trainings["hardy"].effects
        assert char.max_hp == hp + effects.max_hp and characters.resource_max(char) == top + effects.resource_max
        assert paths.pending(char) == ()
        # the offensive package moves the attack and the DC instead
        char2 = char
        char2.build = {**characters.build_of(char2), characters.CHOICES: {"training:5": "keen"}}
        assert characters.spell_stats(char2)[2] == dc0 + prog.trainings["keen"].effects.spell_dc


async def test_a_training_gives_real_hit_points_now_and_does_not_heal_the_rest():
    cid = await hero(5)
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = 3
        await paths.choose_option(s, char, "training:5", "hardy")
        assert char.hp == 3 + get_content().progression.trainings["hardy"].effects.max_hp  # only the new ones


async def test_a_training_cannot_be_taken_twice_or_before_its_level():
    cid = await hero(5)
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await paths.choose_option(s, char, "training:12", "keen")).error == "path.err.no_choice"
        assert (await paths.choose_option(s, char, "training:5", "made_up")).error == "path.err.unknown"
        assert (await paths.choose_option(s, char, "training:5", "keen")).ok
        again = await paths.choose_option(s, char, "training:5", "hardy")
        assert again.error == "path.err.no_choice"
        assert characters.taken_of(char) == {"training:5": "keen"}


async def test_choices_queue_up_when_levels_are_skipped():
    cid = await hero(13)
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert [c.key for c in paths.pending(char)] == ["training:5", "training:12"]  # no branch: no modifier yet


async def test_levelling_up_keeps_the_training_hit_points():
    cid = await hero(5)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await paths.choose_option(s, char, "training:5", "hardy")
        char.xp = get_content().progression.xp[7]
        characters.apply_levels(char, Outcome())
        assert char.max_hp == characters.max_hp_for(char) and char.level == 8
        assert char.max_hp >= get_content().progression.trainings["hardy"].effects.max_hp


# ----------------------------------------------------------- modifiers


async def test_a_modifier_tunes_an_ability_and_a_second_one_grants_a_new_one(branch):
    cid = await hero(17, guild())
    async with session_scope() as s:
        char = await get_char(s, cid)
        await paths.choose_branch(s, char, BRANCH)
        base = characters.abilities_of(char)["second_wind"].cost
        assert (await paths.choose_option(s, char, "modifier:13", "swift")).ok
        assert characters.abilities_of(char)["second_wind"].cost == base - 1
        assert (await paths.choose_option(s, char, "modifier:17", "sharp")).ok
        built = characters.abilities_of(char)
        assert "test_extra" in built and "test_extra" in char.resources
        # the other option of each level was never applied
        assert built["test_strike"].cooldown == 0


async def test_a_modifier_of_another_level_or_branch_is_refused(branch):
    cid = await hero(13, guild())
    async with session_scope() as s:
        char = await get_char(s, cid)
        await paths.choose_branch(s, char, BRANCH)
        assert (await paths.choose_option(s, char, "modifier:13", "sharp")).error == "path.err.unknown"  # level 17's
        assert (await paths.choose_option(s, char, "modifier:17", "sharp")).error == "path.err.no_choice"  # not yet


async def test_two_taps_on_the_same_choice_apply_it_once(branch):
    cid = await hero(13, guild())
    async with session_scope() as s:
        char = await get_char(s, cid)
        await paths.choose_branch(s, char, BRANCH)
        assert (await paths.choose_option(s, char, "modifier:13", "swift")).ok
        assert (await paths.choose_option(s, char, "modifier:13", "swift")).error == "path.err.no_choice"
    async with session_scope() as s:  # and it is the same after a reload
        char = await get_char(s, cid)
        assert characters.taken_of(char)["modifier:13"] == "swift"
        assert (
            characters.abilities_of(char)["second_wind"].cost
            == get_content().classes["warrior"].abilities["second_wind"].cost - 1
        )


# --------------------------------------------------- every view, one catalogue


async def test_sheet_engine_and_rest_see_the_same_abilities(branch):
    cid = await hero(13, guild())
    async with session_scope() as s:
        char = await get_char(s, cid)
        await paths.choose_branch(s, char, BRANCH)
        await paths.choose_option(s, char, "modifier:13", "wide")
        from oathforge.bot import render
        from oathforge.i18n import t

        engine = set(combat_service.ability_defs(char))
        assert engine == set(characters.abilities_of(char))
        assert "test_strike" in engine
        unknown = t("es", "skill.unknown")
        for key in engine:  # the /skill_<key> page knows every one of them, branch abilities included
            assert not render.skill_page(key, "es", char)[0].startswith(unknown), key
        summary, _ = await render.hero(s, char, "es")
        assert summary  # and the summary sheet still renders with the branch
        char.resources = {}
        characters.refill_resources(char)  # a rest
        assert set(char.resources) == {k for k, a in characters.abilities_of(char).items() if a.kind != "passive"}


# ------------------------------------------------------------- the reroll


async def test_a_substantial_change_gives_one_free_second_choice(branch):
    cid = await hero(13, guild())
    content = get_content()
    content.class_specializations["other"] = finished_branch(name=text("Other"))
    try:
        async with session_scope() as s:
            char = await get_char(s, cid)
            await paths.choose_branch(s, char, BRANCH)
            await paths.choose_option(s, char, "training:5", "keen")
            await paths.choose_option(s, char, "modifier:13", "swift")
            assert not paths.reroll_available(char)
            assert (await paths.reroll_branch(s, char, "other")).error == "path.err.no_reroll"
            content.class_specializations[BRANCH] = finished_branch(revision=2)  # the branch was reworked
            assert paths.reroll_available(char)
            assert (await paths.reroll_branch(s, char, "other")).ok
            assert char.specialization == "other"
            taken = characters.taken_of(char)
            assert "training:5" in taken and "modifier:13" not in taken  # the training stays, the modifier goes
            assert not paths.reroll_available(char)  # once
            assert (await paths.reroll_branch(s, char, BRANCH)).error == "path.err.no_reroll"
    finally:
        content.class_specializations.pop("other", None)


async def test_two_choices_at_once_leave_one_applied(branch, is_postgres):
    if not is_postgres:
        pytest.skip("row locks only exist on PostgreSQL")
    cid = await hero(13, guild())
    async with session_scope() as s:
        await paths.choose_branch(s, await get_char(s, cid), BRANCH)

    async def pick(option):
        async with session_scope() as s:
            return (await paths.choose_option(s, await get_char(s, cid), "modifier:13", option)).ok

    results = await asyncio.gather(pick("swift"), pick("wide"))
    assert sorted(results) == [False, True]
    async with session_scope() as s:
        assert characters.taken_of(await get_char(s, cid))["modifier:13"] in ("swift", "wide")


# --------------------------------------------------------- pure catalogue


def test_a_patch_never_makes_a_cost_negative_or_a_duration_zero():
    base = ability(1, "buff", status="blessed", status_turns=1, cost=1, cooldown=1)
    patched = class_build._patched(base, AbilityPatch(cost=-5, cooldown=-5, status_turns=-5))
    assert (patched.cost, patched.cooldown, patched.status_turns) == (0, 0, 1)
