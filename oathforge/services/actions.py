"""Free-text pipeline and NPC conversation.

    read context (short tx)  ->  LLM interprets  ->  lock + validate + resolve (tx)  ->  LLM narrates

Row locks are never held while waiting on the model.
"""

import random
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge import recorder
from oathforge.ai import fallbacks, intent_parser, narrator, npc_dialogue
from oathforge.ai.client import LLM, Budget
from oathforge.ai.intent_parser import ActionContext, Intent
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character, User
from oathforge.database.session import session_scope
from oathforge.engine.checks import clamp_tier
from oathforge.i18n import t
from oathforge.engine.combat import Action, EncounterState
from oathforge.services import (
    activities, audit, characters, combat_service, exploration, inventory, npcs, quests, world_map,
)
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
        pending = list(exploration.open_discoveries(char).values())
        return pending[0].skill if pending else None
    if verb == "qa":
        present = exploration.npcs_present(char.location)
        action = next((a.action for a in await quests.available_actions(session, char, present) if a.ref == arg), None)
        return action.check.skill if action is not None and action.check else None
    return None


async def intent_roll(session: AsyncSession, char: Character, intent: Intent, in_combat: bool) -> str | None:
    """Skill a free-text action will roll outside combat, if any (none when it was already tried today)."""
    if in_combat:
        return None
    if intent.type in ("skill_check", "environment_interaction"):
        if intent.skill not in get_content().skills:
            return None
        return None if exploration.tried(char, exploration.free_check_key(intent.skill, char.location)) else intent.skill
    if intent.type == "inspect":
        return await button_roll(session, char, "look", "")
    if intent.type == "quest_action":
        return await button_roll(session, char, "qa", intent.target or "")
    return None


async def _load(session: AsyncSession, user_id: int, lock: bool = False) -> tuple[User | None, Character | None]:
    user = await session.get(User, user_id)
    char = await characters.get_character(session, user_id, lock=lock) if user else None
    return user, char


def describe_character(char: Character, backstory: bool = False) -> str:
    """For the AI; with backstory, the player-written background too (already reviewed, quoted as data)."""
    c = get_content()
    who = {"male": "man, ", "female": "woman, "}.get(char.gender or "", "")
    text = (f"{char.name}, {who}level {char.level} {c.lineages[char.lineage].name.en} "
            f"{c.classes[char.class_key].name.en}, HP {char.hp}/{char.max_hp}")
    if backstory and char.custom_background:
        custom = char.custom_background
        text += f'; background "{custom["title"]}": "{custom["story"]}"'
    return text


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
    ctx.exits = {r.to: c.locations[r.to].name.en for r in world_map.destinations(char)}
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
        if not await Budget(get_settings()).allow(user_id):
            return FreeTextResult(Outcome(ok=False, error="ai.budget_exhausted"),
                                  fallbacks.pick("freetext", "budget_exhausted", lang, name=char.name))
        ctx = await build_context(session, char, lang)
        manual = manual_rolls(user)
        name = char.name

    intent = await intent_parser.parse(llm, ctx, text, user_id)
    if intent is None:  # Gemini down: say so at once, in a generic voice
        return FreeTextResult(Outcome(), fallbacks.pick("freetext", await _ai_down_reason(user_id), lang, name=name))
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
        place = get_content().locations[char.location].name.get(lang)
        who = describe_character(char, backstory=True)
        char_id, name = char.id, char.name

    narration = await narrator.narrate(llm, lang=lang, scene=scene, character=who, player_text=text,
                                       facts=facts(outcome), user_id=user_id)
    if narration is None and outcome.ok and outcome.events:
        narration = fallbacks.pick("narration", narration_key(intent, outcome, in_combat), lang,
                                   name=name, place=place)
    recorder.action(user_id=user_id, character_id=char_id, text=text, intent=intent.model_dump(),
                    ok=outcome.ok, events=[e.key for e in outcome.events], narration=narration)
    return FreeTextResult(outcome, narration, intent=intent)


