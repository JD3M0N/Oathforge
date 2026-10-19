"""Data-driven quests: stages, player actions and triggers from quests.yaml.

Missions add counted objectives (kill / talk / visit / gather / skin / craft / rest / heal) that complete them
on their own, and a
chain: a locked mission opens when the previous one is completed or a flag is set.
"""

import random
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.i18n import t
from oathforge.content.schemas import Quest, QuestAction, QuestObjective
from oathforge.database.models import Character, QuestProgress
from oathforge.engine.checks import check, dc_for
from oathforge.engine.dice import roll
from oathforge.services import characters, inventory, npcs
from oathforge.services import achievements
from oathforge.services.events import Outcome


@dataclass(frozen=True)
class AvailableAction:
    quest_key: str
    action_key: str
    action: QuestAction

    @property
    def ref(self) -> str:
        return f"{self.quest_key}.{self.action_key}"


async def progress(session: AsyncSession, char: Character, lock: bool = False) -> dict[str, QuestProgress]:
    stmt = select(QuestProgress).where(QuestProgress.character_id == char.id)
    if lock:
        stmt = stmt.with_for_update()
    return {p.quest_key: p for p in await session.scalars(stmt)}


def ordered_quests() -> list[tuple[str, Quest]]:
    return sorted(get_content().quests.items(), key=lambda kv: kv[1].order)


async def ensure_progress(session: AsyncSession, char: Character) -> dict[str, QuestProgress]:
    """Locked progress rows, creating the ones a character made before a quest existed.

    A new quest that replaces old ones (`legacy_done`) starts completed for whoever finished them, so a
    veteran does not redo the tutorial. Rows of removed quests stay in the table and are ignored."""
    prog = await progress(session, char, lock=True)
    for qkey, quest in get_content().quests.items():
        if qkey not in prog:
            veteran = any(old in prog and prog[old].state == "completed" for old in quest.legacy_done)
            stage = quest.complete_stage if veteran and quest.complete_stage else quest.start_stage
            row = QuestProgress(character_id=char.id, quest_key=qkey, stage=stage,
                                state=quest.stages[stage].state, counters={})
            session.add(row)
            prog[qkey] = row
    await session.flush()
    return prog


def _unlocked(quest: Quest, prog: dict[str, QuestProgress], char: Character) -> bool:
    if quest.after is None and quest.unlock_flag is None:
        return False
    after_ok = quest.after is None or (quest.after in prog and prog[quest.after].state == "completed")
    flag_ok = quest.unlock_flag is None or bool(char.flags.get(quest.unlock_flag))
    return after_ok and flag_ok


async def refresh(session: AsyncSession, char: Character, out: Outcome) -> None:
    """Open every locked mission whose requirement is now met (chains can open several at once)."""
    prog = await ensure_progress(session, char)
    changed = True
    while changed:
        changed = False
        for qkey, quest in ordered_quests():
            p = prog[qkey]
            if p.state == "locked" and quest.unlock_stage and _unlocked(quest, prog, char):
                p.stage = quest.unlock_stage
                p.state = quest.stages[quest.unlock_stage].state
                out.add("quest.new", quest=quest.name.model_dump())
                changed = True


def objective_progress(quest: Quest, p: QuestProgress | None) -> list[tuple[QuestObjective, int]]:
    counters = (p.counters if p is not None else None) or {}
    done = p is not None and p.state == "completed"
    return [(o, o.count if done else min(o.count, int(counters.get(str(i), 0))))
            for i, o in enumerate(quest.objectives)]


ANYWHERE = {"es": "cualquier sitio", "en": "anywhere"}


def objective_target(obj: QuestObjective) -> dict:
    c = get_content()
    if obj.target == "any":
        return dict(ANYWHERE)
    if obj.kind == "read":
        return c.rulebook[obj.target].title.model_dump()
    pool = {"kill": c.monsters, "hunt": c.locations, "talk": c.npcs, "visit": c.locations, "gather": c.items, "skin": c.items,
            "craft": c.items, "rest": c.locations, "heal": c.locations}[obj.kind]
    if pool is c.locations:  # «Ve a la Capilla del Alba»
        return pool[obj.target].phrase()
    return pool[obj.target].name.model_dump()


