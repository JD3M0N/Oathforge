"""Play the bot from a real Telegram test account (Telethon), to test changes end to end.

Setup (once): create an app at https://my.telegram.org with the test phone and put in ``.env``::

    TG_TEST_API_ID=...
    TG_TEST_API_HASH=...
    TG_TEST_BOT=@YourBotUsername

    oathforge tgtest login +34600000000           # Telegram sends a code to the test phone
    oathforge tgtest login +34600000000 12345     # finish (add --password if it has 2FA)

Then, with the bot running::

    oathforge tgtest send "/start"                # send, then print what the bot answers
    oathforge tgtest press "Investigar"           # press a button of the latest message that has it
    oathforge tgtest show -n 5                    # last messages of the chat

The session lives in ``.telegram/`` (git-ignored): it is a login to that account, never share it.
"""

import argparse
import asyncio
import json
import sys
import time

from oathforge.config import ROOT_DIR, get_settings

SESSION_DIR = ROOT_DIR / ".telegram"
SESSION = SESSION_DIR / "tester"
PENDING_LOGIN = SESSION_DIR / "login.json"


def _client():
    from telethon import TelegramClient

    s = get_settings()
    if not s.tg_test_api_id or not s.tg_test_api_hash:
        sys.exit("Missing TG_TEST_API_ID / TG_TEST_API_HASH in .env (create them at https://my.telegram.org).")
    SESSION_DIR.mkdir(exist_ok=True)
    return TelegramClient(str(SESSION), s.tg_test_api_id, s.tg_test_api_hash)


def _bot() -> str:
    bot = get_settings().tg_test_bot
    if not bot:
        sys.exit("Missing TG_TEST_BOT in .env (the bot's @username).")
    return bot


# ---------------------------------------------------------------- printing

def render(msg, edited: bool = False) -> str:
    head = f"#{msg.id}" + (" (editado)" if edited else "")
    kind = ""
    if msg.dice:
        kind = f"[dado {msg.dice.emoticon} = {msg.dice.value}] "
    elif msg.photo:
        kind = "[foto] "
    elif msg.document:
        kind = "[archivo] "
    lines = [f"{head} {kind}{msg.raw_text or ''}".rstrip()]
    for row in msg.buttons or []:
        lines.append("   " + "  ".join(f"[{b.text}]" for b in row))
    return "\n".join(lines)


# ---------------------------------------------------------------- talking to the bot

async def _collect(client, bot_entity, act, quiet: float, timeout: float) -> None:
    """Run ``act`` and print every new or edited bot message until it goes quiet."""
    from telethon import events

    seen: list[tuple] = []
    last = [time.monotonic()]

    async def on_event(event):
        seen.append((event.message, isinstance(event, events.MessageEdited.Event)))
        last[0] = time.monotonic()

    new, edit = events.NewMessage(chats=bot_entity), events.MessageEdited(chats=bot_entity)
    client.add_event_handler(on_event, new)
    client.add_event_handler(on_event, edit)
    start = time.monotonic()
    try:
        await act()
        while time.monotonic() - start < timeout:
            await asyncio.sleep(0.3)
            if seen and time.monotonic() - last[0] >= quiet:
                break
    finally:
        client.remove_event_handler(on_event, new)
        client.remove_event_handler(on_event, edit)
    outgoing = [(m, e) for m, e in seen if not m.out]
    if not outgoing:
        print(f"(no reply in {timeout:.0f} s: is the bot running?)")
    for msg, edited in outgoing:
        print(render(msg, edited))
        print()


async def _find_button(client, bot_entity, label: str, msg_id: int | None):
    wanted = label.casefold()
    async for msg in client.iter_messages(bot_entity, limit=30, ids=[msg_id] if msg_id else None):
        if msg is None or msg.out or not msg.buttons:
            continue
        for i, row in enumerate(msg.buttons):
            for j, b in enumerate(row):
                if b.text.casefold() == wanted:
                    return msg, i, j
        for i, row in enumerate(msg.buttons):
            for j, b in enumerate(row):
                if wanted in b.text.casefold():
                    return msg, i, j
    return None


async def cmd_send(args) -> None:
    async with _client() as client:
        bot = await client.get_entity(_bot())
        await _collect(client, bot, lambda: client.send_message(bot, args.text), args.quiet, args.timeout)


async def cmd_press(args) -> None:
    async with _client() as client:
        bot = await client.get_entity(_bot())
        found = await _find_button(client, bot, args.label, args.msg)
        if found is None:
            sys.exit(f"No button '{args.label}' in the bot's latest messages.")
        msg, i, j = found
        print(f"> pressing [{msg.buttons[i][j].text}] on #{msg.id}\n")

        async def click():
            try:
                answer = await msg.click(i, j)
                if answer is not None and getattr(answer, "message", None):
                    print(f"(alert: {answer.message})\n")
            except Exception as exc:  # the bot may answer the callback late; its messages still arrive
                print(f"(callback: {type(exc).__name__})\n")

        await _collect(client, bot, click, args.quiet, args.timeout)


async def cmd_show(args) -> None:
    async with _client() as client:
        bot = await client.get_entity(_bot())
        msgs = [m async for m in client.iter_messages(bot, limit=args.n)]
        for msg in reversed(msgs):
            print(("> " + (msg.raw_text or "")) if msg.out else render(msg))
            print()


async def cmd_login(args) -> None:
    from telethon.errors import SessionPasswordNeededError

    client = _client()
    await client.connect()
    try:
        if await client.is_user_authorized() and not args.code:
            me = await client.get_me()
            print(f"Already logged in: {me.first_name} (@{me.username}, id {me.id})")
            return
        if not args.code:
            sent = await client.send_code_request(args.phone)
            PENDING_LOGIN.write_text(json.dumps({"phone": args.phone, "hash": sent.phone_code_hash}))
            print("Code sent to that phone's Telegram account. Repeat with: login <phone> <code>")
            return
        pending = json.loads(PENDING_LOGIN.read_text()) if PENDING_LOGIN.exists() else {}
        try:
            await client.sign_in(args.phone, args.code, phone_code_hash=pending.get("hash"))
        except SessionPasswordNeededError:
            if not args.password:
                sys.exit("The account has two-step verification: repeat with --password.")
            await client.sign_in(password=args.password)
        PENDING_LOGIN.unlink(missing_ok=True)
        me = await client.get_me()
        print(f"Logged in: {me.first_name} (@{me.username}, id {me.id})")
    finally:
        await client.disconnect()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="oathforge tgtest", description="Play the bot from a Telegram test account.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("login", help="log in the test account (two steps: phone, then phone + code)")
    p.add_argument("phone")
    p.add_argument("code", nargs="?")
    p.add_argument("--password", help="2FA password, if the account has one")

    for name, helptext in (("send", "send a message to the bot"), ("press", "press an inline button")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("text" if name == "send" else "label")
        if name == "press":
            p.add_argument("--msg", type=int, help="message id (default: latest message with that button)")
        p.add_argument("--quiet", type=float, default=4.0, help="stop after this many seconds without news (4)")
        p.add_argument("--timeout", type=float, default=45.0, help="give up after this many seconds (45)")

    p = sub.add_parser("show", help="print the last messages of the chat")
    p.add_argument("-n", type=int, default=6)

    args = parser.parse_args(argv)
    handler = {"login": cmd_login, "send": cmd_send, "press": cmd_press, "show": cmd_show}[args.command]
    asyncio.run(handler(args))


if __name__ == "__main__":
    main(sys.argv[1:])
