"""The hero's class path: the branch (level 10), the training packages (5, 12, 18) and the modifiers (13, 17).

A choice is final. Nothing here recharges anything: the effective catalogue changes, but the bar and
the uses the hero has stay as they were (roadmap_balance D09 and §15.4). The only way back is the free
reroll that a substantial change of a branch grants once (``ClassSpecialization.revision``).

Not to be mixed up with ``services/specializations.py``, the branches of the field masteries.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.content.schemas import ClassSpecialization, Modifier
from oathforge.database.models import Character
from oathforge.engine import class_build
from oathforge.services import achievements, characters
from oathforge.services.events import Outcome


def branches(char: Character) -> dict[str, ClassSpecialization]:
    """Every branch of the hero's class, finished or not."""
    return {k: b for k, b in get_content().class_specializations.items() if b.class_key == char.class_key}


def open_for(char: Character) -> bool:
    """Has the hero reached the level where the branch is chosen, and not chosen one yet?"""
    return char.specialization is None and char.level >= get_content().progression.specialization_level


def pending(char: Character) -> tuple[class_build.Choice, ...]:
    return characters.effective(char).pending


def options(char: Character, choice: class_build.Choice) -> dict[str, object]:
    """What the hero may pick for a choice: both training packages, or the two modifiers of that level."""
    c = get_content()
    if choice.kind == class_build.TRAINING:
        return dict(c.progression.trainings)
    branch = c.class_specializations.get(char.specialization or "")
    if branch is None:
        return {}
    return {k: m for k, m in branch.modifiers.items() if m.level == choice.level}


def reroll_available(char: Character) -> bool:
    """A free second choice, once, if the hero's branch has since been substantially changed."""
    branch = get_content().class_specializations.get(char.specialization or "")
    return branch is not None and characters.build_of(char).get(characters.BRANCH_REV, 1) < branch.revision


def _finish(char: Character) -> None:
    """The catalogue just changed: keep what the hero has, and let the new abilities appear.

    More maximum HP are real HP, now (a training that gives +8 gives 8 more of both); less is a clip.
    Neither the bar nor any use is refilled."""
    characters.sync_resources(char)
    characters.set_pool(char, characters.pool_of(char))  # a smaller bar clips what is in it, never refills it
    before = char.max_hp
    char.max_hp = characters.max_hp_for(char)
    char.hp = min(char.max_hp, char.hp + max(0, char.max_hp - before))


async def choose_branch(session: AsyncSession, char: Character, key: str) -> Outcome:
    """Take the class branch, for good. At the guild, from level 10, once; and only a finished branch."""
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    branch = c.class_specializations.get(key)
    if branch is None or branch.class_key != char.class_key:
        return Outcome.refused("path.err.unknown")
    if char.level < c.progression.specialization_level:
        return Outcome.refused("path.err.level", level=c.progression.specialization_level)
    if not c.locations[char.location].home:
        return Outcome.refused("path.err.not_guild")
    if char.specialization is not None:
        return Outcome.refused("path.err.already")
    if not branch.ready:
        return Outcome.refused("path.err.not_ready")
    return await _take(session, char, key, branch)


async def reroll_branch(session: AsyncSession, char: Character, key: str) -> Outcome:
    """The free second choice, once, after a branch changed substantially. It undoes the old modifiers."""
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    branch = c.class_specializations.get(key)
    if branch is None or branch.class_key != char.class_key or not branch.ready:
        return Outcome.refused("path.err.unknown")
    if not c.locations[char.location].home:
        return Outcome.refused("path.err.not_guild")
    if not reroll_available(char):
        return Outcome.refused("path.err.no_reroll")
    build = characters.build_of(char)
    kept = {k: v for k, v in build.get(characters.CHOICES, {}).items() if k.startswith(class_build.TRAINING)}
    char.build = {**build, characters.CHOICES: kept}  # modifiers belonged to the old branch; trainings stay
    char.specialization = None
    return await _take(session, char, key, branch)


async def _take(session: AsyncSession, char: Character, key: str, branch: ClassSpecialization) -> Outcome:
    char.specialization = key
    char.build = {**characters.build_of(char), "v": characters.BUILD_VERSION,
                  characters.BRANCH_REV: branch.revision}
    out = Outcome().add("path.chosen", branch=branch.name.model_dump())
    _finish(char)
    for akey, a in branch.abilities.items():
        if a.level <= char.level:
            out.add("progress.new_ability", ability=a.name.model_dump(), cls=char.class_key, ability_key=akey)
    await achievements.emit(session, char, out, "class_specialized", {"branch": key},
                            f"branch:{key}:{branch.revision}")
    return out


async def choose_option(session: AsyncSession, char: Character, choice_key: str, option: str) -> Outcome:
    """Answer a pending training or modifier. A choice already made, or one not reached yet, is refused."""
    if refusal := characters.ensure_free(char):
        return refusal
    now = {c.key: c for c in pending(char)}
    choice = now.get(choice_key)
    if choice is None:
        return Outcome.refused("path.err.no_choice")
    picks = options(char, choice)
    if option not in picks:
        return Outcome.refused("path.err.unknown")
    build = characters.build_of(char)
    char.build = {**build, "v": characters.BUILD_VERSION,
                  characters.CHOICES: {**build.get(characters.CHOICES, {}), choice_key: option}}
    picked = picks[option]
    out = Outcome().add("path.picked", kind=choice.kind, level=choice.level, name=picked.name.model_dump())
    _finish(char)
    if isinstance(picked, Modifier):
        for akey, a in picked.grants.items():
            if a.level <= char.level:
                out.add("progress.new_ability", ability=a.name.model_dump(), cls=char.class_key, ability_key=akey)
    await achievements.emit(session, char, out, "class_choice", {"kind": choice.kind, "level": choice.level,
                                                                  "option": option},
                            f"choice:{choice_key}")
    return out
