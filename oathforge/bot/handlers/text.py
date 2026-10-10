"""Plain text: talk to the current NPC, or free-form action via the AI DM."""

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, MessageHandler, filters

from oathforge.bot import render
from oathforge.bot.handlers.common import current_view, load, rate_ok, rng, send
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
    await update.effective_chat.send_action(ChatAction.TYPING)

    npc = context.user_data.get("talk")
    if npc is None:
        result = await actions.handle_free_text(llm, user_id, text, rng())
        if result.talk_to:
            npc = context.user_data["talk"] = result.talk_to
        else:
            if result.outcome.events or result.narration:
                await send(update, render.outcome_text(result.outcome, lang, result.narration))
            async with session_scope() as session:
                _, char = await load(session, update)
                view, kb = await current_view(session, char, lang)
            await send(update, view, kb)
            return

    line, out = await actions.talk(llm, user_id, npc, text)
    async with session_scope() as session:
        _, char = await load(session, update)
        if out.error:
            context.user_data.pop("talk", None)
            await send(update, render.outcome_text(out, lang))
            view, kb = await current_view(session, char, lang)
        else:
            view, kb = await render.conversation(session, char, npc, lang, line=line)
            if out.events:
                view += "\n\n" + render.outcome_text(out, lang)
    await send(update, view, kb)


def handler() -> MessageHandler:
    return MessageHandler(filters.TEXT & ~filters.COMMAND, on_text)
