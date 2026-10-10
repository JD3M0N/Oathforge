"""Data-driven quests: stages, player actions and triggers from quests.yaml."""

import random
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.content.schemas import Quest, QuestAction
from oathforge.database.models import Character, QuestProgress
from oathforge.engine.checks import check, dc_for
from oathforge.engine.dice import roll
from oathforge.services import characters, inventory, npcs
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
        out.add("check.result", skill=get_content().skills[action.check.skill].name.model_dump(),
                roll=res.kept, total=res.total, dc=dc, result="✅" if res.success else "❌")
        if res.success:
            out.text(action.check.success_text)
            await apply_effects(session, char, action.check.success_effects, out, rng)
            await characters.practice(session, char, action.check.skill, action.check.tier, f"quest:{ref}", out)
        else:
            out.text(action.check.failure_text)
            await apply_effects(session, char, action.check.failure_effects, out, rng)
    await apply_effects(session, char, action.effects, out, rng)
    _set_stage(quest, prog, action.to_stage, out)
    return out


async def on_defeat(session: AsyncSession, char: Character, monster_key: str, rng: random.Random) -> Outcome:
    out = Outcome()
    prog = await progress(session, char, lock=True)
    for qkey, quest in get_content().quests.items():
        p = prog.get(qkey)
        if p is None:
            continue
        for trig in quest.triggers:
            if trig.event == "defeat" and trig.target == monster_key and p.stage in trig.stages:
                out.text(trig.text)
                await apply_effects(session, char, trig.effects, out, rng)
                _set_stage(quest, p, trig.to_stage, out)
                break
    return out


def _set_stage(quest: Quest, p: QuestProgress, stage: str, out: Outcome) -> None:
    p.stage = stage
    p.state = quest.stages[stage].state
    key = {"completed": "quest.completed", "failed": "quest.failed"}.get(p.state, "quest.updated")
    out.add(key, quest=quest.name.model_dump())


async def apply_effects(session: AsyncSession, char: Character, effects: list[dict], out: Outcome,
                        rng: random.Random) -> None:
    c = get_content()
    for eff in effects:
        (kind, arg), = eff.items()
        if kind == "give_item":
            for item, qty in arg.items():
                await inventory.add_item(session, char, item, qty)
                out.add("loot.item", item=c.items[item].name.model_dump(), qty=qty)
        elif kind == "take_item":
            for item, qty in arg.items():
                await inventory.remove_item(session, char, item, qty)
                out.add("loot.lost_item", item=c.items[item].name.model_dump(), qty=qty)
        elif kind == "gold":
            char.gold += int(arg)
            out.add("loot.gold", gold=int(arg))
        elif kind == "xp":
            characters.grant_xp(char, int(arg), out)
        elif kind == "reputation":
            for faction, delta in arg.items():
                await npcs.adjust_reputation(session, char, faction, int(delta), out)
        elif kind == "set_flag":
            char.flags = {**char.flags, str(arg): True}
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


async def journal(session: AsyncSession, char: Character) -> list[tuple[Quest, QuestProgress]]:
    c = get_content()
    prog = await progress(session, char)
    return [(c.quests[k], p) for k, p in prog.items() if k in c.quests]


async def location_texts(session: AsyncSession, char: Character) -> list[dict]:
    """Extra scene text a quest stage adds to the current location."""
    c = get_content()
    out = []
    for k, p in (await progress(session, char)).items():
        stage = c.quests[k].stages.get(p.stage)
        if stage and char.location in stage.location_text:
            out.append(stage.location_text[char.location].model_dump())
    return out
