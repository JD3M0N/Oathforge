"""Tiny YAML-backed translator: t(lang, "combat.hit", actor="Lyra")."""

import re
from functools import lru_cache
from pathlib import Path

import yaml

from oathforge.config import get_settings

LOCALES_DIR = Path(__file__).parent / "locales"


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _flatten(prefix: str, node: dict, out: dict[str, str]) -> None:
    for key, value in node.items():
        full = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            _flatten(full, value, out)
        else:
            out[full] = str(value)


@lru_cache
def flat(lang: str) -> dict[str, str]:
    """Every file of locales/<lang>/ merged; a key defined in two files is an error."""
    out: dict[str, str] = {}
    for path in sorted((LOCALES_DIR / lang).glob("*.yaml")):
        with open(path, encoding="utf-8") as fh:
            part: dict[str, str] = {}
            _flatten("", yaml.safe_load(fh) or {}, part)
        if repeated := sorted(out.keys() & part.keys()):
            raise ValueError(f"locales/{lang}/{path.name}: keys already defined in another file: {repeated[:5]}")
        out.update(part)
    return out


def normalize_lang(code: str | None) -> str:
    settings = get_settings()
    base = (code or "").split("-")[0].lower()
    return base if base in settings.supported_languages else settings.default_language


_CONTRACTION = re.compile(r"\b([Aa]|[Dd]e) el\b")  # «a el Mercado» → «al Mercado», «de el» → «del»


COUNTS = ("n", "count", "turns", "left")  # one of these equal to 1 picks "<key>_one" when the locale has it


def t(lang: str, key: str, **params) -> str:
    if any(params.get(p) == 1 for p in COUNTS) and f"{key}_one" in flat(lang):
        key = f"{key}_one"  # «1 ronda», not «1 rondas»
    template = flat(lang).get(key) or flat("en").get(key) or key
    if not params:
        return template
    text = template.format_map(_SafeDict(params))
    if lang == "es":
        text = _CONTRACTION.sub(lambda m: m.group(1)[0] + ("l" if m.group(1).lower() == "a" else "el"), text)
    return text


def has(lang: str, key: str) -> bool:
    return key in flat(lang)
