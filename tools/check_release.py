"""Versioning rules of AGENTS.md, checked before each commit (pre-commit runs it; see .pre-commit-config.yaml).

    .venv\\Scripts\\python tools/check_release.py                  # staged changes: version bumped + CHANGELOG entry
    .venv\\Scripts\\python tools/check_release.py --msg <file>     # the subject starts with "vX.Y.Z: "

A merge commit is not checked: the version came with the merged work.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r'__version__ = "(\d+)\.(\d+)\.(\d+)"')


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def version(text: str) -> tuple[int, int, int] | None:
    m = VERSION.search(text)
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


def staged_version() -> tuple[int, int, int] | None:
    return version(git("show", ":oathforge/__init__.py"))


def check_staged() -> list[str]:
    if not git("diff", "--cached", "--name-only").strip():
        return []
    new, old = staged_version(), version(git("show", "HEAD:oathforge/__init__.py"))
    if new is None:
        return ["oathforge/__init__.py: no __version__"]
    if old is not None and new <= old:
        return [f"the version did not go up ({'.'.join(map(str, old))}): bump it in oathforge/__init__.py"]
    tag = ".".join(map(str, new))
    changelog = git("show", ":CHANGELOG.md")
    top = re.search(r"^## \[([^\]]+)\]", changelog, re.M)
    if top is None or top[1] != tag:
        return [f"CHANGELOG.md: the first entry must be ## [{tag}] (found {top[1] if top else 'none'})"]
    return []


def check_message(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    subject = lines[0] if lines else ""
    if subject.startswith(("Merge ", "Revert ", "fixup!", "squash!")):
        return []
    new = staged_version()
    tag = ".".join(map(str, new)) if new else "?"
    if not subject.startswith(f"v{tag}: "):
        return [f'the subject must start with "v{tag}: " (it is "{subject}")']
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--msg", type=Path, help="commit message file (commit-msg stage)")
    args = parser.parse_args()
    if (ROOT / ".git" / "MERGE_HEAD").exists():
        return 0
    errors = check_message(args.msg) if args.msg else check_staged()
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
