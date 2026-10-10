"""Inline keyboards. callback_data = "verb|arg|nonce" (max 64 bytes).

State-changing buttons share one nonce per rendered message, so only the
first press on a keyboard is honored; stale or double taps are ignored.
"""

import secrets

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
    return [buttons[i:i + cols] for i in range(0, len(buttons), cols)]


def markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([r for r in rows if r])
