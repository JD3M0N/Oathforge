"""The hero's permanent companion: the servant of a pact, the beast of a ranger.

It is the same being fight after fight, with a name the player gave it. It is never an item: it cannot be
bought, sold or duplicated, and being struck down does not end it. A fallen one comes back to the next fight
at half its health, and a long rest mends it entirely (roadmap_balance §7.1 and §7.3).

State lives in ``Character.build["companion"]``: {"name": …, "hp": left or None for full, "down": bool}.
"""

from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine import dice
from oathforge.engine.checks import proficiency_bonus
from oathforge.engine.combat import EntityTemplate

KEY = "companion"
NAME_MAX = 20


def _build(char: Character) -> dict:
    return dict(char.build or {})


def entity_key(char: Character) -> str | None:
    """Which servant or beast the hero's abilities bring along, if any."""
    from oathforge.services import characters  # a late import: characters needs this module to mend on rest

    for a in characters.abilities_of(char).values():
        if a.kind == "passive" and a.entity:
            return a.entity
    return None


def state(char: Character) -> dict:
    return dict(_build(char).get(KEY, {}))


def _save(char: Character, data: dict) -> None:
    char.build = {**_build(char), KEY: data}


def display_name(char: Character, lang: str) -> str:
    """The name the player gave it, or its kind's own name until they do."""
    name = state(char).get("name")
    key = entity_key(char)
    return name or (get_content().entities[key].name.get(lang) if key else "")


def valid_name(name: str) -> bool:
    """Letters, spaces and a few marks, short. It is shown to the player and never put in an AI prompt as an
    instruction: a name is data."""
    text = (name or "").strip()
    return 2 <= len(text) <= NAME_MAX and all(ch.isalpha() or ch in " '-" for ch in text)


def rename(char: Character, name: str) -> bool:
    if entity_key(char) is None or not valid_name(name):
        return False
    _save(char, {**state(char), "name": name.strip()})
    return True


def mend(char: Character) -> None:
    """A long rest: whole again, and no longer fallen."""
    if state(char):
        _save(char, {**state(char), "hp": None, "down": False})


def record(char: Character, hp: int, down: bool) -> None:
    """After a fight: how the companion was left."""
    _save(char, {**state(char), "hp": hp, "down": down})


def scale_dice(expr: str, extra: int) -> str:
    d = dice.parse(expr)
    return f"{d.count}d{d.sides}{d.bonus + extra:+d}"


def template(key: str, char: Character) -> EntityTemplate:
    """An entity's numbers at the hero's level: content gives the seed, the level gives the growth."""
    d = get_content().entities[key]
    bonus = char.level // 3
    return EntityTemplate(
        key=key,
        name=d.name.model_dump(),
        kind=d.kind,
        role=d.role,
        icon=d.icon,
        hp=d.hp + d.hp_per_level * char.level,
        to_hit=d.to_hit + proficiency_bonus(char.level),
        damage=scale_dice(d.damage, bonus) if d.damage else None,
        damage_type=d.damage_type or "force",
        ranged=d.ranged,
        status=d.status,
        status_turns=d.status_turns,
        period=d.period,
        duration=d.duration,
    )


def start_hp(char: Character, tpl: EntityTemplate) -> int:
    """Its health at the start of a fight: what it was left with, half if it had fallen, whole after a rest."""
    data = state(char)
    left = data.get("hp")
    if data.get("down") or left == 0:
        return max(1, tpl.hp // 2)
    return tpl.hp if left is None else max(1, min(left, tpl.hp))
