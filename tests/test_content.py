import re

import yaml

from oathforge.content import load_content
from oathforge.content.schemas import Text
from oathforge.i18n import translator


def walk_texts(obj):
    if isinstance(obj, Text):
        yield obj
    elif hasattr(type(obj), "model_fields") and not isinstance(obj, type):
        for name in type(obj).model_fields:
            yield from walk_texts(getattr(obj, name))
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_texts(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from walk_texts(v)


def test_content_loads_and_references_resolve():
    c = load_content()
    assert c.start_location in c.locations
    assert c.respawn_location in c.locations
    assert len(c.classes) == 8 and len(c.monsters) == 10 and len(c.items) == 62 and len(c.npcs) == 5


def test_every_text_has_both_languages():
    c = load_content()
    for field in c.__dataclass_fields__:
        for text in walk_texts(getattr(c, field)):
            assert text.es.strip() and text.en.strip()


def test_locales_have_same_keys_and_placeholders():
    es, en = translator.flat("es"), translator.flat("en")
    assert set(es) == set(en), set(es) ^ set(en)
    ph = re.compile(r"\{(\w+)")
    for key in es:
        assert set(ph.findall(es[key])) == set(ph.findall(en[key])), key


def test_every_location_reachable_from_start():
    c = load_content()
    seen, todo = set(), [c.start_location]
    while todo:
        loc = todo.pop()
        if loc in seen:
            continue
        seen.add(loc)
        todo += [e.to for e in c.locations[loc].exits]
    assert seen == set(c.locations)


def test_every_static_key_in_code_exists():
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "oathforge"
    pat = re.compile(r"""(?:t\(\w+, |\.add\(|refused\(|key=|_both\(|CombatError\()"([a-z_]+\.[a-z_.]+)\"""")
    keys = set()
    for path in root.rglob("*.py"):
        keys |= set(pat.findall(path.read_text(encoding="utf-8")))
    dynamic = {f"combat.end.{s}" for s in ("victory", "defeat", "fled")} | {"btn.move_back", "btn.move_front"}
    keys = {k for k in keys if not k.endswith(("_", "."))}  # prefixes of dynamic keys
    missing = sorted(k for k in keys | dynamic if k not in translator.flat("es"))
    assert not missing, missing
    assert len(keys) > 100


def test_world_hierarchy():
    c = load_content()
    assert "terra_coronata" in c.continents
    assert c.zones["crownreach"].kind == "city"
    for key, loc in c.locations.items():
        assert loc.zone in c.zones and loc.continent in c.continents, key
    hubs = [k for k, loc in c.locations.items() if loc.hub]
    assert hubs == ["crownreach_plaza"]
    assert c.locations["broken_crown_tavern"].zone == "crownreach"
    assert c.locations["crypt_sanctum"].zone == "sunken_crypt"


def test_media_catalog_finds_city_panorama_and_falls_back_at_night():
    c = load_content()
    day = c.media.zone_images("crownreach", night=False)
    assert [a.key for a in day] == ["terra_coronata/crownreach/images/panorama.jpg"]
    assert day[0].path.is_file() and len(day[0].checksum) == 64
    assert c.media.zone_images("crownreach", night=True) == day  # no night variant yet
    assert c.media.zone_images("thornwood") == []


def test_night_variant_and_duplicate_ids(tmp_path):
    import shutil

    import pytest

    from oathforge.config import CONTENT_DIR
    from oathforge.content.loader import load_world

    shutil.copytree(CONTENT_DIR / "world", tmp_path / "world")
    images = tmp_path / "world/terra_coronata/crownreach/images"
    shutil.copy(images / "panorama.jpg", images / "panorama.night.jpg")
    world = load_world(tmp_path)
    assert [a.night for a in world.media.zone_images("crownreach", night=True)] == [True]
    assert [a.night for a in world.media.zone_images("crownreach", night=False)] == [False]

    shutil.copytree(tmp_path / "world/terra_coronata/crownreach/crownreach_market",
                    tmp_path / "world/terra_coronata/thornwood/crownreach_market")
    with pytest.raises(ValueError, match="duplicate location 'crownreach_market'"):
        load_world(tmp_path)


def test_class_portraits_and_unknown_class_folder(tmp_path):
    import shutil

    import pytest

    from oathforge.config import CONTENT_DIR
    from oathforge.content.loader import scan_keyed_media
    from oathforge.content.media import MediaCatalog

    c = load_content()
    portrait = "classes/{}/images/portrait.{}.jpg"
    for cls in c.classes:  # every class has a man and a woman
        for gender in ("male", "female"):
            assert [a.key for a in c.media.class_images(cls, gender)] == [portrait.format(cls, gender)]
    assert [a.key for a in c.media.class_images("warlock")] == [portrait.format("warlock", "female")]  # no gender: first

    shutil.copytree(CONTENT_DIR / "classes", tmp_path / "classes")
    (tmp_path / "classes/necromancer").mkdir()
    with pytest.raises(ValueError, match="necromancer"):
        scan_keyed_media(tmp_path, "classes", c.classes, MediaCatalog().classes)


def test_monster_art_icons_and_prompt_files(tmp_path):
    import shutil

    import pytest

    from oathforge.config import CONTENT_DIR
    from oathforge.content.loader import scan_keyed_media
    from oathforge.content.media import IMAGE_SUFFIXES, MediaCatalog

    c = load_content()
    for key, m in c.monsters.items():  # every creature: its own icon and its illustration
        assert [a.key for a in c.media.monster_images(key)] == [f"monsters/{key}/images/portrait.jpg"]
        assert m.icon
    icons = [m.icon for m in c.monsters.values()]
    assert len(set(icons)) == len(icons)
    assert c.media.monster_images("dragon") == []

    for img in CONTENT_DIR.rglob("images/*"):  # credits and the prompt it was made with, next to every image
        if img.suffix.lower() in IMAGE_SUFFIXES:
            credits = yaml.safe_load((img.parent / "media.yaml").read_text(encoding="utf-8"))
            assert img.name in credits, img
            assert img.with_name(img.stem + ".prompt.md").is_file(), img

    shutil.copytree(CONTENT_DIR / "monsters", tmp_path / "monsters")
    (tmp_path / "monsters/dragon").mkdir()
    with pytest.raises(ValueError, match="dragon"):
        scan_keyed_media(tmp_path, "monsters", c.monsters, MediaCatalog().monsters)
