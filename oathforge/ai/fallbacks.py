"""Generic texts for when Gemini is down or out of budget (content/fallbacks/).

The engine has already decided everything; these only stand in for the prose the AI would write.
"""

import random

from oathforge.content import get_content


class _Keep(dict):
    """format_map that leaves unknown {placeholders} as they are."""

    def __missing__(self, key):
        return "{" + key + "}"


def pick(category: str, key: str, lang: str, seed: int | None = None, context: str | None = None, **values) -> str:
    """Try key.context, key, then default; fixed by seed, otherwise chosen at random."""
    by_key = get_content().fallbacks.get(category, {})
    texts = (by_key.get(f"{key}.{context}") if context else None) or by_key.get(key) or by_key.get("default") or []
    if not texts:
        return ""
    text = texts[seed % len(texts)] if seed is not None else random.choice(texts)
    return text.get(lang).format_map(_Keep(values))
