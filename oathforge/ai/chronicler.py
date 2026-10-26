"""Expedition chronicles: a short personal story of a field activity. Never decides anything."""

from oathforge.ai.client import LLM
from oathforge.ai.prompts import CHRONICLE_SYSTEM, LANGUAGE_NAMES


async def write(
    llm: LLM, *, lang: str, hero: str, place: str, activity: str, facts: list[str], user_id: int | None
) -> str | None:
    if not facts:
        return None
    system = CHRONICLE_SYSTEM.format(language=LANGUAGE_NAMES.get(lang, "English"))
    prompt = f"Hero: {hero}\nPlace: {place}\nExpedition: {activity}\nFACTS (from the rules engine):\n" + "\n".join(
        f"- {f}" for f in facts
    )
    return await llm.text(tier="chronicle", system=system, prompt=prompt, user_id=user_id)
