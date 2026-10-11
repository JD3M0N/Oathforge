"""Console commands."""

import pytest

from oathforge import cli


def test_help_lists_every_command(capsys):
    cli.main(["help"])
    out = capsys.readouterr().out
    assert all(name in out for name in cli.COMMANDS) and "--yes" in out


def test_unknown_command_shows_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["nope"])
    assert "reset-players" in capsys.readouterr().out
