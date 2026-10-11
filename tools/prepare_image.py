"""Prepares an image for the game: crop to the kind's aspect ratio, resize, strip metadata, save JPEG/PNG.

    .venv\\Scripts\\python tools/prepare_image.py original.png content/world/.../images/panorama.jpg
    .venv\\Scripts\\python tools/prepare_image.py face.png content/npcs/bram/portrait.jpg --kind portrait

Sizes are in planning/audiovisual.md ("Escala de las imágenes"). Requires Pillow (dev extra).
"""

import argparse
from pathlib import Path

from PIL import Image, ImageOps

KINDS = {  # kind -> (width, height); delivery size, Telegram keeps at most 1280 px on the long side
    "panorama": (1280, 720),
    "portrait": (768, 1024),
    "icon": (128, 128),
    "sticker": (512, 512),
}


def prepare(src: Path, dst: Path, kind: str = "panorama") -> tuple[int, int]:
    size = KINDS[kind]
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        out = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() == ".png":
        out.save(dst, "PNG", optimize=True)
    else:
        out.convert("RGB").save(dst, "JPEG", quality=85, progressive=True, optimize=True)
    return out.size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src", type=Path)
    parser.add_argument("dst", type=Path)
    parser.add_argument("--kind", choices=sorted(KINDS), default="panorama")
    args = parser.parse_args()
    w, h = prepare(args.src, args.dst, args.kind)
    print(f"{args.dst}: {w}x{h}, {args.dst.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
