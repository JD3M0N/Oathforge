"""Single router for in-game buttons (everything except creation)."""

import asyncio
import logging

from sqlalchemy.orm.exc import StaleDataError
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from oathforge.bot import render
from oathforge.bot.handlers.common import (
    current_view, edit_or_send, load, rate_ok, rng, schedule_ready_ping, send, send_chronicle, send_outcome, send_photos,
)
from oathforge.bot.keyboards import btn, cb, markup, parse
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine import gathering
from oathforge.engine.combat import Action, EncounterState, valid_targets
from oathforge.i18n import t
from oathforge.ai.intent_parser import Intent
from oathforge.services import (
    actions, activities, audit, characters, combat_service, exploration, inventory, npcs, quests,
)
from oathforge.services.events import Outcome

log = logging.getLogger(__name__)

# verbs that only show something (no nonce, no state change)
VIEWS = {"scene", "trv", "talkm", "talk", "bye", "inv", "hero", "sheet", "jr", "jrm", "jq", "jrb", "jb", "jrr",
         "shopm", "shop", "sellm", "cbp", "lang", "city", "cls", "clsl", "rep"}


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    verb, arg, n = parse(q.data or "")
    if not rate_ok(context, update.effective_user.id):
        await q.answer(t(context.user_data.get("lang", "es"), "err.rate"), show_alert=False)
        return
    await q.answer()
    try:
        if verb in VIEWS:
            await _view(update, context, verb, arg)
        elif verb == "cb":
            await _combat(update, context, arg, n)
        elif verb == "roll":
            await do_roll(update, context)
        elif verb == "rollset":
            await set_manual_rolls(update, context, arg == "on")
        else:
            await _act(update, context, verb, arg, n)
    except StaleDataError:
        await send(update, t(context.user_data.get("lang", "es"), "err.stale"))


async def _view(update: Update, context, verb: str, arg: str) -> None:
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = user.language
        context.user_data["lang"] = lang
        if verb == "lang":
            if arg in ("es", "en"):
                user.language = lang = context.user_data["lang"] = arg
            if char is None:
                await edit_or_send(update, t(lang, "lang.changed"))
                return
        if verb in ("cls", "clsl"):  # class pages work without a character too
            text, kb = render.class_page(arg, lang, char) if verb == "cls" else render.classes_list(lang)
            await edit_or_send(update, text, kb)
            return
        if char is None:
            await edit_or_send(update, t(lang, "start.need_character"))
            return
        in_combat = char.state != "idle"  # fighting or busy with a field activity: no menus to leave
        loc = get_content().locations[char.location]
        if verb == "city" and not in_combat and loc.hub:
            images = get_content().media.zone_images(loc.zone, exploration.is_night())
            if images:
                await send_photos(session, update, context, images, render.zone_caption(loc.zone, lang))
            text, kb = await current_view(session, char, lang)
            await send(update, text, kb)  # the scene again, so its buttons stay below the photo
            return
        if verb == "sheet":
            images = get_content().media.class_images(char.class_key, char.gender)
            if images:  # portrait first, then the sheet as a new message so its buttons stay below
                await send_photos(session, update, context, images, render.portrait_caption(char, lang))
                text, kb = await render.sheet(session, char, lang)
                await send(update, text, kb)
                return
        talked = None
        if verb == "talk" and not in_combat and arg in exploration.npcs_present(char.location):
            context.user_data["talk"] = arg
            talked = await quests.on_talk(session, char, arg, rng())  # "talk to Bram" objectives
            text, kb = await render.conversation(session, char, arg, lang)
        elif verb == "trv" and not in_combat:
            text, kb = render.travel_menu(char, lang)
        elif verb == "talkm" and not in_combat:
            text, kb = render.talk_menu(char, lang)
        elif verb == "inv":
            text, kb = await render.inventory_view(session, char, lang)
        elif verb == "hero":
            text, kb = await render.hero(session, char, lang)
        elif verb == "sheet":
            text, kb = await render.sheet(session, char, lang)
        elif verb == "jr":
            text, kb = await render.journal(session, char, lang)
        elif verb == "jrm":
            text, kb = await render.missions(session, char, lang)
        elif verb == "jq":
            text, kb = await render.mission(session, char, arg, lang)
        elif verb == "rep":  # "<encounter_id>:<page>", or "-" for the latest battle
            enc_id, _, page = arg.partition(":")
            report = await combat_service.battle_report(session, char, int(enc_id) if enc_id.isdigit() else None)
            text, kb = render.report_page(report, int(page) if page.isdigit() else 0, lang)
        elif verb == "jrb":
            text, kb = render.bestiary_list(char, lang)
        elif verb == "jb":
            text, kb = render.bestiary_entry(char, arg, lang)
        elif verb == "jrr":
            text, kb = await render.rumors(session, lang)
        elif verb == "shopm" and not in_combat:
            text, kb = render.shop_menu(char, lang)
        elif verb == "shop" and not in_combat and arg in exploration.npcs_present(char.location):
            text, kb = await render.shop(session, char, arg, lang)
        elif verb == "sellm" and not in_combat and arg in exploration.npcs_present(char.location):
            text, kb = await render.sell_menu(session, char, arg, lang)
        else:  # scene, cbp, bye, lang, or anything not allowed right now
            if verb == "bye":
                context.user_data.pop("talk", None)
            text, kb = await current_view(session, char, lang)
    if verb == "talk" and talked is not None and talked.events:
        await send_outcome(update, talked, lang)
        await send(update, text, kb)
        return
    await edit_or_send(update, text, kb)


