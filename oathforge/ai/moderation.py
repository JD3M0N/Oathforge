"""Reviews player-written text before the game keeps it. It grants nothing."""

from typing import Literal

from pydantic import BaseModel

from oathforge.ai.client import LLM
from oathforge.ai.prompts import BACKGROUND_REVIEW_SYSTEM, LANGUAGE_NAMES

TITLE_MAX = 40
STORY_MIN, STORY_MAX = 20, 300


class BackgroundReview(BaseModel):
    status: Literal["accepted", "adapted", "rejected"]
    reason: str = ""  # friendly explanation for an adaptation or rejection
    title: str = ""  # tidied original title, or the proposed title
    story: str = ""  # proposed story when adapted


def split_background(text: str) -> tuple[str, str] | None:
    """First line is the name, the rest the story; None if either is missing or out of bounds."""
    title, _, story = text.strip().partition("\n")
    title, story = title.strip(), " ".join(story.split())
    if not 2 <= len(title) <= TITLE_MAX or not STORY_MIN <= len(story) <= STORY_MAX:
        return None
    return title, story


async def review_background(llm: LLM, *, lang: str, title: str, story: str, world_context: str,
                            lineage_context: str, user_id: int | None) -> BackgroundReview | None:
    """None when the AI fails or proposes text outside the same limits as player input."""
    system = BACKGROUND_REVIEW_SYSTEM.format(language=LANGUAGE_NAMES.get(lang, "English"),
                                             world_context=world_context)
    prompt = (f"<character_context>\nLineage: {lineage_context}\n</character_context>\n"
              f"<player_text>\nName: {title}\nStory: {story}\n</player_text>")
    review = await llm.json(tier="fast", system=system, prompt=prompt, schema=BackgroundReview, user_id=user_id)
    if review is None:
        return None
    clean_title = " ".join(review.title.split())[:TITLE_MAX] or title
    clean_story = " ".join(review.story.split())
    if review.status == "adapted" and not (2 <= len(clean_title) <= TITLE_MAX
                                            and STORY_MIN <= len(clean_story) <= STORY_MAX):
        return None
    if review.status == "accepted":
        clean_story = story
    return review.model_copy(update={"title": clean_title, "story": clean_story,
                                     "reason": review.reason.strip()[:200]})