def objective_key(obj: QuestObjective) -> str:
    """The i18n key of "what to do": "any" targets have their own wording ("Take a long rest")."""
    return f"quest.objective.{obj.kind}" + ("_any" if obj.target == "any" else "")


def _matches(obj: QuestObjective, kind: str, target: str) -> bool:
    return obj.kind == kind and (obj.target == target or (obj.target == "any" and kind in ("hunt", "rest", "heal")))


async def advance(session: AsyncSession, char: Character, kind: str, target: str, rng: random.Random,
                  amount: int = 1) -> Outcome:
    """Count a kill / talk / visit (or `amount` items gathered, skinned or crafted, a rest, a heal) towards
    active missions; completing one gives its rewards."""
    out = Outcome()
    prog = await ensure_progress(session, char)
    for qkey, quest in ordered_quests():
        p = prog[qkey]
        if p.state != "active" or p.stage != quest.objective_stage:
            continue
        counters = dict(p.counters or {})
        hit = None
        for i, obj in enumerate(quest.objectives):
            if _matches(obj, kind, target) and int(counters.get(str(i), 0)) < obj.count:
                counters[str(i)] = min(obj.count, int(counters.get(str(i), 0)) + amount)
                hit = (obj, counters[str(i)])
        if hit is None:
            continue
        p.counters = counters
        if all(int(counters.get(str(i), 0)) >= o.count for i, o in enumerate(quest.objectives)):
            out.text(quest.stages[quest.complete_stage].journal)
            await apply_effects(session, char, quest.rewards, out, rng)
            await _set_stage(session, char, quest, p, quest.complete_stage, out)
        elif hit[0].count > 1 and hit[1] < hit[0].count:
            out.add("quest.progress", quest=quest.name.model_dump(), target=objective_target(hit[0]),
                    n=hit[1], count=hit[0].count)
        else:  # that objective is done but the mission is not: say what comes next
            nxt = next(o for i, o in enumerate(quest.objectives) if int(counters.get(str(i), 0)) < o.count)
            out.add("quest.next", quest=quest.name.model_dump(),
                    step={lang: t(lang, objective_key(nxt), target=objective_target(nxt)[lang])
                          for lang in ("es", "en")})
    await refresh(session, char, out)
    return out


async def on_talk(session: AsyncSession, char: Character, npc: str, rng: random.Random) -> Outcome:
    return await advance(session, char, "talk", npc, rng)


async def on_visit(session: AsyncSession, char: Character, location: str, rng: random.Random) -> Outcome:
    return await advance(session, char, "visit", location, rng)


TUTORIAL_BOOSTS = "tutorial_boosts"  # char.flags: tutorial missions whose shortcut was already used


async def tutorial_boost(session: AsyncSession, char: Character, kind: str,
                         candidates: set[str]) -> tuple[str, str, int] | None:
    """The accelerated tutorial: (mission, item, how many are missing) when an active tutorial mission asks
    to `kind` (gather / skin) one of the `candidates` and its shortcut is still unused. Once per mission."""
    # beta only: the shortcut works every time, not once per mission
    used = set() if get_settings().beta_instant_tutorial else set((char.flags or {}).get(TUTORIAL_BOOSTS, []))
    prog = await ensure_progress(session, char)
    for qkey, quest in ordered_quests():
        p = prog[qkey]
        if not quest.tutorial or qkey in used or p.state != "active" or p.stage != quest.objective_stage:
            continue
        for obj, n in objective_progress(quest, p):
            if obj.kind == kind and obj.target in candidates and n < obj.count:
                return qkey, obj.target, obj.count - n
    return None


async def in_tutorial(session: AsyncSession, char: Character) -> bool:
    """Whether a tutorial mission is under way."""
    prog = await ensure_progress(session, char)
    return any(quest.tutorial and prog[qkey].state == "active" for qkey, quest in ordered_quests())


