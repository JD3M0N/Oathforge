"""Console commands: ``oath help`` (also ``oathforge help`` or ``python -m oathforge help``)."""

import asyncio
import shutil
import sys
import textwrap

# (group, [(command, arguments, one-line description)]); every command here must be handled in main().
COMMANDS = [
    ("Bot", [
        ("bot", "", "Start the bot (Ctrl+C to stop it)."),
        ("stop", "", "Stop the running bot."),
        ("restart", "", "Restart the bot: stop it if running and start it in the background."),
    ]),
    ("Players", [
        ("delete-player", "[id|name] [--yes]", "Delete one player; without a name, list them."),
        ("reset-players", "[--yes]", "Delete every player (stop the bot first)."),
    ]),
    ("Testing", [
        ("tgtest", "send|press|show|login", "Play the bot from the Telegram test account."),
        ("simulate", "[--level 1-5]", "Simulate fights for balance (--help)."),
        ("achievements-backfill", "[--apply] [--character-id ID] [--after-id ID]", "Preview (default) or apply achievements earned before v0.9."),
        ("tutorial-stats", "", "How long each player takes per tutorial mission and where they get stuck."),
    ]),
    ("Help", [
        ("help", "", "Show this help."),
    ]),
]
FOOTER = "Commands that delete only show what they would delete until you add --yes."
COLUMN = 36  # where descriptions start


def command_names() -> list[str]:
    return [name for _, cmds in COMMANDS for name, _, _ in cmds]


def show_help() -> None:
    from oathforge import __version__

    width = max(60, min(shutil.get_terminal_size().columns, 100))
    indent = " " * COLUMN
    print(f"Oathforge v{__version__}  ·  Usage: oath <command>")
    for group, cmds in COMMANDS:
        print(f"\n{group}")
        for name, args, text in cmds:
            usage = f"  oath {name} {args}".rstrip()
            lines = textwrap.wrap(text, width - COLUMN) or [""]
            if len(usage) < COLUMN - 1:
                print(f"{usage:<{COLUMN}}{lines[0]}")
                lines = lines[1:]
            else:
                print(usage)
            for line in lines:
                print(indent + line)
    print(f"\n{FOOTER}")


def _db():
    from sqlalchemy.ext.asyncio import create_async_engine

    from oathforge.config import get_settings

    url = get_settings().database_url
    print(f"database: {url.split('@')[-1]}")
    return create_async_engine(url)


async def reset_players(confirm: bool) -> None:
    """Delete every player and what they left behind; keeps the schema and ``media_files``.

    Ids keep counting up, so new combats never reuse an old ``artifacts/battles`` file.
    The bot's in-memory state (half-finished character creation) is not in the DB: stop it first.
    """
    from sqlalchemy import text

    from oathforge.database.models import Base

    tables = [t.name for t in Base.metadata.sorted_tables if t.name != "media_files"]
    engine = _db()
    try:
        async with engine.begin() as conn:
            for name in tables:
                count = (await conn.execute(text(f'SELECT count(*) FROM "{name}"'))).scalar()
                print(f"  {name:24} {count}")
            if not confirm:
                print("nothing deleted; repeat with --yes")
                return
            for name in reversed(tables):  # children first
                await conn.execute(text(f'DELETE FROM "{name}"'))
            print("deleted")
    finally:
        await engine.dispose()


def _player_line(p) -> str:
    who = f"{p.name} ({p.class_key}, level {p.level})" if p.name else "(no character)"
    return f"  telegram {p.telegram_id:<14} {who}"


