"""Read-only catalog of images found next to the world content.

Convention, no manifest needed: every node folder (continent, zone, location) may have an
``images/`` folder; files are sorted by name and a ``.night`` suffix (``panorama.night.jpg``)
marks the night variant. Optional ``images/media.yaml`` holds credits and license per file.
Telegram ``file_id``s are cached in the database by ``oathforge.services.media``.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class MediaAsset:
    key: str  # path relative to content/world, with forward slashes; stable id for the file_id cache
    path: Path
    night: bool
    checksum: str  # sha256: replacing the file invalidates the cached file_id


@dataclass(frozen=True)
class MediaCatalog:
    zones: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)
    locations: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)
    continents: dict[str, tuple[MediaAsset, ...]] = field(default_factory=dict)

    def zone_images(self, zone: str, night: bool = False) -> list[MediaAsset]:
        return _pick(self.zones.get(zone, ()), night)

    def location_images(self, location: str, night: bool = False) -> list[MediaAsset]:
        return _pick(self.locations.get(location, ()), night)


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
    return tuple(
        MediaAsset(
            key=p.relative_to(root).as_posix(),
            path=p,
            night=".night" in p.suffixes,
            checksum=hashlib.sha256(p.read_bytes()).hexdigest(),
        )
        for p in files
    )
