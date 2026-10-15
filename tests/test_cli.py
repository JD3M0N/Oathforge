"""Console commands."""

import pytest

from oathforge import cli


def test_help_lists_every_command(capsys):
    cli.main(["help"])
    out = capsys.readouterr().out
    assert all(f"oath {name}" in out for name in cli.command_names()) and "--yes" in out
    assert "delete-player" in cli.command_names()


def test_unknown_command_shows_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["nope"])
    assert "reset-players" in capsys.readouterr().out


def test_stop_and_restart(monkeypatch, tmp_path, capsys):
    from oathforge import cli, pidfile
    monkeypatch.setattr(pidfile, "PATH", tmp_path / "bot.pid")
    monkeypatch.setattr(pidfile, "find_running", lambda: [])
    assert cli.stop_bot() is False and "no hay ningún bot" in capsys.readouterr().out
    killed = []
    pidfile.PATH.write_text("4242")
    monkeypatch.setattr(pidfile, "alive", lambda pid: True)
    monkeypatch.setattr(pidfile, "kill", killed.append)
    assert cli.stop_bot() is True and killed == [4242] and not pidfile.PATH.exists()
    started = []
    monkeypatch.setattr("subprocess.Popen", lambda *a, **k: started.append(a[0]) or type("P", (), {"pid": 7})())
    monkeypatch.setattr("time.sleep", lambda s: None)
    monkeypatch.chdir(tmp_path)
    cli.restart_bot()
    assert started and started[0][-2:] == ["oathforge", "bot"] and "PID 7" in capsys.readouterr().out
    assert "restart" in cli.command_names() and "stop" in cli.command_names()
