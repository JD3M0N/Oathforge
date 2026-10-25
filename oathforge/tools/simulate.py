"""Battle simulator for balance: hundreds of fights class x enemy, no database, no AI.

    python -m oathforge.tools.simulate --n 200 --level 1-3
    python -m oathforge.tools.simulate --classes sorcerer,warrior --monsters bandit,goblin_scout+goblin_scout

Each fight uses ``random.Random(seed + i)``, so the same arguments always give the same numbers.
The player follows a simple fixed policy (see ``play_turn``); results go to the console and to
``artifacts/simulations/<timestamp>.json`` and ``.csv``.
"""

import argparse
import csv
import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character, CharacterSkill, ItemInstance
from oathforge.engine import combat, dice, progression
from oathforge.engine.checks import modifier
from oathforge.engine.combat import Action, CombatError, Combatant, EncounterState
from oathforge.services import characters, combat_service

MAX_ROUNDS = 50
# main-action abilities, most valuable first; limited uses are spent before unlimited ones
PREPARED_POTIONS = 2  # healing potions the simulated hero carries, drunk below 40% HP
SAVE_FOR_WINDOW = True  # the informed hero keeps costed attacks for the boss's exposed window
VETERAN_POTIONS = 3  # from level 10 they are greater potions (4d4+4): the campaign hands out and sells them
ACTION_PRIORITY = ("summon", "converge", "command", "shift", "heal", "turn", "save", "strike", "spell", "curse", "buff")
HELPERS = ("summon", "converge", "command", "shift")  # abilities of the helpers and forms of B05


# ---------------------------------------------------------------- the simulated hero

def default_choices(class_key: str, level: int, branch: str | None, picks: dict | None = None) -> dict:
    """What a player would have picked by `level`: the offensive training at 5 and 18, the resilient one at 12, and
    the first option of every modifier. `picks` overrides any of them ({"modifier:13": "heavy_verdict"})."""
    c = get_content()
    prog = c.progression
    trainings = {5: "keen", 12: "hardy", 18: "keen"}
    out = {f"training:{lvl}": trainings.get(lvl, "keen") for lvl in prog.training_levels if lvl <= level}
    if branch:
        mods = c.class_specializations[branch].modifiers
        for lvl in prog.modifier_levels:
            if lvl <= level:
                out[f"modifier:{lvl}"] = next(k for k, m in mods.items() if m.level == lvl)
    return {**out, **(picks or {})}


def sim_character(class_key: str, level: int, lineage: str, background: str, branch: str | None = None,
                  picks: dict | None = None) -> Character:
    """A transient character as ``create_character`` + ``grant_xp`` would leave it (never saved), with the
    trainings, the branch and the modifiers a player would have chosen by that level."""
    c = get_content()
    cls = c.classes[class_key]
    if branch and c.class_specializations[branch].class_key != class_key:
        raise ValueError(f"branch '{branch}' does not belong to class '{class_key}'")
    scores = characters.starting_scores(class_key, lineage)  # no ability boost on the way: the trainings replaced it
    hp = progression.max_hp(cls.hit_die, modifier(scores["con"]), level)
    char = Character(
        id=0, name="Sim", lineage=lineage, background=background, class_key=class_key, abilities=scores,
        level=level, xp=0, hp=hp, max_hp=hp, gold=0, location=c.start_location, state="idle", flags={},
        conditions={}, resources=characters.full_resources(class_key, level), bestiary={}, checks_tried={},
        specialization=branch if level >= c.progression.specialization_level else None,
        build={"v": characters.BUILD_VERSION, characters.CHOICES: default_choices(class_key, level, branch, picks)},
        pools={},
    )
    characters.refill_resources(char)  # the catalogue now includes the branch and the modifiers
    char.max_hp = char.hp = characters.max_hp_for(char)  # and the trainings' hit points
    return char


T1_BODY = {"str": "steel_breastplate"}  # the piece the guild lends at level 10 (camp_kit): heavy for the strong, boiled leather for the rest
T1_BODY_DEFAULT = "hardened_leather"


