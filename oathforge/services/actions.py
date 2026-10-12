"""Free-text pipeline and NPC conversation.

    read context (short tx)  ->  LLM interprets  ->  lock + validate + resolve (tx)  ->  LLM narrates

Row locks are never held while waiting on the model.
"""

import random
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge import recorder
from oathforge.ai import intent_parser, narrator, npc_dialogue
from oathforge.ai.client import LLM, usage_today, user_exhausted
from oathforge.ai.intent_parser import ActionContext, Intent
from oathforge.content import get_content
from oathforge.database.models import Character, User
from oathforge.database.session import session_scope
from oathforge.engine.checks import clamp_tier
from oathforge.engine.combat import Action, EncounterState
from oathforge.i18n import t
from oathforge.services import audit, characters, combat_service, exploration, inventory, npcs, quests
from oathforge.services.events import Outcome, facts


@dataclass
class FreeTextResult:
    outcome: Outcome = field(default_factory=Outcome)
    narration: str | None = None
    talk_to: str | None = None
    intent: Intent | None = None
    roll_skill: str | None = None  # manual rolls: nothing resolved yet, the player must /roll first
    location: str | None = None


# ---------------------------------------------------------------- manual rolls (/roll)

def manual_rolls(user: User) -> bool:
    return bool((user.settings or {}).get("manual_rolls"))


async def button_roll(session: AsyncSession, char: Character, verb: str, arg: str) -> str | None:
    """Skill a button action will roll, if any: investigating with secrets left, quest actions with a check."""
    c = get_content()
    if char.state == "in_combat":
        return None
    if verb == "look":
        loc = c.locations[char.location]
        pending = [d for d in loc.discoveries.values()
                   if not char.flags.get(d.sets_flag) and (not d.requires_flag or char.flags.get(d.requires_flag))]
        return pending[0].skill if pending else None
    if verb == "qa":
        present = exploration.npcs_present(char.location)
        action = next((a.action for a in await quests.available_actions(session, char, present) if a.ref == arg), None)
        return action.check.skill if action is not None and action.check else None
    return None


async def intent_roll(session: AsyncSession, char: Character, intent: Intent, in_combat: bool) -> str | None:
    """Skill a free-text action will roll outside combat, if any."""
    if in_combat:
        return None
    if intent.type in ("skill_check", "environment_interaction"):
        return intent.skill if intent.skill in get_content().skills else None
    if intent.type == "inspect":
        return await button_roll(session, char, "look", "")
    if intent.type == "quest_action":
        return await button_roll(session, char, "qa", intent.target or "")
    return None


async def _load(session: AsyncSession, user_id: int, lock: bool = False) -> tuple[User | None, Character | None]:
    user = await session.get(User, user_id)
    char = await characters.get_character(session, user_id, lock=lock) if user else None
    return user, char


def describe_character(char: Character) -> str:
    c = get_content()
    who = {"male": "man, ", "female": "woman, "}.get(char.gender or "", "")
    return (f"{char.name}, {who}level {char.level} {c.lineages[char.lineage].name.en} "
            f"{c.classes[char.class_key].name.en}, HP {char.hp}/{char.max_hp}")


async def build_context(session: AsyncSession, char: Character, lang: str) -> ActionContext:
    c = get_content()
    loc = c.locations[char.location]
    ctx = ActionContext(lang=lang, character=describe_character(char), location=loc.name.en,
                        scene=loc.description.en, skills={k: s.name.en for k, s in c.skills.items()})
    for inst in await inventory.items_of(session, char):
        ctx.items[inst.item_key] = c.items[inst.item_key].name.en
    enc = await combat_service.active_encounter(session, char)
    if enc is not None:
        state = EncounterState.model_validate(enc.state)
        ctx.in_combat = True
        ctx.enemies = {cb.id: f"{cb.name['en']} (HP {cb.hp}/{cb.max_hp}, {cb.row} row)"
                       for cb in state.side("enemy")}
        p = state.combatants["p1"]
        ctx.weapons = {a.key: a.name["en"] for a in p.attacks}
        defs = combat_service.ability_defs(char)
        ctx.abilities = {k: defs[k].name.en for k, uses in p.abilities.items() if uses is None or uses > 0}
        ctx.objects = {k: loc.scene_objects[k].name.en for k in state.scene_objects if k in loc.scene_objects}
        return ctx
    present = exploration.npcs_present(char.location)
    ctx.exits = {e.to: c.locations[e.to].name.en for e in exploration.exits(char)}
    ctx.npcs = {k: f"{c.npcs[k].name.en}, {c.npcs[k].title.en}" for k in present}
    for a in await quests.available_actions(session, char, present):
        ctx.quest_actions[a.ref] = a.action.label.en
    return ctx


async def handle_free_text(llm: LLM, user_id: int, text: str, rng: random.Random) -> FreeTextResult:
    async with session_scope() as session:
        user, char = await _load(session, user_id)
        if char is None:
            return FreeTextResult(Outcome.refused("start.need_character"))
        lang = user.language
        if user_exhausted(*await usage_today(session, user_id)):
            return FreeTextResult(Outcome.refused("ai.budget_exhausted"))
        ctx = await build_context(session, char, lang)
        manual = manual_rolls(user)

    intent = await intent_parser.parse(llm, ctx, text, user_id)
    if intent is None:
        return FreeTextResult(Outcome.refused("freetext.unavailable"))
    if intent.type == "talk":
        return FreeTextResult(talk_to=intent.target, intent=intent)
    if manual:
        async with session_scope() as session:
            _, char = await _load(session, user_id)
            skill = await intent_roll(session, char, intent, ctx.in_combat)
            if skill:
                return FreeTextResult(intent=intent, roll_skill=skill, location=char.location)
    return await execute_free_text(llm, user_id, text, intent, ctx.in_combat, rng)


