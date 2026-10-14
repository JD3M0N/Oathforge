"""Console commands: ``oath help`` (also ``oathforge help`` or ``python -m oathforge help``)."""

import asyncio
import shutil
import sys
import textwrap

# (group, [(command, arguments, one-line description)]); every command here must be handled in main().
COMMANDS = [
    ("Bot", [
        ("bot", "", "Arranca el bot (Ctrl+C para pararlo)."),
    ]),
    ("Jugadores", [
        ("delete-player", "[id|nombre] [--yes]", "Borra un jugador; sin nombre, los lista."),
        ("reset-players", "[--yes]", "Borra todos los jugadores (detén el bot)."),
    ]),
    ("Pruebas", [
        ("tgtest", "send|press|show|login", "Juega con el bot desde la cuenta de prueba."),
        ("simulate", "[--level 1-5]", "Simula combates para el balance (--help)."),
    ]),
    ("Ayuda", [
        ("help", "", "Muestra esta ayuda."),
    ]),
]
FOOTER = "Los comandos que borran solo muestran qué borrarían hasta que añades --yes."
COLUMN = 36  # where descriptions start


def command_names() -> list[str]:
    return [name for _, cmds in COMMANDS for name, _, _ in cmds]


def show_help() -> None:
    from oathforge import __version__

    width = max(60, min(shutil.get_terminal_size().columns, 100))
    indent = " " * COLUMN
    print(f"Oathforge v{__version__}  ·  Uso: oath <comando>")
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
                print("no se ha borrado nada; repite con --yes")
                return
            for name in reversed(tables):  # children first
                await conn.execute(text(f'DELETE FROM "{name}"'))
            print("borrado")
    finally:
        await engine.dispose()


def _player_line(p) -> str:
    who = f"{p.name} ({p.class_key}, nivel {p.level})" if p.name else "(sin personaje)"
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
                print(f"{len(players)} jugadores:" if players else "no hay jugadores")
                for p in players:
                    print(_player_line(p))
                if players:
                    print("borra uno con: oath delete-player <id|nombre> --yes")
                return
            found = await admin.find_players(session, query)
            if not found:
                print(f"ningún jugador con id o nombre «{query}»; oath delete-player los lista")
                return
            if len(found) > 1:
                print(f"hay {len(found)} jugadores llamados «{query}»; usa su id de Telegram:")
                for p in found:
                    print(_player_line(p))
                return
            print(_player_line(found[0]))
            counts = await admin.delete_player(session, found[0].user_id)
            for name, n in counts.items():
                print(f"  {name:24} {n}")
            if not confirm:
                print("no se ha borrado nada; repite con --yes")
                return
            await session.commit()
            print("borrado; si el bot está en marcha, el jugador empieza de cero con /start")
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else "help"
    rest = args[1:]
    if command in ("help", "-h", "--help"):
        show_help()
    elif command == "bot":
        from oathforge.main import main as run_bot

        run_bot()
    elif command == "tgtest":
        from oathforge.tools.tgtest import main as tgtest

        tgtest(rest)
    elif command == "simulate":
        from oathforge.tools.simulate import main as simulate

        simulate(rest)
    elif command == "reset-players":
        asyncio.run(reset_players("--yes" in rest))
    elif command == "delete-player":
        names = [a for a in rest if a != "--yes"]
        asyncio.run(delete_player(" ".join(names) or None, "--yes" in rest))
    else:
        print(f"Comando desconocido: {command}\n")
        show_help()
        sys.exit(2)
