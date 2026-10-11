import re

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
    assert len(c.classes) == 4 and len(c.monsters) == 6 and len(c.items) == 14 and len(c.npcs) == 4


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