def use_tutorial_boost(char: Character, quest_key: str) -> None:
    flags = char.flags or {}
    char.flags = {**flags, TUTORIAL_BOOSTS: [*flags.get(TUTORIAL_BOOSTS, []), quest_key]}


async def giver_hint(session: AsyncSession, char: Character, npc_key: str) -> dict | None:
    """The hint of the first active mission this NPC gave, for when the AI cannot answer for them."""
    prog = await ensure_progress(session, char)
    for qkey, quest in ordered_quests():
        if quest.giver == npc_key and quest.hint and prog[qkey].state == "active":
            return quest.hint.model_dump()
    return None


async def finished_giver(session: AsyncSession, char: Character, npc_key: str) -> bool:
    """Whether the hero has completed a mission this NPC gave (the NPC greets them as someone known)."""
    prog = await ensure_progress(session, char)
    return any(quest.giver == npc_key and prog[qkey].state == "completed" for qkey, quest in ordered_quests())


async def on_read(session: AsyncSession, char: Character, section: str, rng: random.Random) -> Outcome:
    """A /rulebook page opened: "look it up in the rulebook" objectives."""
    return await advance(session, char, "read", section, rng)


async def on_items(session: AsyncSession, char: Character, kind: str, items: dict[str, int],
                   rng: random.Random) -> Outcome:
    """Items gathered, skinned or crafted (kind) count towards objectives, by quantity."""
    out = Outcome()
    for key, qty in items.items():
        if qty > 0:
            out.extend(await advance(session, char, kind, key, rng, amount=qty))
    return out


async def available_actions(
    session: AsyncSession, char: Character, present_npcs: list[str], npc: str | None = None
) -> list[AvailableAction]:
    """Quest actions the character can take here. ``npc`` limits to one conversation partner."""
    c = get_content()
    prog = await progress(session, char)
    out = []
    for qkey, quest in c.quests.items():
        p = prog.get(qkey)
        if p is None:
            continue
        for akey, action in quest.actions.items():
            if p.stage not in action.stages:
                continue
            if action.location and action.location != char.location:
                continue
            if action.npc and (action.npc not in present_npcs or (npc is not None and action.npc != npc)):
                continue
            if npc is not None and action.npc is None:
                continue
            if action.requires_item and await inventory.count(session, char, action.requires_item) < 1:
                continue
            out.append(AvailableAction(qkey, akey, action))
    return out


async def perform(
    session: AsyncSession, char: Character, ref: str, present_npcs: list[str], rng: random.Random
) -> Outcome:
    if refusal := characters.ensure_free(char):
        return refusal
    qkey, _, akey = ref.partition(".")
    avail = {a.ref: a for a in await available_actions(session, char, present_npcs)}
    if ref not in avail:
        return Outcome.refused("quest.err.unavailable")
    quest = get_content().quests[qkey]
    action = avail[ref].action
    prog = (await progress(session, char, lock=True))[qkey]

    out = Outcome().text(action.text)
    if action.check:
        skills = await characters.skills_of(session, char)
        dc = dc_for(action.check.tier)
        res = check(rng, action.check.skill, characters.skill_bonus(char, skills, action.check.skill), dc)
        characters.add_check(out, res)
        if res.success:
            out.text(action.check.success_text)
            await apply_effects(session, char, action.check.success_effects, out, rng)
            await characters.practice(session, char, action.check.skill, action.check.tier, f"quest:{ref}", out)
        else:
            out.text(action.check.failure_text)
            await apply_effects(session, char, action.check.failure_effects, out, rng)
    await apply_effects(session, char, action.effects, out, rng)
    await _set_stage(session, char, quest, prog, action.to_stage, out)
    await refresh(session, char, out)
    return out


async def on_defeat(session: AsyncSession, char: Character, monster_key: str, rng: random.Random) -> Outcome:
    out = Outcome()
    prog = await ensure_progress(session, char)
    for qkey, quest in get_content().quests.items():
        p = prog[qkey]
        for trig in quest.triggers:
            if trig.event == "defeat" and trig.target == monster_key and p.stage in trig.stages:
                out.text(trig.text)
                await apply_effects(session, char, trig.effects, out, rng)
                await _set_stage(session, char, quest, p, trig.to_stage, out)
                break
    return out.extend(await advance(session, char, "kill", monster_key, rng))


