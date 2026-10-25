"""Mission objectives that come from a service doing something: equip, buy, sell, stash and take."""

import pytest
from sqlalchemy import select

from oathforge.content import get_content
from oathforge.content.schemas import Quest
from oathforge.database.models import ItemInstance
from oathforge.database.session import session_scope
from oathforge.services import characters, home, inventory, quests
from oathforge.services.events import Outcome

pytestmark = pytest.mark.asyncio


@pytest.fixture
def chores(monkeypatch):
    quest = Quest.model_validate({
        "order": 99, "giver": "bram", "name": {"es": "Tareas", "en": "Chores"},
        "summary": {"es": "-", "en": "-"}, "start_stage": "active", "objective_stage": "active",
        "complete_stage": "done", "rewards": [{"xp": 10}],
        "objectives": [{"kind": "buy", "target": "healing_potion"},
                       {"kind": "sell", "target": "any"},
                       {"kind": "equip", "target": "any"},
                       {"kind": "stash", "target": "any"},
                       {"kind": "take", "target": "any"}],
        "stages": {"active": {"journal": {"es": "-", "en": "-"}},
                   "done": {"state": "completed", "journal": {"es": "Hecho.", "en": "Done."}}},
    })
    monkeypatch.setitem(get_content().quests, "chores", quest)
    return quest


async def test_services_count_towards_event_objectives(chores):
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 5, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        char.gold = 100
        p = (await quests.ensure_progress(s, char))["chores"]
        p.stage, p.state, p.counters = "active", "active", {}
        await inventory.add_item(s, char, "dagger")
        dagger = await s.scalar(select(ItemInstance).where(ItemInstance.owner_character_id == char.id,
                                                           ItemInstance.item_key == "dagger"))
        shop = next(k for k, n in get_content().npcs.items() if n.shop and n.shop.buys
                    and "healing_potion" in n.shop.items)

        await inventory.buy(s, char, shop, "dagger", 0)  # not the potion the mission asks for
        assert (p.counters or {}).get("0", 0) == 0
        assert (await inventory.buy(s, char, shop, "healing_potion", 0)).ok
        assert p.counters["0"] == 1
        assert (await inventory.sell(s, char, shop, dagger.id, 0)).ok and p.counters["1"] == 1
        await inventory.add_item(s, char, "dagger")
        dagger = await s.scalar(select(ItemInstance).where(ItemInstance.owner_character_id == char.id,
                                                           ItemInstance.item_key == "dagger"))
        assert (await inventory.equip(s, char, dagger.id)).ok and p.counters["2"] == 1
        home.install(char, "chest", Outcome())
        char.location = next(k for k, loc in get_content().locations.items() if loc.home)
        assert (await home.deposit(s, char, "healing_potion", 1)).ok and p.counters["3"] == 1
        assert (await home.withdraw(s, char, "healing_potion", 1)).ok
        assert p.counters["4"] == 1 and p.state == "completed"