ROLL_VERBS = {"look", "qa"}  # button actions that can wait for a manual /roll
DICE_SECONDS = 3.5  # Telegram's dice animation, before the engine's d20 appears


async def _act(update: Update, context, verb: str, arg: str, n: str, rolled_at: str | None = None) -> None:
    """State-changing, non-combat actions. One transaction, idempotent by nonce.

    With manual rolls on, an action that needs a skill check is parked until the player sends /roll
    (``rolled_at`` is then the location where it was asked, so a roll never lands somewhere else).
    """
    r = rng()
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        lang = context.user_data["lang"] = user.language
        if char is None:
            await send(update, t(lang, "start.need_character"))
            return
        early = None  # (text, kb) answered without acting: a roll to make, or a roll that no longer fits
        if rolled_at is not None and char.location != rolled_at:
            early = (t(lang, "roll.stale"), None)
        elif rolled_at is None and n != "-" and verb in ROLL_VERBS and actions.manual_rolls(user):
            skill = await actions.button_roll(session, char, verb, arg)
            if skill:
                context.user_data["pending_roll"] = {"type": "button", "verb": verb, "arg": arg, "n": n,
                                                     "location": char.location}
                early = roll_prompt(skill, lang)
        if early is None:
            if n == "-" or await audit.claim(session, f"{user.telegram_id}:{n}", user_id=user.id,
                                             character_id=char.id, verb=verb, payload={"arg": arg}) is None:
                text, kb = await current_view(session, char, lang)
                stale = True
            else:
                stale = False
                char_id = char.id
                out = await _dispatch(session, char, verb, arg, r, context)
                text, kb = await _after(session, char, lang, verb, arg, context)
    if early is not None:
        await send(update, *early)
        return
    if stale:
        await send(update, t(lang, "err.stale"))
        await send(update, text, kb)
        return
    if out.events:
        await send_outcome(update, out, lang)
    if out.activity_id:  # a field activity just finished: its chronicle, after the facts
        await send_chronicle(update, context, out.activity_id, lang)
    if verb == "act" and out.ok:
        schedule_ready_ping(update, context, char_id, gathering.SECONDS[arg.partition(":")[0]])
    await send(update, text, kb)


