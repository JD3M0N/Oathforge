"""No file grows past what an agent (or a person) can read in one go: split it before it does."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 800  # per .py file in oathforge/ and tests/
MAX_YAML = 40 * 1024  # per .yaml file in content/ and the locales
# still too big, each with its way out; take a file off the list the day it shrinks
BIG_YAML = {
    "content/classes.yaml",  # structura phase 1: content/classes/<class>/class.yaml
    "content/class_specializations.yaml",  # structura phase 1: content/classes/<class>/specializations.yaml
    "content/quests.yaml",  # structura phase 1: world/<cont>/<zone>/quests/<quest>.yaml
    "content/fallbacks/chronicles.yaml",  # 12 texts per outcome and language: one file per mastery
    "oathforge/i18n/locales/es.yaml",  # structura phase 1: locales/es/<domain>.yaml
    "oathforge/i18n/locales/en.yaml",  # structura phase 1: locales/en/<domain>.yaml
}


def test_python_files_stay_short():
    long = {}
    for path in [*(ROOT / "oathforge").rglob("*.py"), *(ROOT / "tests").rglob("*.py")]:
        with open(path, encoding="utf-8") as fh:
            n = sum(1 for _ in fh)
        if n > MAX_LINES:
            long[path.relative_to(ROOT).as_posix()] = n
    assert not long, f"split these into a package (see planning/structura.md, phase 2): {long}"


def test_yaml_files_stay_small():
    paths = [p for p in (ROOT / "content").rglob("*.yaml") if "officina" not in p.parts]
    paths += (ROOT / "oathforge" / "i18n").rglob("*.yaml")
    sizes = {p.relative_to(ROOT).as_posix(): p.stat().st_size for p in paths}
    big = {k: v for k, v in sizes.items() if v > MAX_YAML and k not in BIG_YAML}
    assert not big, f"split these into one file per entity or domain: {big}"
    shrunk = sorted(k for k in BIG_YAML if sizes.get(k, 0) <= MAX_YAML)
    assert not shrunk, f"take these off BIG_YAML, they fit now: {shrunk}"