def narration_key(intent: Intent, outcome: Outcome, in_combat: bool) -> str:
    """Which generic narration fits (content/fallbacks/narration.yaml)."""
    keys = {event.key for event in outcome.events}
    for status in ("victory", "defeat", "fled"):
        if f"combat.end.{status}" in keys:
            return status
    if "freetext.no_effect" in keys or "freetext.ooc" in keys:
        return "no_effect"
    if in_combat or "combat.start" in keys:
        return "combat"
    if "steal.caught" in keys:
        return "steal_failure"
    if "steal.success" in keys:
        return "steal_success"
    results = [e.params.get("result") for e in outcome.events if e.key == "check.result"]
    if results:
        return "success" if results[-1] == "✅" else "failure"
    return {"move": "travel", "rest": "rest", "use_item": "use_item",
            "quest_action": "quest"}.get(intent.type, "default")


def _combat_item_action(intent: Intent) -> Action:
    """"I throw the fire bomb": a scroll or bomb when the target is one, else a healing potion."""
    item = get_content().items.get(intent.target or "")
    if item is not None and item.combat is not None:
        return Action(kind="item", ability=intent.target)
    return Action(kind="heal_item")


async def resolve(session: AsyncSession, char: Character, enc, intent: Intent, rng: random.Random) -> Outcome:
    """Map a validated intent onto game services. Only engine/services change state."""
    kind = intent.type
    if enc is not None:
        action = {
            "attack": lambda: Action(kind="attack", weapon=intent.weapon, target=intent.target),
            "ability": lambda: Action(kind="ability", ability=intent.ability, target=intent.target),
            "use_item": lambda: _combat_item_action(intent),
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
    if kind in ("skill_check", "environment_interaction"):
        out, _ = await exploration.check_skill(session, char, intent.skill, clamp_tier(intent.tier), rng)
        return out
    if kind == "inspect":
        return await exploration.investigate(session, char, rng)
    if kind == "steal":
        if intent.target not in present:
            return Outcome.refused("freetext.not_here")
        return await npcs.steal(session, char, intent.target, rng)
    if kind == "rest":
        return await activities.start(session, char, "rest", "rest")
    if kind == "quest_action":
        return await quests.perform(session, char, intent.target, present, rng)
    if kind == "ooc_question":
        return Outcome().add("freetext.ooc")
    return Outcome().add("freetext.no_effect")


# ---------------------------------------------------------------- conversation

async def _ai_down_reason(user_id: int) -> str:
    """Which notice fits when the AI gave nothing: the game's daily budget, or no confirmed cause."""
    return "unavailable" if await Budget(get_settings()).allow(user_id) else "budget_exhausted"


def _dialogue_fallback(npc_key: str, lang: str, npc: str, name: str, reason: str,
                       hint: dict | None = None) -> tuple[str, Outcome]:
    """The NPC's line when the AI is out: a quest giver repeats what to do next, the rest say a generic line."""
    if hint:
        line = t(lang, "talk.quest_hint", npc=npc, hint=hint[lang])
    else:
        line = fallbacks.pick("dialogue", npc_key, lang, npc=npc, name=name)
    seed = random.randrange(2**32)
    notice = {language: fallbacks.pick("freetext", reason, language, seed=seed, name=name)
              for language in ("es", "en")}
    return line, Outcome().text(notice)


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
        name = char.name
        hint = await quests.giver_hint(session, char, npc_key)
        if not await Budget(get_settings()).allow(user_id):
            return _dialogue_fallback(npc_key, lang, npc.name.get(lang), name, "budget_exhausted", hint)
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
    if reply is None:  # Gemini down: a generic line in the NPC's voice
        return _dialogue_fallback(npc_key, lang, npc.name.get(lang), name, await _ai_down_reason(user_id), hint)

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
