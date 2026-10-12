from oathforge.content import get_content
from oathforge.engine import pointbuy


def test_every_class_array_is_a_legal_27_point_buy():
    for key, cls in get_content().classes.items():
        assert pointbuy.valid(cls.array), key
        assert pointbuy.spent(cls.array) == pointbuy.BUDGET, key


def test_costs_and_limits():
    scores = pointbuy.base()
    assert pointbuy.left(scores) == 27
    assert not pointbuy.can_lower(scores, "str")
    for _ in range(7):
        scores = pointbuy.change(scores, "str", +1)
    assert scores["str"] == 15 and pointbuy.left(scores) == 18
    assert not pointbuy.can_raise(scores, "str")
    assert pointbuy.change(scores, "str", +1) == scores  # capped at 15
    scores = pointbuy.change(scores, "str", -1)
    assert scores["str"] == 14 and pointbuy.left(scores) == 20  # 14 -> 15 costs 2


def test_cannot_overspend():
    scores = {"str": 15, "dex": 15, "con": 15, "int": 8, "wis": 8, "cha": 8}
    assert pointbuy.left(scores) == 0
    assert not pointbuy.can_raise(scores, "int")
    assert pointbuy.change(scores, "int", +1) == scores
    assert not pointbuy.valid({**scores, "int": 9})
    assert not pointbuy.valid({**scores, "str": 16})
    assert not pointbuy.change(scores, "luck", +1) != scores
