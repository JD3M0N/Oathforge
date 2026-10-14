"""Read-only catalog of images found next to the world content.

Convention, no manifest needed: every node folder (continent, zone, location), every
``content/classes/<class>/`` folder (class portraits) and every ``content/monsters/<monster>/``
folder (bestiary illustrations) may have an
``images/`` folder; files are sorted by name and a ``.night`` suffix (``panorama.night.jpg``)
marks the night variant and ``.male`` / ``.female`` (``portrait.female.jpg``) a class
portrait for that gender. Optional ``images/media.yaml`` holds credits and license per file,
and ``<name>.prompt.md`` next to each image the prompt it was generated with.
Telegram ``file_id``s are cached in the database by ``oathforge.services.media``.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
GENDERS = ("male", "female")


@dataclass(frozen=True)
class MediaAsset:
    key: str  # path relative to content/world, with forward slashes; stable id for the file_id cache
    path: Path
    night: bool
    checksum: str  # sha256: replacing the file invalidates the cached file_id
    gender: str | None = None  # male | female; None: fits anyone


@dataclass(frozen=True)
class MediaCatalog:
    zones: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)
    locations: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)
    continents: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)
    classes: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)  # content/classes/<class>/images
    monsters: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)  # content/monsters/<monster>/images

    def zone_images(self, zone: str, night: bool = False) -> list[MediaAsset]:
        return _pick(self.zones.get(zone, ()), night)

    def location_images(self, location: str, night: bool = False) -> list[MediaAsset]:
        return _pick(self.locations.get(location, ()), night)

    def class_images(self, class_key: str, gender: str | None = None) -> list[MediaAsset]:
        """One portrait: the character's gender, else a neutral one, else whatever the class has."""
        assets = self.classes.get(class_key, ())
        for match in ([a for a in assets if gender and a.gender == gender], [a for a in assets if a.gender is None],
                      list(assets)):
            if match:
                return match[:1]
        return []

    def monster_images(self, monster: str) -> list[MediaAsset]:
        return list(self.monsters.get(monster, ()))[:1]


def _pick(assets: tuple[MediaAsset, ...], night: bool) -> list[MediaAsset]:
    """Images for the time of day; falls back to the other variant if there are none."""
    match = [a for a in assets if a.night == night]
    return match or list(assets)


def scan_images(folder: Path, root: Path) -> tuple[MediaAsset, ...]:
    images = folder / "images"
    if not images.is_dir():
        return ()
    files = sorted(p for p in images.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
    credits = images / "media.yaml"
    known = (yaml.safe_load(credits.read_text(encoding="utf-8")) or {}) if credits.is_file() else {}
    for p in files:
        if p.name not in known:
            log.warning("media without credits in %s: %s", credits, p.name)
        if not p.with_name(p.stem + ".prompt.md").is_file():
            log.warning("media without prompt file: %s", p)
    return tuple(
        MediaAsset(
            key=p.relative_to(root).as_posix(),
            path=p,
            night=".night" in p.suffixes,
            gender=next((g for g in GENDERS if f".{g}" in p.suffixes), None),
            checksum=hashlib.sha256(p.read_bytes()).hexdigest(),
        )
        for p in files
    )
