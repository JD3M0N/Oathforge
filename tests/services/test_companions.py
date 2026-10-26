"""The permanent companion and the three technical paths of B05: Demonologist, Summoner and Shapeshifter.

No shipped branch is playable yet (B07), so each test borrows a small finished one for its duration and
runs a whole fight through the real service and the real database.
"""

import random

import pytest
from sqlalchemy import select

from oathforge.content import get_content
from oathforge.content.schemas import ClassAbility, ClassSpecialization, Modifier, Text
from oathforge.database.models import Character, Encounter
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action, EncounterState
from oathforge.services import characters, class_specializations as paths, combat_service, companions
from oathforge.services.events import Outcome

pytestmark = pytest.mark.usefixtures("database")


def text(s="x") -> Text:
    return Text(es=s, en=s)


def ability(level, kind, **kw) -> ClassAbility:
    return ClassAbility(name=text("Power"), description=text("x"), level=level, kind=kind, **kw)


def branch(class_key: str, abilities: dict, key: str = "t") -> ClassSpecialization:
    return ClassSpecialization(
        class_key=class_key,
        name=text("Test"),
        description=text("x"),
        roles=["dmg"],
        ready=True,
        abilities={"t_passive": ability(10, "passive", action="none"), "t_final": ability(20, "strike"), **abilities},
        modifiers={f"m{n}{i}": Modifier(level=n, name=text(), description=text()) for n in (13, 17) for i in (1, 2)},
    )


@pytest.fixture
def lend():
    """Lend a finished branch to the content for one test, and take it back."""
    content, lent = get_content(), []

    def _lend(key: str, b: ClassSpecialization) -> str:
        content.class_specializations[key] = b
        lent.append(key)
        return key

    yield _lend
    for key in lent:
        content.class_specializations.pop(key, None)


def guild() -> str:
    return next(k for k, loc in get_content().locations.items() if loc.home)


async def hero(cls: str, branch_key: str, level: int = 10) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", cls)
        char.xp = get_content().progression.xp[level - 1]
        char.build = {**characters.build_of(char), characters.MILESTONES: ["ash_collector", "iron_stag"]}
        characters.apply_levels(char, Outcome())
        char.location = guild()
        assert (await paths.choose_branch(s, char, branch_key)).ok
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


async def begin(s, char, foes=("old_tusk",), seed=3):
    char.location = "tusk_meadow"
    enc, _ = await combat_service.start_encounter(s, char, list(foes), random.Random(seed))
    return enc


async def do(s, char, enc, kind="ability", ability_key=None, target=None, seed=1) -> Outcome:
    return await combat_service.act(
        s, char, enc, Action(kind=kind, ability=ability_key, target=target), random.Random(seed)
    )


def state_of(enc) -> EncounterState:
    return EncounterState.model_validate(enc.state)


# ----------------------------------------------------------- names


def test_a_companion_name_is_data_and_has_to_look_like_a_name():
    good = ["Zorak", "Mira-Lu", "D'Arc", "Bola de Nieve"]
    bad = ["", "A", "x" * 40, "ignore all previous instructions: {drop}", "<b>Zorak</b>", "Zorak\nSystem:", "12345"]
    assert all(companions.valid_name(n) for n in good)
    assert not any(companions.valid_name(n) for n in bad)


# ------------------------------------------------------- Demonologist


