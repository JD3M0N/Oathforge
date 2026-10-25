"""💡 What do I do? Pure rules that read the fight and name the answers the hero's own class has (roadmap_balance
§13.2). No AI and no secrets: it says what is already on the panel (the boss aims, the plate, the HP), never what the
dice will do next."""

from oathforge.engine.combat import EncounterState, affordable

HEAL_KINDS = ("heal",)
GUARD_KINDS = ("buff", "hide", "escape")
CONTROL_KINDS = ("save", "curse")
DAMAGE_KINDS = ("strike", "spell", "surge", "turn", "summon", "command")


def usable(state: EncounterState, me, defs: dict) -> dict[str, list[str]]:
    """The hero's abilities that could be used now, by what they are for."""
    roles: dict[str, list[str]] = {"heal": [], "guard": [], "control": [], "damage": []}
    for key, uses in me.abilities.items():
        a = defs.get(key)
        if a is None or (uses is not None and uses <= 0) or not affordable(me, key, a) or key in me.cooldowns:
            continue
        for role, kinds in (("heal", HEAL_KINDS), ("guard", GUARD_KINDS), ("control", CONTROL_KINDS),
                            ("damage", DAMAGE_KINDS)):
            if a.kind in kinds:
                roles[role].append(key)
                break
    return roles


def hints(state: EncounterState, me, defs: dict) -> list[tuple[str, dict]]:
    """[(hint key, {role: [ability keys]})], most urgent first. Always at least one."""
    roles = usable(state, me, defs)
    foes = [f for f in state.side("enemy") if f.active]
    out: list[tuple[str, dict]] = []
    if any(f.pattern_state == "aiming" for f in foes):
        out.append(("aiming", {"heal": roles["heal"], "guard": roles["guard"]}))
    if any(f.pattern_state == "reloading" for f in foes):
        out.append(("reloading", {"damage": roles["damage"]}))
    if any(f.plate > 0 for f in foes):
        out.append(("plate", {"damage": roles["damage"]}))
    if me.hp * 3 < me.max_hp:
        out.append(("low_hp", {"heal": roles["heal"], "guard": roles["guard"]}))
    if not out:
        out.append(("plain", {"damage": roles["damage"]}))
    return out
