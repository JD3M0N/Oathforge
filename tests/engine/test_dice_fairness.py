"""Statistical checks that the dice are fair.

Seeded tests are deterministic, so they never fail by chance; the threshold is the chi-square
critical value at p = 0.001. The unseeded test uses the production RNG with a looser p ~ 1e-6.
"""

import random
from collections import Counter

import pytest

from oathforge.bot.handlers.common import rng as production_rng
from oathforge.engine import dice

N = 200_000
SEEDS = (0, 1, 2)
# chi-square critical values at p = 0.001, by degrees of freedom
CHI2_001 = {5: 20.52, 10: 29.59, 19: 43.82}
CHI2_1E6_DF19 = 64.0


def chi2(counts: Counter, expected: dict[int, float]) -> float:
    return sum((counts.get(k, 0) - e) ** 2 / e for k, e in expected.items())


def uniform(n: int, sides: int) -> dict[int, float]:
    return {k: n / sides for k in range(1, sides + 1)}


def rolls(seed: int, **kw) -> Counter:
    r = random.Random(seed)
    return Counter(dice.d20(r, **kw).kept for _ in range(N))


@pytest.mark.parametrize("seed", SEEDS)
def test_d20_is_uniform(seed):
    counts = rolls(seed)
    assert set(counts) == set(range(1, 21))
    assert chi2(counts, uniform(N, 20)) < CHI2_001[19]


@pytest.mark.parametrize("seed", SEEDS)
def test_natural_20_and_1_are_five_percent(seed):
    counts = rolls(seed)
    assert abs(counts[20] / N - 0.05) < 0.003
    assert abs(counts[1] / N - 0.05) < 0.003


def test_d20_mean():
    r = random.Random(0)
    mean = sum(dice.d20(r).kept for _ in range(N)) / N
    assert abs(mean - 10.5) < 0.05


@pytest.mark.parametrize("seed", SEEDS)
def test_advantage_and_disadvantage_follow_max_and_min_of_two(seed):
    # P(max of 2d20 = k) = (2k - 1) / 400; P(min = k) = (41 - 2k) / 400
    adv, dis = rolls(seed, advantage=True), rolls(seed + 100, disadvantage=True)
    assert chi2(adv, {k: N * (2 * k - 1) / 400 for k in range(1, 21)}) < CHI2_001[19]
    assert chi2(dis, {k: N * (41 - 2 * k) / 400 for k in range(1, 21)}) < CHI2_001[19]
    assert abs(sum(k * v for k, v in adv.items()) / N - 13.825) < 0.05
    assert abs(sum(k * v for k, v in dis.items()) / N - 7.175) < 0.05


def test_damage_dice_distributions():
    r = random.Random(0)
    d6 = Counter(dice.roll("1d6", r).total for _ in range(N))
    assert chi2(d6, uniform(N, 6)) < CHI2_001[5]
    two_d6 = Counter(dice.roll("2d6", r).total for _ in range(N))
    expected = {s: N * (6 - abs(s - 7)) / 36 for s in range(2, 13)}
    assert chi2(two_d6, expected) < CHI2_001[10]


def test_production_rng_is_uniform():
    r = production_rng()
    counts = Counter(dice.d20(r).kept for _ in range(N))
    assert chi2(counts, uniform(N, 20)) < CHI2_1E6_DF19
