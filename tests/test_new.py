"""``oath new``: every template makes a sheet that loads, with its image prompts, and no TODO is left in content/."""

import re
import shutil

import pytest

from oathforge.config import CONTENT_DIR
from oathforge.content import load_content
from oathforge.tools.new import TODO, create, style

CASES = [
    ("item", "iron_dagger", {"category": "weapon", "name": "Iron Dagger", "desc": 'A "plain" blade: dull iron.'}),
    ("item", "old_hat", {"category": "armor"}),
    ("item", "grey_rag", {"category": "material"}),
    ("monster", "cave_bear", {"desc": "A bear the size of a cart."}),
    ("npc", "ilda", {"zone": "crownreach"}),
    ("quest", "lost_ledger", {"zone": "crownreach", "giver": "bram"}),
    ("quest", "no_giver", {"zone": "crownreach"}),
    ("zone", "saltmarsh", {"sub_kind": "wilds"}),
    ("place", "old_pier", {"zone": "crownreach", "to": "broken_crown_tavern"}),
    ("class", "mystic", {}),
]


@pytest.fixture
def content(tmp_path):
    root = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, root, ignore=shutil.ignore_patterns("officina", "*.jpg"))
    return root


def test_every_template_makes_sheets_that_load_together(content):
    for kind, key, options in CASES:
        created, note = create(kind, key, content=content, **options)
        assert created and note
        for path in created:
            assert path.is_file() and path.is_relative_to(content)
            assert not re.search(r"__[a-z_]+__", path.read_text(encoding="utf-8")), path  # every marker was filled
    load_content(content)


def test_image_prompts_carry_the_style_and_the_description(content):
    created, _ = create("monster", "cave_bear", content=content, desc="A bear the size of a cart.")
    prompt = content / "monsters" / "cave_bear" / "images" / "portrait.prompt.md"
    assert prompt in created and (prompt.parent / "media.yaml") in created
    suffix, formats = style(content)
    text = prompt.read_text(encoding="utf-8")
    assert "Cave Bear: A bear the size of a cart." in text and suffix in text and formats["portrait"] in text

    create("zone", "saltmarsh", content=content)
    folder = content / "world" / "terra_coronata" / "saltmarsh" / "images"
    night = (folder / "panorama.night.prompt.md").read_text(encoding="utf-8")
    assert "panorama.jpg" in night and "keep the exact composition" in night
    assert TODO in (folder / "panorama.prompt.md").read_text(encoding="utf-8")  # no description given: still to write


def test_a_new_place_gets_its_way_back(content):
    create("place", "old_pier", content=content, zone="crownreach", to="broken_crown_tavern")
    tavern = content / "world/terra_coronata/crownreach/broken_crown_tavern/place.yaml"
    assert "- {to: old_pier, minutes: 5}" in tavern.read_text(encoding="utf-8")
    c = load_content(content)
    assert any(e.to == "old_pier" for e in c.locations["broken_crown_tavern"].exits)


def test_a_zone_goes_next_to_the_others(content):
    create("zone", "saltmarsh", content=content)
    assert (content / "world/terra_coronata/saltmarsh/zone.yaml").is_file()
    with pytest.raises(SystemExit, match="no hub"):
        create("place", "old_pier", content=content, zone="saltmarsh")


@pytest.mark.parametrize(
    ("kind", "key", "options", "message"),
    [
        ("item", "Bad-Id", {"category": "weapon"}, "not a valid id"),
        ("item", "dagger", {"category": "weapon"}, "already exists"),
        ("item", "thing", {}, "needs --category"),
        ("monster", "boar", {}, "already exists"),
        ("npc", "ilda", {}, "needs --zone"),
        ("npc", "ilda", {"zone": "nowhere"}, "unknown zone"),
        ("npc", "ilda", {"zone": "crownreach", "place": "nowhere"}, "not a place"),
        ("quest", "q", {"zone": "crownreach", "giver": "nobody"}, "unknown NPC"),
        ("zone", "z", {"continent": "nowhere"}, "unknown continent"),
        ("zone", "z", {"sub_kind": "wild"}, "--kind"),
        ("class", "paladin", {}, "already exists"),
        ("class", "avenger", {}, "already a branch id"),
    ],
)
def test_bad_requests_say_what_is_wrong(kind, key, options, message):
    """They fail before writing anything, so the real content/ is safe to read here."""
    before = sorted(CONTENT_DIR.rglob("*"))
    with pytest.raises(SystemExit, match=message):
        create(kind, key, content=CONTENT_DIR, **options)
    assert sorted(CONTENT_DIR.rglob("*")) == before


def test_no_pending_todo_is_left_in_content():
    """A sheet made by `oath new` is not done until every TODO(new) is written."""
    pending = [
        path.relative_to(CONTENT_DIR).as_posix()
        for path in [*CONTENT_DIR.rglob("*.yaml"), *CONTENT_DIR.rglob("*.prompt.md")]
        if not {"_templates", "officina"} & set(path.parts) and TODO in path.read_text(encoding="utf-8")
    ]
    assert not pending, pending
