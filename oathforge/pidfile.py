"""The running bot's PID in .run/bot.pid, for `oath stop` and `oath restart`."""

import os
import subprocess
import sys
from pathlib import Path

PATH = Path(".run") / "bot.pid"


def write() -> None:
    PATH.parent.mkdir(exist_ok=True)
    PATH.write_text(str(os.getpid()), encoding="utf-8")


def remove() -> None:
    if read() == os.getpid():
        PATH.unlink(missing_ok=True)


def read() -> int | None:
    try:
        return int(PATH.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def alive(pid: int) -> bool:
    """Whether that process still runs (a stale file after a crash points to nothing)."""
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


BOT_COMMAND = r"""(oath|oathforge)(\.exe)?["']?\s+bot\b|-m\s+oathforge\s+bot\b"""


def find_running() -> list[int]:
    """Bots running without a PID file (started before v0.7.27, or by hand): by their command line."""
    import re

    me = os.getpid()
    if sys.platform == "win32":
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            'Get-CimInstance Win32_Process | ForEach-Object { "$($_.ProcessId)`t$($_.CommandLine)" }',
        ]
    else:
        cmd = ["ps", "-eo", "pid=,args="]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    pids = []
    for line in out.splitlines():
        pid, _, args = line.strip().partition("	" if sys.platform == "win32" else " ")
        if pid.isdigit() and int(pid) != me and re.search(BOT_COMMAND, args) and "restart" not in args:
            pids.append(int(pid))
    return pids


def kill(pid: int) -> None:
    if sys.platform == "win32":  # the whole tree: the oath.exe launcher and its python
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        os.kill(pid, 15)