def sim_gear(char: Character, kit: str = "t0") -> dict[str, ItemInstance]:
    """Starting equipment, equipped like ``create_character`` does. ``kit="t1"``: from level 10, the one level-10 body
    piece Tamsin lends in the campaign (a reasonable preparation, not a full set)."""
    c = get_content()
    gear: dict[str, ItemInstance] = {}
    for key in c.classes[char.class_key].equip:
        slot = c.items[key].slot
        if slot and slot not in gear:
            gear[slot] = ItemInstance(item_key=key, qty=1, equipped_slot=slot, history=[])
    if kit == "t1" and char.level >= c.progression.specialization_level:
        key = T1_BODY.get(c.classes[char.class_key].primary, T1_BODY_DEFAULT)
        gear["body"] = ItemInstance(item_key=key, qty=1, equipped_slot="body", history=[])
    return gear


def sim_skills(char: Character) -> dict[str, CharacterSkill]:
    c = get_content()
    proficient = (set(c.classes[char.class_key].skills) | set(c.backgrounds[char.background].skills)
                  | set(c.lineages[char.lineage].skills))
    return {s: CharacterSkill(skill=s, proficient=s in proficient, xp=0, recent=[]) for s in c.skills}


def hero(class_key: str, level: int, lineage: str, background: str, branch: str | None = None,
         picks: dict | None = None) -> tuple[Combatant, dict]:
    char = sim_character(class_key, level, lineage, background, branch, picks)
    return characters.combatant_from(char, sim_gear(char), sim_skills(char)), combat_service.ability_defs(char)


# ---------------------------------------------------------------- the player's policy

def _try(state: EncounterState, action: Action, rng: random.Random, defs: dict) -> bool:
    try:
        combat.player_act(state, "p1", action, rng, defs)
        return True
    except CombatError:
        return False


def _target(state: EncounterState, me: Combatant, ranged: bool) -> str | None:
    foes = combat.valid_targets(state, me, ranged)
    return min(foes, key=lambda f: (f.hp, f.id)).id if foes else None


def _usable(me: Combatant, key: str, defs: dict) -> bool:
    uses = me.abilities.get(key)
    if key not in me.abilities or (uses is not None and uses <= 0):
        return False
    return combat.affordable(me, key, defs[key])


def _bonus(state: EncounterState, me: Combatant, rng: random.Random, defs: dict) -> None:
    """Heal when low; otherwise a buff, curse or hide that is not already running."""
    for key in combat.available_bonus_actions(state, me, defs):
        a = defs[key]
        if a.kind == "heal" and me.hp * 2 >= me.max_hp:
            continue
        if a.kind == "buff" and ((a.status and a.status in me.statuses) or (a.temp_hp and me.temp_hp > 0)):
            continue
        if a.kind == "hide" and "hidden" in me.statuses:
            continue
        if a.kind == "surge":
            continue
        if a.kind in HELPERS and not _helpers_ok(state, me, a):
            continue
        target = _target(state, me, ranged=True)
        if a.kind == "curse" and (target is None or a.status in state.combatants[target].statuses):
            continue
        if _try(state, Action(kind="ability", ability=key, target=target), rng, defs):
            return


def _weapon(me: Combatant):
    ranged = next((p for p in me.attacks if p.ranged), None)
    melee = next((p for p in me.attacks if not p.ranged), None)
    return ranged if ranged and (me.row == "back" or melee is None) else melee


def _helpers_ok(state: EncounterState, me: Combatant, a) -> bool:
    """Summon, order, converge and shift only when they would do something."""
    mine = [e for e in state.entities.values() if e.owner == me.id and e.active]
    if a.kind == "summon":
        return a.entity in state.entity_defs and not any(e.key == a.entity for e in state.entities.values())
    if a.kind == "converge":
        return bool(mine) and not all(e.boost for e in mine)
    if a.kind == "command":
        return any(e.key == a.entity and e.role != "guard" and e.acted_round < state.round for e in mine)
    if a.kind == "shift":
        return a.form != "none" and a.form in me.shapes and me.form != a.form and me.form is None
    return True


def _worth_it(me: Combatant, key: str, a, weapon) -> bool:
    """What costs something is worth it; a free one only if it hits as hard as the weapon."""
    if me.abilities.get(key) is not None or a.cost or a.kind in ("strike", "turn", "heal") + HELPERS:
        return True
    if not a.damage:
        return False
    return weapon is None or dice.parse(a.damage).average + me.spell_damage_bonus >= dice.parse(weapon.damage).average