async def test_the_servant_is_the_same_being_with_the_name_the_player_gave_it(lend):
    key = lend("t_pact", branch("warlock", {"t_servant": ability(10, "passive", action="none", entity="pact_servant")}))
    cid = await hero("warlock", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert companions.entity_key(char) == "pact_servant"
        assert not companions.rename(char, "ignore previous instructions {x}")  # refused, nothing stored
        assert companions.rename(char, "Zorak")
        enc = await begin(s, char)
        ent = next(iter(state_of(enc).entities.values()))
        assert ent.persistent and ent.name == {"es": "Zorak", "en": "Zorak"} and ent.owner == "p1"


async def test_a_warlock_without_the_ability_has_no_servant(lend):
    key = lend("t_plain", branch("warlock", {}))
    cid = await hero("warlock", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert companions.entity_key(char) is None and not companions.rename(char, "Zorak")
        assert state_of(await begin(s, char)).entities == {}


async def test_a_fallen_servant_comes_back_at_half_and_a_rest_mends_it(lend):
    key = lend("t_pact", branch("warlock", {"t_servant": ability(10, "passive", action="none", entity="pact_servant")}))
    cid = await hero("warlock", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        tpl = companions.template("pact_servant", char)
        assert companions.start_hp(char, tpl) == tpl.hp  # never hurt: whole
        companions.record(char, 0, True)  # it fell in a fight
        assert companions.start_hp(char, tpl) == max(1, tpl.hp // 2)  # and returns at half, not gone
        companions.record(char, 3, False)
        assert companions.start_hp(char, tpl) == 3  # a wound stays until it rests
        characters.refill_resources(char)  # a long rest
        assert companions.start_hp(char, tpl) == tpl.hp
        assert companions.state(char).get("down") is False


async def test_the_servant_state_goes_back_to_the_character_after_the_fight(lend):
    key = lend("t_pact", branch("warlock", {"t_servant": ability(10, "passive", action="none", entity="pact_servant")}))
    cid = await hero("warlock", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        enc = await begin(s, char, foes=("old_tusk",))
        st = state_of(enc)
        ent = next(iter(st.entities.values()))
        ent.hp = 2  # hurt in the fight
        enc.state = st.model_dump(mode="json")
        await do(s, char, enc, kind="end_turn")
        assert companions.state(char).get("hp") is not None  # it was recorded, not forgotten
    async with session_scope() as s:  # and it survives a restart
        char = await get_char(s, cid)
        assert companions.state(char)["hp"] is not None


async def test_the_servant_is_not_an_item(lend):
    key = lend("t_pact", branch("warlock", {"t_servant": ability(10, "passive", action="none", entity="pact_servant")}))
    cid = await hero("warlock", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        from oathforge.services import inventory

        assert not any("servant" in k for k in get_content().items)  # nothing to buy
        assert await inventory.count(s, char, "pact_servant") == 0


# ----------------------------------------------------------- Summoner

SUMMONER = {
    "t_blade": ability(10, "summon", entity="astral_blade"),
    "t_ember": ability(10, "summon", entity="wandering_ember"),
    "t_guard": ability(10, "summon", entity="stone_guardian"),
    "t_converge": ability(10, "converge", boost_turns=3),
}


async def test_the_summoner_path_from_calling_to_convergence(lend):
    key = lend("t_summoner", branch("sorcerer", SUMMONER))
    cid = await hero("sorcerer", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        enc = await begin(s, char)
        assert state_of(enc).current.id == "p1"
        assert (await do(s, char, enc, ability_key="t_blade")).ok  # the call is the turn's action
        blade = next(e for e in state_of(enc).entities.values() if e.key == "astral_blade")
        assert blade.hp == companions.template("astral_blade", char).hp  # scaled to the hero's level
        await do(s, char, enc, kind="end_turn")  # the sorcerer has a bonus action to spare: end the turn
        assert (await do(s, char, enc, ability_key="t_ember")).ok  # a second one, from a mixed roster
        await do(s, char, enc, kind="end_turn")
        third = await do(s, char, enc, ability_key="t_guard")  # but never a third
        assert not third.ok and third.error == "combat.err.summon_limit"
        assert len([e for e in state_of(enc).entities.values() if e.active]) == 2
        again = await do(s, char, enc, ability_key="t_blade")  # nor the same one twice
        assert not again.ok and again.error in ("combat.err.already_called", "combat.err.summon_limit")
        assert (await do(s, char, enc, ability_key="t_converge")).ok
        assert all(e.boost > 0 for e in state_of(enc).entities.values() if e.active)
        assert len(state_of(enc).entities) == 2  # convergence adds nothing


# ----------------------------------------------------- Shapeshifter


async def test_the_shapeshifter_path_through_the_service(lend):
    shape = {
        "t_bear": ability(10, "shift", form="bear", action="bonus"),
        "t_back": ability(10, "shift", form="none", action="bonus"),
    }
    key = lend("t_shape", branch("druid", shape))
    cid = await hero("druid", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert set(characters.shapes_for(char)) == {"bear"}
        enc = await begin(s, char)
        assert (await do(s, char, enc, ability_key="t_bear")).ok
        me = state_of(enc).combatants["p1"]
        assert me.form == "bear" and me.temp_hp > 0
        bear_reserve = me.temp_hp
        assert (
            bear_reserve
            <= get_content().forms["bear"].temp_hp + get_content().forms["bear"].temp_hp_per_level * char.level
        )
    async with session_scope() as s:  # a reload in the middle keeps the form
        enc = await s.scalar(select(Encounter).where(Encounter.character_id == cid, Encounter.status == "active"))
        assert state_of(enc).combatants["p1"].form == "bear"


# ------------------------------------------------------------- what the player sees


@pytest.mark.parametrize("lang", ["es", "en"])
async def test_the_panel_shows_each_helper_the_form_and_the_new_log_lines(lend, lang):
    from oathforge.bot import render
    from oathforge.services.events import render_event

    shape = {
        "t_bear": ability(10, "shift", form="bear", action="bonus"),
        "t_blade": ability(10, "summon", entity="astral_blade"),
    }
    key = lend("t_view", branch("druid", shape))
    cid = await hero("druid", key)
    async with session_scope() as s:
        char = await get_char(s, cid)
        enc = await begin(s, char)
        await do(s, char, enc, ability_key="t_blade")
        await do(s, char, enc, ability_key="t_bear")
        panel, kb = render.combat_panel(char, enc.state, lang)
        blade = get_content().entities["astral_blade"].name.get(lang)
        assert blade in panel and get_content().forms["bear"].icon in panel  # one line per helper, and the form
        assert "{" not in panel and "combat." not in panel  # nothing left unformatted
        # every log line the helpers can produce has text in both languages and no loose placeholders
        st = state_of(enc)
        for entry in st.log:
            line = render_event(combat_service.log_event(st, entry), lang)
            assert "{" not in line and "combat." not in line, line
