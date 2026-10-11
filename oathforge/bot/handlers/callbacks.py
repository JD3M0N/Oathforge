"""Single router for in-game buttons (everything except creation)."""

import logging

from sqlalchemy.orm.exc import StaleDataError
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from oathforge.bot import render
from oathforge.bot.handlers.common import current_view, edit_or_send, load, rate_ok, rng, send
from oathforge.bot.keyboards import parse
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine.combat import Action, EncounterState, valid_targets
from oathforge.i18n import t
from oathforge.services import audit, combat_service, exploration, inventory, npcs, quests
from oathforge.services.events import Outcome

log = logging.getLogger(__name__)

# verbs that only show something (no nonce, no state change)
VIEWS = {"scene", "trv", "talkm", "talk", "bye", "inv", "sheet", "jr", "shopm", "shop", "sellm", "cbp", "lang"}


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
        if char is None:
            await edit_or_send(update, t(lang, "start.need_character"))
            return
        in_combat = char.state == "in_combat"
        if verb == "talk" and not in_combat and arg in exploration.npcs_present(char.location):
            context.user_data["talk"] = arg
            text, kb = await render.conversation(session, char, arg, lang)
        elif verb == "trv" and not in_combat:
            text, kb = render.travel_menu(char, lang)
        elif verb == "talkm" and not in_combat:
            text, kb = render.talk_menu(char, lang)
        elif verb == "inv":
            text, kb = await render.inventory_view(session, char, lang)
        elif verb == "sheet":
            text, kb = await render.sheet(session, char, lang)
        elif verb == "jr":
            text, kb = await render.journal(session, char, lang)
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
    await edit_or_send(update, text, kb)


async def _act(update: Update, context, verb: str, arg: str, n: str) -> None:
    """State-changing, non-combat actions. One transaction, idempotent by nonce."""
    r = rng()
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        lang = context.user_data["lang"] = user.language
        if char is None:
            await send(update, t(lang, "start.need_character"))
            return
        if n == "-" or await audit.claim(session, f"{user.telegram_id}:{n}", user_id=user.id,
                                         character_id=char.id, verb=verb, payload={"arg": arg}) is None:
            text, kb = await current_view(session, char, lang)
            stale = True
        else:
            stale = False
            out = await _dispatch(session, char, verb, arg, r, context)
            text, kb = await _after(session, char, lang, verb, arg, context)
    if stale:
        await send(update, t(lang, "err.stale"))
        await send(update, text, kb)
        return
    if out.events:
        await send(update, render.outcome_text(out, lang))
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
    if verb == "rest":
        return await exploration.rest(session, char)
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

        # Ask for a target first when there is a real choice.
        if kind in NEEDS_TARGET and len(parts) == 2:
            need = _needs_target(state, me, kind, parts[1], combat_service.ability_defs(char))
            if need:
                text, kb = render.combat_panel(char, enc.state, lang, target_menu=arg)
                await edit_or_send(update, text, kb)
                return

        if await audit.claim(session, f"{user.telegram_id}:{n}", user_id=user.id, character_id=char.id,
                             verb="combat", payload={"arg": arg}) is None:
            text, kb = render.combat_panel(char, enc.state, lang)
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
        await session.flush()
        text, kb = render.combat_panel(char, enc.state, lang)
        finished = enc.status != "active"
        # rewards / quest updates appear after the panel; per-hit logs already live in the panel
        summary = Outcome(events=[e for e in out.events if not e.key.startswith("combat.")
                                  or e.key == "combat.defeat_penalty"])
        error = out.error

    if error:  # the callback was already answered, so surface the refusal as a message
        await send(update, "⚠️ " + t(lang, error))
    await edit_or_send(update, text, kb)
    if finished and summary.events:
        await send(update, render.outcome_text(summary, lang))


def _needs_target(state, me, kind: str, key: str, defs) -> bool:
    if kind == "atk":
        ranged = any(a.key == key and a.ranged for a in me.attacks)
        return len(valid_targets(state, me, ranged)) > 1
    if kind == "abl":
        a = defs.get(key)
        if a is None or a.kind not in ("strike", "spell"):
            return False
        return len(valid_targets(state, me, ranged=a.kind == "spell")) > 1
    if kind == "obj":
        obj = state.scene_objects.get(key)
        return obj is not None and obj.targets == "one" and len(state.enemies_of(me)) > 1
    return False


def handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(on_callback)