def _main(state: EncounterState, me: Combatant, rng: random.Random, defs: dict, use_abilities: bool,
          informed: bool = True) -> None:
    weapon = _weapon(me)
    if informed and me.consumables.get("healing_potion", 0) > 0 and me.hp * 5 < 2 * me.max_hp:  # a potion when low
        dose = "4d4+4" if me.level >= 10 else "2d4+2"
        if _try(state, Action(kind="heal_item", heal_amount=dice.roll(dose, rng).total), rng, defs):
            return
    aiming = [f for f in state.enemies_of(me) if f.pattern_state == "aiming" and f.heavy]
    if informed and aiming and (me.hp <= 2.5 * dice.parse(aiming[0].heavy.damage).average
                                or me.hp * 5 < 3 * me.max_hp):  # the signal says: guard
        if _try(state, Action(kind="defend"), rng, defs):
            return
    if use_abilities:
        # against a boss with a pattern the informed hero wears the plate down with what is free and saves what costs
        # for the window: the plate gone or the boss reloading (exposed)
        patterned = [f for f in state.enemies_of(me) if f.pattern]
        saving = SAVE_FOR_WINDOW and informed and any(f.plate > 0 and f.pattern_state != "reloading" for f in patterned)
        options = [k for k, a in defs.items()
                   if a.action == "action" and _usable(me, k, defs) and a.kind in ACTION_PRIORITY
                   and _worth_it(me, k, a, weapon) and _helpers_ok(state, me, a)
                   and (a.kind != "heal" or me.hp * 3 < me.max_hp)
                   and not (saving and a.kind in ("strike", "spell", "save", "curse") and (a.cost or me.abilities.get(k) is not None))]
        # the dearest first: what the bar pays for, then what has limited uses, then the free ones
        options.sort(key=lambda k: (ACTION_PRIORITY.index(defs[k].kind), -defs[k].cost,
                                    me.abilities[k] is None))
        for key in options:
            a = defs[key]
            if a.kind == "buff" and a.status in me.statuses:
                continue
            if a.kind == "curse" and all(a.status in f.statuses for f in state.enemies_of(me)):
                continue
            if _try(state, Action(kind="ability", ability=key,
                                  target=_target(state, me, a.kind != "strike" or a.ranged)),
                    rng, defs):
                return
    if weapon and _try(state, Action(kind="attack", weapon=weapon.key, target=_target(state, me, weapon.ranged)),
                       rng, defs):
        return
    _try(state, Action(kind="defend"), rng, defs)


def play_turn(state: EncounterState, rng: random.Random, defs: dict, use_abilities: bool = True,
              informed: bool = True) -> None:
    """One player turn: bonus action first, then the action (twice with Action Surge), then end the turn."""
    me = state.combatants["p1"]
    rnd = state.round
    if use_abilities:
        _bonus(state, me, rng, defs)
    if state.status == "active" and state.current.id == "p1" and state.round == rnd:
        _main(state, me, rng, defs, use_abilities, informed)
    if use_abilities and state.status == "active" and state.current.id == "p1" and state.round == rnd:
        surge = next((k for k in combat.available_bonus_actions(state, me, defs) if defs[k].kind == "surge"), None)
        if surge and _try(state, Action(kind="ability", ability=surge), rng, defs):
            _main(state, me, rng, defs, use_abilities, informed)
    if state.status == "active" and state.current.id == "p1" and state.round == rnd:
        _try(state, Action(kind="end_turn"), rng, defs)


# ---------------------------------------------------------------- fights and stats

@dataclass
class Fight:
    status: str  # victory | defeat | fled | timeout
    rounds: int
    hp_left: float  # fraction of max HP
    damage_dealt: int
    damage_taken: int  # net of healing: max HP minus HP at the end
    ended: dict | None = None  # what the hero keeps for the next fight of a sequence: hp, uses, bar
    potions_used: int = 0


def _bring_helpers(state: EncounterState, player: Combatant, char: Character) -> None:
    """What the hero may call in the fight, like combat_service does at the start of a real one."""
    from oathforge.services import companions
    for a in characters.abilities_of(char).values():
        if a.kind in ("summon", "command") and a.entity:
            state.entity_defs[a.entity] = companions.template(a.entity, char)
        elif a.kind == "passive" and a.entity:
            tpl = state.entity_defs[a.entity] = companions.template(a.entity, char)
            combat.spawn(state, player, tpl, persistent=True, acts_now=True)


