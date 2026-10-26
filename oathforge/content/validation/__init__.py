"""Cross-references of the loaded content, one module per domain. ``validate_references`` runs them
all and fails with every error at once, so a broken YAML says everything that is wrong in one go."""

from typing import TYPE_CHECKING

from oathforge.content.validation.classes import class_errors
from oathforge.content.validation.crafting import crafting_errors
from oathforge.content.validation.fallbacks import fallback_errors
from oathforge.content.validation.items import item_errors
from oathforge.content.validation.quests import quest_errors
from oathforge.content.validation.world import world_errors

if TYPE_CHECKING:
    from oathforge.content.loader import Content


def validate_references(c: "Content") -> None:
    errors = [
        *class_errors(c),
        *world_errors(c),
        *item_errors(c),
        *crafting_errors(c),
        *fallback_errors(c),
        *quest_errors(c),
    ]
    if errors:
        raise ValueError("Content validation failed:\n  " + "\n  ".join(errors))
