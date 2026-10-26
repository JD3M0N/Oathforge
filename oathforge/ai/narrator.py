"""Turns resolved facts into prose. Never decides anything."""

from oathforge.ai.client import LLM
from oathforge.ai.prompts import LANGUAGE_NAMES, NARRATOR_SYSTEM


async def narrate(
    llm: LLM, *, lang: str, scene: str, character: str, player_text: str | None, facts: list[str], user_id: int | None
) -> str | None:
    if not facts:
        return None
    system = NARRATOR_SYSTEM.format(language=LANGUAGE_NAMES.get(lang, "English"))
    prompt = (
        f"Scene: {scene}\nCharacter: {character}\n"
        + (f"<player_text>\n{player_text[:600]}\n</player_text>\n" if player_text else "")
        + "FACTS (from the rules engine):\n"
        + "\n".join(f"- {f}" for f in facts)
    )
    return await llm.text(tier="narrative", system=system, prompt=prompt, user_id=user_id)
