"""Pure condition and content validation boundaries."""

from dataclasses import replace

import pytest
from pydantic import ValidationError

from oathforge.content import get_content
from oathforge.content.achievement_schemas import Achievement, validate_catalog
from oathforge.content.achievement_schemas import AchievementCondition as C
from oathforge.content.loader import _read_file
from oathforge.engine.achievements import advance, progress


def test_counter_threshold_any_and_sequence_boundaries():
    counter = C(kind="counter", event="craft", target=2)
    state = advance(counter, {}, "craft", {})
    assert progress(counter, state) == (1, 2)
    assert progress(counter, advance(counter, state, "craft", {})) == (2, 2)
    assert progress(counter, advance(counter, state, "visit", {})) == (1, 2)
    threshold = C(kind="threshold", event="mastery", field="rank", target=3)
    state = advance(threshold, {}, "mastery", {"rank": 2})
    assert progress(threshold, advance(threshold, state, "mastery", {"rank": 1})) == (2, 3)
    condition = C(kind="any", children=[counter, threshold])
    assert progress(condition, advance(condition, {}, "mastery", {"rank": 3})) == (1, 1)
    condition = get_content().achievements["back_on_feet"].condition
    state = advance(condition, {}, "combat", {"status": "victory", "eligible": True})
    assert progress(condition, state) == (0, 2)
    state = advance(condition, state, "combat", {"status": "defeat"})
    state = advance(condition, state, "combat", {"status": "victory", "eligible": False})
    assert progress(condition, state) == (1, 2)
    assert progress(condition, advance(condition, state, "combat", {"status": "victory", "eligible": True})) == (2, 2)


def test_distinct_ignores_duplicates_and_unrelated_values():
    condition = C(kind="distinct", event="visit", field="location", values=["a", "b"], target=2)
    state = {}
    for value in ["a", "a", "other"]:
        state = advance(condition, state, "visit", {"location": value})
    assert progress(condition, state) == (1, 2)
    assert progress(condition, advance(condition, state, "visit", {"location": "b"})) == (2, 2)


@pytest.mark.parametrize(
    "condition",
    [
        {"kind": "python", "event": "craft"},
        {"kind": "event", "event": "narrator_claim"},
        {"kind": "event", "event": "craft", "match": {"gold": 100}},
        {"kind": "distinct", "event": "craft", "field": "recipe", "values": ["a"], "target": 2},
        {"kind": "all", "children": []},
        {"kind": "threshold", "event": "mastery"},
    ],
)
def test_invalid_conditions_rejected(condition):
    with pytest.raises(ValidationError):
        C.model_validate(condition)


def test_catalog_references_cycles_and_bilingual_text(tmp_path):
    content = get_content()
    assert len(content.achievements) == 36
    assert sum(a.form == "meta" for a in content.achievements.values()) == 2
    assert sum(a.visibility == "hidden" for a in content.achievements.values()) == 2
    assert sum(a.title is not None for a in content.achievements.values()) == 5
    raw = content.achievements["handmade"].model_dump()
    raw["condition"] = {"kind": "event", "event": "craft", "match": {"recipe": "missing"}}
    bad = Achievement.model_validate(raw)
    with pytest.raises(ValueError, match="unknown"):
        validate_catalog(replace(content, achievements={**content.achievements, "handmade": bad}))
    raw["condition"] = {"kind": "event", "event": "unlock", "match": {"key": "handmade"}}
    with pytest.raises(ValueError, match="cyclic"):
        validate_catalog(
            replace(content, achievements={**content.achievements, "handmade": Achievement.model_validate(raw)})
        )
    raw["name"]["es"] = "{missing}"
    with pytest.raises(ValidationError, match="placeholders"):
        Achievement.model_validate(raw)
    path = tmp_path / "duplicate.yaml"
    path.write_text("one: 1\none: 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        _read_file(path)
