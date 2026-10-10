"""Tiny YAML-backed translator: t(lang, "combat.hit", actor="Lyra")."""

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
    path = LOCALES_DIR / f"{lang}.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        out: dict[str, str] = {}
        _flatten("", yaml.safe_load(fh) or {}, out)
        return out


def normalize_lang(code: str | None) -> str:
    settings = get_settings()
    base = (code or "").split("-")[0].lower()
    return base if base in settings.supported_languages else settings.default_language


def t(lang: str, key: str, **params) -> str:
    template = flat(lang).get(key) or flat("en").get(key) or key
    return template.format_map(_SafeDict(params)) if params else template


def has(lang: str, key: str) -> bool:
    return key in flat(lang)
