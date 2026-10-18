"""Plain text: talk to the current NPC, or free-form action via the AI DM."""

import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from oathforge.bot import render
from oathforge.bot.handlers import callbacks
from oathforge.bot.handlers.common import current_view, keep_typing, load, rate_ok, rng, send, send_outcome, send_result
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import actions

log = logging.getLogger(__name__)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = context.user_data["lang"] = user.language
        user_id = user.id
    if char is None:
        await send(update, t(lang, "start.need_character"))
        return
    if not rate_ok(context, update.effective_user.id):
        await send(update, t(lang, "err.rate"))
        return
    llm = context.bot_data["llm"]

    npc = context.user_data.get("talk")
    if npc is None:
        async with keep_typing(update.effective_chat):
            result = await actions.handle_free_text(llm, user_id, text, rng())
        if result.talk_to:
            npc = context.user_data["talk"] = result.talk_to
        elif result.roll_skill:  # manual rolls: park the action until the 🎲 button
            context.user_data["pending_roll"] = {"type": "text", "text": text, "user_id": user_id,
                                                 "intent": result.intent.model_dump(), "location": result.location}
            await send(update, *callbacks.roll_prompt(result.roll_skill, lang))
            return
        else:
            await show_free_text(update, context, result)
            return

    async with keep_typing(update.effective_chat):
        line, out = await actions.talk(llm, user_id, npc, text)
    async with session_scope() as session:
        _, char = await load(session, update)
        if out.error:
            context.user_data.pop("talk", None)
            await send_outcome(update, out, lang)
            view, kb = await current_view(session, char, lang)
        else:
            view, kb = await render.conversation(session, char, npc, lang, line=line)
            events = render.outcome_text(out, lang)
            if events:
                view += "\n\n" + events
    await send(update, view, kb)
    if not out.error:
        for card in render.level_up_cards(out, lang):
            await send(update, card)


async def show_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE, result: actions.FreeTextResult) -> None:
    """What happened and the scene's buttons, in one message (a fight: its panel on its own)."""
    lang = context.user_data.get("lang", "es")
    async with session_scope() as session:
        _, char = await load(session, update)
        fighting = char.state == "in_combat"
        view, kb = await current_view(session, char, lang, compact=True)
    if fighting:
        if result.outcome.events or result.narration:
            await send_outcome(update, result.outcome, lang, result.narration)
        await send(update, view, kb)
        return
    await send_result(update, result.outcome, lang, view, kb, result.narration)


def handler() -> MessageHandler:
    return MessageHandler(filters.TEXT & ~filters.COMMAND, on_text)
