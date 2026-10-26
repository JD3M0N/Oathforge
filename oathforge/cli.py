"""Console commands: ``oath help`` (also ``oathforge help`` or ``python -m oathforge help``)."""

import asyncio
import shutil
import sys
import textwrap
from pathlib import Path

# (group, [(command, arguments, one-line description)]); every command here must be handled in main().
COMMANDS = [
    (
        "Bot",
        [
            ("bot", "", "Start the bot (Ctrl+C to stop it)."),
            ("stop", "", "Stop the running bot."),
            ("restart", "", "Restart the bot: stop it if running and start it in the background."),
        ],
    ),
    (
        "Players",
        [
            ("delete-player", "[id|name] [--yes]", "Delete one player; without a name, list them."),
            ("reset-players", "[--yes]", "Delete every player (stop the bot first)."),
            (
                "launch-reset",
                "[--yes] [--backup FILE]",
                "Wipe the game, keep accounts and quotas; takes a backup first (stop the bot).",
            ),
            ("backup", "FILE", "Write the whole database to a JSON file."),
            ("restore", "FILE [--yes]", "Replace the whole database with a backup (stop the bot)."),
        ],
    ),
    (
        "Content",
        [
            ("validate", "", "Load and cross-check content/ (what the bot does at startup); exit 1 on errors."),
            ("content-index", "", "Rewrite content/INDEX.md: one line per content id with its file."),
            (
                "new",
                "TYPE ID [--zone Z] [--category C] ...",
                "Create an item, monster, npc, quest, zone, place or class from content/_templates/ (--help).",
            ),
        ],
    ),
    (
        "Testing",
        [
            ("tgtest", "send|press|show|login", "Play the bot from the Telegram test account."),
            ("simulate", "[--level 1-5]", "Simulate fights for balance (--help)."),
            ("balance", "[--n 16] [--quick]", "Balance report of the campaign: classes, branches, policies, pace."),
            (
                "achievements-backfill",
                "[--apply] [--character-id ID] [--after-id ID]",
                "Preview (default) or apply achievements earned before v0.9.",
            ),
            ("tutorial-stats", "", "How long each player takes per tutorial mission and where they get stuck."),
        ],
    ),
    ("Help", [("help", "", "Show this help.")]),
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


def _backup_dir():
    from oathforge.config import get_settings

    return get_settings().artifacts_dir / "backups"


async def backup(path: str | None) -> None:
    """Dump every table to one JSON file (read only)."""
    import time

    from sqlalchemy.ext.asyncio import AsyncSession

    from oathforge.services import launch

    target = Path(path) if path else _backup_dir() / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    engine = _db()
    try:
        async with AsyncSession(engine) as session:
            data = await launch.dump(session)
        target.write_text(launch.to_json(data), encoding="utf-8")
        for name, rows in data["tables"].items():
            print(f"  {name:24} {len(rows)}")
        print(f"saved {target}")
    finally:
        await engine.dispose()


async def restore(path: str, confirm: bool) -> None:
    """Replace the whole database with a backup. Shows the counts first; only --yes does it."""
    import json

    from sqlalchemy.ext.asyncio import AsyncSession

    from oathforge.services import launch

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for name, rows in data["tables"].items():
        print(f"  {name:24} {len(rows)}")
    if not confirm:
        print("nothing restored; repeat with --yes (the current data is replaced)")
        return
    engine = _db()
    try:
        async with AsyncSession(engine) as session:
            await launch.restore(session, data)
            await session.commit()
        print("restored")
    finally:
        await engine.dispose()


async def launch_reset(confirm: bool, backup_path: str | None) -> None:
    """The launch reset: show what goes and what stays; with --yes, back up first, wipe, check, commit."""
    import time

    from sqlalchemy.ext.asyncio import AsyncSession

    from oathforge.services import launch

    engine = _db()
    try:
        async with AsyncSession(engine) as session:
            report = await launch.reset_for_launch(session, apply=False)
            print("goes:")
            for name, n in report.wiped.items():
                print(f"  {name:24} {n}")
            print("stays:")
            for name, n in report.kept.items():
                print(f"  {name:24} {n}")
            if not confirm:
                print("nothing changed; repeat with --yes (a backup is written first)")
                return
            target = (
                Path(backup_path)
                if backup_path
                else _backup_dir() / f"before-launch-{time.strftime('%Y%m%d-%H%M%S')}.json"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(launch.to_json(await launch.dump(session)), encoding="utf-8")
            print(f"backup {target}")
            report = await launch.reset_for_launch(session, apply=True)
            if report.orphans:
                await session.rollback()
                print("left hanging, so nothing was committed:")
                for line in report.orphans:
                    print(f"  {line}")
                sys.exit(1)
            await session.commit()
            print(f"reset done; {report.settings_trimmed} accounts lost their old-game preferences")
            print("restore with: oath restore", target, "--yes")
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
        where = (
            "finished"
            if r.done
            else (
                f"on '{quests[r.current].name.en}' for {r.waiting:.0f} min"
                if r.current
                else "no active tutorial mission"
            )
        )
        print(f"  {r.name:20} level {r.level}  {len(r.minutes)}/{len(tut)} missions in {total:.0f} min · {where}")


def validate_content() -> None:
    """Load content/ like the bot does at startup; print the counts, or the errors and exit 1."""
    from oathforge.content import load_content

    try:
        c = load_content()
    except Exception as exc:  # pydantic, YAML or cross-reference errors: all say what is wrong
        print(f"content/ is invalid:\n{exc}")
        sys.exit(1)
    print(
        f"content/ ok: {len(c.items)} items, {len(c.monsters)} monsters, {len(c.locations)} places, "
        f"{len(c.npcs)} NPCs, {len(c.quests)} quests, {len(c.classes)} classes"
    )


def write_content_index() -> None:
    from oathforge.config import CONTENT_DIR
    from oathforge.content import load_content
    from oathforge.content.index import build_index

    path = CONTENT_DIR / "INDEX.md"
    text = build_index(load_content(), CONTENT_DIR)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        print(f"{path} is up to date")
        return
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {path}")


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
        proc = subprocess.Popen(
            [sys.executable, "-m", "oathforge", "bot"],
            stdout=out,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            **kwargs,
        )
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
    elif command == "balance":
        from oathforge.tools.balance import main as balance

        balance(rest)
    elif command == "achievements-backfill":
        from oathforge.tools.achievements_backfill import main as backfill

        backfill(rest)
    elif command == "validate":
        validate_content()
    elif command == "content-index":
        write_content_index()
    elif command == "new":
        from oathforge.tools.new import main as new

        new(rest)
        validate_content()
        write_content_index()
    elif command == "tutorial-stats":
        asyncio.run(tutorial_stats())
    elif command == "reset-players":
        asyncio.run(reset_players("--yes" in rest))
    elif command == "launch-reset":
        path = rest[rest.index("--backup") + 1] if "--backup" in rest else None
        asyncio.run(launch_reset("--yes" in rest, path))
    elif command == "backup":
        asyncio.run(backup(rest[0] if rest else None))
    elif command == "restore":
        files = [a for a in rest if a != "--yes"]
        if not files:
            print("usage: oath restore FILE [--yes]")
            sys.exit(2)
        asyncio.run(restore(files[0], "--yes" in rest))
    elif command == "delete-player":
        names = [a for a in rest if a != "--yes"]
        asyncio.run(delete_player(" ".join(names) or None, "--yes" in rest))
    else:
        print(f"Unknown command: {command}\n")
        show_help()
        sys.exit(2)
