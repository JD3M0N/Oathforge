"""Console commands: ``oathforge help`` (or ``python -m oathforge help``)."""

import asyncio
import sys

COMMANDS = {
    "help": ("", "muestra esta lista de comandos"),
    "bot": ("", "arranca el bot de Telegram (Ctrl+C para pararlo)"),
    "reset-players": ("[--yes]", "borra todos los jugadores y sus datos para una ronda de pruebas limpia; "
                                 "sin --yes solo muestra qué borraría (para el bot antes)"),
}


def show_help() -> None:
    from oathforge import __version__

    print(f"Oathforge v{__version__}\n\nUso: oathforge <comando>\n")
    width = max(len(f"{name} {args}".strip()) for name, (args, _) in COMMANDS.items())
    for name, (args, text) in COMMANDS.items():
        print(f"  {f'{name} {args}'.strip():<{width}}  {text}")


async def reset_players(confirm: bool) -> None:
    """Delete every player and what they left behind; keeps the schema and ``media_files``.

    Ids keep counting up, so new combats never reuse an old ``artifacts/battles`` file.
    The bot's in-memory state (half-finished character creation) is not in the DB: stop it first.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from oathforge.config import get_settings
    from oathforge.database.models import Base

    url = get_settings().database_url
    tables = [t.name for t in Base.metadata.sorted_tables if t.name != "media_files"]
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            print(f"database: {url.split('@')[-1]}")
            for name in tables:
                count = (await conn.execute(text(f'SELECT count(*) FROM "{name}"'))).scalar()
                print(f"  {name:24} {count}")
            if not confirm:
                print("nothing deleted; run again with --yes")
                return
            for name in reversed(tables):  # children first
                await conn.execute(text(f'DELETE FROM "{name}"'))
            print("deleted")
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else "help"
    if command in ("help", "-h", "--help"):
        show_help()
    elif command == "bot":
        from oathforge.main import main as run_bot

        run_bot()
    elif command == "reset-players":
        asyncio.run(reset_players("--yes" in args[1:]))
    else:
        print(f"Comando desconocido: {command}\n")
        show_help()
        sys.exit(2)