async def delete_player(query: str | None, confirm: bool) -> None:
    """One player: list them all without ``query``; delete the match only with ``--yes``."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from oathforge.services import admin

    engine = _db()
    try:
        async with AsyncSession(engine) as session:  # closing without commit rolls back
            if query is None:
                players = await admin.list_players(session)
                print(f"{len(players)} players:" if players else "no players")
                for p in players:
                    print(_player_line(p))
                if players:
                    print("delete one with: oath delete-player <id|name> --yes")
                return
            found = await admin.find_players(session, query)
            if not found:
                print(f"no player with id or name '{query}'; oath delete-player lists them")
                return
            if len(found) > 1:
                print(f"{len(found)} players are called '{query}'; use their Telegram id:")
                for p in found:
                    print(_player_line(p))
                return
            print(_player_line(found[0]))
            counts = await admin.delete_player(session, found[0].user_id)
            for name, n in counts.items():
                print(f"  {name:24} {n}")
            if not confirm:
                print("nothing deleted; repeat with --yes")
                return
            await session.commit()
            print("deleted; if the bot is running, the player starts over with /start")
    finally:
        await engine.dispose()


async def tutorial_stats() -> None:
    """Real minutes per tutorial mission, per player and as a median, and where each one is stuck."""
    from statistics import median

    from sqlalchemy.ext.asyncio import AsyncSession

    from oathforge.content import get_content
    from oathforge.services import admin

    quests = get_content().quests
    engine = _db()
    try:
        async with AsyncSession(engine) as session:
            runs = await admin.tutorial_runs(session)
    finally:
        await engine.dispose()
    if not runs:
        print("nobody has started the tutorial")
        return
    tut = [k for k, q in sorted(quests.items(), key=lambda kv: kv[1].order) if q.tutorial]
    print(f"{len(runs)} players · {sum(r.done for r in runs)} finished the tutorial\n")
    print("Median real minutes per mission (players who finished it):")
    for k in tut:
        times = [r.minutes[k] for r in runs if k in r.minutes]
        stuck = sum(1 for r in runs if r.current == k)
        med = f"{median(times):6.1f} min" if times else "     —    "
        print(f"  {quests[k].order}. {quests[k].name.en:28} {med}  ({len(times)} finished, {stuck} on it now)")
    print("\nPer player:")
    for r in runs:
        total = sum(r.minutes.values())
        where = "finished" if r.done else (f"on '{quests[r.current].name.en}' for {r.waiting:.0f} min"
                                            if r.current else "no active tutorial mission")
        print(f"  {r.name:20} level {r.level}  {len(r.minutes)}/{len(tut)} missions in {total:.0f} min · {where}")


def stop_bot() -> bool:
    """Stop the bot started with `oath bot` (found by its PID file). True if one was running."""
    from oathforge import pidfile

    pid = pidfile.read()
    pids = [pid] if pid is not None and pidfile.alive(pid) else pidfile.find_running()
    pidfile.PATH.unlink(missing_ok=True)
    if not pids:
        print("no bot is running")
        return False
    for p in pids:
        pidfile.kill(p)
        print(f"bot stopped (PID {p})")
    return True


def restart_bot() -> None:
    """Stop the running bot, if any, and start a new one in the background (output to artifacts/logs/)."""
    import subprocess
    import time
    from pathlib import Path

    stop_bot()
    time.sleep(1)  # let Telegram release the polling of the old one
    log = Path("artifacts") / "logs" / "bot-console.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    with open(log, "ab") as out:
        proc = subprocess.Popen([sys.executable, "-m", "oathforge", "bot"], stdout=out, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, **kwargs)
    print(f"bot started in the background (PID {proc.pid}); output in {log}")


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else "help"
    rest = args[1:]
    if command in ("help", "-h", "--help"):
        show_help()
    elif command == "bot":
        from oathforge.main import main as run_bot

        run_bot()
    elif command == "stop":
        stop_bot()
    elif command == "restart":
        restart_bot()
    elif command == "tgtest":
        from oathforge.tools.tgtest import main as tgtest

        tgtest(rest)
    elif command == "simulate":
        from oathforge.tools.simulate import main as simulate

        simulate(rest)
    elif command == "achievements-backfill":
        from oathforge.tools.achievements_backfill import main as backfill

        backfill(rest)
    elif command == "tutorial-stats":
        asyncio.run(tutorial_stats())
    elif command == "reset-players":
        asyncio.run(reset_players("--yes" in rest))
    elif command == "delete-player":
        names = [a for a in rest if a != "--yes"]
        asyncio.run(delete_player(" ".join(names) or None, "--yes" in rest))
    else:
        print(f"Unknown command: {command}\n")
        show_help()
        sys.exit(2)
