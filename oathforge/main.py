"""Entry point: python -m oathforge.main"""

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, ContextTypes, TypeHandler

from oathforge import __version__, recorder

from oathforge.ai.client import build_llm
from oathforge.bot.handlers import callbacks, commands, creation, text
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.session import dispose_engine, init_engine
from oathforge.i18n import t

log = logging.getLogger("oathforge")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("unhandled error", exc_info=context.error)
    recorder.error("telegram handler", context.error)
    if isinstance(update, Update) and update.effective_chat:
        lang = (context.user_data or {}).get("lang", get_settings().default_language)
        try:
            await update.effective_chat.send_message(t(lang, "err.generic"))
        except Exception:
            pass


async def record_update(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Copy every incoming message and button press to artifacts/ (debug only)."""
    if not isinstance(update, Update) or update.effective_user is None:
        return
    user = update.effective_user
    if update.message and update.message.text:
        recorder.incoming(user.id, user.full_name, update.message.text)
    elif update.callback_query and update.callback_query.data:
        recorder.incoming(user.id, user.full_name, update.callback_query.data, button=True)
    elif update.message:  # sticker, photo, voice...: the bot ignores them, but the player tried
        att = update.message.effective_attachment
        kind = type(att[-1] if isinstance(att, (list, tuple)) and att else att).__name__ if att else "?"
        recorder.incoming(user.id, user.full_name, f"[{kind}] {update.message.caption or ''}".strip())


async def post_init(app: Application) -> None:
    init_engine()
    for lang in ("es", "en"):
        await app.bot.set_my_commands(
            [BotCommand(cmd, t(lang, f"cmd.{cmd}")) for cmd in
             ("start", "look", "hero", "inventory", "journal", "language", "help")],
            language_code=lang,
        )


async def post_shutdown(app: Application) -> None:
    await dispose_engine()


def build_app() -> Application:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")
    get_content()  # validate content before accepting players

    app = (Application.builder().token(settings.bot_token)
           .post_init(post_init).post_shutdown(post_shutdown).build())
    app.bot_data["llm"] = build_llm(settings)
    app.add_handler(TypeHandler(Update, record_update), group=-1)
    # One group: the creation conversation gets first pick of text/buttons while it is active.
    app.add_handler(creation.handler())
    for h in commands.handlers():
        app.add_handler(h)
    app.add_handler(callbacks.handler())
    app.add_handler(text.handler())
    app.add_error_handler(on_error)
    return app


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    log.info("Oathforge v%s", __version__)
    recorder.start(get_settings())
    build_app().run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