async def _set_stage(session, char, quest: Quest, p: QuestProgress, stage: str, out: Outcome) -> None:
    p.stage = stage
    p.state = quest.stages[stage].state
    key = {"completed": "quest.completed", "failed": "quest.failed"}.get(p.state, "quest.updated")
    out.add(key, quest=quest.name.model_dump())
    if p.state == "completed":
        await achievements.emit(session, char, out, "quest", {"quest": p.quest_key},
                                f"quest:{p.quest_key}:completed")
    elif p.state == "active":
        await achievements.emit(session, char, out, "quest_start", {"quest": p.quest_key},
                                f"quest:{p.quest_key}:started")
    decisions = {"returned_covenant": "covenant", "sold_syndicate": "syndicate", "opened_box": "opened"}
    if p.quest_key == "sealed_box" and stage in decisions:
        await achievements.emit(session, char, out, "decision", {"key": decisions[stage]},
                                f"decision:sealed_box:{stage}")


async def apply_effects(session: AsyncSession, char: Character, effects: list[dict], out: Outcome,
                        rng: random.Random) -> None:
    c = get_content()
    for eff in effects:
        (kind, arg), = eff.items()
        if kind == "give_item":
            for item, qty in arg.items():
                await inventory.add_item(session, char, item, qty)
                out.add("loot.item", item=c.items[item].labelled(), qty=qty, item_key=item)
        elif kind == "take_item":
            for item, qty in arg.items():
                await inventory.remove_item(session, char, item, qty)
                out.add("loot.lost_item", item=c.items[item].labelled(), qty=qty)
        elif kind == "gold":
            char.gold += int(arg)
            out.add("loot.gold", gold=int(arg))
        elif kind == "xp":
            before_level = char.level
            characters.grant_xp(char, int(arg), out)
            await achievements.levels(session, char, out, before_level)
        elif kind == "reputation":
            for faction, delta in arg.items():
                await npcs.adjust_reputation(session, char, faction, int(delta), out)
        elif kind == "set_flag":
            char.flags = {**char.flags, str(arg): True}
            if arg == "crypt_unlocked":
                await achievements.emit(session, char, out, "flag", {"key": arg}, f"flag:{arg}")
        elif kind == "npc_memory":
            await npcs.remember(session, arg["npc"], char, arg["text"].format(name=char.name),
                                int(arg.get("importance", 3)))
        elif kind == "trust":
            await npcs.adjust_trust(session, arg["npc"], char, int(arg["delta"]))
        elif kind == "damage":
            dmg = roll(str(arg), rng).total
            char.hp = max(1, char.hp - dmg)
            out.add("loot.damage", amount=dmg, hp=char.hp)
        elif kind == "world_rumor":
            text = {lang: s.format(name=char.name) for lang, s in arg.items()}
            await npcs.add_rumor(session, text, source=f"character:{char.id}", tags=[f"character:{char.id}"])


async def journal(session: AsyncSession, char: Character) -> list[tuple[str, Quest, QuestProgress | None]]:
    """Every quest in mission order with its progress (None: the character predates the quest)."""
    prog = await progress(session, char)
    return [(k, q, prog.get(k)) for k, q in ordered_quests()]


def stage_of(quest: Quest, p: QuestProgress | None) -> tuple[str, str]:
    """(stage, state), falling back to the quest's start for rows not created yet."""
    if p is None:
        return quest.start_stage, quest.stages[quest.start_stage].state
    return p.stage, p.state


async def location_texts(session: AsyncSession, char: Character) -> list[dict]:
    """Extra scene text a quest stage adds to the current location."""
    c = get_content()
    out = []
    for k, p in (await progress(session, char)).items():
        if k not in c.quests:
            continue
        stage = c.quests[k].stages.get(p.stage)
        if stage and char.location in stage.location_text:
            out.append(stage.location_text[char.location].model_dump())
    return out
