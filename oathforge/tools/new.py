"""``oath new <type> <id>``: a content folder from ``content/_templates/``, with its image prompts already written.

    oath new item iron_dagger --category weapon --name "Iron Dagger" --desc "A plain blade of dull iron."
    oath new monster cave_bear
    oath new npc ilda --zone crownreach [--place broken_crown_tavern]
    oath new quest lost_ledger --zone crownreach [--giver bram]
    oath new zone saltmarsh [--continent terra_coronata] [--kind wilds]
    oath new place old_pier --zone saltmarsh [--to saltmarsh_square]
    oath new class mystic

The templates are valid sheets: whatever is still to write carries the ``TODO(new)`` mark, and ``tests/test_content.py``
fails while one is left in ``content/``. The image prompts join the description with ``prompts/style.md``.
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import yaml

from oathforge.config import CONTENT_DIR

TODO = "TODO(new)"
ID = re.compile(r"[a-z0-9_]+")
TYPES = ("item", "monster", "npc", "quest", "zone", "place", "class")
CATEGORIES = ("weapon", "armor", "shield", "consumable", "tool", "quest", "material", "trinket")  # blueprint: by hand
# what the validation asks of a category; the other categories need nothing
REQUIRED = {
    "weapon": ["slot: main_hand", "weapon: {damage: 1d4, damage_type: slashing}"],
    "armor": ["slot: body", "base_ac: 11"],
    "shield": ["slot: off_hand", "ac_bonus: 1"],
}
KINDS = {"zone": ("city", "wilds", "dungeon"), "place": ("city", "wild", "dungeon")}
ZONE_TO_PLACE_KIND = {"city": "city", "wilds": "wild", "dungeon": "dungeon"}
# type -> images to prompt: (file, prompt format, template); the night variant starts from the day image
IMAGES = {
    "item": [("icon.jpg", "icon", "prompt")],
    "monster": [("portrait.jpg", "portrait", "prompt")],
    "class": [("portrait.male.jpg", "portrait", "prompt"), ("portrait.female.jpg", "portrait", "prompt")],
    "zone": [("panorama.jpg", "panorama", "prompt"), ("panorama.night.jpg", "panorama", "night")],
    "place": [("panorama.jpg", "panorama", "prompt"), ("panorama.night.jpg", "panorama", "night")],
}
WHAT = {
    "item": "Prompt del icono de `{id}`.",
    "monster": "Prompt del retrato de `{id}`.",
    "class": "Prompt del retrato de la clase `{id}`; es el mismo para el de hombre y el de mujer (anota lo que añadas).",
    "zone": "Prompt de la panorámica de día de la zona `{id}`.",
    "place": "Prompt de la panorámica de día del lugar `{id}`.",
}
MEDIA_HEADER = "# Créditos y licencia de cada archivo de esta carpeta (planning/ars.md §Licencias).\n"
SUBJECT_HINT = f"{TODO}: what it is and from where it is seen, concrete details, one sentence of light"
NEXT = {
    "item": "Decide nivel y precio (`oath balance`) y de dónde sale: tienda, botín, receta, recolección o misión.",
    "monster": "Colócala en `encounters` de algún lugar, dale botín y mídela con `oath simulate --level 1-5`.",
    "npc": "Escribe su ficha en inglés y español, y sus tiendas si las tiene; los 12 respaldos están en dialogue.fallback.yaml.",
    "quest": "Ajusta objetivos y recompensas; si tiene entrega, añade `turn_in_stage` y la etapa `ready`.",
    "zone": "Crea sus lugares con `oath new place <id> --zone {id}` (uno con `hub: true`) y su panorámica.",
    "place": "Revisa las salidas (la vuelta ya está en {to}) y coloca encuentros, recolección o estaciones.",
    "class": "Falta su barra de recurso (si la tiene), la progresión 1-20 y el entrenamiento: skill new-class.",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _fill(text: str, values: dict[str, str | None], escape: bool) -> str:
    """Replace ``__key__`` with its value; a line whose value is None is dropped (an optional field)."""
    out = []
    for line in text.splitlines():
        if any(f"__{k}__" in line and v is None for k, v in values.items()):
            continue
        for key, value in values.items():
            if value is not None:
                line = line.replace(f"__{key}__", json.dumps(value, ensure_ascii=False)[1:-1] if escape else value)
        out.append(line)
    return "\n".join(out) + "\n"


def style(content: Path) -> tuple[str, dict[str, str]]:
    """The common suffix and the format sentence per image kind, from ``_templates/prompts/style.md``."""
    text = _text(content / "_templates" / "prompts" / "style.md")
    suffix = re.search(r"```text\n(.+?)\n```", text, re.S)
    assert suffix, "style.md needs a ```text block"
    return suffix.group(1).strip(), dict(re.findall(r"^- (\w+): (.+)$", text, re.M))


def _find(content: Path, pattern: str) -> list[Path]:
    return sorted(content.glob(pattern))


def _exists(content: Path, kind: str, key: str) -> Path | None:
    pattern = {
        "item": f"items/*/{key}",
        "monster": f"monsters/{key}",
        "npc": f"world/*/*/npcs/{key}",
        "quest": f"world/*/*/quests/{key}.yaml",
        "zone": f"world/*/{key}",
        "place": f"world/*/*/{key}/place.yaml",
        "class": f"classes/{key}",
    }[kind]
    return next(iter(_find(content, pattern)), None)


def _zone(content: Path, key: str) -> tuple[Path, dict]:
    found = _find(content, f"world/*/{key}/zone.yaml")
    if not found:
        zones = ", ".join(p.parent.name for p in _find(content, "world/*/*/zone.yaml"))
        raise SystemExit(f"unknown zone '{key}' (zones: {zones})")
    return found[0].parent, yaml.safe_load(_text(found[0]))


def _hub(zone_dir: Path) -> str | None:
    for path in sorted(zone_dir.glob("*/place.yaml")):
        if (yaml.safe_load(_text(path)) or {}).get("hub"):
            return path.parent.name
    return None


def _place(zone_dir: Path, key: str | None, option: str) -> str:
    """The place an NPC or a quest starts at, or the one a new place connects to: the given one, else the hub."""
    if key:
        if not (zone_dir / key / "place.yaml").is_file():
            raise SystemExit(f"'{key}' is not a place of {zone_dir.name}")
        return key
    hub = _hub(zone_dir)
    if not hub:
        raise SystemExit(f"{zone_dir.name} has no hub place (hub: true): pass {option}")
    return hub


def _add_return_exit(place_file: Path, to: str) -> bool:
    """Append ``- {to: <to>, minutes: 5}`` to the block list of ``exits`` in ``place_file``; False if it has another shape."""
    lines = _text(place_file).splitlines()
    start = next((i for i, line in enumerate(lines) if line.rstrip() == "exits:"), None)
    if start is None:
        return False
    last = start
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("  - "):
            last = i
        elif lines[i].startswith((" ", "#")) or not lines[i].strip():
            continue
        else:
            break
    if last == start:
        return False
    lines.insert(last + 1, f"  - {{to: {to}, minutes: 5}}")
    _write(place_file, "\n".join(lines) + "\n")
    return True


def create(
    kind: str,
    key: str,
    *,
    content: Path = CONTENT_DIR,
    zone: str | None = None,
    category: str | None = None,
    continent: str = "terra_coronata",
    sub_kind: str | None = None,
    place: str | None = None,
    giver: str | None = None,
    to: str | None = None,
    name: str | None = None,
    desc: str | None = None,
    today: datetime.date | None = None,
) -> tuple[list[Path], str]:
    """Create the folder of a new ``kind`` and return the files written and the note on what to do next."""
    if not ID.fullmatch(key):
        raise SystemExit(f"'{key}' is not a valid id: lowercase ASCII letters, digits and '_'")
    if found := _exists(content, kind, key):
        raise SystemExit(f"{kind} '{key}' already exists: {found.relative_to(content).as_posix()}")
    if kind == "item" and category not in CATEGORIES:
        raise SystemExit(f"oath new item needs --category: {', '.join(CATEGORIES)}")
    if kind == "class":
        if any(key in (yaml.safe_load(_text(p)) or {}) for p in _find(content, "classes/*/specializations.yaml")):
            raise SystemExit(f"'{key}' is already a branch id")

    zone_dir, zone_data = None, {}
    if kind in ("npc", "quest", "place"):
        if not zone:
            raise SystemExit(f"oath new {kind} needs --zone")
        zone_dir, zone_data = _zone(content, zone)
    if sub_kind and sub_kind not in KINDS.get(kind, ()):
        raise SystemExit(f"--kind for a {kind}: {', '.join(KINDS.get(kind, ()))}")
    if kind == "place":
        assert zone_dir
        sub_kind = sub_kind or ZONE_TO_PLACE_KIND[zone_data["kind"]]
        to = _place(zone_dir, to, "--to")
    elif kind == "zone":
        sub_kind = sub_kind or "city"
        if not _find(content, f"world/{continent}/continent.yaml"):
            raise SystemExit(f"unknown continent '{continent}'")
    elif kind in ("npc", "quest"):
        assert zone_dir
        place = _place(zone_dir, place, "--place")
    if giver and not _find(content, f"world/*/*/npcs/{giver}/npc.yaml"):
        raise SystemExit(f"unknown NPC '{giver}'")

    title = name or key.replace("_", " ").title()
    values: dict[str, str | None] = {
        "id": key,
        "name": title,
        "name_lower": title.lower(),
        "description": desc or TODO,
        "category": category,
        "kind": sub_kind,
        "place": place,
        "giver": giver if kind == "quest" else None,
        "to": to,
    }
    target = {
        "item": content / "items" / str(category) / key,
        "monster": content / "monsters" / key,
        "npc": zone_dir / "npcs" / key if zone_dir else content,
        "quest": zone_dir / "quests" if zone_dir else content,
        "zone": content / "world" / continent / key,
        "place": zone_dir / key if zone_dir else content,
        "class": content / "classes" / key,
    }[kind]
    created: list[Path] = []
    for template in sorted((content / "_templates" / kind).iterdir()):
        dest = target / f"{key}.yaml" if kind == "quest" else target / template.name
        lines = _fill(_text(template), values, escape=True).splitlines()
        if "__required__" in lines:  # the item's category asks for a few fields
            i = lines.index("__required__")
            lines[i : i + 1] = REQUIRED.get(str(category), [])
        _write(dest, "\n".join(lines) + "\n")
        created.append(dest)

    suffix, formats = style(content)
    date = (today or datetime.date.today()).isoformat()
    images = IMAGES.get(kind, [])
    for file, fmt, skeleton in images:
        subject = f"{title}: {desc}" if desc else f"{title}. {SUBJECT_HINT}"
        prompt = f"{subject.rstrip('.')}. {formats[fmt]} {suffix}"
        text = _text(content / "_templates" / "prompts" / f"{skeleton}.md")
        extra = {
            "file": file,
            "kind": fmt,
            "what": WHAT.get(kind, "").format(id=key),
            "day": file.replace(".night", ""),
            "date": date,
            "prompt": prompt,
        }
        path = target / "images" / (Path(file).stem + ".prompt.md")
        _write(path, _fill(text, extra, escape=False))
        created.append(path)
    if images:
        _write(
            target / "images" / "media.yaml",
            MEDIA_HEADER
            + "".join(f"# {f}:\n#   author:\n#   source:\n#   license:\n#   notes:\n" for f, _, _ in images),
        )
        created.append(target / "images" / "media.yaml")

    note = NEXT[kind].format(id=key, to=to)
    if kind == "place":
        assert zone_dir and to
        if not _add_return_exit(zone_dir / to / "place.yaml", key):
            note = f"Añade la vuelta en {to}: `- {{to: {key}, minutes: 5}}`. " + note
    return created, note


def main(argv: list[str]) -> list[Path]:
    parser = argparse.ArgumentParser(prog="oath new", description="Create content from content/_templates/.")
    parser.add_argument("type", choices=TYPES)
    parser.add_argument("id")
    parser.add_argument("--zone", help="npc, quest and place: the zone it belongs to")
    parser.add_argument("--category", help=f"item: {', '.join(CATEGORIES)}")
    parser.add_argument("--continent", default="terra_coronata", help="zone: the continent folder")
    parser.add_argument("--kind", dest="sub_kind", help="zone: city, wilds, dungeon · place: city, wild, dungeon")
    parser.add_argument("--place", help="npc and quest: where it starts (default: the zone's hub)")
    parser.add_argument("--giver", help="quest: the NPC who gives it")
    parser.add_argument("--to", help="place: the place it connects to (default: the zone's hub)")
    parser.add_argument("--name", help="English name")
    parser.add_argument("--desc", help="English description (also goes into the image prompt)")
    args = parser.parse_args(argv)
    created, note = create(
        args.type,
        args.id,
        zone=args.zone,
        category=args.category,
        continent=args.continent,
        sub_kind=args.sub_kind,
        place=args.place,
        giver=args.giver,
        to=args.to,
        name=args.name,
        desc=args.desc,
    )
    for path in created:
        print(f"created {path.relative_to(CONTENT_DIR).as_posix()}")
    print(f"\nPending: every {TODO} in those files. {note}", file=sys.stdout)
    return created
