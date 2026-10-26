"""Manual rolls (the 🎲 button) and settings."""

import asyncio
import logging

from telegram import Update

from oathforge.bot import render
from oathforge.bot.handlers.common import edit_or_send, load, rng
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.ai.intent_parser import Intent
from oathforge.services import actions, characters
from oathforge.bot.handlers.callbacks.acts import _act


log = logging.getLogger(__name__)
DICE_SECONDS = 3.5  # Telegram's dice animation, before the engine's d20 appears


async def do_roll(update: Update, context) -> None:
    """The 🎲 button: animate Telegram's die (decoration only), then resolve the parked action with the
    engine's d20."""
    pending = context.user_data.pop("pending_roll", None)
    if pending is None:
        await settings(update, context)
        return
    try:
        await update.effective_chat.send_dice(emoji="🎲")
        await asyncio.sleep(DICE_SECONDS)
    except Exception:  # the animation is decoration; the roll is the engine's
        log.warning("could not send the dice animation", exc_info=True)
    if pending["type"] == "button":
        await _act(update, context, pending["verb"], pending["arg"], pending["n"], rolled_at=pending["location"])
        return
    from oathforge.bot.handlers.text import show_free_text  # text imports this module

    result = await actions.execute_free_text(context.bot_data["llm"], pending["user_id"], pending["text"],
                                             Intent.model_validate(pending["intent"]), False, rng(),
                                             location=pending["location"])
    await show_free_text(update, context, result)


async def settings(update: Update, context, new_lang: str | None = None) -> None:
    """⚙️ Settings: language and manual rolls (also /settings)."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        if new_lang in ("es", "en"):
            user.language = new_lang
        lang = context.user_data["lang"] = user.language
        text, kb = render.settings_view(user, lang)
    await edit_or_send(update, text, kb)


async def set_manual_rolls(update: Update, context, on: bool) -> None:
    """Off by default. Turning them on warns that Telegram's die is only decoration."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = context.user_data["lang"] = user.language
        characters.set_setting(user, "manual_rolls", on)
        text, kb = render.settings_view(user, lang)
    if not on:
        context.user_data.pop("pending_roll", None)
    head = t(lang, "roll.warning") if on else t(lang, "roll.changed", state=t(lang, "roll.off"))
    await edit_or_send(update, f"{head}\n\n{text}", kb)
