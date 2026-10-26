"""Invariant 2 of AGENTS.md: only services/ writes state. The import rules live in pyproject.toml (lint-imports);
what an import cannot tell, whether the bot changes a row, is checked here on the syntax tree."""

import ast
from pathlib import Path

BOT = Path(__file__).resolve().parent.parent / "oathforge" / "bot"
WRITES = {"add", "add_all", "delete", "merge"}  # session calls that create or remove rows


def test_the_bot_never_writes_a_model():
    found = []
    for path in sorted(BOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            where = f"{path.relative_to(BOT.parent).as_posix()}:{getattr(node, 'lineno', '?')}"
            targets = node.targets if isinstance(node, ast.Assign) else []
            if isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            for target in targets:
                for attr in ast.walk(target):
                    if (
                        isinstance(attr, ast.Attribute)
                        and isinstance(attr.ctx, ast.Store)
                        and not (isinstance(attr.value, ast.Name) and attr.value.id == "self")
                    ):
                        found.append(f"{where}: {ast.unparse(attr)} = ...")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in WRITES and ast.unparse(node.func.value).endswith("session"):
                    found.append(f"{where}: {ast.unparse(node.func)}(...)")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setattr":
                found.append(f"{where}: setattr(...)")
    assert not found, "the bot changes state itself; call a service instead:\n" + "\n".join(found)
