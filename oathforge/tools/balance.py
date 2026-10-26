"""Balance report of the 0.10 campaign (roadmap_balance §15): classes and branches against level-appropriate encounters,
with two policies, one reasonable kit, fights in sequence, durations by role and the XP pace of the campaign.

    oath balance --n 16 --seed 7            # the whole report (several minutes; uses every core)
    oath balance --quick                    # a few cells, to check that it still runs

Everything is reproducible: each fight uses ``random.Random(seed + i)``. The report names the version, the commit,
the seed and the sample size of every cell, and says what it cannot measure. Results go to ``artifacts/balance/``.
"""

import argparse
import math
import os
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import oathforge
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.tools import simulate as sim

KINDS = ("weak", "standard", "elite", "pair", "boss")
# what a level meets: the rival of each weight, from the creatures that live at that level (None: nothing of that kind yet)
STANDARDS: dict[int, dict[str, str | None]] = {
    1: {"weak": "cave_bat", "standard": "bandit", "elite": "grey_wolf", "pair": "bandit+bandit", "boss": None},
    3: {
        "weak": "boar",
        "standard": "goblin_scout+goblin_scout",
        "elite": "bandit_captain",
        "pair": "bandit+goblin_scout",
        "boss": None,
    },
    5: {
        "weak": "bandit",
        "standard": "bandit_captain",
        "elite": "old_tusk",
        "pair": "bandit_captain+bandit",
        "boss": "old_tusk",
    },
    9: {
        "weak": "ash_hound",
        "standard": "toll_enforcer",
        "elite": "post_sergeant",
        "pair": "toll_enforcer+ash_hound",
        "boss": "ash_collector",
    },
    10: {
        "weak": "post_sergeant",
        "standard": "ash_smuggler",
        "elite": "quarry_crawler",
        "pair": "ash_smuggler+ash_crossbowman",
        "boss": "iron_stag",
    },
    13: {
        "weak": "ash_smuggler",
        "standard": "antler_wolf",
        "elite": "antler_hart",
        "pair": "antler_wolf+antler_wolf",
        "boss": None,
    },
    17: {
        "weak": "antler_hart",
        "standard": "glass_eel",
        "elite": "shard_stalker",
        "pair": "glass_eel+shard_stalker",
        "boss": "regulator_sentinel",
    },
    20: {
        "weak": "shard_stalker",
        "standard": "sawblade_automaton",
        "elite": "regulator_sentinel",
        "pair": "glass_eel+shard_stalker",
        "boss": "beacon_keeper",
    },
}
BASE_LEVELS = (1, 3, 5, 9)
BRANCH_LEVELS = (10, 13, 17, 20)
# three fights in a row, the last the boss when the level has one; the hero rests twice between them if he is hurt
SEQUENCE = ("standard", "elite", "standard", "boss")
MIN_WIN = {"weak": 90, "standard": 75, "elite": 55, "pair": 55, "boss": 35}  # seeds, not promises (roadmap §15.3)


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval of a win rate, in percent: a 100% on 12 fights is not a 100%."""
    if n == 0:
        return 0.0, 100.0
    p = wins / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * max(0, centre - half), 1), round(100 * min(1, centre + half), 1)


def _cell(args: tuple) -> dict:
    """One cell of the matrix (runs in a worker process)."""
    cls, branch, level, kind, group, policy, kit, n, seed = args
    fights = [
        sim.fight(cls, level, group.split("+"), seed + i, "human", "soldier", True, branch, policy, kit)
        for i in range(n)
    ]
    wins = sum(f.status == "victory" for f in fights)
    return {
        "class": cls,
        "branch": branch,
        "level": level,
        "kind": kind,
        "enemies": group,
        "policy": policy,
        "kit": kit,
        "n": n,
        "wins": wins,
        "win_pct": round(100 * wins / n, 1),
        "ci": wilson(wins, n),
        "rounds": round(sum(f.rounds for f in fights) / n, 2),
        "hp_left": round(100 * sum(f.hp_left for f in fights) / n, 1),
    }


def _chain(args: tuple) -> dict:
    cls, branch, level, kit, policy, n, seed = args
    kinds = [k for k in SEQUENCE if STANDARDS[level][k]]
    groups = [STANDARDS[level][k].split("+") for k in kinds]
    runs = [sim.sequence(cls, level, groups, seed + 100 * i, "human", "soldier", branch, policy, kit) for i in range(n)]
    done = sum(len(r) == len(groups) and r[-1].status == "victory" for r in runs)
    return {
        "class": cls,
        "branch": branch,
        "level": level,
        "policy": policy,
        "kit": kit,
        "n": n,
        "fights": len(groups),
        "through_pct": round(100 * done / n, 1),
        "ci": wilson(done, n),
    }


def cells(n: int, seed: int, quick: bool) -> list[tuple]:
    c = get_content()
    out: list[tuple] = []
    classes = list(c.classes)[:2] if quick else list(c.classes)
    branches = list(c.class_specializations)[:2] if quick else list(c.class_specializations)
    for level in BASE_LEVELS[:1] if quick else BASE_LEVELS:
        for cls in classes:
            for kind, group in STANDARDS[level].items():
                if group:
                    for policy in ("basic", "informed"):
                        out.append((cls, None, level, kind, group, policy, "t0", n, seed))
    for level in BRANCH_LEVELS[:1] if quick else BRANCH_LEVELS:
        for b in branches:
            cls = c.class_specializations[b].class_key
            for kind, group in STANDARDS[level].items():
                if group:
                    out.append((cls, b, level, kind, group, "basic", "t0", n, seed))
                    out.append((cls, b, level, kind, group, "informed", "t1", n, seed))
    return out


def chains(n: int, seed: int, quick: bool) -> list[tuple]:
    c = get_content()
    branches = list(c.class_specializations)[:2] if quick else list(c.class_specializations)
    return [
        (c.class_specializations[b].class_key, b, level, "t1", "informed", n, seed)
        for level in (BRANCH_LEVELS[:1] if quick else BRANCH_LEVELS)
        for b in branches
    ]


def role_of(branch: str) -> str:
    return get_content().class_specializations[branch].roles[0]


# ---------------------------------------------------------------- pace of the campaign

MIN_PER_KILL, MIN_PER_GATHER_UNIT, MIN_PER_STEP = 3.0, 1.5, 2.0  # interaction, travel and recovery included
SESSIONS_PER_DAY, MINUTES_PER_SESSION = 2, 75


def _quest_minutes_and_xp(quest) -> tuple[float, int]:
    """What a mission costs in minutes and what it pays in XP, kills included."""
    c = get_content()
    minutes, xp = 0.0, sum(int(e["xp"]) for e in quest.rewards if "xp" in e)
    steps: dict[tuple, int] = {}  # actions of one stage are alternatives (a decision); those of different stages add up
    for a in quest.actions.values():
        gained = sum(int(e["xp"]) for e in a.effects if "xp" in e)
        steps[tuple(a.stages)] = max(steps.get(tuple(a.stages), 0), gained)
    xp += sum(steps.values())
    for o in quest.objectives:
        if o.kind == "kill":
            minutes += MIN_PER_KILL * o.count
            xp += c.monsters[o.target].xp * o.count
        elif o.kind in ("gather", "skin", "craft"):
            minutes += MIN_PER_GATHER_UNIT * o.count
        else:
            minutes += MIN_PER_STEP * o.count
    minutes += MIN_PER_STEP * max(1, len(quest.actions))
    return minutes, xp


def pace() -> list[dict]:
    """Walk the missions in order doing only what they ask: where does the XP stand against the level table?"""
    c = get_content()
    table = c.progression.xp

    def cap(xp: int) -> int:
        return sum(1 for t in table if xp >= t)

    xp, minutes, rows = 0, 0.0, []
    from oathforge.services import quests as q

    for key, quest in q.ordered_quests():
        if quest.order >= 100:
            continue
        m, x = _quest_minutes_and_xp(quest)
        xp, minutes = xp + x, minutes + m
        rows.append({"quest": key, "xp_total": xp, "minutes_total": round(minutes), "level_by_xp": cap(xp)})
    return rows


def hunt_xp_per_minute(level: int) -> float:
    """XP a minute of hunting the standard rival of that level pays: the way to cover a gap."""
    group = STANDARDS[min((k for k in STANDARDS if k >= level), default=20)]["standard"].split("+")
    return sum(get_content().monsters[k].xp for k in group) / (MIN_PER_KILL * len(group))


# ---------------------------------------------------------------- the report


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # pragma: no cover - a source drop without git
        return "unknown"


def report(res: list[dict], seqs: list[dict], n: int, seed: int) -> str:
    c = get_content()
    L = [
        f"# Informe de balance · Oathforge {oathforge.__version__}",
        "",
        f"- Commit de código: `{git_sha()}` · versión de contenido: {oathforge.__version__} · generado {time.strftime('%Y-%m-%d %H:%M')}",
        f"- Semilla base: {seed} · combates por celda: {n} (intervalo de Wilson al 95 % entre corchetes)",
        "- Linaje humano, trasfondo soldado, entrenamientos y modificadores por defecto (`simulate.default_choices`).",
        "- Política **básica**: prioridades fijas, ignora avisos y pociones. **Informada**: se defiende cuando el jefe apunta y bebe pociones por debajo del 40 % de vida.",
        "- Equipo: **T0** = el inicial de la clase. **T1** = además la pieza de nivel 10 que presta el gremio (niveles ≥ 10).",
        "",
    ]
    # 1. base classes
    L += [
        "## Clases base · niveles 1, 3, 5 y 9 (política informada, equipo T0)",
        "",
        "| Nivel | Clase | " + " | ".join(KINDS) + " |",
        "|---|---|" + "---|" * len(KINDS),
    ]
    base = [r for r in res if r["branch"] is None and r["policy"] == "informed"]
    for level in BASE_LEVELS:
        for cls in c.classes:
            row = {r["kind"]: r for r in base if r["class"] == cls and r["level"] == level}
            if row:
                L.append(
                    f"| {level} | {cls} | "
                    + " | ".join(
                        f"{row[k]['win_pct']:.0f} [{row[k]['ci'][0]:.0f}–{row[k]['ci'][1]:.0f}]" if k in row else "—"
                        for k in KINDS
                    )
                    + " |"
                )
    # 2. branches
    L += [
        "",
        "## Ramas · niveles 10, 13, 17 y 20 (política informada, equipo T1)",
        "",
        "| Nivel | Rama | Rol | " + " | ".join(KINDS) + " |",
        "|---|---|---|" + "---|" * len(KINDS),
    ]
    br = [r for r in res if r["branch"] and r["policy"] == "informed"]
    for level in BRANCH_LEVELS:
        for b in c.class_specializations:
            row = {r["kind"]: r for r in br if r["branch"] == b and r["level"] == level}
            if row:
                L.append(
                    f"| {level} | {b} | {role_of(b)} | "
                    + " | ".join(f"{row[k]['win_pct']:.0f}" if k in row else "—" for k in KINDS)
                    + " |"
                )
    # 3. what the policy buys
    L += [
        "",
        "## Qué aporta responder a las señales (jefes: informada + T1 frente a básica + T0)",
        "",
        "| Jefe | Nivel | Básica T0 | Informada T1 | Mejora (puntos) |",
        "|---|---|---|---|---|",
    ]
    lifts = []
    for level in (9, 10, 17, 20):
        kind = "boss"
        pool = [r for r in res if r["level"] == level and r["kind"] == kind]
        if not pool:
            continue
        b0 = [r["win_pct"] for r in pool if r["policy"] == "basic"]
        i1 = [r["win_pct"] for r in pool if r["policy"] == "informed"]
        if b0 and i1:
            lift = sum(i1) / len(i1) - sum(b0) / len(b0)
            lifts.append((level, lift))
            L.append(
                f"| {STANDARDS[level]['boss']} | {level} | {sum(b0) / len(b0):.1f} | {sum(i1) / len(i1):.1f} | {lift:+.1f} |"
            )
    # 4. sequences
    L += [
        "",
        "## Secuencias de combates (estándar, élite, estándar y jefe; dos descansos cortos entre ellos)",
        "",
        "| Nivel | Rama | Rol | Superan toda la secuencia |",
        "|---|---|---|---|",
    ]
    for s in sorted(seqs, key=lambda s: (s["level"], s["through_pct"])):
        L.append(
            f"| {s['level']} | {s['branch']} | {role_of(s['branch'])} | {s['through_pct']:.0f} % [{s['ci'][0]:.0f}–{s['ci'][1]:.0f}] ({s['n']}) |"
        )
    # 5. durations by role
    L += [
        "",
        "## Duración por rol (rondas medias en encuentros estándar y élite, política informada)",
        "",
        "| Rol | Ramas | Rondas medias |",
        "|---|---|---|",
    ]
    by_role: dict[str, list[float]] = defaultdict(list)
    for r in br:
        if r["kind"] in ("standard", "elite"):
            by_role[role_of(r["branch"])].append(r["rounds"])
    means = {k: sum(v) / len(v) for k, v in by_role.items()}
    for role in sorted(by_role):
        L.append(f"| {role} | {len({r['branch'] for r in br if role_of(r['branch']) == role})} | {means[role]:.2f} |")
    # 6. defects
    L += ["", "## Defectos que el informe encuentra", ""]
    defects = []
    for r in res:
        if r["policy"] != "informed":
            continue
        floor = MIN_WIN[r["kind"]]
        if r["win_pct"] < floor:
            who = r["branch"] or r["class"]
            defects.append((r["level"], who, r["kind"], r["win_pct"], floor))
    defects.sort()
    if defects:
        L += ["| Nivel | Quién | Encuentro | Victorias % | Suelo % |", "|---|---|---|---|---|"]
        L += [f"| {a} | {b} | {c_} | {d:.0f} | {e} |" for a, b, c_, d, e in defects[:60]]
        if len(defects) > 60:
            L.append(f"| … | {len(defects) - 60} más | | | |")
    else:
        L.append("Ninguna celda informada queda por debajo de su suelo.")
    L += ["", "Suelos usados (semillas, no promesas): " + ", ".join(f"{k} {v} %" for k, v in MIN_WIN.items()) + ".", ""]
    # 7. pace
    L += [
        "## Ritmo de la campaña (modelo, no medición)",
        "",
        f"Supuestos: {MIN_PER_KILL:.0f} min por criatura derrotada, {MIN_PER_GATHER_UNIT} min por unidad recogida o fabricada, "
        f"{MIN_PER_STEP:.0f} min por paso o visita; {SESSIONS_PER_DAY} sesiones diarias de {MINUTES_PER_SESSION} min. Sólo cuenta lo que piden las misiones, en orden.",
        "",
        "| Misión | XP acumulada | Min acumulados | Nivel por XP | Día (2 sesiones) |",
        "|---|---|---|---|---|",
    ]
    per_day = SESSIONS_PER_DAY * MINUTES_PER_SESSION
    rows = pace()
    for r in rows:
        if (
            r["quest"] in ("tut_chapel", "camp_order", "camp_collector", "camp_stag", "reg_arrive", "reg_trial")
            or r is rows[-1]
        ):
            L.append(
                f"| {r['quest']} | {r['xp_total']} | {r['minutes_total']} | {r['level_by_xp']} | {r['minutes_total'] / per_day:.1f} |"
            )
    gaps = []
    for qk, need_level in (("camp_collector", 9), ("camp_stag", 10), ("reg_trial", 20)):
        row = next((r for r in rows if r["quest"] == qk), None)
        if row:
            need = c.progression.xp[need_level - 1]
            gap = max(0, need - row["xp_total"])
            gaps.append((qk, need_level, need, row["xp_total"], gap, gap / hunt_xp_per_minute(need_level)))
    L += [
        "",
        "| Hito | Nivel que abre/pide | XP necesaria | XP de las misiones | Falta | Min de caza para cubrirlo |",
        "|---|---|---|---|---|---|",
    ]
    L += [f"| {a} | {b} | {c_} | {d} | {e} | {f:.0f} |" for a, b, c_, d, e, f in gaps]
    L += [
        "",
        "## Limitaciones",
        "",
        "- El simulador no modela huida, objetos de combate más allá de la poción de curación, ni la decisión de qué rama o modificador escoger: usa las opciones por defecto.",
        "- Un solo linaje y trasfondo; no se barren las 164 configuraciones 13×17 por rama (cuatro por rama): sólo la primera de cada elección.",
        "- Las criaturas de nivel 11–20 se midieron una a una o en parejas, no en las mezclas de las tablas de encuentros reales.",
        "- El ritmo es un modelo con tiempos supuestos; las sesiones reales (tgtest, `oath tutorial-stats`) lo desmentirán o confirmarán.",
        "- No se mide la latencia ni el coste de la IA (la narración no decide reglas).",
        "",
    ]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="oathforge balance", description="Balance report of the campaign.")
    parser.add_argument("--n", type=int, default=16, help="fights per cell (16)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--quick", action="store_true", help="a handful of cells, to check that it runs")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = parser.parse_args(argv)
    work, chain_work = cells(args.n, args.seed, args.quick), chains(max(4, args.n // 2), args.seed, args.quick)
    print(f"{len(work)} cells and {len(chain_work)} sequences, {args.workers} workers", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(args.workers) as pool:
        res = list(pool.map(_cell, work, chunksize=8))
        seqs = list(pool.map(_chain, chain_work, chunksize=4))
    text = report(res, seqs, args.n, args.seed)
    out = Path(get_settings().artifacts_dir) / "balance"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{time.strftime('%Y%m%d-%H%M%S')}.md"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nsaved {path} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main(sys.argv[1:])