async def execute_free_text(llm: LLM, user_id: int, text: str, intent: Intent, in_combat: bool,
                            rng: random.Random, location: str | None = None) -> FreeTextResult:
    """Resolve an interpreted action and narrate it (also after a deferred /roll)."""
    async with session_scope() as session:
        user, char = await _load(session, user_id, lock=True)
        if char is None:
            return FreeTextResult(Outcome.refused("start.need_character"))
        lang = user.language
        enc = await combat_service.active_encounter(session, char, lock=True)
        if (enc is not None) != in_combat or (location is not None and char.location != location):
            return FreeTextResult(Outcome.refused("freetext.stale"), intent=intent)
        outcome = await resolve(session, char, enc, intent, rng)
        await audit.log(session, user_id=user_id, character_id=char.id, verb=f"free:{intent.type}",
                        payload={"text": text[:600], "intent": intent.model_dump()},
                        result={"ok": outcome.ok, "events": [e.key for e in outcome.events]})
        scene = get_content().locations[char.location].name.en
        who = describe_character(char)
        char_id = char.id

    narration = await narrator.narrate(llm, lang=lang, scene=scene, character=who, player_text=text,
                                       facts=facts(outcome), user_id=user_id)
    recorder.action(user_id=user_id, character_id=char_id, text=text, intent=intent.model_dump(),
                    ok=outcome.ok, events=[e.key for e in outcome.events], narration=narration)
    return FreeTextResult(outcome, narration, intent=intent)


async def resolve(session: AsyncSession, char: Character, enc, intent: Intent, rng: random.Random) -> Outcome:
    """Map a validated intent onto game services. Only engine/services change state."""
    kind = intent.type
    if enc is not None:
        action = {
            "attack": lambda: Action(kind="attack", weapon=intent.weapon, target=intent.target),
            "ability": lambda: Action(kind="ability", ability=intent.ability, target=intent.target),
            "use_item": lambda: Action(kind="heal_item"),
            "defend": lambda: Action(kind="defend"),
            "flee": lambda: Action(kind="flee"),
            "environment_interaction": lambda: Action(kind="interact", object=intent.target),
        }.get(kind)
        if action is None:
            return Outcome().add("freetext.no_effect")
        return await combat_service.act(session, char, enc, action(), rng)

    present = exploration.npcs_present(char.location)
    if kind == "move":
        return await exploration.travel(session, char, intent.target, rng)
    if kind == "use_item":
        return await inventory.use_item_outside_combat(session, char, intent.target, rng)
    if kind == "skill_check":
        out, _ = await exploration.check_skill(session, char, intent.skill, clamp_tier(intent.tier), rng,
                                              f"free:{intent.skill}:{char.location}")
        return out
    if kind == "environment_interaction":
        out, _ = await exploration.check_skill(session, char, intent.skill, clamp_tier(intent.tier), rng,
                                              f"env:{char.location}")
        return out
    if kind == "inspect":
        return await exploration.investigate(session, char, rng)
    if kind == "steal":
        if intent.target not in present:
            return Outcome.refused("freetext.not_here")
        return await npcs.steal(session, char, intent.target, rng)
    if kind == "rest":
        return await exploration.rest(session, char)
    if kind == "quest_action":
        return await quests.perform(session, char, intent.target, present, rng)
    if kind == "ooc_question":
        return Outcome().add("freetext.ooc")
    return Outcome().add("freetext.no_effect")


# ---------------------------------------------------------------- conversation

async def talk(llm: LLM, user_id: int, npc_key: str, text: str) -> tuple[str, Outcome]:
    c = get_content()
    npc = c.npcs.get(npc_key)
    async with session_scope() as session:
        user, char = await _load(session, user_id)
        if char is None:
            return "", Outcome.refused("start.need_character")
        lang = user.language
        if npc is None or npc_key not in exploration.npcs_present(char.location):
            return "", Outcome.refused("talk.err.not_here")
        if user_exhausted(*await usage_today(session, user_id)):
            return t(lang, "talk.fallback", npc=npc.name.get(lang)), Outcome().add("ai.budget_exhausted")
        rel = await npcs.relationship(session, npc_key, char)
        trust = rel.trust
        memories = [m.text for m in await npcs.recall(session, npc_key, char)]
        rumors = [r.get("en", "") for r in await npcs.recent_rumors(session)]
        rep = await npcs.reputation_with(session, char, npc.faction) if npc.faction else None
        who = describe_character(char)

    reply = await npc_dialogue.reply(
        llm, npc=npc, lang=lang, player=who, player_text=text, trust=trust, reputation=rep,
        memories=memories, rumors=rumors, time_of_day="night" if exploration.is_night() else "day",
        user_id=user_id,
    )
    out = Outcome()
    if reply is None:
        return t(lang, "talk.fallback", npc=npc.name.get(lang)), out

    async with session_scope() as session:
        _, char = await _load(session, user_id, lock=True)
        if reply.memory_note.strip():
            await npcs.remember(session, npc_key, char, reply.memory_note.strip(), reply.importance)
        if reply.trust_delta:
            new_trust = await npcs.adjust_trust(session, npc_key, char, reply.trust_delta)
            out.add("talk.trust_up" if reply.trust_delta > 0 else "talk.trust_down",
                    npc=npc.name.model_dump(), trust=new_trust)
        await audit.log(session, user_id=user_id, character_id=char.id, verb="talk",
                        payload={"npc": npc_key, "text": text[:600]},
                        result={"line": reply.line[:1000], "memory": reply.memory_note, "trust": reply.trust_delta})
    return reply.line, out
