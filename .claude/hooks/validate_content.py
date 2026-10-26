"""PostToolUse hook (Edit|Write): after a change to content/*.yaml, run `oath validate` and refresh content/INDEX.md.

Exit 2 sends the validation errors back to Claude, which then fixes the YAML before going on.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"


def main() -> int:
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path")
    if not path:
        return 0
    path = Path(path).resolve()
    if path.suffix not in (".yaml", ".yml") or not path.is_relative_to(CONTENT) or "officina" in path.parts:
        return 0
    run = lambda cmd: subprocess.run(
        [sys.executable, "-m", "oathforge", cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    result = run("validate")
    if result.returncode != 0:
        print(result.stdout + result.stderr, file=sys.stderr)
        return 2
    run("content-index")
    return 0


if __name__ == "__main__":
    sys.exit(main())
