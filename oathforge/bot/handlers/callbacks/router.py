"""The entry point: answers the press and sends each verb to its handler."""

from sqlalchemy.orm.exc import StaleDataError
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from oathforge.bot.handlers import achievements
from oathforge.bot.handlers.common import answer, answered, current_view, edit_or_send, load, rate_ok
from oathforge.bot.keyboards import parse
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.bot.handlers.callbacks.acts import ACTS, _act
from oathforge.bot.handlers.callbacks.combat import _combat
from oathforge.bot.handlers.callbacks.rolls import do_roll, set_manual_rolls, settings
from oathforge.bot.handlers.callbacks.views import _view


# verbs that only show something (no nonce, no state change)
VIEWS = {"scene", "trv", "trvz", "trvs", "talkm", "talk", "bye", "inv", "hero", "sheet", "jr", "jrm", "jrc", "jrl", "jrs", "jq", "jrb", "jb", "jbi", "jrr",
         "shopm", "shop", "shopg", "sellm", "cbp", "lang", "city", "place", "cls", "clsl", "rep", "prof", "profsw", "profcf", "pg", "crf", "rb", "repf",
         "mst", "hob", "acts", "rcl", "rcp", "room", "spec", "specf", "tools", "path", "pathq", "pathv"}


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    verb, arg, n = parse(q.data or "")
    if not rate_ok(context, update.effective_user.id):
        await answer(update, t(context.user_data.get("lang", "es"), "err.rate"))
        answered(update)
        return
    if verb not in ("cb", "place", "city") and verb not in ACTS:  # these answer once they know (a refusal is a popup)
        await answer(update)
    try:
        if verb in ("ach", "achm"):
            await achievements.handle(update, context, arg, mutation=verb == "achm", nonce=n)
        elif verb in VIEWS:
            await _view(update, context, verb, arg)
        elif verb == "cb":
            await _combat(update, context, arg, n)
        elif verb == "roll":
            await do_roll(update, context)
        elif verb == "rollset":
            await set_manual_rolls(update, context, arg == "on")
        elif verb in ("set", "setl"):
            await settings(update, context, arg if verb == "setl" else None)
        else:
            await _act(update, context, verb, arg, n)
    except StaleDataError:  # someone else changed the hero meanwhile: the popup, and the current view in place
        lang = context.user_data.get("lang", "es")
        await answer(update, t(lang, "err.stale_popup"))
        async with session_scope() as session:
            _, char = await load(session, update)
            if char is not None:
                await edit_or_send(update, *await current_view(session, char, lang))
    finally:
        await answer(update)
        answered(update)


def handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(on_callback)
