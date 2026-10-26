"""The Greyforge Vale (roadmap_balance B11): a connected region with a refuge, reachable objectives and a way home."""

from collections import deque

from oathforge.content import get_content

VALE = [
    "valley_crossing",
    "ford_post",
    "ash_quarry",
    "antler_wood",
    "silent_sawmill",
    "glass_shore",
    "regulator_workshop",
    "beacon_height",
]
FLAGS = {"valley_open"}


def reach(c, start, flags=FLAGS):
    seen, queue = {start}, deque([start])
    while queue:
        here = queue.popleft()
        for e in c.locations[here].exits:
            if e.requires_flag and e.requires_flag not in flags:
                continue
            if e.to not in seen:
                seen.add(e.to)
                queue.append(e.to)
    return seen


def test_the_vale_is_closed_until_the_graduation_and_connected_after_it():
    c = get_content()
    assert not set(VALE) & reach(c, "crownreach_plaza", flags=set())  # no flag, no vale
    assert set(VALE) <= reach(c, "crownreach_plaza")  # and with it, everything
    for place in VALE:  # a way home from everywhere (the graph is walked both ways)
        assert "crownreach_plaza" in reach(c, place)


def test_the_vale_has_a_refuge_that_does_not_replace_the_city():
    c = get_content()
    post = c.locations["ford_post"]
    assert post.rest_cost is not None and post.healer is not None
    assert "orsa" in [k for k, n in c.npcs.items() if n.shop and post.name and "ford_post" in n.schedule.values()]
    assert (
        c.locations["ford_post"].zone == "greyforge_vale" and not c.locations["ford_post"].stations
    )  # no crafting there


def test_the_regional_missions_chain_from_the_graduation_to_the_test():
    c = get_content()
    cur, path = "camp_stag", []
    while True:
        nxt = [k for k, q in c.quests.items() if q.after == cur and k.startswith("reg_")]
        if not nxt:
            break
        cur = nxt[0]
        path.append(cur)
    assert path[0] == "reg_arrive" and path[-1] == "reg_trial" and len(path) == 11
    assert c.quests["reg_trial"].turn_in_stage and c.quests["reg_trial"].giver == "iwen"


def test_every_objective_of_the_vale_can_be_met_where_the_text_sends_you():
    c = get_content()
    fighting = {
        m for p in VALE for t in (c.locations[p].encounters + c.locations[p].night_encounters) for m in t.monsters
    }
    fighting |= {m for p in VALE for f in c.locations[p].fixed_encounters for m in f.monsters}
    gatherable = {r.item for p in VALE for g in c.locations[p].gathering for r in g.resources}
    for key, q in c.quests.items():
        if not key.startswith("reg_"):
            continue
        for o in q.objectives:
            if o.kind == "kill":
                assert o.target in fighting, (key, o.target)
            if o.kind == "gather":
                assert o.target in gatherable, (key, o.target)
            if o.kind in ("visit", "talk") and o.kind == "visit":
                assert o.target in VALE + ["crownreach_plaza"], (key, o.target)


def test_the_repair_has_the_cores_it_asks_for_and_the_final_fight_waits_for_it():
    c = get_content()
    assert any(l.item == "regulator_core" and l.chance == 1.0 for l in c.monsters["regulator_sentinel"].loot)
    sentinels = [o.count for o in c.quests["reg_workshop"].objectives if o.target == "regulator_sentinel"]
    assert sentinels and sentinels[0] >= 1  # the repair needs one core, the workshop gives three
    fixed = next(f for f in c.locations["beacon_height"].fixed_encounters)
    assert fixed.if_flag == "beacon_trial"
    assert any({"set_flag": "beacon_trial"} in a.effects for a in c.quests["reg_repair"].actions.values())


def test_creatures_grow_with_the_levels_they_live_at():
    c = get_content()
    order = [
        "ash_smuggler",
        "quarry_crawler",
        "antler_hart",
        "sawblade_automaton",
        "shard_stalker",
        "regulator_sentinel",
        "beacon_warden",
        "beacon_keeper",
    ]
    hps = [c.monsters[m].hp for m in order]
    xps = [c.monsters[m].xp for m in order]
    assert xps == sorted(xps) and hps[0] < hps[-1]
    assert c.monsters["beacon_keeper"].pattern.rearm > 0 and c.monsters["beacon_keeper"].boss


def test_the_water_decision_pays_reputation_on_both_sides_and_flags_it():
    acts = get_content().quests["reg_water"].actions
    assert set(acts) == {"side_with_kellan", "side_with_smuggler"}
    flags = {k: [e["set_flag"] for e in a.effects if "set_flag" in e] for k, a in acts.items()}
    assert flags["side_with_kellan"] != flags["side_with_smuggler"]
