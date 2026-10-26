"""Battle simulator (oathforge.tools.simulate)."""

import json

import pytest

from oathforge import cli
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.services import characters
from oathforge.tools import simulate as sim


def test_every_class_fights_every_monster_to_the_end():
    c = get_content()
    rows = sim.simulate(list(c.classes), list(c.monsters), [1, 5], n=3, seed=0, lineage="human", background="soldier")
    assert len(rows) == 2 * len(c.classes) * len(c.monsters)
    for r in rows:
        assert 0 <= r["win_pct"] <= 100 and 0 <= r["avg_hp_left_pct"] <= 100
        assert r["timeout_pct"] == 0, r
        if c.monsters[r["enemies"]].hp <= 40:  # a creature far above the level may win before a hit lands
            assert r["dmg_per_round"] > 0, r


def test_same_seed_same_numbers():
    def run(seed: int):
        return sim.simulate(
            ["sorcerer"], ["bandit_captain"], [2], n=20, seed=seed, lineage="elf", background="criminal"
        )

    assert run(7) == run(7)
    assert run(7) != run(8)


@pytest.mark.usefixtures("ruins")
def test_abilities_matter():
    with_abilities = sim.simulate(["paladin"], ["test_warden"], [3], 100, 0, "human", "soldier")[0]
    weapons_only = sim.simulate(["paladin"], ["test_warden"], [3], 100, 0, "human", "soldier", False)[0]
    assert with_abilities["win_pct"] > weapons_only["win_pct"]


@pytest.mark.usefixtures("database")
async def test_simulated_hero_matches_a_real_one():
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Sim", "dwarf", "acolyte", "cleric")
        real = await characters.build_combatant(s, char)
    fake, _ = sim.hero("cleric", 1, "dwarf", "acolyte")
    ignore = {"ref", "name"}
    assert fake.model_dump(exclude=ignore) == real.model_dump(exclude=ignore)


def test_cli_writes_results(capsys):
    cli.main(["simulate", "--n", "2", "--classes", "warrior", "--monsters", "boar,cave_bat+cave_bat"])
    out = capsys.readouterr().out
    assert "warrior" in out and "cave_bat+cave_bat" in out
    files = sorted((get_settings().artifacts_dir / "simulations").glob("*.json"))
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    assert [r["enemies"] for r in data["results"]] == ["boar", "cave_bat+cave_bat"]


def test_cli_rejects_unknown_keys():
    with pytest.raises(SystemExit):
        cli.main(["simulate", "--classes", "necromancer"])
