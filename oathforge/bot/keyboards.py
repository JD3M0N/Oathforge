"""Inline keyboards. callback_data = "verb|arg|nonce" (max 64 bytes).

State-changing buttons share one nonce per rendered message, so only the
first press on a keyboard is honored; stale or double taps are ignored.
"""

import re
import secrets

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from oathforge.i18n import t

FIXED = ("place", "activities", "map", "hero", "inventory", "journal")  # the fixed keyboard under the chat
KEYBOARD_VERSION = 3  # bump when FIXED changes, so everyone gets the new keyboard


def nonce() -> str:
    return secrets.token_urlsafe(6)


def cb(verb: str, arg: str = "-", n: str = "-") -> str:
    data = f"{verb}|{arg}|{n}"
    assert len(data.encode()) <= 64, data
    return data


def parse(data: str) -> tuple[str, str, str]:
    verb, arg, n = (data.split("|") + ["-", "-"])[:3]
    return verb, arg, n


def btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)


def grid(buttons: list[InlineKeyboardButton], cols: int = 2) -> list[list[InlineKeyboardButton]]:
    return [buttons[i : i + cols] for i in range(0, len(buttons), cols)]


def markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([r for r in rows if r])


def fixed_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """📍 Place · ⚒ Activities · 🗺 Map / 🧝 Hero · 🎒 Inventory · 📖 Journal, always under the chat."""
    labels = [KeyboardButton(t(lang, f"kb.{k}")) for k in FIXED]
    return ReplyKeyboardMarkup(
        [labels[:3], labels[3:]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=t(lang, "kb.placeholder"),
    )


def fixed_key(text: str) -> str | None:
    """Which fixed button was pressed (its label in any language), or None for ordinary text."""
    text = (text or "").strip()
    return next((k for k in FIXED for lang in ("es", "en") if t(lang, f"kb.{k}") == text), None)


def fixed_pattern() -> re.Pattern:
    labels = {t(lang, f"kb.{k}") for k in FIXED for lang in ("es", "en")}
    return re.compile("^(" + "|".join(re.escape(x) for x in sorted(labels)) + ")$")