def fight(class_key: str, level: int, monsters: list[str], seed: int, lineage: str, background: str,
          use_abilities: bool = True, branch: str | None = None, policy: str = "informed", kit: str = "t0",
          carry: dict | None = None) -> Fight:
    """One fight. ``policy``: "basic" ignores the boss's signals and the potions, "informed" answers them.
    ``kit``: "t0" start gear, "t1" adds the level-10 piece. ``carry``: the hero as a previous fight left him."""
    rng = random.Random(seed)
    char = sim_character(class_key, level, lineage, background, branch)
    player = characters.combatant_from(char, sim_gear(char, kit), sim_skills(char))
    defs = combat_service.ability_defs(char)
    stock = VETERAN_POTIONS if level >= 10 else PREPARED_POTIONS
    player.consumables = {"healing_potion": stock if policy == "informed" else 0}
    if carry:
        player.hp, player.abilities, player.resource = carry["hp"], dict(carry["abilities"]), carry["resource"]
        player.consumables = {"healing_potion": carry["potions"]}
    state = EncounterState(location="simulation", combatants={"p1": player})
    _bring_helpers(state, player, char)
    for i, key in enumerate(monsters, start=1):
        state.combatants[f"m{i}"] = combat_service.monster_combatant(key, f"m{i}")
    combat.start(state, rng)
    while state.status == "active" and state.round <= MAX_ROUNDS:
        play_turn(state, rng, defs, use_abilities, policy == "informed")
    me = state.combatants["p1"]
    foes = [c for c in state.combatants.values() if c.side == "enemy"]
    return Fight(
        status=state.status if state.status != "active" else "timeout",
        rounds=min(state.round, MAX_ROUNDS),
        hp_left=max(0, me.hp) / me.max_hp,
        damage_dealt=sum(f.max_hp - max(0, f.hp) + f.plate_max - f.plate for f in foes),
        damage_taken=me.max_hp - max(0, me.hp),
        ended={"hp": max(0, me.hp), "abilities": dict(me.abilities), "resource": me.resource,
               "potions": me.consumables.get("healing_potion", 0)},
        potions_used=(stock if policy == "informed" else 0) - me.consumables.get("healing_potion", 0),
    )


SHORT_RESTS_BETWEEN = 2  # the campaign's allowance between two long rests (engine/timings.py)


def sequence(class_key: str, level: int, groups: list[list[str]], seed: int, lineage: str, background: str,
             branch: str | None = None, policy: str = "informed", kit: str = "t0") -> list[Fight]:
    """Fights back to back. The informed hero takes a short rest (30% of his HP, half of his bar, one use) when he is
    under 60% and has rests left; the basic one never rests. Stops at the first defeat."""
    from oathforge.engine import timings
    out: list[Fight] = []
    carry, rests = None, SHORT_RESTS_BETWEEN
    for i, keys in enumerate(groups):
        f = fight(class_key, level, keys, seed + i, lineage, background, True, branch, policy, kit, carry)
        out.append(f)
        if f.status != "victory":
            break
        carry = dict(f.ended)
        char = sim_character(class_key, level, lineage, background, branch)
        if policy == "informed" and rests and carry["hp"] < 0.6 * char.max_hp:
            rests -= 1
            carry["hp"] = min(char.max_hp, carry["hp"] + round(char.max_hp * timings.SHORT_REST_HP_PCT))
            full = characters.resource_max(char)
            if full:
                carry["resource"] = min(full, carry["resource"] + round(full * timings.SHORT_REST_POOL_PCT))
    return out


def summarize(fights: list[Fight]) -> dict:
    n = len(fights)
    rounds = sum(f.rounds for f in fights)
    return {
        "fights": n,
        "win_pct": round(100 * sum(f.status == "victory" for f in fights) / n, 1),
        "timeout_pct": round(100 * sum(f.status == "timeout" for f in fights) / n, 1),
        "avg_rounds": round(rounds / n, 2),
        "avg_hp_left_pct": round(100 * sum(f.hp_left for f in fights) / n, 1),
        "dmg_per_round": round(sum(f.damage_dealt for f in fights) / max(1, rounds), 2),
        "hp_lost_per_round": round(sum(f.damage_taken for f in fights) / max(1, rounds), 2),
    }


