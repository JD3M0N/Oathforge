"""The common campaign up to the Ash Collector (roadmap_balance B09): no dead ends, in content."""

from oathforge.content import get_content

TRADES = ["alchemy", "blacksmithing", "carpentry", "leatherworking", "jewelcrafting", "scribing", "engineering", "tailoring"]


def chain(c, start="tut_chapel"):
    """The missions that open one after another from ``start`` through `after`."""
    out, cur = [], start
    while True:
        nxt = [k for k, q in c.quests.items() if q.after == cur and (not k.startswith("camp_trade_") or k == "camp_trade_pick") and k != "old_tusk"]
        if not nxt:
            return out
        out.append(nxt[0])
        cur = nxt[0]


def test_the_campaign_runs_from_the_tutorial_to_the_collector_and_opens_level_ten():
    c = get_content()
    path = chain(c)
    assert path[0] == "camp_order" and "camp_collector" in path
    # every act is on the way, in order
    for act in ("camp_gear", "camp_roof", "camp_trade_pick", "camp_tracks", "camp_rumor", "camp_ledger", "camp_table"):
        assert act in path
    last = c.quests["camp_collector"]
    assert {"milestone": "ash_collector"} in last.rewards
    assert last.turn_in_stage and last.giver == "tamsin"  # beating him pays nothing until Tamsin hears it


def test_the_collector_can_be_reached_and_is_a_telegraphing_boss():
    c = get_content()
    assert any(e.to == "toll_post" for e in c.locations["old_kings_road"].exits)
    post = c.locations["toll_post"]
    fixed = next(f for f in post.fixed_encounters if "ash_collector" in f.monsters)
    flag_set_by = [a for q in c.quests.values() for a in q.actions.values() if {"set_flag": fixed.if_flag} in a.effects]
    assert flag_set_by  # the table of Tamsin is what makes him appear
    boss = c.monsters["ash_collector"]
    assert boss.boss and boss.pattern and boss.pattern.plate > 0 and boss.pattern.heavy.ranged
    assert any(l.item == "forgery_proof" and l.chance == 1.0 for l in boss.loot)


def test_every_trade_has_a_mission_a_master_at_their_stall_and_enough_material():
    c = get_content()
    for prof in TRADES:
        q = c.quests[f"camp_trade_{prof}"]
        assert q.unlock_profession == prof and q.after == "camp_trade_pick"
        start = q.actions["start"]
        assert c.locations[start.location].teaches == prof
        assert start.location in c.npcs[start.npc].schedule.values()
        have = dict(next(e["give_item"] for e in start.effects if "give_item" in e))
        xp = next((e["profession_xp"][prof] for e in start.effects if "profession_xp" in e), 0)
        for obj in (o for o in q.objectives if o.kind == "craft"):
            assert can_make(c, obj.target, obj.count, dict(have), rank_xp=xp, prof=prof), (prof, obj.target)


def can_make(c, item, count, have, rank_xp, prof):
    """Whether ``count`` of ``item`` can be crafted from ``have`` (with refined intermediates) at that trade rank."""
    from oathforge.engine.gathering import rank_for
    rank = rank_for(rank_xp)

    def make(item, n):
        take = min(have.get(item, 0), n)
        have[item] = have.get(item, 0) - take
        n -= take
        if n == 0:
            return True
        recipe = next((r for r in c.recipes.values() if item in r.outputs and not r.special), None)
        if recipe is None:
            return False
        if recipe.profession == prof and recipe.min_rank > rank:
            return False
        batches = -(-n // recipe.outputs[item])
        for ing, q in recipe.ingredients.items():
            if not make(ing, q * batches):
                return False
        have[item] = have.get(item, 0) + batches * recipe.outputs[item] - n
        return True

    return make(item, count)


def test_the_rumour_mission_offers_a_real_choice_with_reputation_on_both_sides():
    c = get_content()
    acts = c.quests["camp_rumor"].actions
    assert set(acts) == {"believe", "check"}
    reps = {k: next(e["reputation"]["silver_covenant"] for e in a.effects if "reputation" in e) for k, a in acts.items()}
    assert reps["believe"] < 0 < reps["check"]


def test_smoke_is_always_obtainable_for_the_escape():
    c = get_content()
    sellers = [k for k, n in c.npcs.items() if n.shop and "smoke_bomb" in n.shop.items]
    assert sellers  # sold, never gated behind a rare drop (roadmap_balance §8.5)


def test_the_graduation_runs_after_the_collector_and_opens_level_twenty():
    c = get_content()
    path = chain(c)
    assert path[-5:] == ["camp_collector", "camp_path", "camp_kit", "camp_signs", "camp_stag"]
    stag = c.quests["camp_stag"]
    assert {"milestone": "iron_stag"} in stag.rewards and stag.turn_in_stage and stag.giver == "tamsin"
    assert any(e.to == "stag_hollow" for e in c.locations["elderwood_grove"].exits)
    fixed = next(f for f in c.locations["stag_hollow"].fixed_encounters if "iron_stag" in f.monsters)
    assert any({"set_flag": fixed.if_flag} in a.effects for q in c.quests.values() for a in q.actions.values())


def test_the_kit_is_one_piece_not_a_full_set_and_every_option_is_level_ten_gear():
    c = get_content()
    kit = c.quests["camp_kit"]
    picks = [a for k, a in kit.actions.items() if k.startswith("pick_")]
    assert len(picks) >= 3
    for a in picks:
        (item,) = next(e["give_item"] for e in a.effects if "give_item" in e)
        assert c.items[item].min_level == 10 and (c.items[item].slot or c.items[item].type)
