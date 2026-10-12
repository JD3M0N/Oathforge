"""The bestiary: which monsters a character has seen and killed, and how much it knows of them.

Like a D&D monster manual filled in by experience: seeing a creature reveals what it is,
the first kill its numbers, and a few more its weaknesses.
"""

from oathforge.content import get_content
from oathforge.database.models import Character

KILLS_FOR_STATS = 1
KILLS_FOR_SECRETS = 3


def see(char: Character, monster_keys: list[str]) -> None:
    book = {k: dict(v) for k, v in (char.bestiary or {}).items()}
    for key in set(monster_keys):
        entry = book.setdefault(key, {"seen": 0, "killed": 0})
        entry["seen"] += 1
    char.bestiary = book


def kill(char: Character, monster_keys: list[str]) -> None:
    book = {k: dict(v) for k, v in (char.bestiary or {}).items()}
    for key in monster_keys:
        entry = book.setdefault(key, {"seen": 1, "killed": 0})
        entry["killed"] += 1
    char.bestiary = book


def known(char: Character) -> list[tuple[str, dict]]:
    """Seen monsters that still exist in the content, in content order."""
    book = char.bestiary or {}
    return [(k, book[k]) for k in get_content().monsters if k in book]


def tier(entry: dict | None) -> int:
    """0: unknown · 1: seen · 2: stats (first kill) · 3: weaknesses and loot."""
    if not entry:
        return 0
    killed = entry.get("killed", 0)
    return 3 if killed >= KILLS_FOR_SECRETS else 2 if killed >= KILLS_FOR_STATS else 1
