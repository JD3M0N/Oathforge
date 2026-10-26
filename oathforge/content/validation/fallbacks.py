"""Template texts used when Gemini is down or out of budget (content/fallbacks/)."""

from string import Formatter
from typing import TYPE_CHECKING

from oathforge.content.schemas import CHRONICLE_KEYS, FALLBACK_KEYS, FALLBACK_PLACEHOLDERS
from oathforge.content.validation.common import collector

if TYPE_CHECKING:
    from oathforge.content.loader import Content


def fallback_errors(c: "Content") -> list[str]:
    """Every key has 12 distinct texts per language, with the same allowed placeholders in es and en."""
    errors, need = collector()
    for outcome in CHRONICLE_KEYS:
        if not c.chronicles.get(outcome):
            errors.append(f"fallbacks/chronicles.yaml: no texts for '{outcome}'")
    for outcome in c.chronicles:
        if outcome not in CHRONICLE_KEYS:
            errors.append(f"fallbacks/chronicles.yaml: unknown outcome '{outcome}'")
    for category, keys in FALLBACK_KEYS.items():
        for key in keys:
            if not c.fallbacks.get(category, {}).get(key):
                errors.append(f"fallbacks/{category}.yaml: no texts for '{key}'")
    for category, by_key in c.fallbacks.items():
        allowed = FALLBACK_PLACEHOLDERS.get(category)
        if allowed is None:
            errors.append(f"fallbacks/{category}.yaml: unknown category")
            continue
        for key, texts in by_key.items():
            if category == "dialogue" and key != "default":
                need("npc", key, c.npcs, "fallbacks/dialogue.yaml")
            if category not in ("dialogue", "chronicles") and key not in FALLBACK_KEYS[category]:
                errors.append(f"fallbacks/{category}.yaml: unknown key '{key}'")
            for lang in ("es", "en"):
                variants = [getattr(text, lang).strip() for text in texts]
                if not all(variants) or len(set(variants)) < 12:
                    errors.append(f"fallbacks/{category}.yaml {key}: need 12 distinct nonempty {lang} texts")
            for text in texts:
                placeholders = []
                for lang in ("es", "en"):
                    try:
                        fields = list(Formatter().parse(getattr(text, lang)))
                        used = {field for _, field, _, _ in fields if field is not None}
                        if any(spec or conversion for _, _, spec, conversion in fields):
                            errors.append(f"fallbacks/{category}.yaml {key}: formatting modifiers forbidden")
                    except ValueError:
                        errors.append(f"fallbacks/{category}.yaml {key}: malformed placeholders")
                        used = set()
                    placeholders.append(used)
                    if used - allowed:
                        errors.append(f"fallbacks/{category}.yaml {key}: unknown placeholders {sorted(used - allowed)}")
                if placeholders[0] != placeholders[1]:
                    errors.append(f"fallbacks/{category}.yaml {key}: es/en placeholders differ")
    for npc_key in c.npcs:
        if not c.fallbacks.get("dialogue", {}).get(npc_key):
            errors.append(f"fallbacks/dialogue.yaml: no texts for '{npc_key}'")
    return errors