async def _dispatch(session, char, verb: str, arg: str, r, context) -> Outcome:
    present = exploration.npcs_present(char.location)
    if char.state == "in_combat" and verb != "use":
        return Outcome.refused("explore.err.in_combat")
    if verb == "go":
        context.user_data.pop("talk", None)
        return await exploration.travel(session, char, arg, r)
    if verb == "look":
        return await exploration.investigate(session, char, r)
    if verb == "hunt":
        return await exploration.hunt(session, char, r)
    if verb == "rest":
        return await exploration.rest(session, char)
    if verb == "act":  # "<gather|stay|track>:<mastery>"
        kind, _, skill = arg.partition(":")
        return await activities.start(session, char, kind, skill)
    if verb == "actc":
        return await activities.claim(session, char)
    if verb == "actx":
        return await activities.cancel(session, char)
    if verb == "qa":
        return await quests.perform(session, char, arg, present, r)
    if verb == "eq":
        return await inventory.equip(session, char, int(arg)) if arg.isdigit() else Outcome.refused("inv.err.not_found")
    if verb == "use":
        if char.state == "in_combat":
            return Outcome.refused("inv.err.in_combat_use")
        return await inventory.use_item_outside_combat(session, char, arg, r)
    if verb in ("buy", "sell"):
        npc_key, _, what = arg.partition(":")
        if npc_key not in present:
            return Outcome.refused("talk.err.not_here")
        rep = await npcs.reputation_with(session, char, get_content().npcs[npc_key].faction)
        if verb == "buy":
            return await inventory.buy(session, char, npc_key, what, rep)
        if not what.isdigit():
            return Outcome.refused("inv.err.not_found")
        return await inventory.sell(session, char, npc_key, int(what), rep)
    return Outcome.refused("err.unknown")


async def _after(session, char, lang: str, verb: str, arg: str, context):
    """Which view to show after an action."""
    await session.flush()
    if char.state == "in_combat":
        return await current_view(session, char, lang)
    npc = context.user_data.get("talk")
    if verb == "qa" and npc in exploration.npcs_present(char.location):
        return await render.conversation(session, char, npc, lang)
    if verb in ("buy", "sell"):
        npc_key = arg.partition(":")[0]
        if verb == "buy":
            return await render.shop(session, char, npc_key, lang)
        return await render.sell_menu(session, char, npc_key, lang)
    if verb in ("eq", "use"):
        return await render.inventory_view(session, char, lang)
    return await render.scene(session, char, lang)


# ---------------------------------------------------------------- manual rolls

def roll_prompt(skill: str, lang: str):
    name = get_content().skills[skill].name.get(lang)
    return t(lang, "roll.prompt", skill=name), markup([[btn(t(lang, "btn.roll"), cb("roll"))]])


async def do_roll(update: Update, context) -> None:
    """/roll or the 🎲 button: animate Telegram's die, then resolve the parked action with the engine's d20."""
    pending = context.user_data.pop("pending_roll", None)
    if pending is None:
        await roll_settings(update, context)
        return
    try:
        await update.effective_chat.send_dice(emoji="🎲")
        await asyncio.sleep(DICE_SECONDS)
    except Exception:  # the animation is decoration; the roll is the engine's
        log.warning("could not send the dice animation", exc_info=True)
    if pending["type"] == "button":
        await _act(update, context, pending["verb"], pending["arg"], pending["n"], rolled_at=pending["location"])
        return
    from oathforge.bot.handlers.text import show_free_text  # text imports this module

    result = await actions.execute_free_text(context.bot_data["llm"], pending["user_id"], pending["text"],
                                             Intent.model_validate(pending["intent"]), False, rng(),
                                             location=pending["location"])
    await show_free_text(update, context, result)


async def roll_settings(update: Update, context) -> None:
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = context.user_data["lang"] = user.language
        on = actions.manual_rolls(user)
    state = t(lang, "roll.on" if on else "roll.off")
    kb = markup([[btn(t(lang, "btn.roll_off" if on else "btn.roll_on"), cb("rollset", "off" if on else "on"))]])
    await send(update, t(lang, "roll.settings", state=state), kb)


async def set_manual_rolls(update: Update, context, on: bool) -> None:
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = context.user_data["lang"] = user.language
        characters.set_setting(user, "manual_rolls", on)
    if not on:
        context.user_data.pop("pending_roll", None)
    await edit_or_send(update, t(lang, "roll.changed", state=t(lang, "roll.on" if on else "roll.off")))


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await do_roll(update, context)


