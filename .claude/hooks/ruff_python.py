"""PostToolUse hook (Edit|Write): after a change to a .py file, ruff formats it and fixes what it can.

Exit 2 sends what is left (an unused variable, a name shadowed…) back to Claude, which fixes it before going on.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = (".venv", "migrations", "content", "artifacts")  # third-party code, generated migrations, Josue's lab


def main() -> int:
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path")
    if not path:
        return 0
    path = Path(path).resolve()
    if path.suffix != ".py" or not path.is_file() or not path.is_relative_to(ROOT):
        return 0
    if path.relative_to(ROOT).parts[0] in SKIP:
        return 0

    def ruff(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "ruff", *args, str(path)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
        )

    ruff("check", "--fix", "--quiet")
    ruff("format", "--quiet")
    result = ruff("check", "--output-format", "concise", "--quiet")
    if result.returncode != 0:
        print(result.stdout + result.stderr, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