def simulate(classes: list[str], monsters: list[str], levels: list[int], n: int, seed: int, lineage: str,
             background: str, use_abilities: bool = True, branch: str | None = None, policy: str = "informed",
             kit: str = "t0") -> list[dict]:
    """One row per class x enemy group x level; ``monsters`` entries are keys joined with ``+``."""
    rows = []
    for level in levels:
        for cls in classes:
            for group in monsters:
                keys = group.split("+")
                fights = [fight(cls, level, keys, seed + i, lineage, background, use_abilities, branch, policy, kit)
                          for i in range(n)]
                rows.append({"class": cls if not branch else f"{cls}/{branch}", "enemies": group, "level": level,
                             **summarize(fights)})
    return rows


# ---------------------------------------------------------------- console

def _levels(text: str) -> list[int]:
    lo, _, hi = text.partition("-")
    return list(range(int(lo), int(hi or lo) + 1))


def _table(rows: list[dict]) -> str:
    cols = ["level", "class", "enemies", "win_pct", "avg_rounds", "avg_hp_left_pct", "dmg_per_round",
            "hp_lost_per_round", "timeout_pct"]
    head = ["lvl", "class", "enemies", "win%", "rounds", "hp left%", "dmg/rnd", "hp lost/rnd", "timeout%"]
    cells = [head] + [[str(r[c]) for c in cols] for r in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(len(cols))]
    lines = ["  ".join(v.ljust(w) if i < 3 else v.rjust(w) for i, (v, w) in enumerate(zip(row, widths)))
             for row in cells]
    lines.insert(1, "  ".join("-" * w for w in widths))
    return "\n".join(lines)


def save(rows: list[dict], params: dict) -> Path:
    out = Path(get_settings().artifacts_dir) / "simulations"
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (out / f"{stamp}.json").write_text(json.dumps({"params": params, "results": rows}, indent=2), encoding="utf-8")
    with open(out / f"{stamp}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return out / f"{stamp}.json"


def main(argv: list[str] | None = None) -> None:
    c = get_content()
    parser = argparse.ArgumentParser(prog="oathforge simulate", description="Simulate fights for balance.")
    parser.add_argument("--n", type=int, default=200, help="fights per class x enemy x level (200)")
    parser.add_argument("--level", default="1", help="level or range, e.g. 3 or 1-5 (1)")
    parser.add_argument("--classes", default=",".join(c.classes), help="comma-separated class keys (all)")
    parser.add_argument("--monsters", default=",".join(c.monsters),
                        help="comma-separated monster keys; join with + for a group, e.g. bandit+bandit (all)")
    parser.add_argument("--lineage", default=next(iter(c.lineages)))
    parser.add_argument("--background", default=next(iter(c.backgrounds)))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--branch", default=None, help="a class branch to play (from level 10), e.g. avenger")
    parser.add_argument("--no-abilities", action="store_true", help="weapon attacks only")
    parser.add_argument("--policy", choices=("basic", "informed"), default="informed",
                        help="informed answers the boss's signals and drinks potions; basic does not")
    parser.add_argument("--kit", choices=("t0", "t1"), default="t0", help="t1: the level-10 piece of the campaign")
    parser.add_argument("--no-save", action="store_true", help="don't write artifacts/simulations/")
    args = parser.parse_args(argv)

    classes, monsters = args.classes.split(","), args.monsters.split(",")
    unknown = [k for k in classes if k not in c.classes] + [
        k for g in monsters for k in g.split("+") if k not in c.monsters]
    if unknown:
        parser.error(f"unknown class or monster: {', '.join(unknown)}")
    if args.branch and args.branch not in c.class_specializations:
        parser.error(f"unknown branch: {args.branch}")
    if args.branch:
        classes = [c.class_specializations[args.branch].class_key]
    levels = _levels(args.level)
    rows = simulate(classes, monsters, levels, args.n, args.seed, args.lineage, args.background,
                    not args.no_abilities, args.branch, args.policy, args.kit)
    print(_table(rows))
    if not args.no_save:
        params = {k: v for k, v in vars(args).items() if k != "no_save"}
        print(f"\nsaved {save(rows, params)}")


if __name__ == "__main__":
    main(sys.argv[1:])