# ---------------------------------------------------------------- combat

NEEDS_TARGET = {"atk", "abl", "obj"}


async def _combat(update: Update, context, arg: str, n: str) -> None:
    parts = arg.split(":")
    kind = parts[0]
    r = rng()
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        lang = context.user_data["lang"] = user.language
        if char is None:
            return
        enc = await combat_service.active_encounter(session, char, lock=True)
        if enc is None:
            text, kb = await current_view(session, char, lang)
            await edit_or_send(update, text, kb)
            return
        state = EncounterState.model_validate(enc.state)
        me = state.combatants["p1"]

        # A button from an older panel (double click, another turn): show the current panel instead.
        if not fresh_token(n, enc.version, state.turn_index):
            text, kb = render.combat_panel(char, enc.state, lang, version=enc.version)
            await edit_or_send(update, text, kb)
            return

        # Ask for a target first when there is a real choice.
        if kind in NEEDS_TARGET and len(parts) == 2:
            need = _needs_target(state, me, kind, parts[1], combat_service.ability_defs(char))
            if need:
                text, kb = render.combat_panel(char, enc.state, lang, target_menu=arg, version=enc.version)
                await edit_or_send(update, text, kb)
                return

        if await audit.claim(session, f"{user.telegram_id}:{n}", user_id=user.id, character_id=char.id,
                             verb="combat", payload={"arg": arg}) is None:
            text, kb = render.combat_panel(char, enc.state, lang, version=enc.version)
            await edit_or_send(update, text, kb)
            return

        target = parts[2] if len(parts) > 2 else None
        action = {
            "atk": lambda: Action(kind="attack", weapon=parts[1], target=target),
            "abl": lambda: Action(kind="ability", ability=parts[1], target=target),
            "obj": lambda: Action(kind="interact", object=parts[1], target=target),
            "def": lambda: Action(kind="defend"),
            "pot": lambda: Action(kind="heal_item"),
            "mov": lambda: Action(kind="move"),
            "flee": lambda: Action(kind="flee"),
            "end": lambda: Action(kind="end_turn"),
        }.get(kind)
        if action is None:
            return
        out = await combat_service.act(session, char, enc, action(), r)
        await session.flush()  # bumps enc.version, so the new buttons carry it
        text, kb = render.combat_panel(char, enc.state, lang, version=enc.version)
        finished = enc.status != "active"
        # rewards / quest updates appear after the panel; per-hit logs already live in the panel
        summary = Outcome(events=[e for e in out.events if not e.key.startswith("combat.")
                                  or e.key == "combat.defeat_penalty"])
        error = out.error

    if error:  # the callback was already answered, so surface the refusal as a message
        await send(update, "⚠️ " + t(lang, error))
    await edit_or_send(update, text, kb)
    if finished and summary.events:
        await send_outcome(update, summary, lang)
    if finished and out.activity_id:  # an ambushed stay or a tracked prey: the expedition's chronicle
        await send_chronicle(update, context, out.activity_id, lang)


def fresh_token(token: str, version: int | None, turn_index: int) -> bool:
    """Combat buttons carry "<version>.<turn_index>.<nonce>"; anything else is stale."""
    parts = token.split(".")
    return len(parts) == 3 and parts[0] == str(version or 0) and parts[1] == str(turn_index)


def _needs_target(state, me, kind: str, key: str, defs) -> bool:
    if kind == "atk":
        ranged = any(a.key == key and a.ranged for a in me.attacks)
        return len(valid_targets(state, me, ranged)) > 1
    if kind == "abl":
        a = defs.get(key)
        if a is None or a.kind not in ("strike", "spell", "save", "curse"):
            return False
        return len(valid_targets(state, me, ranged=a.kind != "strike")) > 1
    if kind == "obj":
        obj = state.scene_objects.get(key)
        return obj is not None and obj.targets == "one" and len(state.enemies_of(me)) > 1
    return False


def handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(on_callback)
