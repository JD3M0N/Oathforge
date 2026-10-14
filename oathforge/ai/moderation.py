"""Reviews player-written text before the game keeps it. The AI only says yes or no; it grants nothing."""

from pydantic import BaseModel

from oathforge.ai.client import LLM
from oathforge.ai.prompts import BACKGROUND_REVIEW_SYSTEM, LANGUAGE_NAMES

TITLE_MAX = 40
STORY_MIN, STORY_MAX = 20, 300


class BackgroundReview(BaseModel):
    ok: bool
    reason: str = ""  # one friendly sentence for the player when rejected
    title: str = ""  # the background's name, tidied up


def split_background(text: str) -> tuple[str, str] | None:
    """First line is the name, the rest the story; None if either is missing or out of bounds."""
    title, _, story = text.strip().partition("\n")
    title, story = title.strip(), " ".join(story.split())
    if not 2 <= len(title) <= TITLE_MAX or not STORY_MIN <= len(story) <= STORY_MAX:
        return None
    return title, story


async def review_background(llm: LLM, *, lang: str, title: str, story: str,
                            user_id: int | None) -> BackgroundReview | None:
    """None when the AI could not answer: the game then refuses the custom background rather than guess."""
    system = BACKGROUND_REVIEW_SYSTEM.format(language=LANGUAGE_NAMES.get(lang, "English"))
    prompt = f"<player_text>\nName: {title}\nStory: {story}\n</player_text>"
    review = await llm.json(tier="fast", system=system, prompt=prompt, schema=BackgroundReview, user_id=user_id)
    if review is None:
        return None
    clean = " ".join(review.title.split())[:TITLE_MAX] or title
    return review.model_copy(update={"title": clean, "reason": review.reason.strip()[:200]})
