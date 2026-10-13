"""Expedition chronicles: the short story told after a field activity ends.

The engine's result is final and already paid; the chronicle only tells it. The chronicle model
(Gemini 3.1 Flash-Lite) writes up to ``AI_USER_DAILY_CHRONICLES`` a day per player; after that, or
when the AI fails, a generic text from content/fallbacks/chronicles.yaml is used instead. Each activity gets
one chronicle, stored with it, so pressing a button again never spends the budget twice.
"""

from dataclasses import dataclass
from datetime import date, datetime
from datetime import time as dtime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.ai import chronicler, fallbacks
from oathforge.ai.client import LLM
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character, WorldActivity
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import activities, characters

# what happened, in plain English, for the chronicler
OUTCOME_FACTS = {
    "gather": "A calm, safe expedition; the hero worked steadily and came back with the materials.",
    "stay_ok": "A long expedition without trouble; the hero came back with a full load.",
    "stay_won": "At the end of a long expedition the hero was ambushed, won the fight and kept the whole load.",
    "stay_fled": "At the end of a long expedition the hero was ambushed and fled, saving only half of the load.",
    "stay_lost": "At the end of a long expedition the hero was ambushed and defeated; the load was lost.",
    "track_tracks": "The hero tracked prey for a while but only found old tracks; no fight.",
    "track_won": "The hero tracked the prey down and killed it.",
    "track_fled": "The hero tracked the prey down but had to flee from it.",
    "track_lost": "The hero tracked the prey down and was defeated by it.",
}


@dataclass
class Chronicle:
    text: str
    ai: bool
    used: int  # AI chronicles today, this one included
    limit: int


def day_start() -> float:
    """Local midnight as unix time: the budget resets with the day, like the other AI limits."""
    return datetime.combine(date.today(), dtime.min).timestamp()


async def chronicles_today(session: AsyncSession, char_id: int) -> int:
    return int(await session.scalar(
        select(func.count(WorldActivity.id))
        .where(WorldActivity.character_id == char_id, WorldActivity.chronicle_ai.is_(True),
               WorldActivity.resolved_at >= day_start())
    ) or 0)


def _values(act: WorldActivity, char: Character, lang: str) -> dict:
    c = get_content()
    res = act.result or {}
    monster = res.get("monster")
    return {
        "name": char.name,
        "place": c.locations[act.location].name.get(lang),
        "loot": activities.loot_text(res.get("items") or {})[lang],
        "monster": c.monsters[monster].name.get(lang) if monster in c.monsters else "",
    }


def generic(act: WorldActivity, char: Character, lang: str) -> str:
    """A hand-written text for this outcome, picked by the activity's seed."""
    return fallbacks.pick("chronicles", (act.result or {}).get("outcome", "gather"), lang, seed=act.seed,
                          **_values(act, char, lang))


def _facts(act: WorldActivity, char: Character) -> list[str]:
    res = act.result or {}
    v = _values(act, char, "en")
    facts = [OUTCOME_FACTS[res["outcome"]]]
    if res.get("items"):
        facts.append(f"Materials the hero brings back: {v['loot']}.")
    elif res["outcome"] in ("stay_lost",):
        facts.append("The hero brings back nothing.")
    if v["monster"]:
        facts.append(f"Creature involved: {v['monster']}.")
    if res.get("xp"):
        facts.append(f"The hero's {characters.mastery_name(act.skill)['en'].lower()} skill improved a little.")
    return facts


def _hero(char: Character, lang: str) -> str:
    c = get_content()
    return (f"{char.name}, {c.lineages[char.lineage].name.get(lang)} {c.classes[char.class_key].name.get(lang)} "
            f"(level {char.level}), {c.backgrounds[char.background].name.get(lang)}")


async def tell(llm: LLM, activity_id: int, lang: str) -> Chronicle | None:
    """The chronicle of a finished activity: stored, AI-written while the daily budget lasts, else generic.

    Runs after the activity's transaction is committed; the AI is called with no row locked.
    """
    limit = get_settings().ai_user_daily_chronicles
    async with session_scope() as session:
        act = await session.get(WorldActivity, activity_id)
        if act is None or act.status != "done":
            return None
        char = await session.get(Character, act.character_id)
        used = await chronicles_today(session, char.id)
        if act.chronicle:
            return Chronicle(act.chronicle, act.chronicle_ai, used, limit)
        user_id = char.user_id
        hero, facts = _hero(char, lang), _facts(act, char)
        place = get_content().locations[act.location].name.get(lang)
        kind = activities.describe(act, "en")
    text = None
    if used < limit:
        text = await chronicler.write(llm, lang=lang, hero=hero, place=place, activity=kind, facts=facts,
                                      user_id=user_id)
    async with session_scope() as session:
        act = await session.scalar(select(WorldActivity).where(WorldActivity.id == activity_id).with_for_update())
        char = await session.get(Character, act.character_id)
        if not act.chronicle:  # another press may have written it meanwhile: keep that one
            act.chronicle = text or generic(act, char, lang)
            act.chronicle_ai = text is not None
            await session.flush()
        return Chronicle(act.chronicle, act.chronicle_ai, await chronicles_today(session, char.id), limit)


def footer(ch: Chronicle, lang: str) -> str:
    if ch.ai:
        return t(lang, "chronicle.footer_ai", used=ch.used, limit=ch.limit)
    if ch.used >= ch.limit:
        return t(lang, "chronicle.footer_rest", limit=ch.limit)
    return t(lang, "chronicle.footer_generic")
