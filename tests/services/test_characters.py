"""Character creation for each class, language and names."""

import pytest

from oathforge.database.session import session_scope
from oathforge.services import characters, inventory, quests
from tests.services.helpers import get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


# ---------------------------------------------------------------- creation


async def test_create_character_sets_everything_up():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert char.abilities == {"str": 16, "con": 15, "cha": 14, "wis": 13, "dex": 11, "int": 9}
        assert char.hp == char.max_hp == 12
        assert char.location == "crownreach_plaza" and char.gold == 15
        gear = await characters.equipped(s, char)
        assert set(gear) == {"main_hand", "body", "off_hand"}
        assert characters.armor_class(char, gear) == 18
        skills = await characters.skills_of(s, char)
        assert skills["athletics"].proficient and skills["intimidation"].proficient
        assert characters.skill_bonus(char, skills, "athletics") == 3 + 2
        prog = await quests.progress(s, char)
        assert prog["tut_muster"].state == "active"
        assert prog["camp_order"].stage == "locked" and prog["tut_town"].state == "locked"
        assert char.resources == {"consecrated_strike": None}  # Conviction pays for it, not uses per rest
        assert characters.resource_max(char) == 2 + 2 * 1


async def test_create_warrior():
    _, cid = await new_character(cls="warrior")
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert set(gear) == {"main_hand", "ranged", "body", "off_hand"}
        assert characters.armor_class(char, gear) == 16 + 2 + 1  # chain mail, shield, Defense style
        assert char.resources == {"second_wind": None, "power_strike": None}  # the warrior pays with Focus
        assert characters.pool_of(char) == characters.resource_max(char) == 4  # base 3 + 1 per level
        cb = await characters.build_combatant(s, char)
        assert cb.row == "front" and cb.crit_range == 20
        assert [(a.key, a.damage_type) for a in cb.attacks] == [("main", "bludgeoning"), ("ranged", "slashing")]
        from oathforge.services.events import Outcome

        characters.grant_xp(char, 1000, Outcome())
        assert char.level == 4 and "action_surge" in char.resources
        assert (await characters.build_combatant(s, char)).crit_range == 19


async def test_create_priest():
    _, cid = await new_character(cls="cleric", bg="acolyte")
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 14 + 1 + 2  # scale mail (dex +1), shield
        assert char.resources == {"sacred_flame": None, "healing_word": None}  # Mana pays, not uses
        assert characters.resource_max(char) == 4 + 2 * 1
        cb = await characters.build_combatant(s, char)
        assert cb.row == "back" and cb.casting_mod == 3 and cb.spell_to_hit == 3 + 2
        assert cb.bonus_damage is None
        from oathforge.services.events import Outcome

        characters.grant_xp(char, 1800, Outcome())
        assert {"turn_undead", "bless"} <= set(char.resources)
        cb = await characters.build_combatant(s, char)
        assert cb.bonus_damage == "1d8" and cb.bonus_damage_type == "radiant"


async def test_create_mage_druid_bard():
    _, cid = await new_character(cls="sorcerer")  # human: every ability +1
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 10 + 2 + 3  # dex +2, Mage Armor
        assert char.resources == {"fire_bolt": None}
        cb = await characters.build_combatant(s, char)
        assert cb.row == "back" and cb.spell_dc == 8 + 3 + 2 and cb.spell_damage_bonus == 0
        await inventory.add_item(s, char, "chain_mail")
        mail = next(i for i in await inventory.items_of(s, char) if i.item_key == "chain_mail")
        await inventory.equip(s, char, mail.id)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 16  # chain mail: no dex, no Mage Armor

    _, cid = await new_character(tg_id=2, cls="druid")
    async with session_scope() as s:
        char = await get_char(s, cid)
        gear = await characters.equipped(s, char)
        assert characters.armor_class(char, gear) == 11 + 2 + 2  # leather (dex +2), shield
        assert char.resources == {"thorn_whip": None, "cure_wounds": None}
        from oathforge.services.events import Outcome

        characters.grant_xp(char, 1800, Outcome())
        assert {"entangle", "wild_shape"} <= set(char.resources)
        cb = await characters.build_combatant(s, char)
        assert cb.spell_damage_bonus == cb.casting_mod > 0

    _, cid = await new_character(tg_id=3, cls="bard")
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert char.resources == {"vicious_mockery": None, "bardic_inspiration": None}
        assert characters.pool_of(char) == characters.resource_max(char) == 2  # Resonance, built up in the fight
        cb = await characters.build_combatant(s, char)
        assert cb.casting_mod == 3 and [a.finesse for a in cb.attacks] == [True]


async def test_create_warlock():
    _, cid = await new_character(cls="warlock")  # human: every ability +1
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert char.gender is None  # created without choosing (as before v0.4.4)
        assert char.resources == {"eldritch_blast": None, "hex": None}  # Essence pays, not uses per rest
        cb = await characters.build_combatant(s, char)
        assert cb.row == "back" and cb.casting_mod == 3 and cb.spell_dc == 8 + 3 + 2 and cb.spell_damage_bonus == 0
        from oathforge.services.events import Outcome

        characters.grant_xp(char, 1800, Outcome())
        assert {"shadow_armor", "void_whispers"} <= set(char.resources) and "agonizing_blast" not in char.resources
        cb = await characters.build_combatant(s, char)
        assert cb.spell_damage_bonus == cb.casting_mod > 0


async def test_user_language_normalized():
    async with session_scope() as s:
        u = await characters.get_or_create_user(s, 99, "en-GB")
        assert u.language == "en"
        u2 = await characters.get_or_create_user(s, 100, "fr")
        assert u2.language == "es"


def test_name_validation():
    assert characters.valid_name("Lyra")
    assert characters.valid_name("Ser Aldric-Vane")
    assert not characters.valid_name("x")
    assert not characters.valid_name("<b>hack</b>")
